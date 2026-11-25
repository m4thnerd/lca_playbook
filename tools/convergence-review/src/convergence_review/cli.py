from __future__ import annotations

import argparse
import asyncio
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .convergence import BLOCKING_SEVERITIES, format_severity_list
from .design_doc_validation import validate_essential_requirements
from .llm_config_loader import llm_config
from .orchestrator import Config, run_convergence_loop
from .reviewers import (
    REVIEWER_NAMES,
    REVIEWER_ROLE_NAMES,
    ROLE_CONFIGS,
    ReviewerSpec,
    format_reviewer_specs,
    is_supported_reviewer,
    reviewer_backend_name,
)


MAX_REVIEW_GUIDELINE_RULES = 15
_R_TAG_RE = re.compile(r"^## R(\d+):\s+(.+)$")


def _validate_design_doc(path: Path) -> str:
    """Read and validate the design doc. Returns content on success, exits on failure."""
    if not path.is_file():
        print(f"ERROR: Design doc not found: {path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text()
    validation = validate_essential_requirements(content)
    if not validation.ok:
        print(f"ERROR: {validation.message}", file=sys.stderr)
        sys.exit(1)

    return content


def _validate_review_guidelines(path: Path) -> str:
    """Read and validate the review guidelines file's R-tagged taxonomy.

    Returns content on success, exits on failure. The file must contain one or
    more H2 sections of the form `## R<N>: <title>`, numbered contiguously
    starting at R1, with at most MAX_REVIEW_GUIDELINE_RULES rules.
    """
    if not path.is_file():
        print(f"ERROR: Review guidelines file not found: {path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text()

    r_tags: list[tuple[int, int, str]] = []  # (line_no, number, title)
    for i, line in enumerate(content.splitlines()):
        match = _R_TAG_RE.match(line)
        if match:
            r_tags.append((i + 1, int(match.group(1)), match.group(2).strip()))

    if not r_tags:
        print(
            "ERROR: Review guidelines file contains no R-tagged taxonomy sections.\n"
            "       Each guideline rule must be an H2 section of the form:\n"
            "           ## R<N>: <title>     (e.g. '## R1: Code Placement')",
            file=sys.stderr,
        )
        sys.exit(1)

    numbers = [n for _, n, _ in r_tags]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        print(
            "ERROR: Review guidelines R-tags must be contiguous starting at R1.\n"
            f"       Found: {numbers}\n"
            f"       Expected: {expected}",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(r_tags) > MAX_REVIEW_GUIDELINE_RULES:
        print(
            f"ERROR: Review guidelines contain {len(r_tags)} R-tagged rules "
            f"(max {MAX_REVIEW_GUIDELINE_RULES}).\n"
            "       A focused taxonomy keeps reviewer attention high. Merge\n"
            "       related rules into single invariants before adding more.",
            file=sys.stderr,
        )
        sys.exit(1)

    return content


def _validate_coder(value: str) -> str:
    """Validate the --coder argument."""
    if value in llm_config.CONVERGENCE_REVIEW_CODER_ALIASES:
        return llm_config.CONVERGENCE_REVIEW_CODER_ALIASES[value]
    valid = llm_config.CONVERGENCE_REVIEW_BASE_CODERS
    if value in valid or value.startswith("opencode:"):
        return value
    accepted = ", ".join((*llm_config.CONVERGENCE_REVIEW_CODER_CHOICES, "opencode:<model>"))
    print(
        f'ERROR: Invalid coder "{value}".\n'
        f"       Accepted values: {accepted}\n"
        f"       Example: opencode:{llm_config.OPENCODE_GEMINI_MODEL}",
        file=sys.stderr,
    )
    sys.exit(1)


START_PHASES = ("implementation", "review")


def _parse_reviewers_arg(value: str) -> tuple[ReviewerSpec, ...]:
    raw = [v.strip() for v in value.split(",") if v.strip()]
    if not raw:
        raise argparse.ArgumentTypeError(_reviewer_syntax_error("--reviewers must list at least one reviewer."))

    specs: list[ReviewerSpec] = []
    invalid: list[str] = []
    for item in raw:
        if item.count(":") != 1:
            invalid.append(item)
            continue
        agent, role = [part.strip() for part in item.split(":", 1)]
        if (
            not agent
            or not role
            or not is_supported_reviewer(agent)
            or role not in REVIEWER_ROLE_NAMES
        ):
            invalid.append(item)
            continue
        specs.append(ReviewerSpec(agent, role))

    if invalid:
        raise argparse.ArgumentTypeError(
            _reviewer_syntax_error(f"Invalid reviewer spec(s): {', '.join(invalid)}.")
        )
    seen: set[str] = set()
    deduped: list[ReviewerSpec] = []
    for spec in specs:
        if spec.label not in seen:
            seen.add(spec.label)
            deduped.append(spec)
    return tuple(deduped)


def _reviewer_syntax_error(prefix: str) -> str:
    return (
        f"{prefix} Use comma-separated <agent>:<role> entries. "
        f"Accepted agents: {', '.join(REVIEWER_NAMES)}. "
        "Claude model overrides use claude-<model> (for example, claude-opus or claude-sonnet). "
        f"Accepted roles: {', '.join(REVIEWER_ROLE_NAMES)}."
    )


def _validate_start_phase(value: str) -> str:
    if value in START_PHASES:
        return value
    print(
        f'ERROR: Invalid start phase "{value}".\n'
        f"       Accepted values: {', '.join(START_PHASES)}",
        file=sys.stderr,
    )
    sys.exit(1)


def _project_root_from_git_common_dir(common_dir: Path) -> Path | None:
    parts = common_dir.parts
    if ".git" not in parts:
        return None
    git_index = parts.index(".git")
    if git_index == 0:
        return None
    return Path(*parts[:git_index])


def _codex_project_config_error(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    common_dir_raw = result.stdout.strip()
    if result.returncode != 0 or not common_dir_raw:
        return None

    common_dir = Path(common_dir_raw)
    if not common_dir.is_absolute():
        common_dir = cwd / common_dir
    project_root = _project_root_from_git_common_dir(common_dir.resolve())
    if project_root is None:
        return None

    project_codex_dir = project_root / ".codex"
    if project_codex_dir.exists() and not project_codex_dir.is_dir():
        return (
            "Codex project config path exists but is not a directory: "
            f"{project_codex_dir}\n"
            "       Codex will try to read "
            f"{project_codex_dir / 'config.toml'} and fail before producing output.\n"
            "       Remove that file or replace it with a directory before selecting "
            "codex as a coder/reviewer."
        )
    return None


def _resolve_role_guidelines(
    reviewers: tuple[ReviewerSpec, ...],
    config_module: object = llm_config,
) -> dict[str, str]:
    config_root = getattr(config_module, "__lca_playbook_root__", None)
    if config_root is None:
        config_root = Path(getattr(config_module, "__file__")).parent
    else:
        config_root = Path(config_root)
    role_guidelines: dict[str, str] = {}
    for role in sorted({spec.role_name for spec in reviewers}):
        guidelines_path = config_root / ROLE_CONFIGS[role]["guidelines"]
        role_guidelines[role] = _validate_review_guidelines(guidelines_path)
    return role_guidelines


def _run_preflight(args: argparse.Namespace) -> Config:
    """Run pre-flight checks and return a Config if everything passes."""
    cwd = Path.cwd()

    # Check .git/ exists
    if not (cwd / ".git").exists():
        print(
            "ERROR: Not a git repository.\n"
            "       Run convergence-review from the root of a git repository.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate design doc
    design_doc_path = Path(args.design_doc)
    design_doc_content = _validate_design_doc(design_doc_path)

    # Validate coder
    coder_agent = _validate_coder(args.coder)

    # Validate start phase
    start_phase = _validate_start_phase(args.start_phase)

    reviewers = tuple(args.reviewers)
    role_guidelines = _resolve_role_guidelines(reviewers)

    reviewer_agents = {reviewer_backend_name(spec.agent_name) for spec in reviewers}
    if coder_agent == "codex" or "codex" in reviewer_agents:
        codex_config_error = _codex_project_config_error(cwd)
        if codex_config_error:
            print(f"ERROR: {codex_config_error}", file=sys.stderr)
            sys.exit(1)

    if "grok" in reviewer_agents and shutil.which("grok") is None:
        print(
            "ERROR: Grok reviewer selected but the grok CLI (`grok`) "
            "was not found on PATH.\n"
            "       Install Grok Build and authenticate with `grok login`.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve and create artifacts directory.
    # Precedence: --artifacts-dir flag > CONVERGENCE_REVIEW_ARTIFACTS_DIR env > default.
    artifacts_dir_raw = args.artifacts_dir or os.environ.get(
        "CONVERGENCE_REVIEW_ARTIFACTS_DIR"
    )
    if artifacts_dir_raw:
        artifacts_dir = Path(artifacts_dir_raw).expanduser()
        if not artifacts_dir.is_absolute():
            artifacts_dir = cwd / artifacts_dir
    else:
        artifacts_dir = cwd / "tmp" / "coding-logs"

    if artifacts_dir.exists() and not artifacts_dir.is_dir():
        print(f"ERROR: Artifacts path exists but is not a directory: {artifacts_dir}", file=sys.stderr)
        sys.exit(1)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    return Config(
        design_doc_content=design_doc_content,
        role_guidelines=role_guidelines,
        coder_agent=coder_agent,
        max_iterations=args.max_iterations,
        cwd=cwd,
        artifacts_dir=artifacts_dir,
        start_phase=start_phase,
        reviewers=reviewers,
    )


class _HelpOnErrorParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_help(sys.stderr)
        self.exit(2, f"\nerror: {message}\n")


def main() -> None:
    blocking_severities = format_severity_list(BLOCKING_SEVERITIES)
    parser = _HelpOnErrorParser(
        prog="convergence-review",
        description=(
            "Drives a coder + reviewers convergence loop against a design doc.\n"
            "Each iteration runs the selected reviewers concurrently, feeds\n"
            "findings to a coder agent, and\n"
            f"repeats until no {blocking_severities}\n"
            "issues remain or max iterations reached.\n"
            "\n"
            "The run can start from either phase:\n"
            "  - implementation: first pass at implementation for the design doc.\n"
            "  - review: review an existing implementation.\n"
            "\n"
            "Prerequisites:\n"
            "  - Run from the root of a git repo. For review-first runs, an\n"
            "    initial implementation must already exist on the current branch.\n"
            "  - Design doc must have an '# Essential Requirements' section (1-10 bullets).\n"
            "  - CLI tools installed & authenticated for the configured coder\n"
            "    and selected reviewers.\n"
            "\n"
            "Example:\n"
            "  convergence-review --start-phase implementation "
            "--design-doc docs/design.md "
            f"--coder {llm_config.CONVERGENCE_REVIEW_DEFAULT_CODER} "
            "--reviewers codex:architecture,claude:core"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--design-doc",
        metavar="PATH",
        required=True,
        help=(
            "Path to the design doc. Must contain an '# Essential Requirements'\n"
            "section with 1-10 bullet points that scope what reviewers focus on."
        ),
    )
    parser.add_argument(
        "--coder",
        metavar="AGENT",
        required=True,
        help=(
            "Coder agent. Accepted values: "
            f"{', '.join(llm_config.CONVERGENCE_REVIEW_CODER_CHOICES)}, "
            "or opencode:<model>."
        ),
    )
    parser.add_argument(
        "--start-phase",
        metavar="PHASE",
        choices=START_PHASES,
        required=True,
        help=(
            "Phase to start in: implementation or review.\n"
            "  implementation - first pass at implementation for the design doc.\n"
            "  review         - review an existing implementation."
        ),
    )
    parser.add_argument(
        "--reviewers",
        metavar="LIST",
        type=_parse_reviewers_arg,
        required=True,
        help=(
            "Comma-separated <agent>:<role> reviewers to run. "
            f"Accepted agents: {', '.join(REVIEWER_NAMES)}. "
            "Use claude-<model> to override the Claude model for one reviewer. "
            f"Accepted roles: {', '.join(REVIEWER_ROLE_NAMES)}."
        ),
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=4,
        metavar="N",
        help="Maximum review-fix iterations (default: %(default)s).",
    )
    parser.add_argument(
        "--artifacts-dir",
        metavar="DIR",
        help=(
            "Directory to write run artifacts/logs. Falls back to the\n"
            "CONVERGENCE_REVIEW_ARTIFACTS_DIR env var, then to ./tmp/coding-logs."
        ),
    )

    args = parser.parse_args()

    config = _run_preflight(args)

    print("convergence-review: starting convergence loop")
    print(f"  start phase: {config.start_phase}")
    print(f"  coder: {config.coder_agent}")
    print(f"  reviewers: {format_reviewer_specs(config.reviewers)}")
    print(f"  max iterations: {config.max_iterations}")
    print(f"  artifacts base dir: {config.artifacts_dir}")

    asyncio.run(run_convergence_loop(config))
