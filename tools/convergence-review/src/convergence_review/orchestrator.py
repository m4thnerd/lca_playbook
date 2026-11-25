from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

from .coder import build_coder_prompt, build_initial_coder_prompt, run_coder
from .convergence import (
    BLOCKING_SEVERITIES,
    SEVERITY_ORDER,
    check_convergence,
    format_category_counts,
    format_severity_list,
    format_severity_counts,
    format_summary,
    severity_delta,
    summarize_issues,
)
from .reviewers import (
    ReviewerSpec,
    ROLE_CONFIGS,
    build_reviewer_prompt,
    format_reviewer_specs,
    reviewer_backend_name,
    run_reviewers,
)


_SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITY_ORDER)}


_ANSI_RESET = "\033[0m"
_REVIEWER_COLOR_CODES: dict[str, str] = {
    "claude": "\033[38;5;208m",  # orange
    "codex": "\033[34m",  # blue
    "gemini": "\033[32m",  # green
    "grok": "\033[38;5;141m",  # purple
}


def _supports_color() -> bool:
    return sys.stdout.isatty()


def _color(text: str, code: str) -> str:
    if not _supports_color():
        return text
    return f"{code}{text}{_ANSI_RESET}"


def _color_reviewer(text: str, agent_name: str) -> str:
    code = _REVIEWER_COLOR_CODES.get(reviewer_backend_name(agent_name))
    if not code:
        return text
    return _color(text, code)


def _role_group(role_name: str) -> str:
    if role_name == "architecture":
        return "architecture"
    if role_name == "core":
        return "core"
    return "persona"


def _issue_role(issue: dict) -> str | None:
    return issue.get("reviewer_role") or issue.get("role")


def _issue_is_blocking_role(issue: dict) -> bool:
    return _issue_role(issue) in {"architecture", "core"}


def _blocking_results(review_results) -> list:
    return [r for r in review_results if not r.is_persona]


def _annotated_issues(result) -> list[dict]:
    issues = []
    for issue in result.issues:
        annotated = dict(issue)
        annotated["reviewer"] = result.label
        annotated["reviewer_agent"] = result.agent_name
        annotated["reviewer_role"] = result.role_name
        issues.append(annotated)
    return issues


def _normalize_deferred_reviewer(deferral: dict) -> None:
    reviewer = deferral.get("reviewer")
    agent = deferral.get("agent")
    role = deferral.get("role")
    if (not agent or not role) and isinstance(reviewer, str) and ":" in reviewer:
        parsed_agent, parsed_role = reviewer.split(":", 1)
        deferral.setdefault("agent", parsed_agent)
        deferral.setdefault("role", parsed_role)
    if deferral.get("agent") and deferral.get("role"):
        deferral["reviewer"] = f"{deferral['agent']}:{deferral['role']}"


_INSERTIONS_RE = re.compile(r"(\d+\s+insertions?\(\+\))")
_DELETIONS_RE = re.compile(r"(\d+\s+deletions?\(-\))")


def _colorize_shortstat(shortstat: str) -> str:
    if not _supports_color():
        return shortstat
    shortstat = _INSERTIONS_RE.sub(f"\033[32m\\1{_ANSI_RESET}", shortstat)
    shortstat = _DELETIONS_RE.sub(f"\033[31m\\1{_ANSI_RESET}", shortstat)
    return shortstat


def _issue_sort_key(issue: dict) -> tuple[int, str]:
    """Sort issues by severity (critical first), then file path for stable grouping."""
    sev = issue.get("severity", "")
    return (_SEVERITY_RANK.get(sev, len(SEVERITY_ORDER)), str(issue.get("file", "")))


def _format_issue_line(issue: dict, max_desc: int = 210) -> str:
    severity = issue.get("severity", "?")
    file = issue.get("file", "general") or "general"
    rg_id = issue.get("review_guideline_id")
    tag = f" [{rg_id}]" if rg_id else ""
    desc = (issue.get("description", "") or "").strip().replace("\n", " ")
    if len(desc) > max_desc:
        desc = desc[: max_desc - 1].rstrip() + "…"
    return f"[{severity}]{tag} {file}: {desc}"


def _fmt_duration(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _git_snapshot(cwd: Path) -> str | None:
    """Capture a tree snapshot (including uncommitted + untracked) so we can diff against it later.

    Uses `git stash create -u` which creates a commit object without touching the working tree or
    stash list. Returns the commit SHA, or HEAD if there are no changes, or None on failure.
    """
    try:
        snap = subprocess.run(
            ["git", "stash", "create", "-u"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        sha = snap.stdout.strip()
        if sha:
            return sha
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return head.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        return None


def _git_diff_info(cwd: Path, snapshot: str) -> dict | None:
    """Return structured diff info vs a prior snapshot.

    Returns a dict with:
        - shortstat: str (empty string when no changes)
        - files_touched: list of {"path": str, "changes": int}
    Returns None on any git failure so the caller can skip silently.
    """
    try:
        shortstat = subprocess.run(
            ["git", "diff", "--shortstat", snapshot],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()

        stat_lines = (
            subprocess.run(
                ["git", "diff", "--stat", snapshot],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            .stdout.strip()
            .splitlines()
        )
    except (subprocess.SubprocessError, OSError):
        return None

    files_touched: list[dict] = []
    for row in stat_lines[:-1] if stat_lines else []:
        if "|" not in row:
            continue
        path, _, rest = row.partition("|")
        path = path.strip()
        num = ""
        for ch in rest.strip():
            if ch.isdigit():
                num += ch
            else:
                break
        if num:
            files_touched.append({"path": path, "changes": int(num)})

    files_touched.sort(key=lambda f: f["changes"], reverse=True)

    return {"shortstat": shortstat, "files_touched": files_touched}


def _format_diff_lines(diff_info: dict) -> list[str]:
    """Human-readable printable lines derived from _git_diff_info output."""
    if not diff_info["shortstat"]:
        return ["Coder changes: none"]
    lines = [f"Coder changes: {_colorize_shortstat(diff_info['shortstat'])}"]
    top = diff_info["files_touched"][:3]
    if top:
        top_str = ", ".join(f"{f['path']} ({f['changes']})" for f in top)
        lines.append(f"Top files: {top_str}")
    return lines


_CODER_DECISIONS_RE = re.compile(
    r"CODER_DECISIONS\s*\n\s*```(?:json)?\s*\n(.*?)```",
    re.DOTALL,
)


def _parse_coder_decisions(output: str) -> dict | None:
    """Extract the CODER_DECISIONS JSON block from coder output.

    Returns the parsed dict, or None if the block is absent or unparseable.
    """
    match = _CODER_DECISIONS_RE.search(output)
    if match:
        text = match.group(1).strip()
    else:
        idx = output.rfind("CODER_DECISIONS")
        if idx == -1:
            return None
        text = output[idx + len("CODER_DECISIONS") :].strip().lstrip(":")
        fence = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()
        elif text.startswith("{"):
            end = text.rfind("}")
            if end != -1:
                text = text[: end + 1]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None
    return parsed


@dataclass
class Config:
    design_doc_content: str
    role_guidelines: dict[str, str]
    coder_agent: str
    max_iterations: int
    cwd: Path
    artifacts_dir: Path
    start_phase: str = "implementation"
    reviewers: tuple[ReviewerSpec, ...] = ()


def _consolidate_reviews(review_results) -> str:
    """Format reviewer findings by influence tier for the coder."""
    sections = []
    groups = [
        (
            "architecture",
            "ARCHITECTURE TIER",
            (
                "Architecture-critic findings are senior architecture direction. "
                "Act on each finding or explicitly defer it with rationale."
            ),
        ),
        (
            "core",
            "CORE TIER",
            "Core reviewer findings block convergence at configured blocking severities.",
        ),
        (
            "persona",
            "PERSONA TIER",
            (
                "Persona findings are advisory stakeholder perspective. Act only when "
                "the fix is cheap and clearly beneficial; persona issues never block convergence."
            ),
        ),
    ]
    for group_name, title, framing in groups:
        group_results = [
            result
            for result in review_results
            if _role_group(result.role_name) == group_name
        ]
        if not group_results:
            continue
        sections.append(f"=== {title} ===")
        sections.append(framing)
        sections.append("")
        for result in group_results:
            sections.append(f"--- {result.label} reviewer ---")
            if result.infrastructure_status != "complete":
                sections.append(
                    "Reviewer infrastructure status: "
                    f"{result.infrastructure_status}. Findings are unavailable and "
                    "must not be treated as a clean review or a code defect."
                )
                if result.status_detail:
                    sections.append(f"Detail: {result.status_detail}")
            elif result.issues:
                sections.append(json.dumps(_annotated_issues(result), indent=2))
            else:
                sections.append("[]")
            if result.assessment:
                sections.append(f"Assessment: {result.assessment}")
            sections.append("")
    return "\n".join(sections)


def _review_incomplete_reason(review_results) -> str | None:
    incomplete = [
        f"{result.label} {result.infrastructure_status}"
        + (f": {result.status_detail}" if result.status_detail else "")
        for result in review_results
        if result.infrastructure_status != "complete"
    ]

    if not incomplete:
        return None
    return "; ".join(incomplete)


def _must_skip_coder_for_incomplete_blocking_review(review_results) -> bool:
    return any(result.infrastructure_status != "complete" for result in review_results)


def _write_repair_artifacts(
    iteration_dir: Path,
    iteration: int,
    prefix: str,
    repair_attempts: list,
) -> list[dict]:
    """Write one repair attempt sequence's raw+meta files; return manifest entries."""
    manifest_entries: list[dict] = []
    for repair_index, repair in enumerate(repair_attempts, 1):
        repair_raw_name = f"{prefix}_repair_attempt_{repair_index}_raw.txt"
        repair_meta_name = f"{prefix}_repair_attempt_{repair_index}_meta.json"
        (iteration_dir / repair_raw_name).write_text(repair.raw_output)
        (iteration_dir / repair_meta_name).write_text(
            json.dumps(
                {
                    "attempt": repair_index,
                    "issue_count": len(repair.issues),
                    "parse_error": repair.parse_error,
                    "timed_out": repair.timed_out,
                    "returncode": repair.returncode,
                    "elapsed_s": round(repair.elapsed_s, 2),
                },
                indent=2,
            )
        )
        manifest_entries.append(
            {
                "attempt": repair_index,
                "raw": f"iteration_{iteration:02d}/{repair_raw_name}",
                "meta": f"iteration_{iteration:02d}/{repair_meta_name}",
            }
        )
    return manifest_entries


def _write_manifest(run_dir: Path, manifest: dict) -> None:
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))


def _snapshot_inputs(
    run_dir: Path, config: Config, reviewer_prompts: dict[str, str]
) -> dict:
    """Copy design doc, review guidelines, and the rendered reviewer prompt into inputs/.

    Returns the `inputs` block for the run manifest.
    """
    inputs_dir = run_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)

    (inputs_dir / "design_doc.md").write_text(config.design_doc_content)
    inputs_block: dict = {"design_doc": "inputs/design_doc.md"}

    guidelines_dir = inputs_dir / "role_guidelines"
    guidelines_dir.mkdir()
    inputs_block["role_guidelines"] = {}
    for role, content in sorted(config.role_guidelines.items()):
        filename = f"{role}.md"
        (guidelines_dir / filename).write_text(content)
        inputs_block["role_guidelines"][role] = f"inputs/role_guidelines/{filename}"

    prompts_dir = inputs_dir / "reviewer_prompts"
    prompts_dir.mkdir()
    inputs_block["reviewer_prompts"] = {}
    for stem, prompt in sorted(reviewer_prompts.items()):
        filename = f"{stem}.txt"
        (prompts_dir / filename).write_text(prompt)
        inputs_block["reviewer_prompts"][stem] = f"inputs/reviewer_prompts/{filename}"

    return inputs_block


async def run_convergence_loop(config: Config) -> None:
    """Execute the main convergence review loop."""
    iteration_results: list[dict] = []
    deferred_issues: list[dict] = []
    run_started_at = _now_iso()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = config.artifacts_dir / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"  artifacts dir: {run_dir}")

    (run_dir / "run_config.json").write_text(
        json.dumps(
            {
                "coder": config.coder_agent,
                "reviewers": [spec.label for spec in config.reviewers],
                "max_iterations": config.max_iterations,
                "cwd": str(config.cwd),
                "artifacts_dir": str(run_dir),
                "roles": {
                    role: {"tier": ROLE_CONFIGS[role]["tier"]}
                    for role in sorted(config.role_guidelines)
                },
            },
            indent=2,
        )
    )

    # Build base reviewer prompts (no deferrals) for inputs snapshot.
    base_reviewer_prompts = {
        spec.artifact_stem: build_reviewer_prompt(
            config.design_doc_content,
            config.role_guidelines[spec.role_name],
            role_name=spec.role_name,
        )
        for spec in config.reviewers
    }
    inputs_block = _snapshot_inputs(run_dir, config, base_reviewer_prompts)

    manifest: dict = {
        "run_id": run_id,
        "started_at": run_started_at,
        "ended_at": None,
        "status": "in_progress",
        "iterations_completed": 0,
        "start_phase": config.start_phase,
        "coder": config.coder_agent,
        "reviewers": [spec.label for spec in config.reviewers],
        "max_iterations": config.max_iterations,
        "role_guidelines": {
            role: ROLE_CONFIGS[role]["guidelines"]
            for role in sorted(config.role_guidelines)
        },
        "design_doc_sha256": _sha256(config.design_doc_content),
        "role_guidelines_sha256": {
            role: _sha256(content)
            for role, content in sorted(config.role_guidelines.items())
        },
        "cwd": str(config.cwd),
        "inputs": inputs_block,
        "initial_implementation": None,
        "iterations": [],
        "summary": None,
    }
    _write_manifest(run_dir, manifest)

    prev_severity: dict[str, int] | None = None
    coder_stopped = False
    stop_category: str | None = None
    stop_reason: str | None = None

    if config.start_phase == "implementation":
        print(f"\n{'=' * 60}")
        print("  Initial implementation")
        print(f"{'=' * 60}")
        print(f"\n  Running coder ({config.coder_agent})...")

        initial_dir = run_dir / "initial_implementation"
        initial_dir.mkdir(parents=True, exist_ok=True)

        initial_prompt = build_initial_coder_prompt(
            config.design_doc_content,
        )
        (initial_dir / "coder_prompt.txt").write_text(initial_prompt)

        snapshot_before = _git_snapshot(config.cwd)
        initial_started_at = _now_iso()
        initial_start = time.monotonic()
        initial_result = await run_coder(config.coder_agent, initial_prompt, config.cwd)
        initial_elapsed = time.monotonic() - initial_start
        initial_ended_at = _now_iso()

        (initial_dir / "coder_output.txt").write_text(initial_result.output)
        print(f"    Coder finished in {_fmt_duration(initial_elapsed)}.")

        snapshot_after = _git_snapshot(config.cwd)
        diff_info = (
            _git_diff_info(config.cwd, snapshot_before) if snapshot_before else None
        )
        if diff_info is not None:
            for line in _format_diff_lines(diff_info):
                print(f"    {line}")

        initial_decisions = _parse_coder_decisions(initial_result.output)
        if initial_decisions:
            (initial_dir / "coder_decisions.json").write_text(
                json.dumps(initial_decisions, indent=2)
            )
            if initial_decisions.get("stop_run"):
                stop_category = initial_decisions.get("stop_category") or "unspecified"
                stop_reason = (
                    initial_decisions.get("stop_reason") or "(no reason given)"
                )
                print(
                    f"\n  Coder escalated for human review "
                    f"[{stop_category}]: {stop_reason}"
                )
                coder_stopped = True

        initial_meta = {
            "started_at": initial_started_at,
            "ended_at": initial_ended_at,
            "elapsed_s": round(initial_elapsed, 2),
            "snapshot_before": snapshot_before,
            "snapshot_after": snapshot_after,
            "returncode": initial_result.returncode,
            "diff_shortstat": diff_info["shortstat"] if diff_info else None,
            "files_touched": diff_info["files_touched"] if diff_info else None,
            "coder_decisions": initial_decisions,
        }
        (initial_dir / "meta.json").write_text(json.dumps(initial_meta, indent=2))

        manifest["initial_implementation"] = {
            "dir": "initial_implementation",
            "meta": "initial_implementation/meta.json",
            "prompt": "initial_implementation/coder_prompt.txt",
            "output": "initial_implementation/coder_output.txt",
        }
        _write_manifest(run_dir, manifest)

    iteration_range = (
        range(1, config.max_iterations + 1) if not coder_stopped else range(0)
    )
    for iteration in iteration_range:
        print(f"\n{'=' * 60}")
        print(f"  Iteration {iteration}/{config.max_iterations}")
        print(f"{'=' * 60}")
        iteration_dir = run_dir / f"iteration_{iteration:02d}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        iter_started_at = _now_iso()

        # Build per-iteration reviewer prompts (include deferrals from prior iterations).
        final_reviewer_iteration = iteration >= config.max_iterations
        reviewer_prompts = {
            spec.artifact_stem: build_reviewer_prompt(
                config.design_doc_content,
                config.role_guidelines[spec.role_name],
                role_name=spec.role_name,
                deferred_issues=deferred_issues or None,
                final_iteration=final_reviewer_iteration,
            )
            for spec in config.reviewers
        }
        prompts_dir = iteration_dir / "reviewer_prompts"
        prompts_dir.mkdir()
        for stem, prompt in reviewer_prompts.items():
            (prompts_dir / f"{stem}.txt").write_text(prompt)

        # Phase 1: Concurrent review
        print(
            f"\n  Phase 1: Running reviewers ({format_reviewer_specs(config.reviewers)})..."
        )
        phase1_started_at = _now_iso()
        phase1_start = time.monotonic()
        review_results = await run_reviewers(
            config.design_doc_content,
            config.cwd,
            reviewer_specs=config.reviewers,
            role_guidelines=config.role_guidelines,
            deferred_issues=deferred_issues or None,
            iteration_dir=iteration_dir,
            final_iteration=final_reviewer_iteration,
        )
        phase1_elapsed = time.monotonic() - phase1_start
        phase1_ended_at = _now_iso()

        reviewer_manifest: dict[str, dict] = {}
        reviewer_meta_list: list[dict] = []

        name_width = max((len(r.label) for r in review_results), default=6)
        for r in review_results:
            summary = summarize_issues(r.issues)
            sev_str = format_severity_counts(summary["severity"])
            cat_str = format_category_counts(summary["category"])
            tail = f"  ({cat_str})" if cat_str else ""
            repair_note = "  [repaired]" if r.parse_repaired else ""
            status_note = (
                f"  [{r.infrastructure_status}]"
                if r.infrastructure_status != "complete"
                else ""
            )
            retry_note = f"  [retried {r.retry_count}x]" if r.retry_count else ""
            header_line = (
                f"    {r.label:<{name_width}}  {summary['total']:>3} issues  "
                f"[{sev_str}]{tail}{repair_note}{status_note}{retry_note}"
            )
            print(_color_reviewer(header_line, r.agent_name))

            for issue in sorted(r.issues, key=_issue_sort_key):
                print(f"      {_format_issue_line(issue)}")

            if not r.issues:
                print()

            stem = r.artifact_stem
            (iteration_dir / f"{stem}_raw.txt").write_text(r.raw_output)
            (iteration_dir / f"{stem}_stderr.txt").write_text(r.stderr_output)
            (iteration_dir / f"{stem}_issues.json").write_text(
                json.dumps(r.issues, indent=2)
            )
            review_attempt_manifest: list[dict] = []
            for attempt_index, attempt in enumerate(r.prior_attempts, 1):
                attempt_raw_name = f"{stem}_review_attempt_{attempt_index}_raw.txt"
                attempt_stderr_name = (
                    f"{stem}_review_attempt_{attempt_index}_stderr.txt"
                )
                attempt_meta_name = f"{stem}_review_attempt_{attempt_index}_meta.json"
                (iteration_dir / attempt_raw_name).write_text(attempt.raw_output)
                (iteration_dir / attempt_stderr_name).write_text(attempt.stderr_output)
                attempt_meta = {
                    "attempt": attempt_index,
                    "infrastructure_status": attempt.infrastructure_status,
                    "status_detail": attempt.status_detail,
                    "parse_repaired": attempt.parse_repaired,
                    "repair_attempts": len(attempt.repair_attempts),
                    "returncode": attempt.returncode,
                    "elapsed_s": round(attempt.elapsed_s, 2),
                }
                (iteration_dir / attempt_meta_name).write_text(
                    json.dumps(attempt_meta, indent=2)
                )
                attempt_entry = {
                    "attempt": attempt_index,
                    "raw": f"iteration_{iteration:02d}/{attempt_raw_name}",
                    "stderr": f"iteration_{iteration:02d}/{attempt_stderr_name}",
                    "meta": f"iteration_{iteration:02d}/{attempt_meta_name}",
                }
                prior_repair_manifest = _write_repair_artifacts(
                    iteration_dir,
                    iteration,
                    f"{stem}_review_attempt_{attempt_index}",
                    attempt.repair_attempts,
                )
                if prior_repair_manifest:
                    attempt_entry["repair_attempts"] = prior_repair_manifest
                review_attempt_manifest.append(attempt_entry)
            repair_manifest = _write_repair_artifacts(
                iteration_dir,
                iteration,
                stem,
                r.repair_attempts,
            )
            reviewer_meta = {
                "agent": r.agent_name,
                "role": r.role_name,
                "label": r.label,
                "tier": r.tier,
                "issue_count": summary["total"],
                "assessment": r.assessment,
                "infrastructure_status": r.infrastructure_status,
                "status_detail": r.status_detail,
                "parse_error": r.parse_error,
                "parse_repaired": r.parse_repaired,
                "repair_attempts": len(r.repair_attempts),
                "timed_out": r.timed_out,
                "retry_count": r.retry_count,
                "returncode": r.returncode,
                "elapsed_s": round(r.elapsed_s, 2),
            }
            (iteration_dir / f"{stem}_meta.json").write_text(
                json.dumps(reviewer_meta, indent=2)
            )
            reviewer_meta_list.append(reviewer_meta)
            reviewer_manifest[stem] = {
                "raw": f"iteration_{iteration:02d}/{stem}_raw.txt",
                "stderr": f"iteration_{iteration:02d}/{stem}_stderr.txt",
                "issues": f"iteration_{iteration:02d}/{stem}_issues.json",
                "meta": f"iteration_{iteration:02d}/{stem}_meta.json",
            }
            if repair_manifest:
                reviewer_manifest[stem]["repair_attempts"] = repair_manifest
            if review_attempt_manifest:
                reviewer_manifest[stem]["prior_review_attempts"] = (
                    review_attempt_manifest
                )

        print(f"  Phase 1 done in {_fmt_duration(phase1_elapsed)}")

        all_issues = []
        for r in review_results:
            all_issues.extend(_annotated_issues(r))
        convergence_issues = [i for i in all_issues if _issue_is_blocking_role(i)]

        iter_summary = summarize_issues(all_issues)
        totals_str = format_severity_counts(iter_summary["severity"])
        delta_str = ""
        if prev_severity is not None:
            d = severity_delta(iter_summary["severity"], prev_severity)
            delta_str = f"   (Δ vs prev: {d})" if d else "   (Δ vs prev: no change)"
        print(f"  Iteration {iteration} totals: {totals_str}{delta_str}")
        prev_severity = iter_summary["severity"]

        review_incomplete_reason = _review_incomplete_reason(
            _blocking_results(review_results)
        )
        review_incomplete = review_incomplete_reason is not None
        if review_incomplete_reason:
            print(f"  Review incomplete: {review_incomplete_reason}")

        converged = (not review_incomplete) and check_convergence(convergence_issues)

        iteration_results.append(
            {
                "iteration": iteration,
                "issues": all_issues,
                "convergence_issues": convergence_issues,
                "roles_run": [spec.role_name for spec in config.reviewers],
                "assessments": [
                    {
                        "reviewer": r.label,
                        "agent": r.agent_name,
                        "role": r.role_name,
                        "assessment": r.assessment,
                    }
                    for r in review_results
                    if r.assessment
                ],
                "reviewer_statuses": [
                    {
                        "reviewer": r.label,
                        "agent": r.agent_name,
                        "role": r.role_name,
                        "infrastructure_status": r.infrastructure_status,
                        "status_detail": r.status_detail,
                        "retry_count": r.retry_count,
                    }
                    for r in review_results
                ],
                "converged": converged,
                "review_incomplete": review_incomplete,
                "review_incomplete_reason": review_incomplete_reason,
            }
        )

        consolidated = _consolidate_reviews(review_results)
        (iteration_dir / "coder_input.txt").write_text(consolidated)

        # Phase 2: Coder fix (skipped when converged or on the final iteration)
        phase_2: dict = {"ran": False}
        coder_manifest: dict = {
            "prompt": None,
            "output": None,
            "ran": False,
            "skip_reason": None,
        }
        decisions: dict | None = None

        stop_for_incomplete_blocking_review = (
            _must_skip_coder_for_incomplete_blocking_review(
                _blocking_results(review_results)
            )
        )

        if stop_for_incomplete_blocking_review:
            print(
                "\n  Review incomplete — at least one blocking reviewer did not "
                "produce output that can be shared with the coder."
            )
            phase_2["skip_reason"] = "review_incomplete"
            coder_manifest["skip_reason"] = "review_incomplete"
        elif converged:
            blocking = format_severity_list(BLOCKING_SEVERITIES)
            print(f"\n  Converged — no {blocking} issues found.")
            phase_2["skip_reason"] = "converged"
            coder_manifest["skip_reason"] = "converged"
        elif iteration >= config.max_iterations:
            (iteration_dir / "coder_output.txt").write_text(
                "SKIPPED: Final iteration reached; coder not run so summary reflects final reviewed state.\n"
            )
            print(
                "\n  Phase 2: Skipped coder on final iteration to keep summary "
                "aligned with final reviewed state."
            )
            phase_2["skip_reason"] = "final_iteration"
            coder_manifest["skip_reason"] = "final_iteration"
            coder_manifest["output"] = f"iteration_{iteration:02d}/coder_output.txt"
        else:
            print(f"\n  Phase 2: Running coder ({config.coder_agent})...")
            snapshot = _git_snapshot(config.cwd)
            coder_prompt = build_coder_prompt(
                config.design_doc_content,
                consolidated,
                deferred_issues=deferred_issues or None,
            )
            (iteration_dir / "coder_prompt.txt").write_text(coder_prompt)

            phase2_started_at = _now_iso()
            phase2_start = time.monotonic()
            coder_result = await run_coder(config.coder_agent, coder_prompt, config.cwd)
            phase2_elapsed = time.monotonic() - phase2_start
            phase2_ended_at = _now_iso()

            (iteration_dir / "coder_output.txt").write_text(coder_result.output)
            print(f"    Coder finished in {_fmt_duration(phase2_elapsed)}.")

            post_snapshot = _git_snapshot(config.cwd)
            diff_info = _git_diff_info(config.cwd, snapshot) if snapshot else None
            if diff_info is not None:
                for line in _format_diff_lines(diff_info):
                    print(f"    {line}")

            phase_2 = {
                "ran": True,
                "started_at": phase2_started_at,
                "ended_at": phase2_ended_at,
                "elapsed_s": round(phase2_elapsed, 2),
                "snapshot_before": snapshot,
                "snapshot_after": post_snapshot,
                "returncode": coder_result.returncode,
                "diff_shortstat": diff_info["shortstat"] if diff_info else None,
                "files_touched": diff_info["files_touched"] if diff_info else None,
            }
            coder_manifest = {
                "ran": True,
                "prompt": f"iteration_{iteration:02d}/coder_prompt.txt",
                "output": f"iteration_{iteration:02d}/coder_output.txt",
                "skip_reason": None,
            }

            # Parse coder decisions (stop_run, deferred issues)
            decisions = _parse_coder_decisions(coder_result.output)
            if decisions:
                (iteration_dir / "coder_decisions.json").write_text(
                    json.dumps(decisions, indent=2)
                )
                new_deferrals = decisions.get("deferred_issues") or []
                if new_deferrals:
                    for d in new_deferrals:
                        d["iteration"] = iteration
                        _normalize_deferred_reviewer(d)
                    deferred_issues.extend(new_deferrals)
                    (run_dir / "deferred_issues.json").write_text(
                        json.dumps(deferred_issues, indent=2)
                    )
                    print(
                        f"    Coder deferred {len(new_deferrals)} issue(s) for human review:"
                    )
                    for d in new_deferrals:
                        summ = d.get("summary", "(no summary)")[:120]
                        print(f"      {summ}")

                if decisions.get("stop_run"):
                    stop_category = decisions.get("stop_category") or "unspecified"
                    stop_reason = decisions.get("stop_reason") or "(no reason given)"
                    print(
                        f"\n  Coder escalated for human review "
                        f"[{stop_category}]: {stop_reason}"
                    )
                    coder_stopped = True

        iter_ended_at = _now_iso()

        iteration_meta = {
            "iteration": iteration,
            "started_at": iter_started_at,
            "ended_at": iter_ended_at,
            "phase_1": {
                "started_at": phase1_started_at,
                "ended_at": phase1_ended_at,
                "elapsed_s": round(phase1_elapsed, 2),
                "reviewers": reviewer_meta_list,
            },
            "phase_2": phase_2,
            "severity_totals": iter_summary["severity"],
            "convergence_severity_totals": summarize_issues(convergence_issues)[
                "severity"
            ],
            "converged": converged,
            "review_incomplete": review_incomplete,
            "review_incomplete_reason": review_incomplete_reason,
            "coder_decisions": decisions,
            "deferred_issues_total": len(deferred_issues),
        }
        (iteration_dir / "iteration_meta.json").write_text(
            json.dumps(iteration_meta, indent=2)
        )

        manifest["iterations"].append(
            {
                "index": iteration,
                "dir": f"iteration_{iteration:02d}",
                "meta": f"iteration_{iteration:02d}/iteration_meta.json",
                "coder_input": f"iteration_{iteration:02d}/coder_input.txt",
                "reviewers": reviewer_manifest,
                "coder": coder_manifest,
            }
        )
        manifest["iterations_completed"] = iteration
        _write_manifest(run_dir, manifest)

        if converged or coder_stopped or stop_for_incomplete_blocking_review:
            break

    # Final summary
    summary = format_summary(
        iteration_results,
        deferred_issues=deferred_issues,
        coder_stopped=coder_stopped,
        stop_category=stop_category,
        stop_reason=stop_reason,
        review_incomplete=(
            bool(iteration_results)
            and bool(iteration_results[-1].get("review_incomplete"))
            and not coder_stopped
        ),
        review_incomplete_reason=(
            iteration_results[-1].get("review_incomplete_reason")
            if iteration_results
            else None
        ),
    )
    (run_dir / "summary.txt").write_text(summary)
    (run_dir / "summary.json").write_text(json.dumps(iteration_results, indent=2))
    print(summary)

    if coder_stopped:
        manifest["status"] = "coder_stopped"
        manifest["stop_category"] = stop_category
        manifest["stop_reason"] = stop_reason
    elif iteration_results and iteration_results[-1]["converged"]:
        manifest["status"] = "converged"
    elif iteration_results and iteration_results[-1].get("review_incomplete"):
        manifest["status"] = "review_incomplete"
        manifest["review_incomplete_reason"] = iteration_results[-1].get(
            "review_incomplete_reason"
        )
    else:
        manifest["status"] = "max_iterations"
    manifest["ended_at"] = _now_iso()
    manifest["summary"] = {
        "summary_txt": "summary.txt",
        "summary_json": "summary.json",
    }
    if deferred_issues:
        manifest["deferred_issues"] = "deferred_issues.json"
        manifest["deferred_issues_count"] = len(deferred_issues)
    _write_manifest(run_dir, manifest)

    print(f"\n  Run manifest: {run_dir / 'run_manifest.json'}")
    if deferred_issues:
        print(f"  Deferred issues file: {run_dir / 'deferred_issues.json'}")
