# Module Charter Compatibility Review

This guide defines an optional post-implementation review for asking whether a
non-trivial branch fits the maintainability and ownership direction described in
[`module_charters.md`](module_charters.md) and
[`architecture_pressure_scoring.md`](../requirements/architecture_pressure_scoring.md).

Where the in-loop [`architecture_critic.md`](../reviewers/architecture_critic.md)
flags untraceable surfaces while `convergence-review` is running, and
[`staff_engineer_reviewer.md`](../reviewers/staff_engineer_reviewer.md) reviews
branch-diff craft directly, this review serves one focused diagnostic purpose:
**mapping finished-branch architectural pressure back to the specific
requirements or implementation choices that caused it**.

## When To Run It

Run this review selectively on large or cross-cutting branches when:

- `convergence-review` passed, yet the resulting diff feels heavier or more
  coupled than expected;
- one feature spread logic across several modules or lanes; or
- you suspect an Essential Requirement's wording forced agents to overbuild and
  want to decide whether to narrow the requirement before merging.

## Inputs

- the design doc, user stories, `# Essential Requirements`, and any linked
  `Verbatim Human Intent Reference`;
- `git diff --stat` and the touched module boundaries;
- affected module charters or responsibility charters;
- [`architecture_pressure_scoring.md`](../requirements/architecture_pressure_scoring.md)
  (using the standard 1-5 Architecture Pressure scale, where 1 = tiny durable
  surface and 5 = system-shaped retained burden).

## Core Dimensions To Check

Evaluate the finished branch across four questions:

1. **Ownership & boundary clarity:** Can a future maintainer tell which single
   module owns each rule, state transition, setting, and external contract?
2. **Isolation of complexity:** Is genuine complexity pulled behind a narrow
   module or `full_spec/` / `fast_lane/` seam, or scattered across unrelated
   packages?
3. **Contract narrowness:** Are cross-module calls, API payloads, and persisted
   shapes minimal, or duplicated across layers?
4. **Surgical scope:** Did the branch stay within the accepted requirements, or
   mix in unrequested surfaces and opportunistic churn?

## Requirement Pressure Attribution

For each area carrying material steady-state Architecture Pressure (typically
pressure 3-5, or a positive pressure delta above what the outcome needed),
separate **what caused the pressure** from **what to do next**:

### Causal Attribution

| Category | Meaning |
|---|---|
| **Direct requirement pressure** | An Essential Requirement or story explicitly mandated the heavy mechanism or cross-module contract. |
| **Interpretation pressure** | The requirement could be satisfied simply, but ambiguous or overly prescriptive wording nudged agents toward a broader subsystem. |
| **Implementation choice** | The requirements were clean; the coder chose a heavier pattern than necessary. |
| **Existing architecture constraint** | The branch exposed coupling or unclear ownership that already existed in the codebase. |

### Recommended Disposition

| Disposition | When to use |
|---|---|
| **Accept trade-off** | Product value genuinely justifies the retained pressure. |
| **Narrow requirement** | Rewrite the ER to preserve the core user outcome at materially lower pressure (for example, frontend-only preview gating instead of new backend denial branches when security is not at issue). |
| **Refactor implementation** | Keep the ER unchanged and simplify the implementation behind one clear owner. |
| **Document debt** | Defer cleanup consciously with a short note rather than blocking delivery. |

## Compact Output Template

```markdown
# Module Charter Compatibility Review: <branch>

- Overall Target Architecture Pressure: <1-5> (Delta: <signed delta>)
- Main takeaway: <1-2 sentences>

| Area / Concern | Pressure | Source ER / Section | Attribution | Disposition | Concrete Simpler Option |
|---|---:|---|---|---|---|
| <module or contract> | 4 (+2) | ER-3 | Direct requirement pressure | Narrow requirement | <one specific simplification> |
```

Lead with the 1-3 highest-leverage findings; do not pad a clean, well-bounded
branch with minor style notes.
