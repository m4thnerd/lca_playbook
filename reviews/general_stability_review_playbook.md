# General Stability Review Playbook

General Stability Review (GSR) is a lightweight review pattern for catching
ordinary PR-quality defects after an implementation is basically accepted, or on
branches that do not need a full requirements-driven `convergence-review` run.

It is intentionally not an Essential Requirements process and should not become
a second `convergence-review` loop.

## Core Question

`convergence-review` asks:

> Does this implementation satisfy the Essential Requirements?

General stability review asks:

> Are there obvious correctness, stability, deployment, data-integrity, or
> user-facing bugs that a general PR review would flag?

Good GSR findings are things the branch should not ship with, even if they were
not named directly in the design doc.

## Mental Model: Sampling, Not Dialogue

Each GSR pass is an independent sample, not a conversation turn. The reviewer
is stateless: it does not know what earlier passes found, what the LCA
rejected, or why. Think of the branch as holding two pools of potential
findings - typically zero to three legitimate defects, and a larger pool of
technically-true-but-inapplicable hazards (rare races, hardening for loads the
system will never see). Each pass draws from both pools, and sometimes draws
nothing.

Three consequences:

- A zero-finding reviewer result is a draw of zero, not proof of zero. That is
  why the non-actionable-pass guidance below calls for more than one pass on
  meaningful branches.
- Repetition is re-sampling, not corroboration. When two passes surface the
  same concern, that means the pattern is salient to a fresh reviewer reading
  this code - not that it matters in this system's operating context. Salience
  and severity are different things, and only the LCA holds the operating
  context that separates them.
- A non-actionable pass is an LCA verdict, not a reviewer output shape. It may
  contain findings at any severity when none warrants a current-branch
  correction after the LCA applies project context and the rubric below.

Examples of actionable GSR catches:

- a generated static artifact is missing after frontend changes;
- a migration, fixture, or build output is incomplete;
- an event path can create misleading analytics state;
- a permission, tenant, or data-boundary check is bypassed;
- tests pass incidentally without actually covering the changed invariant.

## What GSR Is Not

GSR is not a broad codebase audit, a refactoring wish list, a design-doc rewrite
process, an automated fix loop, or a reason to reopen accepted product choices.
The LCA owns judgment; reviewer agents provide fresh signal and do not decide
scope.

## When To Run It

Run GSR when:

- `convergence-review` has finished and the branch looks basically complete;
- a small or medium branch did not need `convergence-review` but still deserves a
  fresh PR-style review;
- CI, deployment, generated assets, migrations, or runtime wiring are plausible
  risk areas;
- a prior review found a subtle bug and the LCA wants a second pass after fixing
  it.

When a diff adds or changes API payloads, backend serializers/DTOs, frontend
TypeScript contract types, or store state shapes, also apply the focused checks
in [`full_stack_data_shape_review.md`](full_stack_data_shape_review.md).

Usually skip GSR when the change is trivial and already validated, the branch is
still structurally incomplete, or the task scope is not yet accepted.

## Staff Engineer Review Companion

Alongside GSR passes for a non-trivial branch, the LCA may also run a **Staff
Engineer Review** pass (`general-stability-review --mode staff-engineer`) using
[`reviewers/staff_engineer_reviewer.md`](../reviewers/staff_engineer_reviewer.md).
Where GSR hunts for point defects, the Staff Engineer pass acts as a generalist
Staff / Principal Engineer - judging both whether the diff (including its tests)
can achieve the same benefit in materially less code or lower architectural
pressure, and whether what is there is built right: one source of truth, state
modeled directly rather than inferred, cutovers completed across every consumer
in the repository, and failures fixed at their cause rather than silenced.

Use a top-tier reasoning model for the Staff Engineer pass (configured via the
`STAFF_ENGINEER_*` constants in `llm_config.py`). On a time-travel benchmark
against a complex full-stack production PR with 9 human Staff Engineer findings,
top-tier reasoning models recovered 7.5 to 9 of 9 findings while a one-sided
bloat-only prompt scored 0 across all vendors and mid-tier models recovered
only ~5 of 9. Pass `--reviewer claude|codex|gemini|agy|grok` when you want a
cross-family second opinion (especially when the same model family wrote the
implementation). The LCA may also consult
[`reviewers/staff_engineer_reviewer.md`](../reviewers/staff_engineer_reviewer.md)
mid-flight as an on-demand situational advisor.

## Reviewer Selection

Ask a fresh reviewer agent to inspect the branch diff versus the base ref.
Model pins per role live in the repo-root `llm_config.py` (copied from
`llm_config.example.py`). If a reviewer finds a legitimate issue, invite that
same reviewer back after the fix; clean passes matter most from reviewers that
previously found real issues or from the strongest available reviewer.

## Review Prompt

When invoking manually without the CLI helper, keep the prompt short and avoid
turning GSR into an ER-centered review:

```text
Review this branch diff as a general pull request review. Focus on correctness,
stability, deployment/runtime behavior, data integrity, test reliability, and
user-visible bugs. Prefer concrete issues over broad refactor suggestions. Treat
rare theoretical edge cases as non-actionable unless they have meaningful impact
in the expected operating context or a simple low-complexity fix.
```

When recurring noise depends on context the reviewer cannot infer from code,
promote the authoritative boundary into the design doc's
`## Settled Implementation Decisions` section before requesting more samples,
and pass `--context` to point the reviewer to that section rather than arguing
it inline.

## Actionability Rubric

Before changing code for a GSR finding, ask:

- is the premise true in the real product and operating context?
- how likely is the failure in normal use, and what is the impact if it happens?
- can the fix stay simpler than the risk it addresses?
- will the fix make future LCA work easier or harder?

Usually actionable: incorrect user-visible behavior; misleading, corrupted, or
inconsistent data; deployment, build, migration, fixture, or generated-artifact
problems; violated invariants needed for the branch's accepted intent;
permission, security, tenant, or boundary risks; test reliability issues.

Usually non-actionable: broad refactors; cleaner abstractions without a concrete
bug; performance micro-optimizations without measured risk; speculative edge
cases requiring new architecture; rare timing, concurrency, or admin-workflow
races in low-traffic operational paths (unless they risk serious data loss or
security exposure).

When uncertain, classify each finding explicitly: `fix now`, `clarify docs or PR
description only`, `defer follow-up`, `reject as false premise`, `reject as
scope churn`, or `ask the human`.

## Architecture Pressure Checkpoint

Before implementing any GSR finding whose fix would expand scope, cross module
boundaries, or add durable machinery (locks, helper modules, transaction
contracts, new operational concepts), delegate a quick independent
architecture-pressure check using
[`architecture_pressure_scoring.md`](../requirements/architecture_pressure_scoring.md):

- Is this a real, likely defect in this system's actual operating context, or
  hypothetical hardening?
- What is the smallest correct target state, and what retained module or
  contract burden does the fix add?
- Is the pressure delta worth the risk reduction?

Delegating the checkpoint is the point: once a confident reviewer has argued for
hardening, the LCA's own in-context judgment is anchored toward the reviewer's
framing.

## Fix Routing

The LCA delegates every accepted fix with no size carve-out - not a missing
generated artifact, not a one-file bug, not a focused regression test. One line
can spiral into a multi-hundred-thousand-token rabbit hole that clouds the LCA's
judgment for the rest of the session. Supply a compact packet (`accepted
finding`, `why it matters`, `expected minimal fix`, `relevant files`,
`validation target`, `non-goals`) rather than the full review transcript.

## Concurrent Review Rounds & Non-Actionable-Pass Guidance

Run all GSR passes intended to evaluate the same candidate concurrently as one
read-only review round while keeping HEAD and the worktree frozen.

A pass is **non-actionable** when, after LCA adjudication, it produces no
accepted current-branch code correction (even if the reviewer assigned high
severity to a rejected false premise or scope churn).

Calibration defaults (not rigid quotas):

- **After `convergence-review`:** three independent non-actionable passes
  against the same frozen candidate, launched as one concurrent round. Once the
  GSR phase reaches five completed passes in total, two concurrent
  non-actionable passes against the corrected candidate are sufficient unless
  branch risk is unusually high.
- **Standalone GSR (without `convergence-review`):** two concurrent
  non-actionable passes under 10 changed files and 500 changed lines; three
  above either threshold.

Only an LCA-accepted current-branch code correction creates a new candidate and
resets the pass count; doc-only clarifications, rejections, and deferrals do
not.

## Iteration Brake

Each GSR round after `convergence-review` faces a higher marginal-value bar.
Stop the loop when repeated GSR passes mostly surface edge cases, rare
operational races, already-settled proposals, or suggestions requiring more
machinery than the accepted scope deserves, regardless of reviewer severity
labels. Because GSR passes are stateless, a fresh reviewer re-raising a
previously rejected concern is re-sampling, not new corroboration; reopen a
rejected finding only when a pass presents concrete new reasoning.

## Case Study: The Bulk-Grant Lock Helper (real incident)

A simple admin feature - one button granting a user premium access to every
course they lacked, on an internal ops page used by roughly one admin at a
time - was expected to take about a minute to implement. A GSR reviewer flagged
a theoretical race: two admins clicking at the exact same instant could create
duplicate access records. The LCA accepted the finding and added advisory
locking and transaction-ordering machinery across three modules. A second GSR
pass raised another variant of the race, and roughly forty minutes went into
hardening a workflow whose real-world concurrency is one admin.

An independent architecture-pressure pass scored the simple bulk grant at
pressure 2 and the lock-helper branch at 3 (+1 avoidable pressure), leaving a
permanent cross-module locking contract against a near-nonexistent operational
event. The right disposition: reject the concurrency hardening with rationale
and keep the bulk grant local.

## Running the CLI Helper

Install from the `lca_playbook` repository root into a virtual environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ./tools/general-stability-review
```

Run GSR or Staff Engineer mode from any target git repository:

```bash
general-stability-review --base origin/main --reviewer codex
general-stability-review --mode staff-engineer --base origin/main
```

See [`tools/general-stability-review/README.md`](../tools/general-stability-review/README.md)
for full CLI options and output artifacts.
