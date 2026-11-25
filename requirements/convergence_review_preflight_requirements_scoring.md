# `convergence-review` Preflight ER Scoring

This guide defines a lightweight preflight review for drafted
`# Essential Requirements` before they are used as input to
`convergence-review`.

Use this alongside
[convergence_review_essential_requirements.md](convergence_review_essential_requirements.md)
and
[convergence_review_preflight_requirements_justification.md](convergence_review_preflight_requirements_justification.md).
The drafting guide explains how to write ERs; the justification preflight checks
source necessity and tag legitimacy; this guide scores each drafted ER bullet on
Minimal, Clear, and Architecture Pressure before implementation begins. See the
before/after examples in
[requirements-language-clarity](../example-case-studies/requirements-language-clarity/)
for real rewrites produced by this pass.

Score each ER independently rather than scoring only the whole document.
Existing code and integration points should still be inspected when needed to
judge what is truly minimal, clear, or architecturally pressured.

## Core Principle

ERs are not a place to be helpful, robust, or ambitious. They are a forcing
function for minimal clarity.

User stories define the product substance. The design doc body may define
accepted decisions, constraints, and non-goals. ERs distill the smallest durable
requirements needed to make an implementation materially correct. An ER must not
expand product or technical scope beyond what is explicitly supported elsewhere
in the design doc or by unavoidable system constraints.

## When To Use This

Every implementation slice runs this preflight before implementation or review
loops (see [Mandatory Requirements Preflights](../lca_playbook.md#mandatory-requirements-preflights)).
Scrutinize the ER set most closely when:

- the design doc is long or exploratory
- the work may touch several modules, layers, or product surfaces
- the ER set is near the 10-bullet limit
- the work is meant to simplify, consolidate, delete, or establish a durable
  module boundary
- broad implementation scope may be legitimate but should be scrutinized before
  coding

Small, local changes still run it. A short ER set makes a short pass, and a
clean result is evidence that the gate was exercised, not that it was
unnecessary.

## Reviewer Standard

Run this as an independent pass where possible. A fresh reviewer is less likely
to defend a just-drafted ER set and more likely to notice scope expansion or
ambiguity.

Inputs:

- the design doc, including user stories and body text
- the drafted `# Essential Requirements`
- any supporting docs explicitly named as requirement sources
- relevant module charters or draft charters when the work affects module
  ownership
- existing code, contracts, fixtures, tests, or integration points needed to
  understand implementation pressure
- an existing implementation, if one already exists and helps clarify how the
  ERs interact with the codebase

## Scoring Model

Score each ER on three dimensions:

| Dimension | Target | Meaning |
|---|---:|---|
| Minimal | 5 / 5 | The ER is fully source-supported and states the least ambitious requirement that would satisfy the user stories and required system constraints. |
| Clear | 5 / 5 | Future AI coding and review agents are unlikely to materially diverge about what the ER requires. |
| Architecture Pressure | No fixed target | A 1-5 pressure score (per [architecture_pressure_scoring.md](architecture_pressure_scoring.md)) estimating the steady-state maintenance burden the codebase retains, introduces, or removes after the ER lands. |

Minimal and Clear must reach 5 / 5 before implementation unless the human owner
explicitly accepts a tradeoff. High Architecture Pressure is acceptable when
necessary and intentional.

## Minimal

Target: 5 / 5 before implementation.

Core question:

> Does this ER state the least ambitious, fully source-supported requirement
> that would still satisfy the user stories and required system constraints?

An ER is source-supported only when every behavior, constraint, scope boundary,
and implementation obligation in the ER is supported by user stories, explicit
design-doc decisions or non-goals, compatibility/migration rules, necessary
security/privacy/billing/audit/data-integrity rules, adopted module-charter
ownership rules, or unavoidable existing-system constraints. The ER itself
cannot be its own source.

| Score | Meaning |
|---|---|
| 1 | ER introduces major unsupported or non-essential scope. |
| 2 | ER includes meaningful scope, protections, mechanisms, or obligations that are not necessary. |
| 3 | ER is directionally acceptable but broader than the smallest correct requirement. |
| 4 | ER is mostly minimal, but a phrase or sub-clause could still invite extra scope. |
| 5 | ER states only the minimum source-supported truth that must hold. |

Low-score signals:

- Introduces behavior not clearly present in the design doc or expands a story
  into a broader capability.
- Turns optional implementation ideas or named helpers/fields/routes into
  mandatory scope when an outcome would suffice.
- Quietly resolves an open product ambiguity.
- Adds robustness, polish, analytics, future-proofing, or extra protections not
  required for correctness.
- Bundles several separable concerns into one obligation.

When in doubt, apply the laziest correct implementation test:

> If a competent implementer chose the smallest reasonable implementation that
> satisfies the user stories, design decisions, and existing-system constraints,
> would this ER force them to do more?

If yes, the ER is not minimal.

## Clear

Target: 5 / 5 before implementation.

Core question:

> Would future AI coding and review agents interpret this ER the same way?

| Score | Meaning |
|---|---|
| 1 | Future agents are likely to disagree about what the ER requires. |
| 2 | Important terms, states, paths, exclusions, or compatibility expectations are unclear. |
| 3 | Mostly understandable, but likely to create review churn. |
| 4 | Clear enough, with minor ambiguity remaining. |
| 5 | Precise, compact, and unlikely to create materially different interpretations. |

Low-score signals:

- Key terms have multiple meanings in the design doc or codebase.
- Says "all", "every", or "must not vary" without naming or bounding the
  relevant paths.
- Names many surfaces without stating what must hold on each one.
- Leaves migration, compatibility, permissions, or edge states ambiguous where
  those details affect correctness.
- Mixes requirement, rationale, example, and implementation advice in a way that
  blurs what reviewers should enforce (or buries dense technical jargon where
  plain domain language would be clearer).

## Architecture Pressure

Score 1-5 (plus `Architecture Pressure Delta` when simplifying or migrating)
using [architecture_pressure_scoring.md](architecture_pressure_scoring.md).
High pressure (4 or 5) should trigger scrutiny:

- Is all of this pressure necessary to satisfy the user stories and system
  constraints?
- Could the ER be narrower while preserving the same product outcome?
- Is the pressure caused by a real domain boundary, or by wording that invites
  overbuild or leaks semantics across consumers?
- If adding a new path, is it clear whether old paths remain authoritative,
  become thin compatibility wrappers, or are deleted?

## Recommended Output Format

| ER | Minimal | Clear | Arch Pressure | Arch Delta | Action |
|---|---:|---:|---:|---:|---|
| ER 1 short label | 5 | 5 | 2 | 0 | Keep |
| ER 2 short label | 3 | 4 | 4 | +2 | Rewrite: too broad and ambiguous. |
| ER 3 short label | 1 | 3 | 2 | -2 | Keep simplification direction; remove unsupported scope. |

Follow the table with concrete rewrite wording or questions only for bullets
that need changes.

Good finding shape:

- ER 4 scores Minimal 3 because it requires both a new backend endpoint and a
  frontend store rewrite, while the user story only requires the SPA to receive
  confirmed state after save. Rewrite around the outcome and leave the mechanism
  flexible.

## Relationship To Module-Charter Review

[module_charter_compatibility_review.md](../architecture/module_charter_compatibility_review.md)
checks during or after implementation whether module boundaries remained clean;
this preflight checks *before* coding whether the ER wording itself nudges
agents toward excess scope, duplicated contracts, or unclear ownership.

## Practical Sequence

1. Run user-story language preflight (`user_story_preflight_scoring.md`).
2. Draft or revise `# Essential Requirements`
   (`convergence_review_essential_requirements.md`).
3. Run this ER scoring preflight alongside ER justification preflight
   (`convergence_review_preflight_requirements_justification.md`).
4. Rewrite ERs until Minimal and Clear are both 5 / 5 and any high Architecture
   Pressure is intentional.
5. Begin implementation and `convergence-review`.
