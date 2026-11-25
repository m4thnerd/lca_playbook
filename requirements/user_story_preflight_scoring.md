# User Story Language Preflight

This guide defines a lightweight preflight review for user stories before they
drive Essential Requirements.

## Canonical User Story Shape

Write implementation-candidate stories in plain stakeholder language:

```text
US-1
As a <user or stakeholder>, I want <capability or outcome>, so that <purpose or value>.
```

Stories are either in scope for the current pass or listed under
`## Deferred Stories / Non-Goals`. Only in-scope stories drive Essential
Requirements (`ERs`). Never invent a fake user story merely to give an
exception-label ER (`Data Integrity`, `Security/Privacy`, `Maintainability`,
`Reliability`, `Performance`) a source.

This is a fast language and scope review, not a code-aware LoC impact analysis.
For code-aware blast-radius and LoC estimation after language has converged, see
[architecture_pressure_scoring.md](architecture_pressure_scoring.md#enhanced-option-independent-code-aware-impact--loc-estimation).

## Core Question

> Are these stories source-supported, clearly worded, minimal in scope, and
> suitable to justify ERs?

## Inputs

- current design doc draft (and linked `Verbatim Human Intent Reference` when present)
- stakeholder request, ticket, or product notes
- relevant operating conditions or module charters
- current user-story section

Inspect code only when a specific wording ambiguity cannot be resolved from the
docs. Do not scan implementation broadly for this preflight.

## Scoring Model

Score each user story independently.

| Dimension | Target | Meaning |
|---|---:|---|
| Source | Pass | The story is supported by the request, stakeholder context, module charter, or observed product need. |
| Shape | 5 / 5 | The story names a stakeholder, capability/outcome, and real purpose without smuggling in ER or implementation detail. |
| Minimal Scope | 5 / 5 | The story states the smallest product or operational outcome that still captures the value. |
| ER Support | Strong / Weak / None | Whether the story is specific enough to justify likely ERs without being stretched beyond its actual value. |
| ER Readiness | Ready / Needs revision / Defer / Remove | Whether the story can safely justify current-pass ERs. |

Do not score LoC burden or Architecture Pressure in this preflight.

## Source

Pass when the story is supported by one of:

- explicit user request, `Verbatim Human Intent Reference`, or ticket text
- stakeholder communication, customer example, or support context
- product strategy accepted for the branch
- module charter user stories or durable requirements
- observed production pain that the branch is explicitly addressing
- operational, maintainability, or reviewability need that the design doc makes
  part of the branch

Fail when the story exists only because:

- an implementation idea needed product justification after the fact
- an ER needed a source
- a reviewer or agent invented a nice-to-have expansion
- the story states generic value that could justify almost anything

## Shape

Target: 5 / 5.

| Score | Meaning |
|---|---|
| 1 | Not a user story; mostly an implementation task or vague goal. |
| 2 | Stakeholder, outcome, or purpose is missing or materially unclear. |
| 3 | Directionally useful but bundled, broad, or mixed with implementation detail. |
| 4 | Clear enough, with minor wording or splitting issues. |
| 5 | One stakeholder, one outcome, one real purpose, with implementation left flexible. |

## Minimal Scope

Target: 5 / 5.

| Score | Meaning |
|---|---|
| 1 | The story pulls in major unsupported or future-facing capability. |
| 2 | The story includes meaningful extra scope beyond the core value. |
| 3 | The story is directionally right but broader than needed. |
| 4 | Mostly minimal, with one phrase that may imply extra work. |
| 5 | Smallest clear outcome that captures the intended value. |

Low-score signals:

- the story implies dashboards, analytics, custom UI, or automation not needed
  for the current pass
- the story includes specific field, function, endpoint, component, or model
  names unless that identifier is part of the stakeholder-facing contract
- the story combines a current workflow with a future optimization
- the story would let reviewers demand scope the product owner has not accepted

## ER Support

Use this field to prevent downstream ERs from over-claiming user-story support.

- `Strong`: the story can clearly justify one or more current-pass ERs.
- `Weak`: the story is real, but too broad, vague, or indirect to justify the
  specific ER wording likely to depend on it.
- `None`: the story is deferred, exploratory, unsupported, or too unrelated to
  justify any current-pass ER.

If this preflight runs after an ER draft exists, inspect each claimed story tag
lightly: ask whether the ER would still be justified by that story if all
exception labels were removed. If not, mark the story support as weak and tell
the ER preflight to remove or replace that tag.

## Recommended Output Format

```text
| Story | Source | Shape | Minimal Scope | ER Support | ER Readiness | Action |
|---|---|---:|---:|---|---|---|
| US-1 short label | Pass | 5 | 5 | Strong | Ready | Keep |
| US-2 short label | Pass | 3 | 4 | Weak | Needs revision | Split operator tuning from analytics. |
```

Then list only:

- required story rewrites
- missing plainly implied stories that should be added before ER drafting
- stories to defer or remove
- story tags that downstream ERs should not claim
- open product-judgment questions

## Readiness Standard

Before drafting ERs, each in-scope story should pass `Source`, score `5 / 5` on
`Shape` and `Minimal Scope`, and have `Strong` ER Support; deferred stories must
not drive ERs. Run sequential preflight iterations (review, revise, then review
again if the story set materially changed) rather than concurrent passes on the
same draft.
