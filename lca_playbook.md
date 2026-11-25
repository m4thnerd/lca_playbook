# Agentic Coding Playbook

This playbook is for the Lead Coding Agent (LCA): the agent helping a human
owner orchestrate software design, implementation, review, validation, and
handoff work.

The human owner may bring the LCA into the work at any point: requirements
drafting, design-doc cleanup, implementation, review, stabilization, CI
follow-up, or PR handoff. This document gives the LCA shared vocabulary for the
available building blocks so they can be composed concisely during an active
session.

The repository and playbook are model-agnostic and harness-agnostic by design
(Claude Code, Codex, Antigravity `agy`, Grok CLI, OpenCode, or equivalents).
Operational CLI commands and model pins live in local `llm_config.py` (copied
from tracked [llm_config.example.py](llm_config.example.py); tools fall back to
`llm_config.example.py` automatically when `llm_config.py` is absent). If more
than two weeks have passed since a local `llm_config.py` pin table was updated,
ask the human owner before changing pins; never downgrade review roles to
lightweight/mini models silently.

For autonomous unattended shifts, see
[lca_overnight_playbook.md](lca_overnight_playbook.md). For coordinating
multiple independently progressing workstreams, see
[engineering_director_playbook.md](engineering_director_playbook.md).

Any request involving user-facing UI/UX starts with [`uiux/`](uiux/ui_ux_design_patterns.md)
and its standing [design patterns](uiux/ui_ux_design_patterns.md), plus optional
[UX persona review](uiux/ux_persona_review.md).

> **REQUIRED AT THE START OF EVERY LCA SESSION:** Read and apply every case
> study in [`example-case-studies/requirements-risk/`](example-case-studies/requirements-risk/)
> plus any local calibration files in `case-studies/local/` (see
> [`case-studies/local/README.md`](case-studies/local/README.md)). Requirements
> bloat and review-driven overbuilding are the most consistent failure modes in
> agent-led engineering. Stay vigilant even when a session begins via handoff
> and even when a reviewer marks a speculative concern as blocking.

## Playbook Document Root Location

When referenced from inside another target repository via a symlink (typically
`local/lca_playbook/`), resolve relative playbook paths inside the playbook
checkout rather than the target repository root.

## Core Idea

The LCA's attention is the scarce resource.

The LCA owns the engineering outcome: requirements judgment, scope control,
sequencing, integration, review adjudication, and truthful acceptance. It
delegates 100% of implementation and 100% of line-level code review to focused
tools, independent agent sessions, and compact plain-English task packets, and
it arranges the validation needed to establish the requested user outcome.

A single LCA can lead an autonomous build through integration and deployment
within the human owner's authorization. Absence of an Engineering Director does
not make the human the integration manager: requirements interpretation,
evaluating evidence, catching incomplete behavior, and deciding whether a review
finding matters are ordinary LCA duties that do not justify adding a second
leadership layer.

The LCA writes no product code and reviews no code line by line - not even a
"one-line" fix. One line can spiral into a multi-hundred-thousand-token rabbit
hole that clouds the judgment the LCA exists to provide for the rest of the
session. When a bug appears, delegate diagnosis-or-fix with known context
pre-supplied rather than opening source files directly. This holds even when the
delegate runs on the same model as the LCA: the benefit is attention isolation
per level of abstraction, not model tiering.

Requirements, design docs, decision logs, and reports remain the LCA's own
writing surface, along with final judgment over delegated findings. Delegate
noisy test suite runs and receive a compact pass/fail summary with actionable
failures only.

### Requirements-Risk Calibration

Before the LCA does either of the following in a session, read and apply every
Markdown case study in
[`example-case-studies/requirements-risk/`](example-case-studies/requirements-risk/)
plus any files in `case-studies/local/` (including `operating-conditions.md` when
present; see example
[lean-saas-team.md](example-case-studies/operating-conditions/lean-saas-team.md)):

- draft, revise, preflight, or approve user stories or Essential Requirements;
  or
- dispatch independent agents to find implementation defects, or adjudicate
  findings from `convergence-review`, GSR, situational reviews, CI, or automated
  PR review.

Use these cases and the repository's real operating conditions to separate
material product/branch defects from technically coherent but disproportionate
safeguards, speculative concurrency/recovery protocols, and hyperscale machinery
that does not fit the team's maintenance capacity.

#### Autonomous Story Discipline (No Autonomous Story Invention)

Story brainstorming happens with the human owner in the loop. Once autonomous
refinement or implementation begins, the LCA never brainstorms new features or
user stories into scope (because downstream reviewers treat every in-scope story
as mandatory):

- **Gap-catching:** add a story only when plainly implied by written human
  context in hand (a forgotten transcription of stated intent with trivially low
  Architecture Pressure), logging the addition explicitly.
- **Capture, do not adopt:** record genuinely new product ideas noticed mid-run
  in the decisions log or morning report as proposed stories for the human to
  triage later; never adopt them into current-slice scope autonomously.

#### Verbatim Human Intent Reference & ER Sign-Off Status

When the LCA runs autonomously from initial human intent without a human
checkpoint reviewing the drafted `# Essential Requirements`, downstream
reviewers (`ER Justification Preflight`, the `architecture` critic, and `GSR`)
need a reliable way to distinguish what the human asked for from mechanisms the
LCA extrapolated:

1. Maintain a companion **Verbatim Human Intent Reference** file linked at the
   top of the design doc (`Verbatim Human Intent Reference: <path>`), following
   [verbatim_human_intent_reference_playbook.md](requirements/verbatim_human_intent_reference_playbook.md).
2. Record `ER Sign-Off Status: Human-Approved | Agent-Drafted (Unreviewed)`
   immediately beneath `# Essential Requirements`.
3. When `ER Sign-Off Status` is `Agent-Drafted (Unreviewed)`:
   - Keep the ER list as small as the request warrants (1-2 ERs for a focused
     1-2 goal request; never pad the list).
   - Never use exception labels (`[Reliability]`, `[Data Integrity]`,
     `[Maintainability]`) to invent new operational refusal gates, interactive
     prompts, bootstrap/recovery modes, or state machines absent from the
     Verbatim Human Intent Reference.
   - Downstream critics compare `# Essential Requirements` and the
     implementation against the linked Verbatim Human Intent Reference and flag
     unrequested bloat for deletion rather than demanding second-order fixes
     inside it.

## Building Blocks

### Convergence-Review

`convergence-review` ([tools/convergence-review/README.md](tools/convergence-review/README.md))
is the LCA's primary implementation delegation path for moderate/high-complexity
slices with a design doc:

1. A coder agent implements the design doc from the current branch state (or the
   run starts at `review` on an existing implementation).
2. Independent reviewer agents evaluate the implementation against `# Essential
   Requirements`.
3. The coder receives consolidated findings and repairs legitimate requirement
   gaps.
4. The loop repeats until zero blocking findings remain, the iteration cap is
   reached, or an unresolved design contradiction triggers escalation.

It answers: *"Does this implementation satisfy the Essential Requirements?"*

#### Required Companion Context: GSR

Before initiating any `convergence-review` run, read the full
[General Stability Review playbook](reviews/general_stability_review_playbook.md).
`convergence-review` and GSR are sequential halves of one acceptance workflow:
`convergence-review` verifies explicit Essential Requirements, while GSR samples
for ordinary correctness, data-integrity, deployment, and runtime defects
outside those requirements. Treat reviewer output in both stages as
probabilistic samples rather than automatic edit orders.

#### Essential Requirements

Essential Requirements (ERs) are the 1-10 high-signal truths an acceptable
implementation must satisfy. For humans, ERs form a compact, jargon-free
specification surface where every word can be scrutinized cleanly (see
[README.md](README.md#essential-requirements-high-leverage-human-specifications)
and the real rewrites in
[requirements-language-clarity](example-case-studies/requirements-language-clarity/)).
For agents drafting or reviewing ERs, follow
[convergence_review_essential_requirements.md](requirements/convergence_review_essential_requirements.md)
and [core_reviewer.md](reviewers/core_reviewer.md).

#### Canonical Design Doc Shape

```text
# Feature Name

Verbatim Human Intent Reference: docs/design/<feature>_human_intent.md

## Goal

## User Stories

US-1
As a <user or stakeholder>, I want <capability or outcome>, so that <purpose or value>.

## Current Architecture Fit

## Proposed Approach

## Settled Implementation Decisions

## Deferred Stories / Non-Goals

## Validation Plan

# Essential Requirements
ER Sign-Off Status: Agent-Drafted (Unreviewed)

- [US-1] ...
- [US-2; Data Integrity] ...
- [Maintainability] ...
```

#### Massive Brainstorms: Parent Doc + Slices

When scope exceeds one bounded design document (more than the 10-bullet
`# Essential Requirements` cap), split it into cohesive outcome slices using
[design_doc_slicing.md](requirements/design_doc_slicing.md). Keep the parent
thin: objective, global non-goals, slice status index, shared interfaces, and
actual dependencies. Refine each slice just in time before implementation.

A slice boundary does not impose a rigid serial execution chain: sequence work
only where an unresolved contract or shared mutation requires it. Once a shared
interface is stable, let independently owned implementation, fixtures, UI
composition, and integration prep proceed concurrently (keeping one writer per
checkout and one deployment owner).

#### Mandatory Requirements Preflights

Every implementation slice runs three focused requirements reviews before coding:

1. [User-story preflight](requirements/user_story_preflight_scoring.md) (source,
   shape, and minimal scope);
2. [ER scoring preflight](requirements/convergence_review_preflight_requirements_scoring.md)
   (Minimal, Clear, and Architecture Pressure per
   [architecture_pressure_scoring.md](requirements/architecture_pressure_scoring.md));
   and
3. [ER justification preflight](requirements/convergence_review_preflight_requirements_justification.md)
   (mechanism necessity, proportionality, and inline tag legitimacy).

Run all three even when a slice looks small; a short slice makes a fast pass.
Run ER scoring and ER justification concurrently per draft revision, revise the
ERs based on worthwhile findings, and re-run sequentially across revisions until
clean (never run multiple duplicate scoring passes on the exact same unchanged
draft).

For workflows where AI agents are participants or operators, also apply
[agentic_delivery_foundations.md](requirements/agentic_delivery_foundations.md),
[agentic_pm_user_story_preflight.md](requirements/agentic_pm_user_story_preflight.md),
and
[agentic_architecture_pressure_scoring.md](requirements/agentic_architecture_pressure_scoring.md)
so capabilities an agent can deliver directly (`Agentic`) or via thin wiring
(`Hybrid`) are not overbuilt as heavy application software. When a slice looks
LoC-heavy or risky after ERs converge, optionally delegate the code-aware impact
pass in
[architecture_pressure_scoring.md](requirements/architecture_pressure_scoring.md#enhanced-option-independent-code-aware-impact--loc-estimation).

#### Reviewer Roles

`convergence-review` reviewers are passed as `<agent>:<role>` pairs:

- `core` ([core_reviewer.md](reviewers/core_reviewer.md)): standard
  ER-satisfaction and implementation-quality reviewers. Blocking findings halt
  mechanical convergence.
- `architecture` ([architecture_critic.md](reviewers/architecture_critic.md)):
  senior critic of implementation shape, scope justification, over-engineering,
  and avoidable architectural pressure (one influence tier above `core`).
  Blocking findings halt mechanical convergence.

Example default panel (adjust backend names to match your `llm_config.py`):

```text
--reviewers agy:architecture,codex:core,claude:core,grok:core
```

#### Invocation Basics

Start at `implementation` when building from a ready design doc:

```bash
convergence-review --start-phase implementation --design-doc docs/design_file.md --coder codex --reviewers agy:architecture,codex:core,claude:core,grok:core
```

Start at `review` when checking an existing implementation against its design doc:

```bash
convergence-review --start-phase review --design-doc docs/design_file.md --coder codex --reviewers agy:architecture,codex:core,claude:core,grok:core
```

#### Runtime, Timing, & Output Expectations

- Long quiet periods are normal: initial coder passes on larger slices may take
  15-40 minutes, and a 4-iteration run can exceed an hour.
- Prefer completion or failure callbacks from the process owner (for example
  background task notifications) over tight polling loops. When polling a
  genuinely detached process is necessary, keep polling in the execution layer,
  choose a multi-minute interval appropriate to the phase, and back off after
  unchanged checks so the LCA never burns context just to confirm a healthy
  process is still running.
- Secondary liveness signals (`tmp/coding-logs/run_*/run_manifest.json`,
  artifact mtimes, `git diff HEAD --shortstat`) are phase-sensitive: zero diff
  movement during reviewer phases is expected.

#### When It Does Not Converge

`convergence-review` stops at its iteration cap so the LCA can exercise judgment
rather than letting a loop spin forever.

Apply the same iteration brake to repeated model tests, prompt repairs, and
integration attempts outside `convergence-review`: before launching another
cycle, name the changed hypothesis, the evidence it should produce, and the user
outcome it advances. After **two unsuccessful attempts** at the same behavior,
reassess the approach before commissioning a third (change strategy or propose a
concrete scope/deferral trade-off rather than burning the session on a secondary
objective).

At every `convergence-review` cap, disposition each remaining critical, high,
and medium finding explicitly (`fix`, `reject`, `defer`, `requirements
clarification`, or `human-owned`) by what stage owns it:

- **`convergence-review`-owned:** a material Essential Requirement failure. Pass
  the exact accepted finding and minimal fix direction to a scoped coder, then
  restart `convergence-review` at `--start-phase review`.
- **GSR-stage:** a concrete branch-quality defect that does not block ER
  acceptance. Delegate the minimal fix directly, then proceed into GSR.
- **Neither fix loop:** a false premise, speculative hardening, discretionary
  preference, or scope churn. Reject or defer with rationale and move to GSR.

#### Between-Run Design Memory Checkpoint

Before starting any follow-up `convergence-review` run, promote durable boundary
decisions, rejected recurring mechanisms, and settled ownership choices into
`## Settled Implementation Decisions` in the design doc (kept canonical rather
than chronological) so fresh coders and reviewers do not reverse or rediscover
them. Never restart at `--start-phase implementation` on an already-implemented
slice. When zero accepted `convergence-review`-owned findings remain, record
dispositions and proceed to GSR as *"requirements convergence accepted with
residual findings dispositioned"*.

### General Stability Review & Staff Engineer Review

General Stability Review (GSR) samples a frozen candidate for ordinary
correctness, data-integrity, deployment, security, and user-facing bugs before
PR review. Use `general-stability-review`
([tools/general-stability-review/README.md](tools/general-stability-review/README.md))
guided by
[general_stability_review_playbook.md](reviews/general_stability_review_playbook.md):

- Treat reviewer output as evidence, never an automatic edit queue.
- Before accepting any GSR finding that expands scope, crosses module
  boundaries, or adds durable state/machinery, run the GSR playbook's
  Architecture Pressure Checkpoint.
- Become progressively more skeptical in later GSR rounds after early passes
  return clean; see
  [review-findings-became-requirements.md](example-case-studies/requirements-risk/review-findings-became-requirements.md).
- Alongside or inside stabilization (`general-stability-review --mode
  staff-engineer`), run the **Staff Engineer Reviewer**
  ([staff_engineer_reviewer.md](reviewers/staff_engineer_reviewer.md)) to judge
  whether the diff (and its tests) can deliver the same benefit in materially
  less code and whether state, sources of truth, repo-wide cutovers, and root
  causes are handled cleanly without needing a design doc.
- **Full-stack boundary trigger:** Whenever a branch adds, renames, or reshapes
  fields across backend models/serializers, API payloads, and frontend
  stores/templates, run a focused pass with
  [full_stack_data_shape_review.md](reviews/full_stack_data_shape_review.md) to
  catch field-existence and shape mismatches that GSR and unit mocks can miss.

### Module Charters and Lane-Aware Design

Module Charters record a module's durable user stories, invariants, ownership,
and contracts:

- Read [module_charters.md](architecture/module_charters.md) and
  [module_charter_annotations.md](architecture/module_charter_annotations.md)
  whenever work touches module boundaries, hazard tags, or invokes the
  **Critical**, **Careful**, **Full-Spec**, or **Fast** lanes (lanes apply to
  specific architectural positions, never as blanket labels over an entire
  multi-layer feature).
- Read
  [module_charters_full_spec_lane.md](architecture/module_charters_full_spec_lane.md)
  and the calibration cases in
  [full-spec-lane-judgment-calls](example-case-studies/full-spec-lane-judgment-calls/README.md)
  whenever evaluating Full-Spec placement (formerly called the Rebuildable
  lane).
- Use [module_charter_drafting_guidelines.md](architecture/module_charter_drafting_guidelines.md)
  when authoring or updating charters and
  [module_charter_compatibility_review.md](architecture/module_charter_compatibility_review.md)
  to check boundary drift on larger cross-module changes.
- To generate human-facing ground-truth architecture posters for an unfamiliar
  or refactored codebase, use
  [engineer_architecture_visuals.md](visualizations/engineer_architecture_visuals.md).

### Runtime and Visual Evidence

For any new or materially changed user-facing workflow spanning components,
establish the normal user journey early: delegate a walkthrough of the actual
entry points, permissions, and state transitions so missing screens or broken
handoffs surface before polishing individual components. Rehearse end-to-end
wiring early and again whenever an interface changes; component completion
counts never establish end-to-end completion.

Use delegated [smoke testing](testing/smoke_testing.md) (verifying HTTP `200` on
all CSS/JS/font/image subresources plus visual rendering on the actual modified
surface) and [UI screenshot review](uiux/ui_screenshot_review.md) for runtime
and visual proof:

- **The LCA never opens screenshot batches directly in its own context.**
  Delegate visual inspection to fresh independent multimodal reviewers (`<= 5`
  full-size images per call, never contact sheets, un-anchored open review
  first; see headless `agy` and `grok` CLI recipes in
  [low_risk_ux_enhancements_loop.md](uiux/low_risk_ux_enhancements_loop.md#gemini-and-grok-as-screenshot-reviewers-validated-2026-10-19)).
- **Every UI-affecting change or human UI question ships with a reviewable HTML
  page** built per [ui_review_format.md](uiux/ui_review_format.md) showing
  screenshots of each option (`A / B / neither`, `before / after`, or `now +
  throwaway mockup`).

## Common Request Shapes

The human owner may compose building blocks concisely:

- **Requirements to Implementation:** Draft `# Essential Requirements` -> run
  sequential ER preflight rounds until Minimal/Clear `5/5` and human-readable ->
  run `convergence-review` -> validate & run GSR (+ `full_stack_data_shape_review`
  / `module_charter_compatibility_review` when applicable) -> report evidence and
  residual risk.
- **Implementation to Draft PR:** Run `convergence-review` -> disposition any
  residual cap findings and update `## Settled Implementation Decisions` -> run
  GSR and Staff Engineer review -> delegate full-stack smoke test + visual
  verification (and build `ui_review_format` HTML for UI changes) -> open draft
  PR.
- **Existing Branch Private Review:** Inspect diff against intended base -> run
  independent GSR + Staff Engineer passes -> delegate minimal local fixes only
  where requested, separating suggested peer feedback from local edits without
  chasing speculative churn.

## Handoff and Escalation

Ask the human owner before proceeding when requirements contradict each other, a
fix requires missing product judgment, or a direct fix would materially expand
scope.

Report implementation, local validation, `convergence-review`, GSR, merge,
deployment, activation, and operational proof as distinct states - never
compress them into a blanket `"done"`.

Before opening or merging a PR, run a **Turn-End Human Agreement &
Deferred-Scope Check** against the Verbatim Human Intent Reference and active
chat history: confirm that (a) no work explicitly deferred by the human in an
earlier turn was built anyway, (b) every late-turn human-approved fix or
simplification was committed, and (c) any agent-drafted charter or ER text is
honestly labeled `Agent-Drafted (Unreviewed)` rather than sitting beneath an
earlier `"Human-Approved"` header.
