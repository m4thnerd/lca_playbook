# Case Study: Exception Labels and a Perfect-Concurrency Snapshot Protocol

> **Status: required calibration reading; the normative rules live in the
> [ER justification preflight guide](../../requirements/convergence_review_preflight_requirements_justification.md).**

## Context

During a Daily Course Progress Snapshots design, a small learner-facing sidecar
was intended to preserve study-date topic and Sub-Skill (SK) progress across
browser refreshes. It also captured a compact, fixed scoring-provenance JSON
object (`scoring_metadata`) for later analysis.

The intended architecture was deliberately narrow:

- one uncached sidecar row per learner, course, and study date;
- ordinary creation on the common course-progress bootstrap read;
- straightforward activity-first creation at the existing topic or SK score
  seam when a long-lived tab crossed midnight;
- sparse SK prior/current facts rather than a full SK baseline or event ledger;
- exactly two surgical Critical score-update touchpoints; and
- no changes to `CourseProgress`, its cache protocol, canonical scoring
  behavior, or activity endpoint orchestrators.

The product owner explicitly preferred simple behavior over engineering for
one-in-a-million or one-in-a-billion races. The product serves a few thousand
learners and is maintained by a lean founder-led team; retained complexity has a
high opportunity cost.

The original ER set nevertheless expanded ordinary uniqueness and first/latest
storage into exact concurrent-first-observation ordering, row locking,
transaction coupling, retry idempotency, repair semantics, and failure
atomicity. Justification preflight passed because `Data Integrity`,
`Reliability`, and `Performance` accurately described safeguards required by
that expanded mechanism.

During `convergence-review`, those obligations produced:

- exclusive locks on the Critical `CourseProgress` row;
- lock-order and deadlock concerns across topic and SK paths;
- new transaction decorators around Critical scoring functions;
- attempts to coordinate snapshot state across the two seams;
- state attached to Django's private, reusable `Atomic` objects, creating a real
  cross-request/thread data-corruption defect;
- requirements debates about perfectly ordering concurrent reads and activities;
  and
- historical topic reconstruction questions for a canonical progress row that is
  missing in an effectively nonexistent repair edge case.

## Relevant User Stories

### US-1: Durable learner progress across refreshes

> As a learner, I want the system to retain the starting and latest score values
> for my topics and for each individual SK that changes during a study date, so
> the frontend can still show that date's changes after I close the browser,
> refresh the page, or return later that day.

### US-6: Learner-relevant date rollover

> As a learner who studies across midnight, I want progress after midnight in my
> study timezone to begin a new snapshot, so separate study dates are not merged
> into one arbitrary server-date record.

### US-7: Minimal impact on Critical learner-data code

> As a maintainer of the learner-data system, I want snapshot capture isolated
> from live course-progress caching and canonical scoring behavior, so adding
> historical observations does not destabilize Critical paths.

### US-9: Durable review-card score feedback

> As a learner who completes review cards, I want any resulting topic-score
> increase retained as part of my study-date progress even though review cards
> do not change an individual SK, so the frontend can continue to show the score
> movement I earned after a refresh or same-date revisit.

These stories require durable study-date facts, ordinary database uniqueness,
activity-first support at the existing seams, and a review-card topic delta
without a fabricated SK delta. They do not require perfect observation ordering
under concurrent first reads, cross-seam transaction state, canonical-row
locking, historical repair, or a retry/deduplication protocol.

## Before: Over-Specified Essential Requirements (All 10 Bullets)

- `[US-1, US-2, US-6, US-9; Data Integrity]` On the first course-progress read, or at either approved scoring seam while processing the first tracked activity, for a learner, course, and resolved calendar study date, create exactly one snapshot and retain its study timezone. Once the resolved date advances, the prior row must remain immutable and a new current-date row must be created; dates must not use rolling 24-hour windows.
- `[US-1, US-2, US-8, US-9; Data Integrity]` Each row must preserve an immutable starting and mutable latest copy of the base `CourseProgress.get_data()` contract; latest values may rise or fall, starting values must never change, and request-specific API overlays must enter neither copy. Topic-only score movement, including a review-card-derived increase, must update the topic facts without requiring or fabricating an SK change. These persisted topic and SK facts, rather than one-shot frontend route state, must remain authoritative across browser refreshes and same-date revisits.
- `[US-1, US-3; Data Integrity, Performance]` SK history must remain sparse: for each SK whose authoritative score changes at least once during the study date, retain its topic identifier, first authoritative prior score, and latest authoritative current score, storing neither a full SK baseline nor intermediate events.
- `[US-4; Data Integrity]` Each row must store one `scoring_metadata` JSON field, captured once at row creation and never refreshed. Its finalized version 1 shape has exactly the `readiness` and `topic_progress` top-level descriptors; each descriptor has exactly `implementation` (`standard` or `track_specific`), `algorithm_version` (positive small integer), and `parameters` (a JSON object containing the effective configurable values). Implementation must add no other top-level or descriptor-level provenance fields or keys and must not duplicate the context as starting/current values.
- `[US-5; Maintainability]` Every readiness or topic-progress algorithm version recorded in `scoring_metadata` must map to a nearby source-controlled, plain-text, plain-English changelog entry describing that version. Runtime version exposure must remain a minimal integer constant or attribute; production code must not parse the changelog or introduce a database registry, admin UI, generic versioning subsystem, or code-location metadata.
- `[US-6, US-8; Reliability]` On course-progress bootstrap, the client must send the browser-reported IANA timezone when the browser provides one; the backend must validate it and otherwise use the most recent snapshot timezone, then UTC. The response must expose one dedicated typed projection containing study-date identity plus per-topic and sparse per-SK starting/current scores, while scoring manifests remain backend-only. The client must tolerate the field's absence during deployment ordering, but a snapshot failure must remain an error rather than being represented as an absent or empty successful value.
- `[US-7, US-9; Maintainability, Performance]` One learner-data-owned sidecar service must be the only snapshot creator and updater. Existing Critical scoring code may call it only from `LearnerProgressService.record_topic_progress_update`, which must preserve the pre-update base observation and dispatch topic before/after values for graded and topic-only activity, and `record_skill_attempt_and_compute_score_delta`, which must dispatch SK before/after values for supported graded activity. No snapshot call may be added to practice-set, review-card, CR, question, answer, or other callers, or to a third score-write location; multi-SK practice behavior is outside this version's supported scope.
- `[US-7; Maintainability, Performance]` The existing `CourseProgress` class and `learner_data/cache.py` must receive zero code changes. Lower-level `SkillRecord` mutation code and existing scoring, readiness, calibration, registry-selection, and resynchronization behavior must remain unchanged; scoring-module additions are limited to the provenance resolution, parameter serialization, integer versions, and changelog documentation required by the finalized metadata and changelog requirements. The snapshot must not be cached.
- `[Reliability, Data Integrity]` Database uniqueness and row locking must ensure that concurrent snapshot creation and mutation produce one row without losing immutable starting values or an SK's first authoritative prior value; repeated snapshot merges carrying the same absolute values must not change the stored result. Snapshot failures must remain visible and participate in the authoritative activity transaction where one exists rather than being logged and silently discarded.
- `[Maintainability]` Version 1 must not add backfill, full-SK daily copies, an intraday event ledger, rolling-window semantics, snapshot caching, background/signal infrastructure, admin UI, research-export changes, machine-learning execution, or any checkpoint/consolidation policy owned by later Topic Progress epics.

## How Bloat Entered

The ninth ER (interacting with ER-6's error-propagation mandate and ER-7/8's
seam rules) was the main laundering point:

- `Data Integrity` appeared to justify database uniqueness, immutable starting
  values, first-prior SK preservation, and lost-update prevention.
- `Reliability` appeared to justify retries, visible failures, and joining the
  authoritative scoring transaction.

Once the ER demanded perfect concurrency, the implementation needed ordering and
shared state across seams that did not previously exist. Reviewers then
accurately found real locking, deadlock, cleanup, and thread-safety defects
*inside* the unnecessary machinery, and fixing each defect would have made that
machinery more permanent.

## After: Lean Essential Requirements (All 8 Bullets)

- `[US-1, US-2, US-6, US-9; Data Integrity]` Persist one snapshot for each learner, course, and resolved local study date. Create it on the common first course-progress read, or by straightforward get-or-create at the existing topic or SK scoring seam when tracked activity comes first. A later local date creates a new row and ordinary activity must not rewrite prior-date rows; dates are calendar dates, not rolling 24-hour windows.
- `[US-1, US-2, US-8, US-9; Data Integrity]` Each row must preserve an immutable starting and mutable current copy of the base `CourseProgress.get_data()` contract without request-specific overlays. Topic score captured at the approved topic seam may rise or fall and must include review-card-derived movement without requiring or fabricating an SK change. Other derived course-progress fields may refresh on a later bootstrap read; version 1 does not add another activity touchpoint solely to synchronize them. Persisted topic and SK facts must remain available across browser refreshes and same-date revisits.
- `[US-1, US-3; Data Integrity, Performance]` SK history must remain sparse: for each SK whose authoritative score changes at least once during the study date, retain its topic identifier, first authoritative prior score, and latest authoritative current score, storing neither a full SK baseline nor intermediate events.
- `[US-4; Data Integrity]` Each row must store one `scoring_metadata` JSON field, captured once at row creation and never refreshed. Its finalized version 1 shape has exactly the `readiness` and `topic_progress` top-level descriptors; each descriptor has exactly `implementation` (`standard` or `track_specific`), `algorithm_version` (positive small integer), and `parameters` (a JSON object containing the effective configurable values). Implementation must add no other top-level or descriptor-level provenance fields or keys and must not duplicate the context as starting/current values.
- `[US-5; Maintainability]` Every readiness or topic-progress algorithm version recorded in `scoring_metadata` must map to a nearby source-controlled, plain-text, plain-English changelog entry describing that version. Runtime version exposure must remain a minimal integer constant or attribute; production code must not parse the changelog or introduce a database registry, admin UI, generic versioning subsystem, or code-location metadata.
- `[US-6, US-8]` On course-progress bootstrap, the client must send a browser-reported IANA timezone when available; the backend must validate it and otherwise use the most recent snapshot timezone for that learner and course, then UTC. The response must expose one dedicated typed projection containing study-date identity plus per-topic and sparse per-SK starting/current scores, while scoring provenance remains backend-only.
- `[US-7, US-9; Maintainability, Performance]` Implement one simple, uncached, learner-data-owned sidecar whose only production integrations are the existing course-progress read, `LearnerProgressService.record_topic_progress_update` for topic observations, and `record_skill_attempt_and_compute_score_delta` for SK observations. Add no snapshot calls to practice-set, review-card, CR, question, answer, or other callers. The existing `CourseProgress` class, `learner_data/cache.py`, lower-level `SkillRecord` mutation, scoring/readiness formulas and calibration, registry selection, and resynchronization behavior must remain unchanged; scoring additions are limited to the provenance contract and changelog documentation.
- `[Maintainability]` Version 1 must not add historical reconstruction or backfill, full-SK daily copies, an intraday event ledger, multi-SK practice semantics, snapshot caching, cross-seam transaction coordination, snapshot-specific retry/deduplication machinery, background/signal repair infrastructure, or checkpoint/consolidation policy owned by later epics.

## Lessons For Requirements Preflight

1. Run the mechanism-removal counterfactual before validating exception tags:
   if row locking, retry state, and transaction coupling disappear, can the
   stories still be satisfied by uniqueness plus existing seams?
2. Treat exact concurrency guarantees as product scope. Do not infer them from
   `Data Integrity` when the owner accepts ordinary last-writer or
   creation-winner behavior for rare races.
3. Scale safeguards to the actual organization and user base. A lean team
   serving thousands of learners cannot sustainably own machinery designed for a
   hyperscale platform unless user value truly requires it.
4. Distinguish invariants from globally ordered observations: "starting never
   changes after creation" does not imply "the chronologically earliest of all
   overlapping requests must win."
5. Keep Critical-lane touchpoint restrictions strict while keeping sidecar
   semantics simple.
6. When `convergence-review` repeatedly discovers new defects inside newly added
   safeguards, reconsider the safeguard mechanism before repairing it again.
7. Rare repair states (such as a missing canonical progress row whose existing
   self-healing is already authoritative) belong in design rationale, not ERs.

## Calibration Questions

1. Does every `Reliability` or `Data Integrity` mechanism name an independently
   existing user-visible failure and its realistic frequency?
2. Are exact concurrency, retry, and transactional-coupling guarantees treated
   as first-class scope additions requiring explicit human sign-off rather than
   exception-label inference?
3. When the owner explicitly accepts rare-race imprecision, does preflight mark
   contrary perfect-ordering language as unsupported?
4. Should a rapid increase in locks, transaction boundaries, coordination state,
   and concurrency tests during coding trigger automatic re-evaluation of the
   originating ER?
5. Are safeguards calibrated to the team's actual operating conditions rather
   than theoretical perfection?
