# Core Reviewer Guidelines

These are the guidelines for the `core` reviewer role in convergence-review:
the bread-and-butter reviewers that check the implementation against the design
doc's `# Essential Requirements` and the quality rules below. The companion
[architecture critic](architecture_critic.md) reviews implementation shape,
scope justification, over-engineering, and architectural pressure.

These guidelines are tuned for a layered web application with shared and
deployment-specific modules. Adapt examples to the target repository without
weakening the rubric.

## Review Priorities

In addition to checking the implementation against the design doc's
`# Essential Requirements`, review the changed code for:

- code placement
- minimal / surgical scope
- decoupling
- encapsulation of complexity
- naming clarity and consistency

These are important quality checks, but they should still be judged through a
convergence lens: raise issues that materially improve correctness,
maintainability, or architectural fit. Do not generate churn over stylistic
alternatives that are reasonable and low-risk.

## Convergence Mindset

- Prefer one strong issue over several overlapping ones that describe the same
  underlying concern.
- If the current implementation is acceptable and consistent with the surrounding
  architecture, do not ask for a different approach just because you can imagine
  another reasonable one.
- When a concern is subjective and not likely to create future bugs, coupling, or
  maintenance cost, keep it `low` severity or omit it entirely.
- If an earlier implementation choice already includes a concise, durable
  placement or structure rationale and the choice is reasonable, treat that as
  sufficient and avoid continuing to nit-pick alternate locations.
- Do not ask for speculative abstraction, speculative reuse, or cleanup beyond
  what is needed for this branch.

## R1: Code Placement

Review whether new code was added in the most natural long-term location within
the existing architecture.

Check for:

- new helpers added in an arbitrary file when an existing service/helper/module is
  the clearer long-term home
- logic being placed in a layer that should only orchestrate, render, or delegate
- duplicated business rules that should extend nearby existing logic instead
- shared logic being placed in company-specific or exam-specific code when it
  belongs in shared code, or vice versa

Before raising a placement issue, consider the top plausible locations for the
code and whether the current location is meaningfully worse than the best one.

Only raise a placement issue when the current location would likely cause future
confusion, coupling, duplication, or discoverability problems.

If you do raise a placement issue:

- keep it to one issue unless multiple unrelated placement problems exist
- include a one-sentence rationale for the better location
- optionally mention the main alternative you considered and why it is weaker

If the placement was genuinely ambiguous and the changed code already includes a
brief, durable rationale near the new code explaining why this location was
chosen, do not continue pushing for relocation unless the location is still
meaningfully wrong.

## R2: Minimal / Surgical Scope

Prefer the smallest coherent change that satisfies the requirements cleanly.

Raise an issue when the implementation:

- introduces extra abstractions, configuration, helpers, or indirection that the
  design doc does not need
- rewrites adjacent code without a clear payoff
- broadens behavior beyond the branch's intended scope
- mixes opportunistic cleanup with requirement-driven changes in a way that makes
  review harder or riskier

Do not raise an issue merely because the implementation did not also clean up
every nearby imperfection.

When in doubt, prefer:

- extending an existing pattern over inventing a new framework
- a local change over a broad refactor
- one well-scoped helper over a mini-architecture

## R3: Decoupling

Check whether the change preserves healthy boundaries between modules and layers.

Raise an issue when the implementation:

- leaks business rules across unrelated modules
- reaches through multiple layers for data that should be exposed through a
  clearer interface
- hard-codes deployment-specific, company-specific, or exam-specific behavior in
  a shared layer without an established extension point
- creates unnecessary two-way coupling between modules that should remain
  independently understandable

Do not demand theoretical purity. Some coupling is acceptable if it matches the
existing architecture and keeps the solution simpler.

## R4: Encapsulate Complexity

Complexity should be hidden behind the narrowest clear interface that fits the
existing codebase.

Raise an issue when the implementation:

- spreads one piece of logic across many call sites
- duplicates branching or state-transition logic that should live in one place
- leaves complex logic inline in a view, endpoint, serializer, or component when
  that logic is substantial enough to deserve a named helper/service/composable
- makes the main execution path harder to read because details are not grouped
  behind a clear abstraction

Do not request extraction for trivially small logic where the helper would be
more ceremonial than useful.

## R5: Naming Clarity And Consistency

Core Principle: Prioritize clarity at the point of use over brevity. Function names must be unambiguous, especially when imported across different modules. This prevents bugs from misinterpretation.

### Naming Guidelines

- **Be Specific:** Names must precisely describe the function's action and the data it affects. Avoid generic verbs like reset or update without clarifying context.
- **Embed Critical Context:** The name must include non-obvious operational context.
- **Scope Ambiguity:** If a function's scope (e.g., single-item vs. collection, one user vs. all users) is not obvious from its context, add a suffix to resolve the ambiguity (e.g., ...\_for_user, ...\_for_all_users). Add these clarifications only where necessary to prevent misinterpretation by a future reader unfamiliar with the code.

### Function & Variable Naming Examples

- **bad:** `reset_module_counts(course)`
- **good:** `refresh_cached_modules_total_durations_and_counts(course)`

- **bad:** `courses_for_refresh.append(course)`
- **good:** `courses_with_module_additions_or_removals.append(course)`

- **bad:** `reset_user_topic_view_counts(course)`
- **bad:** `invalidate_user_topic_view_counts(course)`
- **good:** `invalidate_cached_topic_view_counts_for_all_users(course)`
- **rationale:** The `course` argument should be a hint this applies across all
  users, but an intelligent AI coding agent missed the hint and called the
  initially named function for all users when it should have used a function
  for a single user. When the stakes of calling the function incorrectly are
  higher, lean towards more explicit names.

## Severity Guidance For These Review Dimensions

- `high`: the issue is likely to create bugs, architectural damage, duplicated
  business logic, or a materially wrong long-term home for important code
- `medium`: the issue weakens maintainability or clarity in a meaningful way, but
  does not obviously break behavior
- `low`: the suggestion is valid but discretionary, or the current implementation
  is acceptable even if another option may be slightly better

For these architecture-oriented guidelines, prefer under-reporting to
over-reporting when the current implementation is reasonable.
