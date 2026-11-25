from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .convergence import ReviewPayload, parse_review_payload
from .llm_config_loader import llm_config
from .prompts import (
    REVIEW_JSON_REPAIR_PROMPT,
    REVIEWER_DEFERRED_ISSUES_SECTION,
    REVIEWER_GUIDELINE_TAGGING_INSTRUCTION,
    REVIEWER_PROMPT,
)


REVIEWER_TIMEOUT = 15 * 60  # 15 minutes
REVIEW_REPAIR_TIMEOUT = 5 * 60  # 5 minutes
REVIEW_REPAIR_ATTEMPTS = 3
REVIEWER_ATTEMPTS = 2

REVIEWER_COMMANDS: dict[str, list[str]] = {
    name: list(command)
    for name, command in llm_config.CONVERGENCE_REVIEW_REVIEWER_COMMANDS.items()
}

REVIEWER_NAMES: tuple[str, ...] = llm_config.CONVERGENCE_REVIEW_AVAILABLE_REVIEWERS
_CLAUDE_REVIEWER_RE = re.compile(r"^claude-([A-Za-z0-9][A-Za-z0-9._-]*)$")
ROLE_CONFIGS: dict[str, dict] = {
    name: dict(config)
    for name, config in llm_config.CONVERGENCE_REVIEW_REVIEWER_ROLES.items()
}
REVIEWER_ROLE_NAMES: tuple[str, ...] = tuple(ROLE_CONFIGS.keys())
PERSONA_TIER = 3
AGY_TIMEOUT_MARKERS = ("error: timed out waiting for response",)
OPENCODE_REVIEWER_PERMISSIONS = {
    "edit": "deny",
    "bash": "deny",
    "external_directory": "deny",
}


def reviewer_backend_name(agent_name: str) -> str:
    """Resolve a CLI reviewer selector to its configured command backend."""
    if _CLAUDE_REVIEWER_RE.fullmatch(agent_name):
        return "claude"
    return agent_name


def is_supported_reviewer(agent_name: str) -> bool:
    """Return whether an agent name is configured or a Claude model selector."""
    return reviewer_backend_name(agent_name) in REVIEWER_COMMANDS


def _reviewer_command(agent_name: str) -> list[str]:
    """Build a reviewer command, applying any per-run Claude model override."""
    backend_name = reviewer_backend_name(agent_name)
    cmd = list(REVIEWER_COMMANDS[backend_name])
    model_match = _CLAUDE_REVIEWER_RE.fullmatch(agent_name)
    if model_match:
        model_index = cmd.index("--model") + 1
        cmd[model_index] = model_match.group(1)
    return cmd


@dataclass(frozen=True)
class ReviewerSpec:
    agent_name: str
    role_name: str

    @property
    def label(self) -> str:
        return f"{self.agent_name}:{self.role_name}"

    @property
    def artifact_stem(self) -> str:
        return f"{self.agent_name}_{self.role_name}"

    @property
    def tier(self) -> int:
        return int(ROLE_CONFIGS[self.role_name]["tier"])

    @property
    def is_persona(self) -> bool:
        return self.tier == PERSONA_TIER


def format_reviewer_specs(specs: tuple[ReviewerSpec, ...] | list[ReviewerSpec]) -> str:
    return ", ".join(spec.label for spec in specs)


@dataclass
class ReviewRepairAttempt:
    raw_output: str
    issues: list[dict] = field(default_factory=list)
    payload: ReviewPayload | None = None
    parse_error: bool = False
    elapsed_s: float = 0.0
    returncode: int | None = None
    timed_out: bool = False


@dataclass
class ReviewResult:
    agent_name: str
    raw_output: str
    role_name: str = "core"
    issues: list[dict] = field(default_factory=list)
    assessment: str | None = None
    parse_repaired: bool = False
    repair_attempts: list[ReviewRepairAttempt] = field(default_factory=list)
    elapsed_s: float = 0.0
    returncode: int | None = None
    infrastructure_status: str = "complete"
    status_detail: str | None = None
    stderr_output: str = ""
    retry_count: int = 0
    prior_attempts: list[ReviewAttempt] = field(default_factory=list)

    @property
    def parse_error(self) -> bool:
        return self.infrastructure_status == "parse_failed"

    @property
    def timed_out(self) -> bool:
        return self.infrastructure_status == "timed_out"

    @property
    def label(self) -> str:
        return f"{self.agent_name}:{self.role_name}"

    @property
    def artifact_stem(self) -> str:
        return f"{self.agent_name}_{self.role_name}"

    @property
    def tier(self) -> int:
        return int(ROLE_CONFIGS[self.role_name]["tier"])

    @property
    def is_persona(self) -> bool:
        return self.tier == PERSONA_TIER


@dataclass
class ReviewAttempt:
    raw_output: str
    infrastructure_status: str
    status_detail: str | None = None
    stderr_output: str = ""
    elapsed_s: float = 0.0
    returncode: int | None = None
    parse_repaired: bool = False
    repair_attempts: list[ReviewRepairAttempt] = field(default_factory=list)


def _format_deferrals_for_prompt(deferred_issues: list[dict]) -> str:
    """Format accumulated deferred issues into a readable block for prompts."""
    lines = []
    for i, d in enumerate(deferred_issues, 1):
        header = f"{i}. [{d.get('severity', '?')}] {d.get('summary', '(no summary)')}"
        reviewer = d.get("reviewer") or _format_deferral_reviewer(d)
        meta_parts = [f"Reviewer: {reviewer}"]
        if d.get("iteration") is not None:
            meta_parts.append(f"Iteration: {d['iteration']}")
        meta = "   " + " | ".join(meta_parts)
        rationale = f"   Rationale: {d.get('rationale', '(none)')}"
        lines.append("\n".join([header, meta, rationale]))
    return "\n\n".join(lines)


def _format_deferral_reviewer(deferral: dict) -> str:
    agent = deferral.get("agent")
    role = deferral.get("role")
    if agent and role:
        return f"{agent}:{role}"
    return deferral.get("reviewer", "?")


def build_reviewer_prompt(
    design_doc_content: str,
    review_guidelines: str,
    role_name: str = "core",
    deferred_issues: list[dict] | None = None,
    final_iteration: bool = False,
) -> str:
    guidelines_section = f"ADDITIONAL REVIEW GUIDELINES:\n{review_guidelines}"
    tagging_instruction = REVIEWER_GUIDELINE_TAGGING_INSTRUCTION
    assessment_instruction = ""
    reviewer_output_format = (
        "Respond with a JSON array of issues. Each issue must have:"
    )
    if role_name != "core" and final_iteration:
        reviewer_output_format = (
            "Respond with either a JSON array of issues or an object of the form "
            '{"issues": [...], "assessment": "..."}. Each issue must have:'
        )
        assessment_instruction = (
            "\n\nIf you use the object form, keep `assessment` to a concise closing "
            "assessment."
        )

    deferred_section = ""
    if deferred_issues:
        deferred_section = REVIEWER_DEFERRED_ISSUES_SECTION.format(
            formatted_deferrals=_format_deferrals_for_prompt(deferred_issues),
        )

    return REVIEWER_PROMPT.format(
        design_doc_content=design_doc_content,
        review_guideline_tagging_instruction=tagging_instruction,
        review_guidelines_section=guidelines_section,
        deferred_issues_section=deferred_section,
        assessment_instruction=assessment_instruction,
        reviewer_output_format=reviewer_output_format,
    )


def _agy_mock_home(cwd: Path, iteration_dir: Path | None) -> Path:
    if iteration_dir:
        return iteration_dir / "agy_mock_home"
    return cwd / "tmp" / "coding-logs" / f"agy_mock_home_{time.time()}"


def _prepare_reviewer_process(
    agent_name: str,
    prompt: str,
    cwd: Path,
    iteration_dir: Path | None = None,
) -> tuple[list[str], dict[str, str], bytes | None]:
    """Build command/env/stdin payload for a reviewer subprocess."""
    backend_name = reviewer_backend_name(agent_name)
    cmd = _reviewer_command(agent_name)
    env = os.environ.copy()

    if cmd and cmd[0] == "opencode":
        # OpenCode merges this supported environment override after project
        # configuration, so repository settings cannot weaken the deny rules.
        env["OPENCODE_PERMISSION"] = json.dumps(OPENCODE_REVIEWER_PERMISSIONS)

    if backend_name == "grok":
        # Socket stdin cannot be reopened via /dev/stdin; argv has a size limit.
        if iteration_dir is not None:
            iteration_dir.mkdir(parents=True, exist_ok=True)
        fd, prompt_path = tempfile.mkstemp(
            prefix="grok_prompt_", suffix=".md", dir=iteration_dir
        )
        with os.fdopen(fd, "w", encoding="utf-8") as prompt_file:
            prompt_file.write(prompt)
        cmd.extend(["--prompt-file", str(Path(prompt_path).resolve())])
        return cmd, env, None

    # `gemini` is the playbook name for the Antigravity (`agy`) backend.
    if backend_name != "agy" and not (cmd and cmd[0] == "agy"):
        return cmd, env, prompt.encode()

    mock_home = _agy_mock_home(cwd, iteration_dir)
    agy_cli_dir = mock_home / ".gemini" / "antigravity-cli"
    agy_cli_dir.mkdir(parents=True, exist_ok=True)
    settings_file = agy_cli_dir / "settings.json"

    settings_data = {
        "model": llm_config.AGY_MODEL,
        "permissions": {
            "deny": [
                "write_file(*)",
                "edit_file(*)",
                "command(*)",
                "replace_file_content(*)",
                "multi_replace_file_content(*)",
                "invoke_subagent(*)",
                "define_subagent(*)",
            ]
        },
    }
    settings_file.write_text(json.dumps(settings_data, indent=2))
    env["HOME"] = str(mock_home.resolve())

    # agy --print expects the prompt as an argv value. It also consumes stdin
    # when provided, so keep Agy single-channel to avoid duplicate prompts.
    cmd.append(prompt)
    return cmd, env, None


def _reviewer_output_is_timeout(raw_output: str) -> bool:
    text = " ".join(raw_output.strip().lower().split())
    return text in AGY_TIMEOUT_MARKERS


async def _run_single_repair_attempt(
    agent_name: str,
    raw_output: str,
    cwd: Path,
    iteration_dir: Path | None = None,
    previous_attempt: ReviewRepairAttempt | None = None,
    label: str | None = None,
) -> ReviewRepairAttempt:
    """Ask an LLM to convert malformed reviewer output into the JSON array contract."""
    reviewer_label = label or agent_name
    previous_attempt_section = ""
    if previous_attempt is not None:
        previous_attempt_section = (
            "PREVIOUS REPAIR ATTEMPT FAILED TO PARSE:\n"
            f"{previous_attempt.raw_output}\n\n"
        )
    prompt = REVIEW_JSON_REPAIR_PROMPT.format(
        raw_output=raw_output,
        previous_attempt_section=previous_attempt_section,
    )
    cmd, env, input_payload = _prepare_reviewer_process(
        agent_name,
        prompt,
        cwd,
        iteration_dir=iteration_dir,
    )

    started = time.monotonic()
    proc: asyncio.subprocess.Process | None = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=(
                asyncio.subprocess.PIPE
                if input_payload is not None
                else asyncio.subprocess.DEVNULL
            ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=input_payload),
            timeout=REVIEW_REPAIR_TIMEOUT,
        )
    except asyncio.TimeoutError:
        elapsed = time.monotonic() - started
        print(
            f"  WARNING: {reviewer_label} reviewer JSON repair timed out after "
            f"{REVIEW_REPAIR_TIMEOUT // 60} minutes",
            file=sys.stderr,
        )
        if proc is not None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
        return ReviewRepairAttempt(
            raw_output="",
            parse_error=True,
            elapsed_s=elapsed,
            timed_out=True,
        )
    except OSError as exc:
        elapsed = time.monotonic() - started
        print(
            f"  WARNING: {reviewer_label} reviewer JSON repair could not start: {exc}",
            file=sys.stderr,
        )
        return ReviewRepairAttempt(
            raw_output=str(exc),
            parse_error=True,
            elapsed_s=elapsed,
        )

    elapsed = time.monotonic() - started
    raw = stdout.decode(errors="replace")
    if proc.returncode != 0:
        err = stderr.decode(errors="replace")
        print(
            f"  WARNING: {reviewer_label} reviewer JSON repair exited with code "
            f"{proc.returncode}",
            file=sys.stderr,
        )
        if err:
            print(f"    stderr: {err[:500]}", file=sys.stderr)

    parsed = parse_review_payload(raw, allow_embedded=proc.returncode == 0)
    if parsed is None:
        return ReviewRepairAttempt(
            raw_output=raw,
            issues=[],
            parse_error=True,
            elapsed_s=elapsed,
            returncode=proc.returncode,
        )

    return ReviewRepairAttempt(
        raw_output=raw,
        issues=list(parsed.issues),
        payload=parsed,
        parse_error=False,
        elapsed_s=elapsed,
        returncode=proc.returncode,
    )


async def _repair_review_json(
    agent_name: str,
    raw_output: str,
    cwd: Path,
    iteration_dir: Path | None = None,
    label: str | None = None,
) -> tuple[ReviewPayload | None, list[ReviewRepairAttempt]]:
    if not raw_output.strip():
        return None, []

    reviewer_label = label or agent_name
    attempts: list[ReviewRepairAttempt] = []
    for attempt_number in range(1, REVIEW_REPAIR_ATTEMPTS + 1):
        print(
            f"  Attempting {reviewer_label} reviewer JSON repair "
            f"({attempt_number}/{REVIEW_REPAIR_ATTEMPTS})...",
            file=sys.stderr,
        )
        attempt = await _run_single_repair_attempt(
            agent_name,
            raw_output,
            cwd,
            iteration_dir=iteration_dir,
            previous_attempt=attempts[-1] if attempts else None,
            label=reviewer_label,
        )
        attempts.append(attempt)
        if not attempt.parse_error:
            return attempt.payload, attempts

    return None, attempts


async def _run_single_reviewer_attempt(
    reviewer: str | ReviewerSpec,
    prompt: str,
    cwd: Path,
    iteration_dir: Path | None = None,
) -> ReviewResult:
    """Spawn a single reviewer subprocess and collect its output."""
    spec = (
        reviewer
        if isinstance(reviewer, ReviewerSpec)
        else ReviewerSpec(reviewer, "core")
    )
    agent_name = spec.agent_name
    cmd, env, input_payload = _prepare_reviewer_process(
        agent_name,
        prompt,
        cwd,
        iteration_dir=iteration_dir,
    )

    # Keep a prompt snapshot for parity with existing diagnostics cleanup.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    started = time.monotonic()
    proc: asyncio.subprocess.Process | None = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=(
                asyncio.subprocess.PIPE
                if input_payload is not None
                else asyncio.subprocess.DEVNULL
            ),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=input_payload),
            timeout=REVIEWER_TIMEOUT,
        )
    except asyncio.TimeoutError:
        elapsed = time.monotonic() - started
        print(
            f"  WARNING: {spec.label} reviewer timed out after {REVIEWER_TIMEOUT // 60} minutes",
            file=sys.stderr,
        )
        if proc is not None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
        return ReviewResult(
            agent_name=agent_name,
            role_name=spec.role_name,
            raw_output="",
            elapsed_s=elapsed,
            infrastructure_status="timed_out",
            status_detail=f"reviewer exceeded {REVIEWER_TIMEOUT} seconds",
        )
    except OSError as exc:
        elapsed = time.monotonic() - started
        print(
            f"  WARNING: {spec.label} reviewer could not start: {exc}",
            file=sys.stderr,
        )
        return ReviewResult(
            agent_name=agent_name,
            role_name=spec.role_name,
            raw_output="",
            elapsed_s=elapsed,
            infrastructure_status="tool_failed",
            status_detail=f"reviewer process could not start: {exc}",
            stderr_output=str(exc),
        )
    finally:
        Path(prompt_file).unlink(missing_ok=True)

    elapsed = time.monotonic() - started
    raw = stdout.decode(errors="replace")
    err = stderr.decode(errors="replace")
    if proc.returncode != 0:
        print(
            f"  WARNING: {spec.label} reviewer exited with code {proc.returncode}",
            file=sys.stderr,
        )
        if err:
            print(f"    stderr: {err[:500]}", file=sys.stderr)

    if _reviewer_output_is_timeout(raw):
        print(
            f"  WARNING: {spec.label} reviewer reported an internal timeout",
            file=sys.stderr,
        )
        return ReviewResult(
            agent_name=agent_name,
            role_name=spec.role_name,
            raw_output=raw,
            issues=[],
            elapsed_s=elapsed,
            returncode=proc.returncode,
            infrastructure_status="timed_out",
            status_detail="reviewer reported an internal timeout",
            stderr_output=err,
        )

    payload = parse_review_payload(raw, allow_embedded=proc.returncode == 0)
    if payload is None:
        print(
            f"  WARNING: {spec.label} reviewer output could not be parsed as JSON",
            file=sys.stderr,
        )
        repaired, repair_attempts = await _repair_review_json(
            agent_name,
            raw,
            cwd,
            iteration_dir=iteration_dir,
            label=spec.label,
        )
        if repaired is not None and repaired.infrastructure_status != "complete":
            print(
                f"  WARNING: {spec.label} reviewer JSON repair reported "
                f"{repaired.infrastructure_status}",
                file=sys.stderr,
            )
            return ReviewResult(
                agent_name=agent_name,
                role_name=spec.role_name,
                raw_output=raw,
                issues=[],
                assessment=repaired.assessment,
                repair_attempts=repair_attempts,
                elapsed_s=elapsed,
                returncode=proc.returncode,
                infrastructure_status=repaired.infrastructure_status,
                status_detail=repaired.status_detail,
                stderr_output=err,
            )
        if repaired is not None:
            print(
                f"  Repaired {spec.label} reviewer JSON on attempt "
                f"{len(repair_attempts)}",
                file=sys.stderr,
            )
            return ReviewResult(
                agent_name=agent_name,
                role_name=spec.role_name,
                raw_output=raw,
                issues=list(repaired.issues),
                assessment=repaired.assessment,
                parse_repaired=True,
                repair_attempts=repair_attempts,
                elapsed_s=elapsed,
                returncode=proc.returncode,
                stderr_output=err,
            )

        if proc.returncode != 0:
            return ReviewResult(
                agent_name=agent_name,
                role_name=spec.role_name,
                raw_output=raw,
                issues=[],
                repair_attempts=repair_attempts,
                elapsed_s=elapsed,
                returncode=proc.returncode,
                infrastructure_status="tool_failed",
                status_detail=(
                    f"reviewer exited with code {proc.returncode} without a "
                    "parseable review"
                ),
                stderr_output=err,
            )

        return ReviewResult(
            agent_name=agent_name,
            role_name=spec.role_name,
            raw_output=raw,
            issues=[],
            repair_attempts=repair_attempts,
            elapsed_s=elapsed,
            returncode=proc.returncode,
            infrastructure_status="parse_failed",
            status_detail="reviewer output remained unparseable after JSON repair",
            stderr_output=err,
        )

    if payload.infrastructure_status != "complete":
        return ReviewResult(
            agent_name=agent_name,
            role_name=spec.role_name,
            raw_output=raw,
            issues=[],
            assessment=payload.assessment,
            elapsed_s=elapsed,
            returncode=proc.returncode,
            infrastructure_status=payload.infrastructure_status,
            status_detail=payload.status_detail,
            stderr_output=err,
        )

    return ReviewResult(
        agent_name=agent_name,
        role_name=spec.role_name,
        raw_output=raw,
        issues=payload.issues,
        assessment=payload.assessment,
        elapsed_s=elapsed,
        returncode=proc.returncode,
        stderr_output=err,
    )


def _attempt_from_result(result: ReviewResult) -> ReviewAttempt:
    return ReviewAttempt(
        raw_output=result.raw_output,
        infrastructure_status=result.infrastructure_status,
        status_detail=result.status_detail,
        stderr_output=result.stderr_output,
        elapsed_s=result.elapsed_s,
        returncode=result.returncode,
        parse_repaired=result.parse_repaired,
        repair_attempts=result.repair_attempts,
    )


async def _run_single_reviewer(
    reviewer: str | ReviewerSpec,
    prompt: str,
    cwd: Path,
    iteration_dir: Path | None = None,
) -> ReviewResult:
    """Run a reviewer, retrying infrastructure failures independently once."""
    spec = (
        reviewer
        if isinstance(reviewer, ReviewerSpec)
        else ReviewerSpec(reviewer, "core")
    )
    prior_attempts: list[ReviewAttempt] = []
    for attempt_number in range(1, REVIEWER_ATTEMPTS + 1):
        result = await _run_single_reviewer_attempt(spec, prompt, cwd, iteration_dir)
        if result.infrastructure_status == "complete":
            result.prior_attempts = prior_attempts
            result.retry_count = len(prior_attempts)
            return result
        if attempt_number < REVIEWER_ATTEMPTS:
            prior_attempts.append(_attempt_from_result(result))
            print(
                f"  Retrying {spec.label} reviewer after "
                f"{result.infrastructure_status} ({attempt_number}/{REVIEWER_ATTEMPTS})...",
                file=sys.stderr,
            )

    result.prior_attempts = prior_attempts
    result.retry_count = len(prior_attempts)
    return result


async def run_reviewers(
    design_doc_content: str,
    cwd: Path,
    reviewer_specs: tuple[ReviewerSpec, ...] | list[ReviewerSpec],
    role_guidelines: dict[str, str],
    deferred_issues: list[dict] | None = None,
    iteration_dir: Path | None = None,
    final_iteration: bool = False,
) -> list[ReviewResult]:
    """Spawn the chosen reviewers concurrently with role-specific prompts."""
    specs = tuple(reviewer_specs)
    if not specs:
        raise ValueError("At least one reviewer must be selected.")
    unknown = [
        spec.agent_name for spec in specs if not is_supported_reviewer(spec.agent_name)
    ]
    if unknown:
        raise ValueError(f"Unknown reviewer(s): {', '.join(unknown)}")

    tasks = []
    for spec in specs:
        prompt = build_reviewer_prompt(
            design_doc_content,
            role_guidelines[spec.role_name],
            role_name=spec.role_name,
            deferred_issues=deferred_issues,
            final_iteration=final_iteration,
        )
        tasks.append(_run_single_reviewer(spec, prompt, cwd, iteration_dir))

    results = await asyncio.gather(*tasks)

    return list(results)
