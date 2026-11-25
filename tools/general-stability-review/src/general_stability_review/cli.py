from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .llm_config_loader import llm_config


REVIEWER_TIMEOUT = 20 * 60
# Staff Engineer passes trace consumers across the repository and routinely run
# 10-17 minutes on a mid-sized Django repo (measured 2026-10-29), so they get more headroom.
STAFF_REVIEWER_TIMEOUT = 30 * 60
KNOWN_REVIEWERS = llm_config.GENERAL_STABILITY_AVAILABLE_REVIEWERS

REVIEWER_COMMANDS: dict[str, list[str]] = {
    name: list(command)
    for name, command in llm_config.GENERAL_STABILITY_REVIEWER_COMMANDS.items()
}
STAFF_REVIEWER_COMMANDS: dict[str, list[str]] = {
    name: list(command)
    for name, command in llm_config.STAFF_ENGINEER_REVIEWER_COMMANDS.items()
}
DEFAULT_REVIEWER_BY_MODE = {
    "gsr": llm_config.GENERAL_STABILITY_REVIEW_DEFAULT_REVIEWER,
    "staff-engineer": llm_config.STAFF_ENGINEER_DEFAULT_REVIEWER,
}


@dataclass
class GitContext:
    repo_root: Path
    base_ref: str
    branch: str
    head: str
    merge_base: str | None
    shortstat: str
    name_status: str
    worktree_status: str


@dataclass
class ReviewRun:
    reviewer: str
    command: list[str]
    raw_output: str
    stderr: str
    elapsed_s: float
    returncode: int | None
    timed_out: bool = False
    worktree_status_before: str = ""
    worktree_status_after: str = ""

    @property
    def worktree_mutated(self) -> bool:
        return self.worktree_status_before != self.worktree_status_after


def _run_git(args: list[str], cwd: Path, *, timeout: int = 30) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def _try_git(args: list[str], cwd: Path, *, timeout: int = 30) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _default_base_ref(repo_root: Path) -> str:
    origin_head = _try_git(
        ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        repo_root,
    )
    if origin_head.startswith("origin/"):
        return origin_head
    return "origin/main"


def _resolve_repo(path: str | None) -> Path:
    cwd = Path(path or ".").expanduser().resolve()
    root = _run_git(["rev-parse", "--show-toplevel"], cwd)
    return Path(root).resolve()


def _collect_git_context(repo_root: Path, base_ref: str | None) -> GitContext:
    base = base_ref or _default_base_ref(repo_root)
    _run_git(["rev-parse", "--verify", base], repo_root)

    return GitContext(
        repo_root=repo_root,
        base_ref=base,
        branch=_try_git(["branch", "--show-current"], repo_root) or "(detached)",
        head=_run_git(["rev-parse", "HEAD"], repo_root),
        merge_base=_try_git(["merge-base", base, "HEAD"], repo_root) or None,
        shortstat=_try_git(["diff", "--shortstat", f"{base}...HEAD"], repo_root),
        name_status=_try_git(["diff", "--name-status", f"{base}...HEAD"], repo_root),
        worktree_status=_try_git(["status", "--short"], repo_root),
    )


def _command_for_reviewer(reviewer: str, mode: str = "gsr") -> list[str]:
    commands = STAFF_REVIEWER_COMMANDS if mode == "staff-engineer" else REVIEWER_COMMANDS
    if reviewer in commands:
        return list(commands[reviewer])
    if reviewer.startswith("opencode:"):
        model = reviewer.split(":", 1)[1]
        if not model:
            raise ValueError("opencode reviewer must include a model name")
        return [
            "opencode",
            "run",
            "-m",
            model,
            "--variant",
            llm_config.OPENCODE_VARIANT,
        ]
    raise ValueError(
        f"Unknown reviewer '{reviewer}'. Use one of {', '.join(KNOWN_REVIEWERS)} "
        "or opencode:<model>."
    )


def _load_staff_guidelines() -> tuple[str, Path]:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "reviewers" / "staff_engineer_reviewer.md"
        if candidate.is_file():
            content = candidate.read_text(encoding="utf-8")
            if not content.strip():
                raise RuntimeError(f"Empty Staff reviewer guidelines: {candidate}")
            return content, parent
    raise RuntimeError(
        "Could not find reviewers/staff_engineer_reviewer.md in the lca_playbook checkout."
    )


def build_staff_review_prompt(git_ctx: GitContext, extra_context: str | None = None) -> str:
    guidelines, playbook_root = _load_staff_guidelines()
    context_section = ""
    if extra_context:
        context_section = f"\nADDITIONAL CONTEXT FROM THE LCA:\n{extra_context.strip()}\n"

    changed_files = git_ctx.name_status or "(no committed branch diff)"
    status = git_ctx.worktree_status or "(clean)"
    shortstat = git_ctx.shortstat or "(no committed branch diff)"

    return f"""{guidelines}

---

## Current Review Invocation

This is a read-only review. Do not edit files, stage files, commit, install
dependencies, or run destructive commands.

Playbook root: {playbook_root}
Repository: {git_ctx.repo_root}
Branch: {git_ctx.branch}
HEAD: {git_ctx.head}
Base ref: {git_ctx.base_ref}
Merge base: {git_ctx.merge_base or "(unknown)"}
Diff shortstat: {shortstat}

Changed files:
{changed_files}

Worktree status, including uncommitted and untracked files:
{status}
{context_section}
Suggested inspection commands:
- git diff --stat {git_ctx.base_ref}...HEAD
- git diff {git_ctx.base_ref}...HEAD -- <relevant paths>
- git diff -- <relevant paths>                         # for unstaged changes
- git diff --cached -- <relevant paths>                # for staged changes
- git status --short
- git grep -n "<symbol>"                                 # every consumer of a model, field, lifecycle state, or contract whose meaning this branch changed, including files the branch did not touch

Return only the JSON object specified in the guidelines above.
"""


def build_review_prompt(git_ctx: GitContext, extra_context: str | None = None) -> str:
    context_section = ""
    if extra_context:
        context_section = f"\nADDITIONAL CONTEXT FROM THE LCA:\n{extra_context.strip()}\n"

    changed_files = git_ctx.name_status or "(no committed branch diff)"
    status = git_ctx.worktree_status or "(clean)"
    shortstat = git_ctx.shortstat or "(no committed branch diff)"

    return f"""You are performing one General Stability Review (GSR) pass.

This is a read-only review. Do not edit files, stage files, commit, install
dependencies, or run destructive commands.

Review the current repository as a general pull request review. Focus on
correctness, stability, deployment/runtime behavior, data integrity, test
reliability, permission or tenant boundaries, and user-visible bugs. Prefer
concrete issues over broad refactor suggestions. Do not rerun Essential
Requirements convergence-review. Treat rare theoretical edge cases as
non-actionable unless they have meaningful impact in the expected operating
context or a simple low-complexity fix.

Treat explicit settled implementation decisions in changed design documents or
LCA-provided context as authoritative operating context unless the current diff
provides concrete new evidence that invalidates their rationale or the decision
exceeds the linked Verbatim Human Intent Reference under an `Agent-Drafted (Unreviewed)`
ER list. Do not reopen a settled decision merely because another architecture is plausible.

Anti-Ratchet Rule: Never demand second-order edge-case hardening, cleanup traps,
or extra state-tracking inside an unrequested operational refusal gate, bootstrap
mode, or state machine that was not asked for in the linked Verbatim Human Intent
Reference. When an unrequested mechanism has edge cases, either recommend
removing/simplifying the unrequested mechanism itself or record the theoretical
concern in `non_actionable_notes`.

Repository: {git_ctx.repo_root}
Branch: {git_ctx.branch}
HEAD: {git_ctx.head}
Base ref: {git_ctx.base_ref}
Merge base: {git_ctx.merge_base or "(unknown)"}
Diff shortstat: {shortstat}

Changed files:
{changed_files}

Worktree status, including uncommitted and untracked files:
{status}
{context_section}
Suggested inspection commands:
- git diff --stat {git_ctx.base_ref}...HEAD
- git diff {git_ctx.base_ref}...HEAD -- <relevant paths>
- git diff -- <relevant paths>                         # for unstaged changes
- git diff --cached -- <relevant paths>                # for staged changes
- git status --short

Return only a JSON object matching this schema:
{{
  "overall": "clean" | "findings" | "incomplete",
  "summary": "One concise sentence for the Lead Coding Agent.",
  "findings": [
    {{
      "severity": "critical" | "high" | "medium" | "low",
      "file": "path/to/file.ext or general",
      "line": 123,
      "title": "Short issue title",
      "description": "Why this is a concrete branch-quality defect in the expected operating context.",
      "recommendation": "Minimal expected fix or validation that does not add more complexity than the risk justifies.",
      "confidence": "high" | "medium" | "low"
    }}
  ],
  "non_actionable_notes": [
    "Optional short note for rejected scope churn, false-premise concerns, or follow-up-only ideas."
  ]
}}

Use "overall": "clean" only when you found no actionable branch-quality
defects. Use "overall": "incomplete" if you could not inspect enough to make a
useful judgment. Use null for "line" when no specific line applies.
"""


def _parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    parsed = _loads_object(stripped)
    if parsed is not None:
        return parsed

    fence_pattern = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)
    for match in fence_pattern.finditer(stripped):
        parsed = _loads_object(match.group(1).strip())
        if parsed is not None:
            return parsed

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", stripped):
        try:
            candidate, _ = decoder.raw_decode(stripped[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
    return None


def _loads_object(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _normalized_result(parsed: dict[str, Any] | None, run: ReviewRun) -> dict[str, Any]:
    failure = _classify_failure(run)
    if parsed is None:
        return {
            "overall": "incomplete",
            "summary": _incomplete_summary(run, failure),
            "findings": [],
            "non_actionable_notes": [],
            "parse_error": True,
            "failure_classification": failure,
            "stderr_excerpt": _excerpt(run.stderr),
            "stdout_excerpt": _excerpt(run.raw_output),
            "reviewer_returncode": run.returncode,
            "reviewer_timed_out": run.timed_out,
            "worktree_mutated": run.worktree_mutated,
        }

    findings = parsed.get("findings")
    if not isinstance(findings, list):
        findings = []

    overall = parsed.get("overall")
    if overall not in {"clean", "findings", "incomplete"}:
        overall = "findings" if findings else "clean"
    if findings and overall == "clean":
        overall = "findings"

    notes = parsed.get("non_actionable_notes")
    if not isinstance(notes, list):
        notes = []

    return {
        "overall": overall,
        "summary": str(parsed.get("summary") or "").strip(),
        "findings": findings,
        "non_actionable_notes": notes,
        "parse_error": False,
        "failure_classification": failure,
        "stderr_excerpt": _excerpt(run.stderr),
        "stdout_excerpt": _excerpt(run.raw_output),
        "reviewer_returncode": run.returncode,
        "reviewer_timed_out": run.timed_out,
        "worktree_mutated": run.worktree_mutated,
    }


# Antigravity (`agy`) read-only control: a per-run fake HOME whose settings
# allow only read-only shell commands and deny every write and subagent tool.
# Headless agy auto-denies anything not allowed, so the launcher never passes
# --dangerously-skip-permissions. Verified 2026-10-29.
# Two observed limits: a denied tool call ends the turn with no output (the
# run then reports incomplete and should simply be re-run), and agy's
# search_web is not permission-gated, so the deny entry below is accepted but
# does not stop web lookups.
AGY_READ_ONLY_SETTINGS = {
    "permissions": {
        "allow": [
            "read_file(*)",
            "command(git)",
            "command(grep)",
            "command(rg)",
            "command(cat)",
            "command(sed)",
            "command(head)",
            "command(tail)",
            "command(ls)",
            "command(find)",
            "command(wc)",
            "command(awk)",
            "command(sort)",
            "command(uniq)",
            "command(cut)",
            "command(tr)",
            "command(diff)",
            "command(echo)",
            "command(pwd)",
            "command(stat)",
            "command(file)",
            "command(nl)",
        ],
        "deny": [
            "write_file(*)",
            "edit_file(*)",
            "replace_file_content(*)",
            "multi_replace_file_content(*)",
            "search_web(*)",
            "schedule(*)",
            "invoke_subagent(*)",
            "define_subagent(*)",
            "command(python3)",
            "command(python)",
            "command(node)",
            "command(rm)",
            "command(mv)",
            "command(cp)",
            "command(tee)",
            "command(bash)",
            "command(sh)",
        ],
    }
}


def _prepare_reviewer_process(
    command: list[str], prompt: str, run_dir: Path
) -> tuple[list[str], dict[str, str], str | None]:
    """Return (argv, env, stdin payload) for a reviewer command.

    Most harnesses read the prompt from stdin. agy needs it as the --print
    argument plus an isolated HOME carrying the read-only settings; grok needs
    a prompt file.
    """
    env = os.environ.copy()
    argv = list(command)
    executable = Path(argv[0]).name if argv else ""
    if executable == "agy":
        home = run_dir / "agy_home"
        settings_dir = home / ".gemini" / "antigravity-cli"
        settings_dir.mkdir(parents=True, exist_ok=True)
        (settings_dir / "settings.json").write_text(
            json.dumps(AGY_READ_ONLY_SETTINGS, indent=2), encoding="utf-8"
        )
        env["HOME"] = str(home.resolve())
        return argv + [prompt], env, None
    if executable == "grok":
        run_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = run_dir / "grok_prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        return argv + ["--prompt-file", str(prompt_path.resolve())], env, None
    return argv, env, prompt


def _run_reviewer(
    reviewer: str,
    prompt: str,
    repo_root: Path,
    timeout: int,
    mode: str = "gsr",
    run_dir: Path | None = None,
) -> ReviewRun:
    command = _command_for_reviewer(reviewer, mode)
    if run_dir is None:
        run_dir = repo_root / "tmp" / "reviewer-launch"
    argv, env, stdin_payload = _prepare_reviewer_process(command, prompt, run_dir)
    status_before = _try_git(["status", "--short"], repo_root)
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=repo_root,
            input=stdin_payload,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        status_after = _try_git(["status", "--short"], repo_root)
        return ReviewRun(
            reviewer=reviewer,
            command=command,
            raw_output=_text_or_empty(exc.stdout),
            stderr=_text_or_empty(exc.stderr),
            elapsed_s=elapsed,
            returncode=None,
            timed_out=True,
            worktree_status_before=status_before,
            worktree_status_after=status_after,
        )

    status_after = _try_git(["status", "--short"], repo_root)
    return ReviewRun(
        reviewer=reviewer,
        command=command,
        raw_output=proc.stdout,
        stderr=proc.stderr,
        elapsed_s=time.monotonic() - started,
        returncode=proc.returncode,
        worktree_status_before=status_before,
        worktree_status_after=status_after,
    )


def _classify_failure(run: ReviewRun) -> str | None:
    if run.timed_out:
        return "timeout"
    if run.returncode == 0 and _parse_json_object(run.raw_output) is not None:
        return None

    combined = f"{run.stderr}\n{run.raw_output}".lower()
    compact = combined.replace(" ", "")

    quota_markers = (
        "quota",
        "rate limit",
        "rate_limit",
        "usage limit",
        "credit",
        "billing",
        "subscription",
        "insufficient_quota",
        "payment required",
        "too many requests",
        "429",
    )
    if any(marker in combined for marker in quota_markers):
        return "quota_or_billing"

    auth_markers = (
        "api key",
        "apikey",
        "authentication",
        "unauthorized",
        "forbidden",
        "permission denied by api",
        "401",
        "403",
    )
    if any(marker in combined for marker in auth_markers):
        return "auth"

    local_state_markers = (
        "state_5.sqlite",
        "read-only file system",
        "os error 30",
        "permission denied",
        "operation not permitted",
    )
    if any(marker in combined for marker in local_state_markers):
        return "local_state_or_sandbox"

    network_markers = (
        "connectionrefused",
        "connection refused",
        "unable to connect",
        "econnrefused",
        "network",
        "dns",
        "name or service not known",
        "temporary failure in name resolution",
        "connection reset",
        "connection timed out",
    )
    if any(marker in combined or marker in compact for marker in network_markers):
        return "network"

    if "api error" in combined or "apierror" in compact:
        return "api_error"
    if run.returncode not in (0, None):
        return "process_exit"
    return "unparseable_reviewer_output"


def _incomplete_summary(run: ReviewRun, failure: str | None) -> str:
    if run.timed_out:
        return f"{run.reviewer} timed out before completing review."
    if failure:
        detail = _first_nonempty_line(run.stderr) or _first_nonempty_line(run.raw_output)
        if detail:
            return f"{run.reviewer} review incomplete ({failure}): {detail}"
        return f"{run.reviewer} review incomplete ({failure})."
    return "Reviewer output could not be parsed as the GSR JSON contract."


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return _truncate(stripped, 240)
    return ""


def _excerpt(text: str, limit: int = 1200) -> str:
    return _truncate(text.strip(), limit)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _text_or_empty(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _resolve_artifacts_dir(repo_root: Path, raw: str | None, mode: str = "gsr") -> Path:
    default_subdir = "staff-engineer-reviews" if mode == "staff-engineer" else "gsr-reviews"
    base = Path(raw).expanduser() if raw else repo_root / "tmp" / default_subdir
    if not base.is_absolute():
        base = repo_root / base
    return base / f"run_{_now_slug()}"


def _write_artifacts(
    artifacts_dir: Path,
    git_ctx: GitContext,
    prompt: str,
    run: ReviewRun,
    parsed: dict[str, Any] | None,
    result: dict[str, Any],
    mode: str = "gsr",
) -> None:
    # The reviewer launcher may already have created this run directory (agy
    # fake HOME, grok prompt file live inside it); the timestamped name keeps
    # runs distinct, so an existing directory is not an error.
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "prompt.txt").write_text(prompt)
    (artifacts_dir / "raw_review.txt").write_text(run.raw_output)
    (artifacts_dir / "stderr.txt").write_text(run.stderr)
    (artifacts_dir / "parsed_review.json").write_text(
        json.dumps(parsed, indent=2, sort_keys=True) if parsed is not None else "null\n"
    )
    (artifacts_dir / "result.json").write_text(
        json.dumps(
            {
                "mode": mode,
                "result": result,
                "reviewer": run.reviewer,
                "command": run.command,
                "elapsed_s": round(run.elapsed_s, 3),
                "worktree": {
                    "mutated": run.worktree_mutated,
                    "status_before": run.worktree_status_before,
                    "status_after": run.worktree_status_after,
                },
                "git": {
                    "repo_root": str(git_ctx.repo_root),
                    "base_ref": git_ctx.base_ref,
                    "branch": git_ctx.branch,
                    "head": git_ctx.head,
                    "merge_base": git_ctx.merge_base,
                    "shortstat": git_ctx.shortstat,
                    "name_status": git_ctx.name_status,
                    "worktree_status": git_ctx.worktree_status,
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    (artifacts_dir / "summary.md").write_text(
        _format_summary(run, result, artifacts_dir, mode=mode)
    )


def _format_summary(
    run: ReviewRun,
    result: dict[str, Any],
    artifacts_dir: Path,
    mode: str = "gsr",
) -> str:
    heading = (
        "# Staff Engineer Review Result"
        if mode == "staff-engineer"
        else "# General Stability Review Result"
    )
    lines = [
        heading,
        "",
        f"- Status: {result['overall']}",
        f"- Mode: {mode}",
        f"- Reviewer: {run.reviewer}",
        f"- Elapsed: {run.elapsed_s:.1f}s",
        f"- Artifacts: {artifacts_dir}",
        f"- Summary: {result.get('summary') or '(none)'}",
        f"- Failure classification: {result.get('failure_classification') or '(none)'}",
        f"- Reviewer return code: {run.returncode}",
        f"- Worktree mutated during review: {'yes' if run.worktree_mutated else 'no'}",
        "",
    ]

    stderr_excerpt = result.get("stderr_excerpt")
    if stderr_excerpt:
        lines.extend(["## Stderr Excerpt", "", "```text", stderr_excerpt, "```", ""])

    stdout_excerpt = result.get("stdout_excerpt")
    if result.get("parse_error") and stdout_excerpt:
        lines.extend(["## Stdout Excerpt", "", "```text", stdout_excerpt, "```", ""])

    findings = result.get("findings") or []
    if findings:
        lines.append("## Findings")
        for i, finding in enumerate(findings, 1):
            severity = finding.get("severity", "?")
            file = finding.get("file", "general")
            line = finding.get("line")
            loc = f"{file}:{line}" if line else file
            title = finding.get("title", "(untitled)")
            description = finding.get("description", "")
            recommendation = finding.get("recommendation", "")
            lines.extend(
                [
                    "",
                    f"{i}. [{severity}] {loc} - {title}",
                    f"   Description: {description}",
                    f"   Recommendation: {recommendation}",
                ]
            )
    else:
        lines.append("No actionable findings reported.")

    notes = result.get("non_actionable_notes") or []
    if notes:
        lines.extend(["", "## Non-Actionable Notes"])
        lines.extend(f"- {note}" for note in notes)

    lines.append("")
    return "\n".join(lines)


def _print_result(
    run: ReviewRun,
    result: dict[str, Any],
    artifacts_dir: Path,
    mode: str = "gsr",
) -> None:
    findings = result.get("findings") or []
    print(f"general-stability-review: {result['overall']}")
    print(f"  mode: {mode}")
    print(f"  reviewer: {run.reviewer}")
    print(f"  findings: {len(findings)}")
    print(f"  elapsed: {run.elapsed_s:.1f}s")
    print(f"  artifacts: {artifacts_dir}")
    print(f"  failure classification: {result.get('failure_classification') or '(none)'}")
    print(f"  return code: {run.returncode}")
    if run.worktree_mutated:
        print("  WARNING: worktree status changed during reviewer run")
    summary = result.get("summary")
    if summary:
        print(f"  summary: {summary}")
    for finding in findings[:8]:
        severity = finding.get("severity", "?")
        file = finding.get("file", "general")
        line = finding.get("line")
        loc = f"{file}:{line}" if line else file
        title = finding.get("title", "(untitled)")
        print(f"  [{severity}] {loc}: {title}")
    if len(findings) > 8:
        print(f"  ... {len(findings) - 8} more finding(s) in summary.md")


class _HelpOnErrorParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_help(sys.stderr)
        self.exit(2, f"\nerror: {message}\n")


def _print_playbook_reminder(mode: str = "gsr") -> None:
    if mode == "staff-engineer":
        print(
            "You just initiated a Staff Engineer Review. Read "
            "reviewers/staff_engineer_reviewer.md and "
            "reviews/general_stability_review_playbook.md to interpret "
            "findings proportionately."
        )
        return
    print(
        "You just initiated a GSR. If you have not read the LCA's GSR playbook "
        "yet, read reviews/general_stability_review_playbook.md now; it is "
        "essential for interpreting GSR results proportionately."
    )


def main() -> None:
    parser = _HelpOnErrorParser(
        prog="general-stability-review",
        description=(
            "Run one read-only General Stability Review or Staff Engineer "
            "reviewer pass and write raw output plus a concise LCA-facing result."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("gsr", "staff-engineer"),
        default="gsr",
        help="Review mode: 'gsr' (default) or 'staff-engineer'.",
    )
    parser.add_argument(
        "--repo",
        metavar="PATH",
        help="Target git repository. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--base",
        metavar="REF",
        help="Base ref for branch diff. Defaults to origin/HEAD, then origin/main.",
    )
    parser.add_argument(
        "--reviewer",
        default=None,
        metavar="AGENT",
        help=(
            "Reviewer agent: "
            f"{', '.join(KNOWN_REVIEWERS)}, or opencode:<model> "
            f"(default: {DEFAULT_REVIEWER_BY_MODE['gsr']} for gsr, "
            f"{DEFAULT_REVIEWER_BY_MODE['staff-engineer']} for staff-engineer, "
            "using the per-mode model pins in llm_config.py)."
        ),
    )
    parser.add_argument(
        "--artifacts-dir",
        metavar="DIR",
        help=(
            "Base directory for run artifacts. Defaults to "
            "<repo>/tmp/gsr-reviews (or <repo>/tmp/staff-engineer-reviews)."
        ),
    )
    parser.add_argument(
        "--context",
        metavar="TEXT",
        help="Optional short LCA context to include in the review prompt.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        metavar="SECONDS",
        help=(
            f"Reviewer timeout in seconds (default: {REVIEWER_TIMEOUT} for gsr, "
            f"{STAFF_REVIEWER_TIMEOUT} for staff-engineer)."
        ),
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Exit with status 3 when actionable findings are reported.",
    )
    args = parser.parse_args()
    if args.reviewer is None:
        args.reviewer = DEFAULT_REVIEWER_BY_MODE[args.mode]
    if args.timeout is None:
        args.timeout = (
            STAFF_REVIEWER_TIMEOUT if args.mode == "staff-engineer" else REVIEWER_TIMEOUT
        )
    _print_playbook_reminder(args.mode)

    try:
        repo_root = _resolve_repo(args.repo)
        git_ctx = _collect_git_context(repo_root, args.base)
        prompt = (
            build_staff_review_prompt(git_ctx, args.context)
            if args.mode == "staff-engineer"
            else build_review_prompt(git_ctx, args.context)
        )
        artifacts_dir = _resolve_artifacts_dir(
            repo_root, args.artifacts_dir, mode=args.mode
        )
        run = _run_reviewer(
            args.reviewer, prompt, repo_root, args.timeout, mode=args.mode, run_dir=artifacts_dir
        )
        parsed = _parse_json_object(run.raw_output)
        result = _normalized_result(parsed, run)
        if run.timed_out:
            result["overall"] = "incomplete"
            result["summary"] = f"{args.reviewer} timed out before completing review."
        elif run.returncode not in (0, None):
            result["overall"] = "incomplete"
            result["summary"] = (
                result.get("summary") or f"{args.reviewer} exited with status {run.returncode}."
            )
        if run.worktree_mutated:
            result["overall"] = "incomplete"
            previous_summary = result.get("summary")
            result["summary"] = f"{args.reviewer} changed the worktree during review."
            if previous_summary:
                result["summary"] += f" Reviewer summary: {previous_summary}"
        _write_artifacts(
            artifacts_dir, git_ctx, prompt, run, parsed, result, mode=args.mode
        )
        _print_result(run, result, artifacts_dir, mode=args.mode)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if result["overall"] == "incomplete":
        sys.exit(2)
    if result["overall"] == "findings" and args.fail_on_findings:
        sys.exit(3)


if __name__ == "__main__":
    main()
