# Case Study: Exception Labels and an Unsupported Completion-ID Protocol

> **Status: required calibration reading; the normative rules live in the
> [ER justification preflight guide](../../requirements/convergence_review_preflight_requirements_justification.md).**

## Context

During a Topic Progress Daily Checkpoint design, a learner-facing requirement
needed the system to recognize when enough graded practice had been completed on
a topic. An early ER expanded that outcome into a new cross-layer completion-ID
and idempotency protocol.

The ER passed justification preflight because its inline exception labels
accurately described the kinds of safeguards it proposed. The technical owner
and the architecture critic later rejected it because those safeguards protected
a new mechanism that the product requirement did not need.

## Relevant User Stories

### DCP-US-4: Receive a healthy recommendation after enough graded practice

> As a learner who completes enough graded practice on a topic without reaching
> either checkpoint path, I want the page to treat the day as normal, successful
> learning progress and recommend consolidation, so I can reinforce what I
> learned, move to another topic, and return for the next graded check on the
> topic the next day instead of chasing the score into burnout.

### DCP-US-5: Avoid another activity quota to chase

> As a learner who has not yet reached the internal graded-practice threshold,
> I do not want to see a partial activity count or progress meter toward it, so
> the anti-burnout recommendation does not become another quota that pressures
> me to keep practicing.

### DCP-US-6: Keep one stable checkpoint for the study date

> As a learner who refreshes, closes the browser, or returns to a topic later on
> the same study date, I want to see the same baseline, cumulative progress, and
> completed status, so the finish line does not move or disappear during my day.

These stories justify correct completed-practice counting, a hidden
all-or-nothing activity signal, and same-client sticky completion. They do not
request a new practice-completion identity protocol.

## Rejected ER

The rejected ER was:

> - `[DCP-US-4; Data Integrity, Maintainability, Reliability]` Each newly
>   generated practice set must carry a stable, opaque completion identity that
>   the client returns with its results. `ActivityEvent` must add a nullable
>   activity-completion-identity field distinct from its Topic ID content
>   identity and a conditional database uniqueness constraint across learner,
>   event name, and non-null completion identity. A successful single-topic
>   `topicScope` submission qualifies only when its first accepted submission
>   persists at least one new question attempt; its attempts and existing
>   `PRACTICE_SET_COMPLETED` event must persist in one outer database
>   transaction, and the sole `record_activity_event` write path must ensure
>   only the uniqueness winner performs coupled event effects. The event must
>   durably identify the learner, resolved Topic ID, completion identity, and
>   completion instant. Sequential or concurrent replay must not add another
>   equivalent, and empty or rejected submissions must add none. Legacy
>   submissions without an identity must continue existing attempt, score, and
>   analytics behavior but contribute zero; existing events receive no backfill.
>   Each qualifying event contributes one standard equivalent regardless of
>   question count, while other practice scopes and review cards contribute
>   zero. The focused helper must count those events within the resolved local
>   study date and invoke one existing-registry APPEND hook for track-specific
>   extra equivalents without letting handlers recount standard practice sets;
>   the default handler contributes zero extras, and CFP contributes
>   `floor(completed same-topic CR attempts during the study date / 3)`.
>   Practice sessions must not be inferred from timestamp clusters.

The justification preflight passed the ER because each exception label appeared
locally legitimate:

- `Data Integrity` appeared to justify the persisted identity and uniqueness
  constraint.
- `Maintainability` appeared to justify preserving `record_activity_event` as
  the sole writer and using the existing track registry.
- `Reliability` appeared to justify atomicity, retry idempotency, and
  legacy-client compatibility.
- `DCP-US-4` genuinely justified counting completed graded practice.

That analysis validated the safeguards *after* accepting the proposed mechanism.
It did not first test whether the mechanism itself was necessary.

## Why It Was Rejected

The technical owner and the architecture critic rejected the ER because
`DCP-US-4` requires a correct count of completed topic practice, not a new
completion-ID subsystem.

The ER would have introduced:

- a new frontend/backend completion-identity protocol;
- a new nullable `ActivityEvent` field;
- a conditional database uniqueness constraint;
- new transaction coupling between question-attempt persistence and the Critical
  activity-event writer;
- uniqueness-winner handling for coupled event effects;
- a permanent legacy-client compatibility path; and
- retained migrations, contract tests, concurrency tests, and protocol
  semantics.

The existing `PRACTICE_SET_COMPLETED` event already represented completed
practice sets. Adding the resolved Topic ID to its existing content-identity
field was sufficient to query completed, nonempty, single-topic practice sets
for the learner, topic, and study date. The track-specific registry already
supplied the extension point for CFP equivalents.

The exception labels described real concerns only because the rejected ER first
invented a mechanism that created those concerns.

## Lean Replacement ER

The accepted replacement was:

> - `[DCP-US-4; Maintainability]` The backend must count one standard
>   graded-activity equivalent for each completed, nonempty, single-topic
>   `topicScope` practice set on the active topic and study date by recording
>   the resolved Topic ID on the existing `PRACTICE_SET_COMPLETED` event. Other
>   practice scopes and review cards count zero. The existing track registry may
>   add track-specific equivalents without recounting standard practice sets;
>   the default adds zero, while CFP adds `floor(completed same-topic CR
>   attempts on the study date / 3)`.

Adjacent ERs separately owned the Boolean-only response, hidden partial activity
progress, and reason-free same-client sticky status.

## Calibration Questions

1. Before evaluating inline tags, does this ER represent the laziest correct
   implementation of its source story?
2. Did `Data Integrity` or `Reliability` launder an unsupported mechanism by
   describing safeguards required *only* because the ER invented a new protocol?
3. Does the underlying failure mode exist independently of the proposed
   machinery, and is the safeguard proportionate to actual operating conditions?
4. Counterfactual check: if the proposed new protocol were removed, could the
   user story still be satisfied cleanly by extending an existing contract or
   event field?
5. Are product outcomes bundled with schema, transaction, retry, and
   compatibility machinery that should be separated and justified independently?
