# `convergence-review` Essential Requirements Drafting Reference

> **Human reviewers:** You do not need to read this agent drafting manual. See
> [Essential Requirements: High-Leverage Human Specifications](../README.md#essential-requirements-high-leverage-human-specifications)
> in the repository README for the compact human guide.

`# Essential Requirements` is the compact scope anchor that keeps
`convergence-review` reviewers and coder iterations aligned on the same truths.
Design docs legitimately mix hard requirements, rationale, recommended shapes,
examples, and non-goals; `# Essential Requirements` extracts only the 1-10
behavioral truths and constraints whose absence would make the implementation
materially wrong.

## Output Format

- Output only the `# Essential Requirements` section, starting with the exact
  heading `# Essential Requirements` and no surrounding commentary.
- Immediately beneath `# Essential Requirements`, include:
  - `ER Sign-Off Status: Human-Approved` when a human explicitly reviewed and
    approved the ER list, or
  - `ER Sign-Off Status: Agent-Drafted (Unreviewed)` whenever drafted
    autonomously without human sign-off on the ER list.
- Include **1-10 bullet points** (`- ` prefix). Match count to intent
  complexity: 1-2 bullets for a focused 1-2 goal change (never pad to reach
  3-8); 3-8 for broader features. `10` is a hard cap, not a target: merge
  related facets of one invariant before adding bullets.
- Start every bullet with a bracketed justification tag (`[US-1]`,
  `[US-1, US-3]`, or `[US-2; Data Integrity]`).

## Inline Justification Tags

```text
- [US-1] Every inbound learner conversation message must receive one bounded
  message-based routing decision before the main response model call.
- [US-2; Data Integrity] Admin validation must reject blank prompt text and
  invalid route-map JSON.
- [US-4; Maintainability] The first pass must reuse existing runtime-config,
  model-router, ops-validation, and graph extension seams.
```

Use user-story IDs whenever product value justifies the ER. Use narrow exception
labels only when an ER must hold even without a direct user story (verified via
[convergence_review_preflight_requirements_justification.md](convergence_review_preflight_requirements_justification.md)):

| Label | Meaning |
|---|---|
| `Data Integrity` | Validation, migration safety, canonical data shape, persisted-state correctness, duplicate prevention, and guards against invalid or corrupt state. |
| `Security/Privacy` | Authentication, authorization, tenant isolation, permission boundaries, sensitive data handling, prompt-injection safety, and privacy constraints. |
| `Maintainability` | Alignment with [module_charters.md](../architecture/module_charters.md): ownership boundaries, lane expectations, avoiding parallel systems, minimizing needless LoC, and keeping future changes understandable. Optional lane qualifier when the lane changes the review bar: `Maintainability:CriticalLane`, `Maintainability:CarefulLane`, `Maintainability:FullSpecLane`, or `Maintainability:FastLane`. |
| `Reliability` | Graceful failure, fallback behavior, idempotency, retry/timeout boundaries, and avoiding user-visible breakage when an optional path fails. |
| `Performance` | Caching, query reduction, latency, throughput, background-work boundaries, and avoiding unnecessary high-frequency work. |

Rules for tags:

- Never invent a user story solely to justify a technical constraint, and never
  use an exception label as a loophole for implementation preference.
- Ordinary logging, debugging, telemetry, or traceability are not exception
  labels; unless product-visible via a user story, keep them out of ERs.
- **Agent-Drafted ER Ceiling (`ER Sign-Off Status: Agent-Drafted (Unreviewed)`):**
  When unreviewed by a human, standalone exception labels may only protect
  existing behavioral invariants or module boundaries. They must **never**
  introduce new operational refusal gates, interactive prompts, modes, or state
  machines not requested in the linked Verbatim Human Intent Reference (see
  [verbatim_human_intent_reference_playbook.md](verbatim_human_intent_reference_playbook.md)
  and
  [agent-authored-ers-and-operational-gates.md](../example-case-studies/requirements-risk/agent-authored-ers-and-operational-gates.md)).

## Drafting Rules & Heuristics

1. **Flag unresolved product ambiguity rather than guessing.** If the design doc
   leaves branch-defining behavior genuinely unresolved, stop and surface the
   question before locking an arbitrary guess into `# Essential Requirements`.
2. **State outcomes and invariants, never speculative identifier names.**
   Convert suggested mechanisms into behavioral truths. Pin a field, function,
   endpoint, component, or setting identifier *only* when it is already an
   established canonical symbol in the codebase with no chance of rename. Refer
   to new surfaces by role ("the promo banner card", "the account-context payload")
   rather than proposed names (`PromoBannerCard.vue`,
   `promo_offer_state`).
3. **Preserve scope-bounding exclusions (`must not` / `do not`).** Explicit
   negative constraints (such as preserving grandfathered subscriber pricing or
   forbidding discount stacking) prevent reviewer scope invention. Exclude
   background rationale, rejected alternatives, future ideas, sample UI copy
   (unless exact wording is mandatory), and weak signals (`recommended`,
   `suggested`, `could`, `may`).
4. **Lift mandatory guards out of deep sub-sections.** Reviewers anchor heavily
   on the `# Essential Requirements` list and systematically miss `must return 0
   when...` or `must short-circuit when...` guards buried in lower design
   sections. Surface true mandatory guards in the ER list.
5. **Give invariant-style ERs explicit path discipline.** An ER of the form
   "X must hold on every Y" or "X must not vary across Y" with implicit `Y`
   causes reviewers to spot-check one path and leak defects one iteration at a
   time. Either enumerate the concrete `Y` dimensions in the bullet (every
   purchase path, deployment mode, or user state) or state explicitly that the
   invariant must be verified across every such path. If `Y` cannot be bounded
   cleanly, split the requirement.
6. **Keep compatibility and rollout constraints only when behavioral.** Include
   legacy/new flow parity or active-subscription preservation when required;
   omit general rollout advice.

## Per-Bullet Quality Check

Before finalizing, verify every bullet passes all five checks:

1. **Necessary:** If omitted, could an implementation satisfy the rest of the
   list and still be materially wrong, or would reviewers predictably invent
   unwanted scope?
2. **Unambiguous:** Would two independent reviewers interpret this bullet the
   same way without spot-check leakage?
3. **Source-backed:** Is every obligation backed by a user story, accepted
   design decision, or legitimate exception constraint rather than invented in
   the ER list?
4. **Mechanism-free:** Would an equivalent implementation under a different
   helper, route, field, or component name still pass this bullet?
5. **Readable in seconds:** Can a human product or technical owner scan the
   bullet and immediately tell what product promise or invariant they are
   approving?

## Mini Examples

Bad (pins proposed identifiers and UI copy):

- "Add a `has_target_date` field to `enrolled_courses`."
- "Show `20% off for the next 7 days` in the promo banner card."
- "Expose `promo_offer_state` with fields `active`, `discount_percent`,
  `days_remaining`, `is_stacked`."

Better (states the behavioral contract):

- "The SPA must receive enough per-course data to distinguish
  existing-schedule switches from first-time switches."
- "Upgrade messaging must make any time-limited discount and remaining
  eligibility window clear without implying the discount lasts longer than it
  does."
- "The backend must expose promotional-offer state in the account-context
  payload so the SPA can render discount mode in a single request (whether
  active, effective percent, and remaining window)."

## Full Before / After Example (`self_service_course_reset`)

Bad (7 bloated bullets mixing obvious hygiene and awkward UI phrasing):

- Authenticated users must be able to reset all practice progress for a single
  enrolled course they have access to, initiated from their Account page and
  confirmed via a dialog before the destructive action executes.
- The confirmation dialog must be explicit that the action is destructive and
  irreversible, and must clearly distinguish it from score-submission-based
  preservation (users seeking a preserved snapshot should use score submission
  instead).
- The reset path must reuse the existing single-course reset helper; this
  deliverable must not introduce new destructive data logic, new models, or
  migrations.
- Every successful reset must emit an activity-log entry distinct from
  score-submission events, so support can audit self-service resets after the
  fact.
- Self-service reset must not create any score-associated record (no
  `FormalAssessmentRecord`, no denormalized snapshot); data-preserving
  behavior is owned by the companion score-submission flow.
- Self-service reset must not set any retake-oriented user flag; users may reset
  for reasons other than retake, and conflating the two would mis-classify them.
- Requests against courses the user does not have access to, or unknown course
  slugs, must fail cleanly without performing any reset or emitting a reset
  event.

Better (3 crisp bullets capturing the actual product contract):

- `[US-1]` Authenticated users must be able to reset all practice progress for a
  single enrolled course they have access to, initiated from their Account page
  and confirmed via a dialog before the action executes.
- `[US-1]` The confirmation dialog must be explicit that the action cannot be
  undone.
- `[US-2]` Every successful reset must emit an activity-log entry distinct
  from score-submission events so downstream coaching history can see the reset.

Why the rewrite wins: the 7-bullet draft reads like a legal maze of obvious
mistakes to avoid and nudges the coder toward robotic user-facing copy
("destructive and irreversible, and not score-submission-based preservation"),
whereas the 3-bullet draft states the exact product contract a human can approve
in 15 seconds.
