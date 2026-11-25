from __future__ import annotations

import json
import re
from dataclasses import dataclass
from collections.abc import Sequence


@dataclass(frozen=True)
class ReviewPayload:
    issues: list[dict]
    assessment: str | None = None
    infrastructure_status: str = "complete"
    status_detail: str | None = None


REVIEW_INFRASTRUCTURE_STATUSES = (
    "complete",
    "parse_failed",
    "tool_failed",
    "timed_out",
)


_INVALID_REVIEW_OBJECT = object()


def _parse_json_list(text: str) -> list[dict] | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, list):
        return None
    return parsed


def _payload_from_parsed(parsed: object) -> ReviewPayload | object | None:
    if isinstance(parsed, list):
        return ReviewPayload(parsed)
    if isinstance(parsed, dict) and isinstance(parsed.get("issues"), list):
        infrastructure_status = parsed.get("infrastructure_status", "complete")
        if infrastructure_status not in REVIEW_INFRASTRUCTURE_STATUSES:
            return _INVALID_REVIEW_OBJECT
        assessment = parsed.get("assessment")
        status_detail = parsed.get("status_detail")
        return ReviewPayload(
            parsed["issues"],
            assessment=assessment if isinstance(assessment, str) else None,
            infrastructure_status=infrastructure_status,
            status_detail=status_detail if isinstance(status_detail, str) else None,
        )
    return None


def _parse_json_payload(text: str) -> ReviewPayload | object | None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    return _payload_from_parsed(parsed)


def _parse_embedded_json_payload(text: str) -> ReviewPayload | object | None:
    decoder = json.JSONDecoder()
    matches = sorted(
        [m for m in re.finditer(r"[\[{]", text)],
        key=lambda match: match.start(),
    )
    for match in matches:
        try:
            parsed, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        payload = _payload_from_parsed(parsed)
        if payload is not None:
            return payload
    return None


def parse_review_payload(
    raw_output: str, *, allow_embedded: bool = True
) -> ReviewPayload | None:
    """Parse reviewer JSON output.

    Reviewers may return either a bare JSON issue array or an object containing
    an `issues` array and optional `assessment` string.

    A review-shaped object whose `infrastructure_status` is not one of
    REVIEW_INFRASTRUCTURE_STATUSES fails parsing for the whole output rather
    than falling through to embedded-fragment extraction.

    With allow_embedded=False, only whole-output or fenced payloads are
    accepted; JSON fragments embedded in surrounding prose fail parsing.
    Callers use this when the reviewer process already signalled distress
    (nonzero exit), so an incidental fragment cannot masquerade as a
    completed review.

    Returns:
        - ReviewPayload when parsing succeeds (including empty `issues`)
        - None when parsing fails
    """
    text = raw_output.strip()

    parsed = _parse_json_payload(text)
    if isinstance(parsed, ReviewPayload):
        return parsed
    if parsed is _INVALID_REVIEW_OBJECT:
        return None

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_pattern = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)
    for match in fence_pattern.finditer(text):
        parsed = _parse_json_payload(match.group(1).strip())
        if isinstance(parsed, ReviewPayload):
            return parsed
        if parsed is _INVALID_REVIEW_OBJECT:
            return None

    if not allow_embedded:
        return None

    parsed = _parse_embedded_json_payload(text)
    if isinstance(parsed, ReviewPayload):
        return parsed
    return None


def parse_review_json(raw_output: str) -> list[dict] | None:
    """Parse JSON issue array from reviewer output.

    Returns:
        - list[dict] when parsing succeeds (including empty list `[]`)
        - None when parsing fails
    """
    payload = parse_review_payload(raw_output)
    return payload.issues if payload is not None else None


BLOCKING_SEVERITIES = ("critical", "high", "medium")


def format_severity_list(severities: Sequence[str]) -> str:
    """Return a compact slash-separated severity list for user-facing text."""
    return "/".join(severities)


def format_quoted_severity_list(severities: Sequence[str]) -> str:
    """Return a prose severity list with each value quoted."""
    quoted = [f'"{severity}"' for severity in severities]
    if len(quoted) <= 1:
        return "".join(quoted)
    return f"{', '.join(quoted[:-1])}, or {quoted[-1]}"


def check_convergence(issues: list[dict]) -> bool:
    """Return True if no blocking severity issues remain."""
    for issue in issues:
        if issue.get("severity") in BLOCKING_SEVERITIES:
            return False
    return True


SEVERITY_ORDER = ("critical", "high", "medium", "low")
SEVERITY_SHORT = {"critical": "crit", "high": "high", "medium": "med", "low": "low"}
CATEGORY_SHORT = {
    "bug": "bug",
    "missing_requirement": "missing_req",
    "design_mismatch": "design",
    "code_quality": "quality",
    "other": "other",
}


def summarize_issues(issues: list[dict]) -> dict:
    """Count issues by severity and category.

    Returns a dict with:
        - severity: dict[severity_name, count] — always has keys for the 4 known severities (0 if absent)
        - category: dict[category_name, count] — only non-zero entries
        - total: int
        - unknown_severity: int (issues with severity outside the known set)
    """
    severity: dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
    category: dict[str, int] = {}
    unknown_sev = 0

    for issue in issues:
        sev = issue.get("severity")
        if sev in severity:
            severity[sev] += 1
        else:
            unknown_sev += 1

        cat = issue.get("category", "other")
        category[cat] = category.get(cat, 0) + 1

    return {
        "severity": severity,
        "category": category,
        "total": len(issues),
        "unknown_severity": unknown_sev,
    }


def format_severity_counts(severity: dict[str, int]) -> str:
    """Compact severity string like 'crit:1 high:2 med:0 low:2'."""
    return " ".join(f"{SEVERITY_SHORT[s]}:{severity.get(s, 0)}" for s in SEVERITY_ORDER)


def format_category_counts(category: dict[str, int]) -> str:
    """Compact category string showing only non-zero entries, e.g. 'bug:3 quality:1'."""
    parts = []
    for cat, count in sorted(category.items(), key=lambda kv: -kv[1]):
        if count == 0:
            continue
        label = CATEGORY_SHORT.get(cat, cat)
        parts.append(f"{label}:{count}")
    return " ".join(parts)


def severity_delta(curr: dict[str, int], prev: dict[str, int]) -> str:
    """Format a delta string like 'crit -2, high -1, med +1'. Returns empty string when no change."""
    parts = []
    for s in SEVERITY_ORDER:
        d = curr.get(s, 0) - prev.get(s, 0)
        if d != 0:
            parts.append(f"{SEVERITY_SHORT[s]} {d:+d}")
    return ", ".join(parts)


def format_summary(
    iteration_results: list[dict],
    deferred_issues: list[dict] | None = None,
    coder_stopped: bool = False,
    stop_category: str | None = None,
    stop_reason: str | None = None,
    review_incomplete: bool = False,
    review_incomplete_reason: str | None = None,
) -> str:
    """Format a human-readable summary of the convergence loop."""
    lines = ["\n=== Convergence Review Summary ===\n"]

    for result in iteration_results:
        iteration = result["iteration"]
        issues = result["issues"]

        summary = summarize_issues(issues)
        if summary["total"] == 0:
            counts_str = "no issues"
        else:
            counts_str = format_severity_counts(summary["severity"])
        lines.append(f"  Iteration {iteration}: {counts_str}")

    lines.append("")

    final = iteration_results[-1] if iteration_results else None
    if final and final["converged"]:
        lines.append(
            "Status: CONVERGED "
            f"(no {format_severity_list(BLOCKING_SEVERITIES)} issues remaining)"
        )
    elif review_incomplete:
        lines.append("Status: REVIEW INCOMPLETE")
        lines.append(
            "  One or more reviewer outputs could not be converted into "
            "structured findings, so convergence cannot be trusted."
        )
        if review_incomplete_reason:
            lines.append(f"  Reason: {review_incomplete_reason}")
    elif coder_stopped:
        cat_label = (stop_category or "unspecified").upper()
        lines.append(f"Status: CODER ESCALATED FOR HUMAN REVIEW [{cat_label}]")
        lines.append(
            "  The coder identified a design-doc-level issue and halted further "
            "iterations. Human review of the design doc is required before resuming."
        )
        if stop_reason:
            lines.append(f"  Reason: {stop_reason}")
        if final:
            remaining = [
                i
                for i in _final_convergence_issues(final)
                if i.get("severity") in BLOCKING_SEVERITIES
            ]
            if remaining:
                lines.append(f"  {len(remaining)} blocking issue(s) at halt:")
                for issue in remaining:
                    lines.append(
                        f"    [{issue.get('severity')}] "
                        f"{issue.get('file', 'general')}: {issue.get('description', '')}"
                    )
    else:
        lines.append("Status: MAX ITERATIONS REACHED")
        lines.extend(
            [
                "  This usually means one or more of the following:",
                "    a) legitimate implementation work remains;",
                "    b) subtle Essential Requirements wording is causing churn "
                "and may need human simplification; or",
                "    c) subtle requirements bloat is entering the implementation.",
                "  Requirements bloat is currently the LCA's most common failure "
                "mode. Before deciding how to proceed, read "
                "example-case-studies/requirements-risk/ (and case-studies/local/ when present) "
                "if you have not already.",
            ]
        )
        if final:
            remaining = [
                i
                for i in _final_convergence_issues(final)
                if i.get("severity") in BLOCKING_SEVERITIES
            ]
            if remaining:
                lines.append(f"  {len(remaining)} blocking issue(s) remaining:")
                for issue in remaining:
                    lines.append(
                        f"    [{issue.get('severity')}] "
                        f"{issue.get('file', 'general')}: {issue.get('description', '')}"
                    )

    lines.append("")
    lines.extend(_format_tier_sections(final, deferred_issues or []))
    if lines[-1] != "":
        lines.append("")
    return "\n".join(lines)


def _final_convergence_issues(final: dict) -> list[dict]:
    return final.get("convergence_issues") or [
        issue
        for issue in final.get("issues", [])
        if issue.get("reviewer_role") in {"architecture", "core"}
        or "reviewer_role" not in issue
    ]


def _format_tier_sections(final: dict | None, deferred_issues: list[dict]) -> list[str]:
    if not final:
        return []

    roles_run = set(final.get("roles_run") or [])
    final_issues = final.get("issues") or []
    assessments = final.get("assessments") or []
    reviewer_statuses = final.get("reviewer_statuses") or []

    lines: list[str] = []
    if "architecture" in roles_run:
        lines.append("Architecture Tier:")
        _append_issue_list(
            lines,
            "  Final findings",
            [i for i in final_issues if i.get("reviewer_role") == "architecture"],
        )
        _append_deferred_list(
            lines,
            "  Deferred items",
            [d for d in deferred_issues if d.get("role") == "architecture"],
        )
        _append_assessments(
            lines,
            [a for a in assessments if a.get("role") == "architecture"],
        )
        _append_reviewer_statuses(
            lines,
            [s for s in reviewer_statuses if s.get("role") == "architecture"],
        )
        lines.append("")

    if "core" in roles_run:
        lines.append("Core Tier:")
        _append_deferred_list(
            lines,
            "  Deferred items",
            [d for d in deferred_issues if d.get("role") == "core"],
        )
        _append_reviewer_statuses(
            lines,
            [s for s in reviewer_statuses if s.get("role") == "core"],
        )
        lines.append("")

    persona_roles = set(roles_run) - {"architecture", "core"}
    if persona_roles:
        lines.append("Persona Tier:")
        _append_issue_list(
            lines,
            "  Final findings",
            [i for i in final_issues if i.get("reviewer_role") in persona_roles],
        )
        _append_deferred_list(
            lines,
            "  Deferred items",
            [d for d in deferred_issues if d.get("role") in persona_roles],
        )
        _append_assessments(
            lines,
            [a for a in assessments if a.get("role") in persona_roles],
        )
        _append_reviewer_statuses(
            lines,
            [s for s in reviewer_statuses if s.get("role") in persona_roles],
        )
        lines.append("")

    return lines


def _append_reviewer_statuses(lines: list[str], statuses: list[dict]) -> None:
    incomplete = [
        status
        for status in statuses
        if status.get("infrastructure_status", "complete") != "complete"
    ]
    if not incomplete:
        return
    lines.append("  Incomplete reviews:")
    for status in incomplete:
        detail = status.get("status_detail")
        suffix = f": {detail}" if detail else ""
        lines.append(
            f"    {status.get('reviewer', '?')}: "
            f"{status.get('infrastructure_status')}{suffix}"
        )


def _append_issue_list(lines: list[str], heading: str, issues: list[dict]) -> None:
    lines.append(f"{heading}:")
    if not issues:
        lines.append("    None.")
        return
    for issue in issues:
        reviewer = issue.get("reviewer", "?")
        lines.append(
            f"    [{issue.get('severity', '?')}] {reviewer} "
            f"{issue.get('file', 'general')}: {issue.get('description', '')}"
        )


def _append_deferred_list(
    lines: list[str], heading: str, deferrals: list[dict]
) -> None:
    lines.append(f"{heading}:")
    if not deferrals:
        lines.append("    None.")
        return
    for deferral in deferrals:
        reviewer = deferral.get("reviewer", "?")
        iter_num = deferral.get("iteration", "?")
        lines.append(
            f"    [iter {iter_num}] [{deferral.get('severity', '?')}] "
            f"{reviewer}: {deferral.get('summary', '')}"
        )
        rationale = deferral.get("rationale")
        if rationale:
            lines.append(f"      Why: {rationale}")


def _append_assessments(lines: list[str], assessments: list[dict]) -> None:
    if not assessments:
        return
    lines.append("  Closing assessments:")
    for assessment in assessments:
        lines.append(
            f"    {assessment.get('reviewer', '?')}: {assessment.get('assessment', '')}"
        )
