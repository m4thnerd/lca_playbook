"""Example LLM harness configuration for the Lead Coding Agent Playbook.

Quick setup:
    cp llm_config.example.py llm_config.py

`llm_config.py` is ignored by Git so you can pin the models and CLI harnesses
matching your own subscriptions without merge conflicts. If `llm_config.py` is
absent, the bundled CLI tools (`convergence-review` and `general-stability-review`)
automatically fall back to this file.

Authentication stays in each CLI's own local login; never place API keys,
service-account paths, or secrets in this file.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# 1. Core reviewers: `convergence-review` and plain `general-stability-review`.
#    Adjust these aliases/model IDs to match your active CLI plans:
#      - Budget / standard plans: e.g. CLAUDE_MODEL = "sonnet", CODEX_MODEL = None
#      - Frontier multi-vendor plans: pin each vendor's strongest reasoning model
# ---------------------------------------------------------------------------
CLAUDE_MODEL = "sonnet"  # Set to "opus" on high-capacity Anthropic plans
CLAUDE_EFFORT = "high"

# Leave CODEX_MODEL = None to use whatever default model your ~/.codex/config.toml
# selects, or pin an explicit model slug (for example "o3" or your current flagship).
CODEX_MODEL: str | None = None
CODEX_REASONING_EFFORT = "high"

# Optional additional reviewer harnesses (only invoked when passed via --reviewers
# or --reviewer): Antigravity (`agy`) for Gemini and Grok Build (`grok`) for xAI.
AGY_MODEL = "gemini-4-carbon-high"  # Run `agy models` to list available IDs
GROK_MODEL = "grok-4.7"
GROK_REASONING_EFFORT = "high"


# ---------------------------------------------------------------------------
# 2. Staff Engineer reviewer (`general-stability-review --mode staff-engineer`).
#    Whole-branch design judgment benefits strongly from top-tier reasoning
#    models rather than fast/lightweight tiers.
# ---------------------------------------------------------------------------
STAFF_ENGINEER_CLAUDE_MODEL = "opus"
STAFF_ENGINEER_CLAUDE_EFFORT = "high"
STAFF_ENGINEER_CODEX_MODEL: str | None = CODEX_MODEL
STAFF_ENGINEER_CODEX_REASONING_EFFORT = "high"
STAFF_ENGINEER_AGY_MODEL = AGY_MODEL
STAFF_ENGINEER_GROK_MODEL = GROK_MODEL
STAFF_ENGINEER_GROK_REASONING_EFFORT = "high"

# Default CLI backends (CONVERGENCE_REVIEW_DEFAULT_CODER is used in --help examples;
# GENERAL_STABILITY_REVIEW_DEFAULT_REVIEWER and STAFF_ENGINEER_DEFAULT_REVIEWER are
# used when --reviewer is omitted).
CONVERGENCE_REVIEW_DEFAULT_CODER = "codex"
GENERAL_STABILITY_REVIEW_DEFAULT_REVIEWER = "codex"
STAFF_ENGINEER_DEFAULT_REVIEWER = "claude"


# ---------------------------------------------------------------------------
# 3. Optional OpenCode escape hatch (`opencode:<model>` and `gemini` coder alias).
# ---------------------------------------------------------------------------
OPENCODE_GEMINI_MODEL = "google/gemini-3.1-pro-preview"
OPENCODE_VARIANT = "high"


# ---------------------------------------------------------------------------
# 4. Read-only and workspace-write command builders per CLI harness.
# ---------------------------------------------------------------------------
def _claude_read_only(model: str, effort: str, *, allow_shell: bool) -> tuple[str, ...]:
    disallowed = "Edit,Write,NotebookEdit" if allow_shell else "Edit,Write,NotebookEdit,Bash"
    return (
        "claude",
        "--print",
        "--model",
        model,
        "--effort",
        effort,
        "--permission-mode",
        "plan",
        "--disallowed-tools",
        disallowed,
        "--no-session-persistence",
    )


def _codex_exec(model: str | None, effort: str, *, sandbox: str) -> tuple[str, ...]:
    command: tuple[str, ...] = ("codex", "exec")
    if model:
        command += ("-c", f'model="{model}"')
    command += (
        "-c",
        f'model_reasoning_effort="{effort}"',
        "--sandbox",
        sandbox,
    )
    if sandbox == "read-only":
        command += ("--ephemeral",)
    return command + ("-",)


def _agy_read_only(model: str, *, skip_permissions: bool = False) -> tuple[str, ...]:
    # Each launcher creates a per-run temporary HOME with read-only permissions
    # and appends the prompt as the --print argument.
    command: tuple[str, ...] = ("agy", "--model", model)
    if skip_permissions:
        command += ("--dangerously-skip-permissions",)
    return command + ("--print",)


def _grok_read_only(model: str, effort: str) -> tuple[str, ...]:
    # Each launcher appends `--prompt-file <path>` at invocation time.
    return (
        "grok",
        "-m",
        model,
        "--reasoning-effort",
        effort,
        "--permission-mode",
        "dontAsk",
        "--disable-web-search",
        "--no-subagents",
        "--disallowed-tools",
        "run_terminal_command,search_replace,write,spawn_subagent,enter_plan_mode,exit_plan_mode,ask_user_question",
        "--output-format",
        "plain",
    )


CONVERGENCE_REVIEW_CODER_ALIASES = {
    "gemini": f"opencode:{OPENCODE_GEMINI_MODEL}",
}
CONVERGENCE_REVIEW_BASE_CODERS = ("claude", "codex")
CONVERGENCE_REVIEW_CODER_CHOICES = ("claude", "codex", "gemini")

CONVERGENCE_REVIEW_CODER_COMMANDS = {
    "claude": (
        "claude",
        "--print",
        "--model",
        CLAUDE_MODEL,
        "--effort",
        CLAUDE_EFFORT,
        "--permission-mode",
        "acceptEdits",
    ),
    "codex": _codex_exec(CODEX_MODEL, CODEX_REASONING_EFFORT, sandbox="workspace-write"),
}

CONVERGENCE_REVIEW_REVIEWER_COMMANDS = {
    "claude": _claude_read_only(CLAUDE_MODEL, CLAUDE_EFFORT, allow_shell=False),
    "codex": _codex_exec(CODEX_MODEL, CODEX_REASONING_EFFORT, sandbox="read-only"),
    "gemini": _agy_read_only(AGY_MODEL, skip_permissions=True),
    "grok": _grok_read_only(GROK_MODEL, GROK_REASONING_EFFORT),
    "agy": _agy_read_only(AGY_MODEL, skip_permissions=True),
}
CONVERGENCE_REVIEW_AVAILABLE_REVIEWERS = tuple(
    CONVERGENCE_REVIEW_REVIEWER_COMMANDS.keys()
)

CONVERGENCE_REVIEW_REVIEWER_ROLES = {
    "architecture": {
        "tier": 1,
        "guidelines": "reviewers/architecture_critic.md",
    },
    "core": {
        "tier": 2,
        "guidelines": "reviewers/core_reviewer.md",
    },
}

GENERAL_STABILITY_REVIEWER_COMMANDS = {
    "claude": _claude_read_only(CLAUDE_MODEL, CLAUDE_EFFORT, allow_shell=True),
    "codex": _codex_exec(CODEX_MODEL, CODEX_REASONING_EFFORT, sandbox="read-only"),
    "gemini": _agy_read_only(AGY_MODEL),
    "agy": _agy_read_only(AGY_MODEL),
    "grok": _grok_read_only(GROK_MODEL, GROK_REASONING_EFFORT),
}
GENERAL_STABILITY_AVAILABLE_REVIEWERS = tuple(
    GENERAL_STABILITY_REVIEWER_COMMANDS.keys()
)

STAFF_ENGINEER_REVIEWER_COMMANDS = {
    "claude": _claude_read_only(
        STAFF_ENGINEER_CLAUDE_MODEL, STAFF_ENGINEER_CLAUDE_EFFORT, allow_shell=True
    ),
    "codex": _codex_exec(
        STAFF_ENGINEER_CODEX_MODEL, STAFF_ENGINEER_CODEX_REASONING_EFFORT, sandbox="read-only"
    ),
    "gemini": _agy_read_only(STAFF_ENGINEER_AGY_MODEL),
    "agy": _agy_read_only(STAFF_ENGINEER_AGY_MODEL),
    "grok": _grok_read_only(STAFF_ENGINEER_GROK_MODEL, STAFF_ENGINEER_GROK_REASONING_EFFORT),
}
