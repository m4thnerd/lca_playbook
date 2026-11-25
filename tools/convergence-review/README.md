# convergence-review

A CLI tool that automates the CODER <> REVIEWERS convergence loop. Starting from a design doc, it either takes a first pass at implementation or reviews an existing one, then iteratively:

1. Spawns concurrent reviewer agents configured in `llm_config.py` (or `llm_config.example.py`) to review the implementation against the design doc
2. Feeds consolidated review findings to a coder agent to address legitimate issues
3. Repeats until convergence (no blocking-severity issues) or max iterations reached
4. Produces a final summary of remaining concerns

The run can start from either phase:

- **implementation** - first pass at implementation for the design doc.
- **review** - review an existing implementation.

## Prerequisites

Install and authenticate only the CLI harnesses you choose to invoke:

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (`claude`)
- [Codex](https://github.com/openai/codex) (`codex`)
- Antigravity CLI (`agy`) - optional; used when selecting `gemini:<role>` or `agy:<role>`
- Grok Build CLI (`grok`) - optional; used when selecting `grok:<role>` (sign in with `grok login`)
- [OpenCode](https://opencode.ai/) (`opencode`) - optional; used only for the explicit `opencode:<model>` escape hatch and the `gemini` coder alias

## Installation

Requires Python 3.10+. From the `lca_playbook` repository root, install into a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ./tools/convergence-review
```

To customize models for your active subscriptions, copy the root example file:

```bash
cp llm_config.example.py llm_config.py
```

(`llm_config.py` is ignored by Git; if absent, `convergence-review` falls back to `llm_config.example.py`.)

## Usage

Run from the root of a target git repository:

```bash
convergence-review \
  --start-phase implementation \
  --design-doc docs/design.md \
  --coder codex \
  --reviewers codex:architecture,claude:core
```

If you run a multi-vendor panel across additional CLI subscriptions:

```bash
convergence-review \
  --start-phase implementation \
  --design-doc docs/design.md \
  --coder codex \
  --max-iterations 4 \
  --reviewers gemini:architecture,codex:core,claude:core,grok:core \
  --artifacts-dir tmp/coding-logs
```

Use `claude-<model>:<role>` to select a specific Claude model alias or full ID for an individual reviewer (for example `claude-opus:architecture` or `claude-sonnet:core`). Bare `claude:<role>` uses `CLAUDE_MODEL` from `llm_config.py`.

### Arguments

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--start-phase` | Yes | - | Where to begin: `implementation` or `review`. |
| `--design-doc` | Yes | - | Path to the design doc. Must contain an `# Essential Requirements` section. |
| `--coder` | Yes | - | Coder agent configured in `llm_config.py`, or `opencode:<model>`. |
| `--reviewers` | Yes | - | Comma-separated `<agent>:<role>` pairs. Built-in agents: `claude`, `codex`, `gemini`, `grok`, `agy` (plus `claude-<model>`). Built-in roles: `architecture` and `core` (additional custom tier-3 advisory roles can be added in `llm_config.py`). |
| `--max-iterations` | No | 4 | Maximum review-fix iterations. |
| `--artifacts-dir` | No | `./tmp/coding-logs` | Directory where run artifacts are written (falls back to `CONVERGENCE_REVIEW_ARTIFACTS_DIR`, then `./tmp/coding-logs`). |

## Design Doc Requirements

Your design doc **must** contain an `# Essential Requirements` section with 1-10 bullet points:

```markdown
# Essential Requirements
ER Sign-Off Status: Human-Approved

- [US-1] User can upload a CSV and see parsed results in a table
- [US-2] Validation errors display inline next to the affected row
- [US-3; Performance] Processing completes in under 30 seconds for files up to 10k rows
```

See [`requirements/convergence_review_essential_requirements.md`](../../requirements/convergence_review_essential_requirements.md) for the agent-facing drafting rules.

## How It Works

When starting in `implementation` mode, the run begins with a single coder pass that takes a first cut at the design doc before any reviewers run. From there, each iteration:

1. **Review** - Selected reviewer `agent:role` pairs run concurrently in the target repo using their role guidelines from `reviewers/`. Reviewers run in read-only mode (no edits, builds, or worktree mutations).
2. **Fix** - The coder agent receives consolidated reviews grouped by influence tier (`architecture` above `core`, with any custom tier-3 roles shown as non-blocking advisory notes) and fixes legitimate blocking issues.
3. **Converge** - The loop stops when no `architecture` or `core` blocking-severity issues remain, or max iterations is reached. Deferred issues are passed forward within the run so they are not re-raised without new reasoning. On the final iteration, coder execution is skipped so summary results reflect the final reviewed code state.

The coder may escalate (`stop_run`) when the design doc itself has a contradiction or flawed requirement; iteration halts and the run is reported as escalated for human review.

Per run, artifacts are written under `./tmp/coding-logs/run_<timestamp>/` by default:
- `run_manifest.json` - table of contents for the whole run
- `inputs/` - snapshot of the design doc, role guidelines, and rendered reviewer prompts
- `initial_implementation/` - coder prompt, output, decisions, and meta for the initial pass (implementation-first runs)
- per-iteration reviewer raw output, stderr, parsed issues, and meta (timings, infrastructure status, retry and repair counts, returncode)
- per-iteration `iteration_meta.json` with phase timings, git diff shortstat, and files touched
- final summary files (`summary.txt`, `summary.json`)

The coder starts fresh each iteration (no carried chat context) - the codebase on disk is the shared state.

### Between-Run Design Memory Checkpoint

At every run boundary, and always before a fresh invocation, the LCA reconciles durable decisions into `## Settled Implementation Decisions` in the target design doc so a fresh coder or reviewer does not reverse settled boundaries or re-propose rejected mechanisms. Keep that section canonical rather than chronological: record the accepted decision, its operating or architectural rationale, and the specific rejected expansion when recurrence is plausible.

### Reviewer Infrastructure Status and Read-Only Controls

Every reviewer ends in one of four states: `complete`, `parse_failed`, `tool_failed`, or `timed_out`. A zero-finding result counts as clean only when its status is `complete`. Malformed JSON goes through an automatic repair pass, and failed or timed-out reviewers are retried independently once before marking an architecture/core pass review-incomplete.

Backend sandboxes enforce read-only behavior: Codex uses an ephemeral `read-only` sandbox; Claude runs in `plan` mode with edit and shell tools denied; `gemini`/`agy` runs with a temporary `HOME` whose generated settings deny file writes and shell commands; and `grok` runs headless with shell, edit, write, subagent, plan, and web tools disabled.
