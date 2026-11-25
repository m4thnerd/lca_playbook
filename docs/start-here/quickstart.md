# Quickstart

This quickstart walks through the smallest complete Lead Coding Agent (LCA)
workflow. Use it on one bounded feature or fix before adopting multi-slice
slicing, overnight runs, or multi-stream coordination.

## What You Need

- A target repository.
- One human-owned outcome or problem to solve.
- A coding-agent harness (`claude`, `codex`, `agy`, `grok`, `opencode`, etc.).
- At least one fresh, independent read-only reviewer session.

The Python CLIs (`convergence-review` and `general-stability-review`) automate
the build/review and stability passes, and you can also run every step directly
through subagents while learning the flow.

## Your First Slice in 7 Steps

### 1. Ground in the Target Repo

Read the target repository's instructions, current code seams, and any relevant
[Module Charter](../../architecture/module_charters.md). If running
autonomously across turns, save the user's exact words in a
[Verbatim Human Intent Reference](../../requirements/verbatim_human_intent_reference_playbook.md).

### 2. Draft & Preflight User Stories

Write concise user stories (`As a <actor>, I want <outcome>, so that <value>`)
and run the
[User-Story Preflight](../../requirements/user_story_preflight_scoring.md)
(plus [Agentic PM Preflight](../../requirements/agentic_pm_user_story_preflight.md)
when AI agents participate in the workflow). Remove unsupported scope and
disguised implementation steps before moving on.

### 3. Draft & Preflight 1-10 Essential Requirements

Write 1-10 plain-language bullets under `# Essential Requirements` (using
[ER Drafting Reference](../../requirements/convergence_review_essential_requirements.md)),
mark `ER Sign-Off Status: Human-Approved | Agent-Drafted (Unreviewed)`, and run
both ER preflights concurrently:

- [ER Scoring Preflight](../../requirements/convergence_review_preflight_requirements_scoring.md)
  (`Minimal = 5/5`, `Clear = 5/5`, and visible [Architecture Pressure](../../requirements/architecture_pressure_scoring.md));
- [ER Justification Preflight](../../requirements/convergence_review_preflight_requirements_justification.md)
  (necessity, proportionality to [operating conditions](../../example-case-studies/operating-conditions/lean-saas-team.md),
  and inline tag legitimacy).

Scrutinize every word of the final ER bullets so the behavioral contract is
unambiguous and free of internal implementation clutter.

### 4. Check Positional Lane Posture

Check whether each touched code responsibility sits in the **Critical**,
**Careful**, **Full-Spec**, or **Fast** lane
([Module Charters](../../architecture/module_charters.md)). Apply each lane's
discipline where its conditions hold rather than labeling the whole feature with
one lane.

### 5. Implement & Converge

Install the bundled CLI once inside your `lca_playbook` checkout, then run
`convergence-review` from the root of your **target repository** using whichever
agent CLIs you have installed:

```bash
# One-time editable install inside your lca_playbook checkout:
cd /path/to/lca_playbook && python3 -m venv .venv
.venv/bin/pip install -e ./tools/convergence-review -e ./tools/general-stability-review

# Run inside your target repository:
cd /path/to/your-repo
/path/to/lca_playbook/.venv/bin/convergence-review --start-phase implementation \
  --design-doc docs/design/my_slice.md \
  --coder codex \
  --reviewers codex:architecture,claude:core
```

See [tools/convergence-review/README.md](../../tools/convergence-review/README.md)
for CLI options and [lca_playbook.md](../../lca_playbook.md#when-it-does-not-converge)
for dispositioning residual findings at iteration caps.

### 6. Validate & Stabilize (GSR)

Run your test suite and [smoke tests](../../testing/smoke_testing.md), then run
independent [General Stability Review](../../reviews/general_stability_review_playbook.md)
and [Staff Engineer](../../reviewers/staff_engineer_reviewer.md) passes on the
frozen candidate from your target repository:

```bash
/path/to/lca_playbook/.venv/bin/general-stability-review --reviewer codex --base main
/path/to/lca_playbook/.venv/bin/general-stability-review --mode staff-engineer --reviewer claude --base main
```

Fix genuine branch defects (which resets the clean-pass counter) and reject
speculative over-engineering with brief rationale.

### 7. Hand Off Truthful Evidence

Report separately what was *implemented*, *locally validated*, *reviewed*,
*deferred*, *merged*, *deployed*, and *operationally proven* (and include a
visual HTML decision page via [ui_review_format.md](../../uiux/ui_review_format.md)
for any user-facing UI change).

## Next Reading

- [Mental Model](mental-model.md)
- [Choosing a Workflow](choosing-a-workflow.md)
- [Full LCA Playbook](../../lca_playbook.md)
- [Example Case Studies](../../example-case-studies/README.md)
