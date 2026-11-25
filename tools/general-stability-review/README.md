# general-stability-review

A small CLI for running one read-only General Stability Review (GSR) or Staff
Engineer (`--mode staff-engineer`) reviewer pass against a target git
repository.

GSR is intentionally not a full convergence loop. This helper removes the
mechanical friction of prompting a reviewer, saving the raw transcript, parsing
the JSON result, and printing a compact summary for the Lead Coding Agent (LCA).
The LCA still owns clean-pass counts, fix decisions, reruns, and escalation.
Reviewer findings are judgment input, not an automatic edit list: rare
theoretical edge cases or fixes that add more maintenance burden than the risk
justifies should be rejected, deferred, or documented rather than patched by
default.

## Installation

Requires Python 3.10+. From the `lca_playbook` repository root, install into a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ./tools/general-stability-review
```

Model pins and defaults come from the repo-root `llm_config.py` (copied from
`llm_config.example.py`; if `llm_config.py` is absent, the CLI automatically
falls back to `llm_config.example.py`).

## Usage

Run from the target repository:

```bash
general-stability-review --base origin/main --reviewer codex
```

Or pass a target repository explicitly:

```bash
general-stability-review \
  --repo /path/to/target/repo \
  --base origin/main \
  --reviewer codex
```

When a changed design doc contains `## Settled Implementation Decisions`, use
`--context` to point the reviewer to that section without restating or arguing
the decisions:

```bash
general-stability-review \
  --base origin/main \
  --reviewer codex \
  --context "Read the changed design doc's Settled Implementation Decisions as authoritative operating context."
```

Supported reviewers (configured per mode in `llm_config.py`):

- `codex` - runs `codex exec` in an ephemeral read-only sandbox (`CODEX_MODEL` / `STAFF_ENGINEER_CODEX_MODEL`);
- `claude` - runs `claude --print` in read-only plan mode with edit tools disallowed (`CLAUDE_MODEL` / `STAFF_ENGINEER_CLAUDE_MODEL`);
- `gemini` / `agy` - runs Antigravity's `agy` CLI (`AGY_MODEL` / `STAFF_ENGINEER_AGY_MODEL`) with a per-run temporary `HOME` that allows only read-only git inspection and denies write/subagent tools;
- `grok` - runs the `grok` CLI headless (`GROK_MODEL` / `STAFF_ENGINEER_GROK_MODEL`) with shell, edit, and web tools disallowed;
- `opencode:<model>` - escape hatch for a custom OpenCode model.

By default, artifacts are written under `<target-repo>/tmp/gsr-reviews/run_<timestamp>/`:

- `prompt.txt` - exact reviewer prompt;
- `raw_review.txt` - raw reviewer output;
- `stderr.txt` - reviewer stderr;
- `parsed_review.json` - parsed JSON if the reviewer followed the contract;
- `result.json` - normalized result and git context;
- `summary.md` - compact LCA-facing summary.

The command exits with status `0` for clean passes and for parsed passes with
findings, `2` for incomplete review output, and `3` for findings when
`--fail-on-findings` is passed.

Each invocation performs one pass. When the GSR playbook calls for two or three
samples of the same candidate, launch that many invocations concurrently while
keeping HEAD and the worktree frozen until all finish.

## Staff Engineer Mode (`--mode staff-engineer`)

To run a holistic Staff Engineer Review pass alongside GSR, pass
`--mode staff-engineer`:

```bash
general-stability-review \
  --mode staff-engineer \
  --base origin/main
```

In `staff-engineer` mode:

- The CLI loads [`reviewers/staff_engineer_reviewer.md`](../../reviewers/staff_engineer_reviewer.md)
  from the `lca_playbook` checkout and appends the target repository git context
  and optional `--context` notes.
- It uses the staff-mode pins and `STAFF_ENGINEER_DEFAULT_REVIEWER` from
  `llm_config.py` (with a 30-minute default timeout so the reviewer can trace
  superseded identifiers and changed contracts across the whole repository).
  Pass `--reviewer claude|codex|gemini|agy|grok` for cross-family second opinions,
  especially when another model family wrote the implementation.
- Artifacts default to `<target-repo>/tmp/staff-engineer-reviews/run_<timestamp>/`
  separate from `tmp/gsr-reviews/`.

## Failure Classification

When a reviewer does not return parseable JSON, the CLI records a diagnostic
`failure_classification` in `result.json`, `summary.md`, and terminal output
(`quota_or_billing`, `auth`, `network`, `local_state_or_sandbox`, `api_error`,
`process_exit`, `timeout`, or `unparseable_reviewer_output`). Inspect
`stderr.txt` and `raw_review.txt` before deciding whether to retry or switch
reviewers.
