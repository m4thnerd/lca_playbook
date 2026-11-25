# `convergence-review` ER Justification Preflight

This guide defines the independent justification review for a drafted
`# Essential Requirements` section.

Run this alongside
[convergence_review_preflight_requirements_scoring.md](convergence_review_preflight_requirements_scoring.md).
The scoring preflight asks whether each ER is Minimal, Clear, and
architecturally well bounded. This justification preflight asks whether every
ER is necessary and proportionate to its sources, and whether every inline
source tag is legitimate.

## Required Reading

Before every review, read and apply:

1. the [architecture critic guidelines](../reviewers/architecture_critic.md),
   especially its core questions and its tests for unjustified scope,
   over-engineering, unpriced cost, and avoidable architectural pressure;
2. **every Markdown case study** in
   [`example-case-studies/requirements-risk/`](../example-case-studies/requirements-risk/),
   plus any local calibration files under `case-studies/local/` when present; and
3. the target repository's operating conditions (`case-studies/local/operating-conditions.md`
   when present; see the example profile in
   [lean-saas-team.md](../example-case-studies/operating-conditions/lean-saas-team.md)).

The tracked requirements-risk calibration set includes:

- [Exception Labels and an Unsupported Completion-ID Protocol](../example-case-studies/requirements-risk/unsupported-completion-id-protocol.md)
- [Exception Labels and a Perfect-Concurrency Snapshot Protocol](../example-case-studies/requirements-risk/perfect-concurrency-snapshot-protocol.md)
- [Review Findings Became Requirements](../example-case-studies/requirements-risk/review-findings-became-requirements.md)
- [Agent-Authored ERs and Unrequested Operational Refusal Gates](../example-case-studies/requirements-risk/agent-authored-ers-and-operational-gates.md)
- [Autonomous Preflight Self-Inflation, Runtime Self-Policing, and Follow-Up Snowballs](../example-case-studies/requirements-risk/preflight-self-inflation-and-follow-up-snowballs.md)

The first two failures occurred independently within the same hour on real
deliverables. That frequency is the calibration signal: without active
architecture-critic scrutiny, exception labels can launder unnecessary
mechanisms in almost every ER pass. Apply their mindset upstream while
requirements are still cheap to simplify.

Use your actual team staffing, deployment, administrative-usage, and maintenance
constraints when deciding whether a failure mode or safeguard is proportionate.
Do not review against an imagined hyperscale operating environment when the
target system is operated by a lean product team.

## Core Principle

Every ER must visibly justify why it exists **and why it carries this much
mechanism**.

The source tag is not decoration. It is a claim that the ER is justified by a
specific user story, accepted design constraint, module-charter concern, or
narrow exception label. A reviewer must test that claim independently.

A locally truthful tag does not prove that an ER belongs. `Data Integrity`,
`Reliability`, `Maintainability`, `Performance`, or `Security/Privacy` may
accurately describe safeguards made necessary by a protocol, schema, lock,
retry path, compatibility layer, or abstraction that the stories never needed
in the first place. Test the necessity and proportionality of the underlying
mechanism before validating the labels attached to its safeguards.

## Inputs

- the design doc, including user stories and body text
- the linked Verbatim Human Intent Reference (when present; see
  [verbatim_human_intent_reference_playbook.md](verbatim_human_intent_reference_playbook.md))
- the drafted `# Essential Requirements`
- [convergence_review_essential_requirements.md](convergence_review_essential_requirements.md)
- all required reading above
- relevant module charters or draft charters when a `Maintainability` tag is
  used for module-boundary or lane reasoning

Do not run code-aware LoC estimation for this review. Lightweight architecture
inspection is allowed when needed to identify an existing contract, extension
point, or repository-standard mechanism, or to verify a source-tag claim.

## Allowed Tags

Use user-story IDs when an ER is justified by product value (`[US-1]`,
`[US-1, US-3]`). Use exception labels only when the ER needs to exist even
without a direct user story:

- `Data Integrity`
- `Security/Privacy`
- `Maintainability`
- `Maintainability:CriticalLane`
- `Maintainability:CarefulLane`
- `Maintainability:FullSpecLane`
- `Maintainability:FastLane`
- `Reliability`
- `Performance`

Mixed tags are allowed (`[US-2; Data Integrity]`,
`[US-4; Maintainability:CarefulLane]`).

## Architecture-Critic Precheck

Before parsing tags, test each ER as an architecture critic working upstream:

0. **Verify against the linked Verbatim Human Intent Reference (mandatory when
   `ER Sign-Off Status` is `Agent-Drafted (Unreviewed)` or absent).** Read the
   companion Verbatim Human Intent Reference file linked from the design doc
   (if present). Does this ER introduce a new operational refusal gate,
   interactive confirmation prompt, state machine, mode, or workflow change that
   the human did not ask for? If yes, **Fail** the ER immediately: standalone
   exception labels (`[Reliability]`, `[Data Integrity]`, `[Maintainability]`,
   etc.) cannot authorize unrequested behavioral gates or state machines without
   human sign-off.
1. **Name the source outcome.** State the user-visible outcome, independently
   existing failure mode, accepted constraint, or module-boundary need that
   requires the ER.
2. **Remove the proposed mechanism.** If its new protocol, persistence,
   abstraction, concurrency guarantee, transaction coupling, retry state,
   compatibility path, or configurability disappeared, could the source still
   be satisfied correctly through an existing contract or a materially simpler
   mechanism?
3. **Test proportionality.** Is each guarantee warranted by the actual failure
   frequency, product scale, operational environment, and maintenance capacity?
   Treat exact concurrency, ordering, retry, atomicity, and compatibility
   guarantees as scope additions, not free implications of an exception label.
4. **Separate bundled obligations.** When an ER combines a product outcome with
   schema, transaction, migration, fallback, compatibility, or future-facing
   machinery, require each obligation to demonstrate independent necessity.
5. **Choose the least architectural pressure.** If the source can be satisfied
   correctly by extending an existing contract or by a clearly smaller durable
   surface, fail the heavier requirement and name the concrete simplification.

One clear lower-pressure path is enough to show that a proposed obligation is
not essential. When no materially simpler correct path is apparent, continue to
the tag review without manufacturing a finding.

## Tag Review Questions

Only after the architecture-critic precheck passes, parse the inline tag and
evaluate every entry independently.

For each user-story tag:

- Does the story actually require or strongly motivate this ER?
- Would the ER still be justified by that story if all exception labels were
  removed?
- Is the ER narrower than, or equal to, the story's actual value rather than an
  expansion beyond it?
- Is the story current-pass scope rather than deferred, exploratory, or merely
  adjacent?

For each exception label:

- First ask whether the failure mode exists independently of machinery proposed
  by the ER and whether the safeguard is proportionate. A label that becomes
  relevant only because the ER invented a heavier mechanism does not justify
  that mechanism.
- `Data Integrity`: validation, migration safety, canonical data shape,
  persisted-state correctness, duplicate prevention, or preventing corrupt
  state?
- `Security/Privacy`: auth, permission boundaries, tenant isolation,
  sensitive-data handling, prompt-injection safety, or privacy? (Context limits
  for cost or model quality are not `Security/Privacy`.)
- `Maintainability`: module-charter alignment, decoupling, module ownership,
  lane expectations, avoiding parallel systems, minimizing needless LoC, or
  future understandability?
- `Reliability`: graceful failure, fallback behavior, idempotency,
  timeout/retry boundaries, or avoiding user-visible breakage?
- `Performance`: caching, query reduction, latency, throughput, background-work
  boundaries, or avoiding high-frequency work?

## Verdicts

Use one verdict per ER, covering both necessity and tag legitimacy:

- `Pass`: the ER is necessary, proportionate, and no heavier than its sources
  require; every claimed user-story ID and exception label is legitimate.
- `Fix Tags`: the ER is necessary and proportionate, but one or more tags are
  weak or false positive and should be removed or replaced.
- `Retag`: the ER is necessary and proportionate, but the current tag set misses
  the real justification.
- `Fail`: the ER has no legitimate source, or it imposes unnecessary or
  disproportionate mechanism even though its tags may locally describe that
  mechanism truthfully.

Do not rewrite an ER just because a tag is wrong; recommend a tag-only fix when
the ER itself is valid.

## Recommended Output Format

```text
| ER | Justification Verdict | Action | Rationale |
|---|---|---|---|
| ER-1 short label | Pass | Keep `[US-1]`. | US-1 directly requires routed model choice for learner response quality. |
| ER-2 short label | Fix Tags | Remove `Security/Privacy`; keep `[US-1; Performance]`. | Context limiting is about routing quality/cost, not privacy. |
| ER-3 short label | Retag | Replace `[US-2]` with `[Data Integrity]`. | Validation is needed to prevent invalid config, not because US-2 directly asks for validation. |
| ER-4 exact-concurrency protocol | Fail | Replace with ordinary uniqueness through the existing write seam. | The story requires one durable fact, not perfect ordering, locks, transaction coupling, and retry state for vanishingly rare races. |
```

Follow the table with concise lists of tag-only fixes, retags, failed ERs, and
any questions requiring human judgment.

## Readiness Standard

Before implementation:

- every ER has a visible inline source tag
- every ER passes the architecture-critic precheck before its tags are evaluated
- every durable mechanism and guarantee is necessary and proportionate to an
  independently established source outcome or failure mode
- existing contracts or clearly smaller correct mechanisms win over new durable
  surfaces
- every user-story tag and exception label matches its defined meaning without
  false positives or laundered safeguards
- ERs with `Fail` verdicts are rewritten, retagged, or removed
