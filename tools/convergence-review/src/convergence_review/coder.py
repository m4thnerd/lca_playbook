from __future__ import annotations

import asyncio
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .convergence import BLOCKING_SEVERITIES, format_quoted_severity_list
from .prompts import (
    CODER_PRIOR_DEFERRALS_CONTEXT,
    CODER_PROMPT,
    INITIAL_CODER_PROMPT,
)
from .reviewers import _format_deferrals_for_prompt
from .llm_config_loader import llm_config


CODER_TIMEOUT = 45 * 60  # 45 minutes

# Maps coder agent name to its CLI command builder
CODER_COMMANDS: dict[str, list[str]] = {
    name: list(command)
    for name, command in llm_config.CONVERGENCE_REVIEW_CODER_COMMANDS.items()
}


@dataclass
class CoderResult:
    output: str
    elapsed_s: float
    returncode: int | None


def _get_coder_command(coder_agent: str) -> list[str]:
    """Return the CLI command list for the given coder agent."""
    if coder_agent in CODER_COMMANDS:
        return list(CODER_COMMANDS[coder_agent])

    # opencode:<model> format
    if coder_agent.startswith("opencode:"):
        model = coder_agent.split(":", 1)[1]
        return [
            "opencode",
            "run",
            "-m",
            model,
            "--variant",
            llm_config.OPENCODE_VARIANT,
        ]

    raise ValueError(f"Unknown coder agent: {coder_agent}")


def build_coder_prompt(
    design_doc_content: str,
    consolidated_reviews: str,
    review_guidelines: str | None = None,
    deferred_issues: list[dict] | None = None,
) -> str:
    guidelines_section = ""
    if review_guidelines:
        guidelines_section = f"REVIEW GUIDELINES:\n{review_guidelines}\n\n"

    prior_context = ""
    if deferred_issues:
        prior_context = CODER_PRIOR_DEFERRALS_CONTEXT.format(
            formatted_deferrals=_format_deferrals_for_prompt(deferred_issues),
        )

    return CODER_PROMPT.format(
        design_doc_content=design_doc_content,
        review_guidelines_section=guidelines_section,
        consolidated_reviews=consolidated_reviews,
        prior_deferrals_context=prior_context,
        blocking_severities=format_quoted_severity_list(BLOCKING_SEVERITIES),
    )


def build_initial_coder_prompt(
    design_doc_content: str,
    review_guidelines: str | None = None,
) -> str:
    guidelines_section = ""
    if review_guidelines:
        guidelines_section = f"REVIEW GUIDELINES:\n{review_guidelines}\n\n"

    return INITIAL_CODER_PROMPT.format(
        design_doc_content=design_doc_content,
        review_guidelines_section=guidelines_section,
    )


async def run_coder(coder_agent: str, prompt: str, cwd: Path) -> CoderResult:
    """Spawn the coder agent with a pre-built prompt and return its output."""
    cmd = _get_coder_command(coder_agent)

    # Write prompt to temp file for debugging, pipe via stdin
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    started = time.monotonic()
    proc: asyncio.subprocess.Process | None = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode()),
            timeout=CODER_TIMEOUT,
        )
    except asyncio.TimeoutError:
        print(f"ERROR: Coder ({coder_agent}) timed out after {CODER_TIMEOUT // 60} minutes", file=sys.stderr)
        if proc is not None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
        raise RuntimeError(f"Coder ({coder_agent}) timed out")
    finally:
        Path(prompt_file).unlink(missing_ok=True)

    elapsed = time.monotonic() - started
    raw = stdout.decode(errors="replace")
    if proc.returncode != 0:
        err = stderr.decode(errors="replace")
        print(f"WARNING: Coder ({coder_agent}) exited with code {proc.returncode}", file=sys.stderr)
        if err:
            print(f"  stderr: {err[:500]}", file=sys.stderr)

    return CoderResult(output=raw, elapsed_s=elapsed, returncode=proc.returncode)
