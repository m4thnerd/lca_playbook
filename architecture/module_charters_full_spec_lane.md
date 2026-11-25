# Module Charters: Full-Spec Lane

The canonical purpose of the Full-Spec lane, its relationship to the other
three lane postures, and the distinction between Fast-lane deletion and
Full-Spec implementation substitution are owned by
[`module_charters.md`](./module_charters.md). Existing file-annotation and
Fast-lane mechanics are documented in
[`module_charter_annotations.md`](./module_charter_annotations.md); the
Full-Spec-specific enforcement additions are defined in this guide.

This document is the detailed how-to reference for lead coding agents and
humans designing, placing, implementing, verifying, changing, or reviewing a
Full-Spec responsibility cluster.

## Definition

A **Full-Spec responsibility cluster** is a cohesive group of closely related
production responsibilities that:

1. is the sole owner of a short, complete Responsibility Charter;
2. owns a named product or system outcome that callers consume through a narrow
   public boundary;
3. contains, or explicitly contracts for, the state and side effects required
   to deliver that outcome;
4. has no unrecorded non-local invariant that an implementer would need to
   rediscover from the existing code; and
5. can have its implementation replaced within the package while its accepted
   charter, boundary contract, and verification harness remain fixed.

The cluster may be implemented in one file or several closely related files.
The directory and charter identify the ownership unit; individual function
annotations do not create lane membership.

"Full" refers to specification completeness: all identified materially relevant
behavior, constraints, boundaries, and invariants are recorded outside the
implementation. It does not require the charter to restate every line or
incidental implementation choice, and it does not claim formal verification.
Full-Spec and Fast are both Spec-Driven Development (SDD) styles; this guide
defines the stronger specification and verification bar particular to
Full-Spec responsibilities.

## The Responsibility Charter

Each direct child responsibility package under `full_spec/` owns one
Responsibility Charter. It uses the same durable language as a Module Charter
but is scoped to one cohesive slice rather than requiring the parent module's
entire history to be documented first.

> **Legacy naming compatibility (`rebuildable/`):** Earlier adopters implemented
> this lane under its original name, **Rebuildable Lane**, using `rebuildable/`
> package directories, `REBUILDABLE.json` manifests, and `Rebuildable` hazard
> taxonomy headers in repository CI checks. New repositories should standardize
> on `full_spec/` and `FULL_SPEC.json`; existing repositories with active
> `rebuildable/` CI enforcement should follow their repository's enforced
> directory and manifest names until migrated.

Required sections:

```markdown
# <Responsibility Cluster> Charter

## Essential User Stories

## Durable Requirements

## Owned Responsibilities

## Public And Integration Contracts

## Explicit Non-Ownership

## Verification Contract
```

The first two sections remain the load-bearing core. The other sections make
the specification and implementation-substitution boundary concrete:

- **Owned Responsibilities** names what this cluster alone decides, reads,
  mutates, or coordinates.
- **Public And Integration Contracts** describes supported callers, inputs,
  outputs, error behavior, state semantics, and required lifecycle seams.
- **Explicit Non-Ownership** prevents adjacent framework, persistence,
  presentation, or domain concerns from leaking inward accidentally.
- **Verification Contract** identifies the protected tests, fixtures,
  properties, compatibility checks, and performance or concurrency evidence
  that make replacement credible.

A broad parent Module Charter may point to several responsibility charters.
This permits incremental adoption without pretending that the entire parent
module is already comprehensively chartered.

## Choosing The Right Granularity

The goal is cohesive ownership, not maximum fragmentation.

A responsibility cluster is appropriately grouped when its responsibilities:

- serve the same small set of Essential User Stories;
- change for substantially the same product reasons;
- participate in the same state or decision lifecycle;
- are naturally changed and verified together;
- expose one coherent result or capability to callers; and
- can be described completely by one short charter without vague language.

Split the cluster when two areas:

- have unrelated user stories or independent reasons to change;
- own different authoritative state;
- require materially different hazard or review postures;
- expose separate contracts with separate consumers; or
- could be specified and changed independently without coordinating their
  implementations.

Do not create a directory per function, formula clause, or minor helper. A
single cohesive frontend epic may reasonably own policy evaluation, local state
progression, and a stable completion result in one Full-Spec responsibility
cluster. Several unrelated frontend epics should not be merged merely because
they share a page.

Example responsibility-package names:

```text
frontend/src/pages/topic_progress/full_spec/
├── topic-progress-checkpoint-responsibilities/
└── topic-progress-nongraded-learning-responsibilities/
```

These names describe durable ownership clusters. A narrowly named package such
as `topic_progress_formula/` is appropriate only when the formula genuinely is
the complete responsibility, not as a canonical requirement to split every
epic into formula-sized fragments.

## Positional Placement: Nearest Legitimate Owner

`full_spec/` is a positional marker that may appear at different depths. A
responsibility cluster should live beneath the narrowest existing code area
that legitimately owns or primarily consumes it, rather than in one global
warehouse for every Full-Spec responsibility in the application.

For example, a page-specific frontend responsibility may use this shape:

```text
frontend/src/pages/
└── topic_progress/
    ├── TopicProgressPage.vue             # Careful page orchestration
    ├── topicProgress.ts                  # Careful shared page integration, if needed
    └── full_spec/
        ├── topic-progress-checkpoint-responsibilities/
        └── topic-progress-nongraded-learning-responsibilities/
```

A responsibility shared by many composables rather than owned by one page may
instead live here:

```text
frontend/src/composables/
└── full_spec/
    └── <cohesive-responsibility-cluster>/
```

The same principle applies to backend modules and other frontend areas:

```text
backend/scoring/full_spec/<responsibility>/
frontend/src/store/full_spec/<responsibility>/
frontend/src/components/<feature>/full_spec/<responsibility>/
```

Placement guidance:

- Put page-specific logic beside its page so the charter and lane cannot be
  missed during page work.
- Put genuinely cross-page logic under the shared owner that gives it meaning,
  such as `composables/`, `store/`, or a named feature directory.
- Keep Careful integration and visible presentation at the owning directory's
  root when they do not belong inside the Full-Spec charter.
- Do not move a responsibility upward merely to make it easier for hypothetical
  future consumers to find.
- Do not create `frontend/src/full_spec/` as a default dumping ground when a
  narrower owner exists.
- Do not duplicate one responsibility under several nearby `full_spec/`
  directories; one cluster remains the sole owner of its charter.

The lane map remains derived: any path segment named `full_spec/` declares
Full-Spec placement. CI evaluates each direct child responsibility package
relative to its nearest `full_spec/` ancestor.

Reorganizing an existing single-file page into a page directory may be a useful
part of introducing a Full-Spec cluster, but it is not mandatory when another
nearby owner already provides a clear and discoverable boundary. File movement
should improve ownership, not serve the directory convention mechanically.

## Eligibility Bar

Full-Spec eligibility is earned through evidence. A responsibility cluster is
eligible when all of the following are true.

### 1. Sole charter ownership

- The package is the sole production owner of a short, complete Responsibility
  Charter.
- The charter states user outcomes and durable requirements precisely enough
  to judge substantially different implementations.
- The charter does not merely restate the current algorithm, file layout, or
  framework mechanics.
- Any parent Module Charter and adjacent responsibility charters agree about
  ownership; no rule is silently duplicated.

### 2. Cohesive responsibility boundary

- The cluster owns one coherent outcome or a tightly related group of outcomes.
- Callers use a named public boundary instead of importing implementation
  internals.
- Responsibilities that must change together remain together; unrelated
  responsibilities remain outside.
- Integration points and non-ownership are explicit enough that an internal
  implementation change does not require editing callers opportunistically.

### 3. Complete state and side-effect semantics

Database writes, cache operations, network calls, filesystem access, browser
storage, framework state, clocks, randomness, and global state are not
categorically prohibited. They are eligible only when their relevant semantics
are contained and verifiable.

For every stateful or side-effecting behavior, the charter and implementation
boundary must make clear:

- which state the cluster is authorized to read or mutate;
- whether it is the sole writer or which named write seam it must use;
- transaction, retry, idempotency, concurrency, and failure semantics where
  applicable;
- cache update or invalidation ownership, if any;
- persistence shape and migration compatibility for durable data;
- study-day, clock, randomness, identity, tenant, or request-context semantics
  when those affect behavior;
- cleanup and versioning responsibilities for Pinia, browser storage, or other
  client state; and
- how tests control, reproduce, or verify those effects.

A package may write database fields when it solely owns those writes and the
write lifecycle is local and fully specified. It is not eligible when a
seemingly local write depends on an undocumented cache sequence, parallel write
path, cross-module resynchronization protocol, or transaction ordering that is
outside the package's accepted contract.

A frontend package may read Pinia, Vue state, browser storage, the clock, or
route context when those are legitimate parts of its cohesive responsibility.
Framework independence and functional purity are useful isolation techniques,
not eligibility requirements.

### 4. Bounded coupling

- Dependencies are explicit, few enough to review, and consumed through stable
  seams.
- The package does not reach through other modules' internal layers or acquire
  behavior through incidental import side effects.
- Code outside the package may import its supported public entry point but may
  not deep-import its implementation files.
- The implementation can change while preserving the public entry point and
  integration contracts without coordinating internal edits in consumers.
- Any cross-boundary lifecycle ordering is named and tested rather than left to
  convention.

Unlike `fast_lane/`, imports from a Full-Spec package are expected and
permitted. The restriction is public-boundary enforcement, not a no-import
valve.

### 5. Sufficient verification

- Durable Requirements map to independent contract or acceptance tests.
- Boundary cases, error paths, state transitions, and recovery behavior are
  tested in proportion to consequence.
- Persisted writes have integration tests covering their authoritative write
  path and compatibility semantics.
- Concurrency, retry, idempotency, cache, time, or randomness behavior has
  focused verification when the responsibility owns it.
- Calibrated or mathematical behavior uses boundary, property, golden,
  metamorphic, or parity tests as appropriate rather than relying only on line
  coverage.
- Performance-sensitive behavior has an explicit envelope and repeatable
  evidence.
- The full consumer suite can run without implementation-specific changes.

Coverage percentage alone does not establish Full-Spec eligibility. The
question is whether the harness would reject plausible implementations that
violate the charter while accepting materially different correct
implementations.

#### Charter-first contract test design

Full-Spec responsibilities use a charter-first verification sequence. The
accepted user stories and Durable Requirements are reviewed before the
verification target is considered complete. Test-driven development is welcome
when it clarifies the contract, but is not mandatory: tests may be written
before the implementation, alongside an exploratory implementation, or during
the hardening pass. What is mandatory is that the protected harness ultimately
be derived from the accepted charter rather than reverse-engineered only from
the implementation that happened to be written.

Before a material spec-preserving implementation change is accepted, perform a
focused blind-spot review against the charter. At minimum:

- each Durable Requirement maps to a test or to a named non-test verification
  method when automated testing is not the right evidence;
- each Essential User Story has representative journey or outcome coverage;
- likely and possible system states implied by those journeys are considered,
  including not-started or empty state, in-progress or partial state,
  completed or terminal state, resumed or retried state, threshold boundaries,
  and legitimate user continuation beyond a recommendation or checkpoint;
- the most plausible boundary, failure, state-transition, and integration bugs
  are considered explicitly; and
- each compatible or conditional hazard tag's required action is represented
  in the verification contract.

An independent agent or reviewer should perform this pass from the charter and
public contract before studying implementation details when practical. The
purpose is to find omissions, not to maximize the test count.

**Do:**

- test externally meaningful behavior, invariants, state transitions, and
  owned side effects;
- select representative equivalence classes and high-risk boundaries;
- add property, parity, mutation, concurrency, or integration testing only
  where the responsibility's risk makes that evidence valuable;
- name the Durable Requirement or plausible defect class protected by each
  contract test; and
- prefer a small set of tests that would reject materially wrong alternative
  implementations over many tests that restate one implementation.

**Do not:**

- require one test per line, helper, branch, or private method;
- chase a universal line-coverage percentage as the quality target;
- duplicate cases that add no new requirement, boundary, or failure evidence;
- mock internal collaborators so heavily that tests encode the current file
  structure;
- exhaust every theoretical input combination without a credible risk model;
- test framework behavior already guaranteed by the framework; or
- make the harness so prescriptive that substantially different correct
  implementations cannot pass.

If an edge case, failure mode, or invariant matters to production correctness,
put it directly into `Durable Requirements` and give it protected contract
coverage; nothing that matters has to stay unwritten or unverified. Stop adding
protected tests once every material requirement and credible defect class is
covered and the next proposed test would only duplicate existing evidence or
lock in an incidental implementation choice.

### 6. Replacement feasibility

- An implementer can understand the accepted behavior without reverse
  engineering the current internal implementation.
- The implementation can be replaced inside the package without changing
  callers, the accepted charter, or protected contract tests.
- Durable data can be preserved, migrated through an accepted plan, or is
  explicitly declared expendable.
- The replacement does not require relaxing hazard requirements, bypassing
  authorization, or distributing new responsibility across unrelated files.

The standard is a complete, reviewable specification and contract suite strong
enough that incidental implementation choice is no longer the primary
human-review surface.

## State And Database Writes

The Full-Spec lane is permitted to own durable state. This is a major
difference from a stateless-only interpretation and from the Fast lane's
expendable-data default.

Durable writes are appropriate when:

- the responsibility charter names the state and its learner, operator, or
  system purpose;
- one Full-Spec cluster is the sole owner of the write path, or every write
  routes through a single named seam it owns;
- authorization and tenant boundaries are explicit and verified;
- transaction and failure behavior are locally understandable;
- cache behavior is either absent, fully contained, or delegated through a
  narrow documented owner;
- migrations and compatibility are part of the replacement contract; and
- recovery and repair expectations are documented.

Durable writes are not appropriate when safe mutation depends on several
modules remembering to perform coordinated actions that the Full-Spec
cluster neither owns nor can verify.

The presence of persistence raises the verification bar; it does not
automatically make an otherwise isolated responsibility non-Full-Spec.

## Framework And Runtime State

A Full-Spec responsibility may legitimately depend on a framework. Django
models, Pinia stores, Vue reactivity, request context, browser storage, clocks,
and random selection can all be part of an owned responsibility.

The relevant question is not “Does this code touch a framework?” It is:

> Can the charter and verification harness completely describe the framework
> interaction that must remain true while allowing the internal implementation
> to change?

Prefer dependency injection or plain values when they materially simplify
testing and isolation, but do not manufacture adapters solely to satisfy a
purity aesthetic. Direct framework use is acceptable when it is the clearest
owner, remains within the package boundary, and is covered by the appropriate
integration tests.

## Hazard Tags And Full-Spec Eligibility

Hazard tags are not categorical evidence that code is non-Full-Spec. They
name non-obvious risk and prescribe a required action. Some hazards can be
fully contained within a responsibility cluster; others demonstrate exactly
the sort of non-local coupling that defeats Full-Spec eligibility.

Each repo's hazard taxonomy should eventually classify each tag's interaction
with the Full-Spec lane as one of:

- **Compatible:** the hazard can normally live in `full_spec/` when its
  required action is included in the verification contract.
- **Conditional:** the tag creates a presumption against Full-Spec eligibility, but an
  explicit isolation argument and stronger harness may rebut it.
- **Incompatible:** the hazard necessarily depends on a non-local invariant or
  review posture that cannot be contained behind the responsibility boundary.

Likely examples, subject to repo-specific review:

| Hazard shape | Likely posture | Reason |
|---|---|---|
| Sole write path fully owned inside the cluster | Compatible | Exclusive ownership strengthens isolation when every mutation and repair path is covered. |
| Calibrated values | Compatible or Conditional | Full-Spec when values and approval constraints are protected inputs/contracts; changing calibration remains a product decision. |
| Hot path | Conditional | Requires a measurable performance envelope and before/after evidence. |
| Persisted shape contract | Conditional | Full-Spec only with explicit compatibility, migration, and consumer verification. |
| At-most-once behavior | Conditional | May be contained, but claim, transaction, and failure semantics need unusually strong tests. |
| Order-dependent pipeline | Conditional or Incompatible | Internal ordering may be contained; ordering coupled to external steps usually defeats the boundary. |
| Cache/commit coupling across modules | Normally Incompatible | Safety depends on non-local sequencing and coordinated owners. |
| Denormalized state with cross-module resync | Normally Incompatible | Incremental writes and repair ownership commonly escape the package boundary. |
| Trust boundary or PII egress | Conditional | Isolation is possible, but security/privacy review remains mandatory and implementation-only review may be insufficient. |
| External API quirks | Conditional | Requires provider-contract tests and may still carry change risk outside local control. |

This table is guidance, not a substitute for updating each repo's authoritative
hazard taxonomy. The taxonomy must define the actual classification and required
evidence.

A new hazard tag inside a Full-Spec package triggers a lane-compatibility
review. Possible outcomes:

1. retain the package because the hazard is compatible and the harness already
   satisfies its required action;
2. strengthen the charter, boundary, or verification for a conditional hazard;
3. move the hazardous mechanic to a Careful or Critical owner while preserving
   a Full-Spec core; or
4. graduate the responsibility out of `full_spec/`.

Do not invent “important function” hazard tags. Product importance belongs in
Essential User Stories and the verification bar; hazard tags carry technical
knowledge that cannot be reconstructed locally.

## Protected Charter And Verification Harness

Full-Spec eligibility depends on preserving the specification and evidence
while the implementation changes. An agent must not establish correctness by
weakening the charter and tests alongside a rewrite.

A responsibility package therefore distinguishes:

- **protected artifacts:** Responsibility Charter, public contract, durable
  acceptance tests, compatibility fixtures, and required performance or
  concurrency evidence;
- **implementation artifacts:** internal implementation, local helpers, and
  implementation-specific tests.

Protected does not mean immutable. It means changes to these artifacts are
behavior or architecture changes and receive Careful product/architecture
review before an implementation change is evaluated against the new target.

Contract tests may live outside the Full-Spec directory, or CI/CODEOWNERS may
apply stronger review rules to protected paths inside it. Physical placement is
less important than making the review distinction enforceable and obvious.

Example backend shape:

```text
scoring/
└── full_spec/
    └── topic_progress_responsibilities/
        ├── CHARTER.md
        ├── __init__.py              # supported public boundary
        ├── scoring_policy.py
        ├── calibration_adapter.py
        └── persistence.py           # allowed when the cluster owns it

tests/
└── full_spec_contracts/
    └── scoring/
        └── test_topic_progress_responsibilities.py
```

Example frontend shape:

```text
frontend/src/pages/topic_progress/
├── TopicProgressPage.vue
└── full_spec/
    └── topic-progress-checkpoint-responsibilities/
        ├── CHARTER.md
        ├── index.ts                     # supported public boundary
        ├── topicProgressCheckpoint.ts   # may be the sole implementation file
        └── localState.ts                # add only if cohesion benefits

frontend/test/full-spec-contracts/
└── topicProgressCheckpoint.spec.ts
```

The examples illustrate cohesive clusters, not required file counts. A single
implementation file is preferred when it remains clear. Split files only when
the responsibilities remain cohesive but distinct internal concerns improve
readability or verification.

## Public Boundary And Import Rules

The Full-Spec lane permits external production consumers, unlike the Fast
lane. It protects implementation freedom through an import membrane:

- every responsibility package exposes one supported public entry point;
- code outside the package imports only that entry point;
- deep imports into internal files are CI-prohibited;
- internal files may use framework and domain dependencies named by the
  charter;
- the package must not import from its downstream consumers;
- circular dependencies across the boundary are prohibited; and
- changing the public boundary is a protected contract change, not an
  ordinary spec-preserving implementation change.

The public entry point may expose functions, types, a service object, framework
registration, or another idiomatic contract. The lane does not require every
language or framework to imitate a pure-function API.

## Implementation-Substitution Test

A responsibility remains eligible only if it can pass this thought experiment
and, for material replacements, the corresponding real review:

1. Freeze the accepted Responsibility Charter, public boundary, protected
   tests, compatibility fixtures, and performance/concurrency envelopes.
2. Remove or ignore the replaceable implementation.
3. Give an implementer the protected artifacts and documented integration
   seams, but do not require them to imitate the prior internal design.
4. Produce the replacement entirely within the responsibility package.
5. Make no production changes to callers or unrelated modules.
6. Preserve or explicitly migrate durable state according to the accepted
   contract.
7. Pass protected tests, focused integration tests, full consumer tests, and
   the repo's normal verification.
8. Confirm that no new hazard, owner, public dependency, or non-local invariant
   appeared.

If a competent implementer must study the deleted implementation to rediscover
essential behavior, the charter or harness is incomplete. If callers must
change to accommodate the replacement, the public boundary is not stable enough
or the responsibility was scoped incorrectly.

## Change Process

### Spec-preserving implementation change

A spec-preserving implementation change - whether a surgical edit, refactor, or
complete replacement - preserves:

- Essential User Stories;
- Durable Requirements;
- owned and non-owned responsibilities;
- public and integration contracts;
- protected acceptance tests and fixtures;
- durable data compatibility; and
- required hazard actions and operational envelopes.

Line-level human review can be lighter because the charter and independent
evidence are the primary review surface. Architecture compatibility and any
security/privacy evidence still apply.

### Specification or boundary change

A change to any protected artifact is not an ordinary spec-preserving
implementation change. It begins with the normal design process:

1. update and review the user stories or Durable Requirements;
2. update ownership and contract language;
3. update the protected verification target;
4. reassess lane and hazard eligibility; and
5. then implement against the newly accepted contract.

### Post-change check

Reviewers verify that:

- actual ownership still matches the charter;
- no consumer deep-imports implementation details;
- state and side-effect behavior remained inside the accepted boundary;
- no protected tests were weakened to admit the new implementation;
- no new cross-module coordination burden appeared; and
- the implementation remains substantially replaceable rather than merely
  well-tested in its current form.

When a defect in a materially changed responsibility could break an affected
journey end to end, the implementer must also perform smoke testing equivalent
in scope to an integration test. This requirement applies especially when
automated browser or end-to-end coverage is absent, too slow, or too flaky to
provide reliable evidence. The smoke test must exercise the real integration
path far enough to detect wiring, state, rendering, and interaction failures
that unit or contract tests would miss, and its result must be recorded with
the change evidence.

For UI changes with fragile or materially user-visible behavior, capture
representative screenshots and place them in the repository's gitignored local
review area, such as `local/`, so a local human developer can scan and confirm
the resulting states. Capture the states that matter to the charter and risk,
not an exhaustive screenshot matrix.

## Progressive Adoption In Existing Codebases

The Full-Spec lane makes module-charter adoption incremental. Teams do not
need to retroactively produce a comprehensive charter for every large legacy
module before gaining value.

When adding or materially changing a responsibility:

1. identify the smallest cohesive responsibility cluster that serves the
   accepted user stories;
2. map its current state, writes, consumers, hazards, and integration seams;
3. draft and obtain human agreement on its Responsibility Charter;
4. create protected contract tests that reflect intended behavior rather than
   blindly freezing incidental legacy behavior;
5. characterize legacy outputs where parity matters;
6. isolate the public boundary and move the implementation into
   `full_spec/<responsibility>/` only when the eligibility bar is met;
7. enforce imports and hazard compatibility in CI; and
8. leave unrelated legacy code and undocumented responsibilities in their
   existing Careful or Critical posture.

This is a strangler-style migration of responsibilities, not a documentation
campaign. Each accepted move both improves the architecture and expands the
portion of the codebase that agents can safely change against an accepted
specification.

Do not move code merely because it has high coverage or appears simple. The
move must create real ownership isolation, a complete charter, an enforceable
boundary, and independent evidence.

## Frontend Application: Topic Progress

The Topic Progress work illustrates how a frontend `full_spec/` cluster pairs
with backend-owned persistence so each side stays cohesive without entangling
UI evaluation with canonical backend score storage.

One responsibility cluster owns the stateless daily checkpoint evaluator:

```text
frontend/src/pages/topic_progress/full_spec/
└── topic-progress-checkpoint-responsibilities/
```

While the backend (`learner_data/daily_snapshots.py`) owns per-day
starting/current progress snapshots, study-day rollover, and authoritative
graded-activity equivalence facts, the frontend checkpoint cluster's charter
owns the pure, server-derived responsibilities to:

- compute the learner's daily topic-gain target from backend-supplied daily
  starting score and current score data;
- evaluate the dynamic topic-score gain and three-SK breadth completion
  paths;
- combine checkpoint completion with backend-supplied daily graded-practice
  facts to determine whether review consolidation is recommended; and
- expose one stable, stateless presentation result that the visible Topic
  Progress UI consumes.

Keeping durable daily baseline persistence, study-day rollover, and activity
counting on the backend lets the frontend cluster remain a deterministic
evaluator without owning browser-persisted state, sticky completion latches,
client-side date comparisons, or cross-tab reconciliation machinery.

A second cohesive cluster could own the non-graded consolidation epic if its
accepted user stories remain distinct:

```text
frontend/src/pages/topic_progress/full_spec/
└── topic-progress-nongraded-learning-responsibilities/
```

It may own the frontend state machine and assistant kickoff orchestration for
guided consolidation, teach-back selection, completion, and move-on readiness,
while UI components own exact markup and styling and the backend assistant
context owns authoritative tutor behavior.

The correct split follows user stories and reasons to change, not a desire to
maximize the number of Full-Spec packages.

## Backend Application: Scoring

The Scoring module illustrates why product importance and technical hazard
must remain distinct.

A canonical mastery or recommendation responsibility may be highly
consequential while still being eligible for Full-Spec when:

- its accepted rules and calibration boundaries are completely chartered;
- its relevant inputs and outputs are explicit;
- it is the sole owner of its computation and, where appropriate, its write
  path;
- persistence and repair semantics are contained and tested;
- cache invalidation or denormalized resynchronization does not depend on
  unowned cross-module sequencing; and
- independent tests exercise boundaries, invariants, representative fixtures,
  and compatibility.

Other responsibilities in the same parent module may remain Critical because
they coordinate caches, transactions, denormalized state, migrations, or many
consumers through non-local invariants. A `full_spec/` island inside a
Critical-heavy module is an intended shape, just as a `fast_lane/` island may
exist inside one today.

The goal is not to move an entire module into the new lane. It is to isolate
specific responsibility clusters gradually as new work supplies the charter,
boundary, and verification evidence needed to earn Full-Spec eligibility.

## CI And Enforcement

A repo adopting the lane should implement mechanical checks appropriate to its
languages and frameworks:

- identify every direct child package under any `full_spec/` directory;
- require one Responsibility Charter per package;
- require a declared public entry point;
- reject production deep imports into internal package files;
- reject circular dependencies across the public boundary;
- validate hazard tags against the repo's Full-Spec compatibility mapping;
- require a protected contract-test target or manifest;
- distinguish protected-artifact changes from implementation-only changes;
- require broader review when charter, contract, durable-state, authorization,
  hazard, or protected-test files change; and
- include Full-Spec contract suites in normal CI.

CI should not impose blanket bans on database, cache, network, framework,
Pinia, Vue, clock, randomness, or storage imports. It should instead enforce
the boundaries, declared ownership, hazard posture, and required verification
that make those dependencies acceptable.

## Graduation And Demotion Triggers

A Full-Spec responsibility receives a lane review when:

- a new hazard tag is added or an existing tag's classification changes;
- an external consumer begins deep-importing internals;
- a second package starts writing state the cluster claims to own exclusively;
- durable state changes without an accepted compatibility or migration plan;
- cache, transaction, retry, or ordering correctness begins depending on
  unowned external steps;
- authorization, privacy, compliance, or external-contract scope materially
  expands;
- protected tests can no longer express the requirements without imitating the
  implementation; or
- unrelated user stories accumulate until the charter is no longer short and
  cohesive.

Review outcomes:

1. repair the boundary and remain Full-Spec;
2. split unrelated responsibilities into separate cohesive clusters;
3. move a hazardous seam to a Careful or Critical owner and retain a
   Full-Spec core;
4. graduate the whole responsibility to Careful or Critical; or
5. redesign the public contract.

Code may also move from Careful or Critical into Full-Spec when a refactor
eliminates or contains the hazards and the complete eligibility bar is met.

## Common Failure Modes

### Responsibility confetti

Every formula and helper receives its own charter and directory. This makes the
system harder to understand and forces related changes across many artificial
boundaries. Group tightly related responsibilities that share user stories,
state lifecycle, and reasons to change.

### Charter laundering

A vague charter is written after implementation to declare existing code
Full-Spec. A charter must be precise enough to reject incorrect alternative
implementations and must receive human agreement before it serves as the
accepted implementation target.

### Test co-rewrite

The implementation and its acceptance tests are weakened together until CI
passes. Protected tests and charter changes are behavior changes, not ordinary
implementation-change mechanics.

### Coverage as proof

High line coverage is treated as evidence of a complete responsibility
contract. Coverage says which lines executed, not whether the accepted behavior
has been specified.

### Purity as architecture theater

Framework state and writes are pushed into thin adapters solely so the core can
be called pure, even though ownership becomes less coherent and the adapters
retain all meaningful risk. Use purity when it simplifies the assurance case;
do not use it to hide distributed responsibility.

See [`daily-snapshot-semantics-boundary.md`](../example-case-studies/full-spec-lane-judgment-calls/daily-snapshot-semantics-boundary.md)
for a complete worked case where a structurally valid pure semantics package
was compared against a simpler Critical sidecar service and rejected because the
protected boundary did not repay its coordination and verification cost. Keep
project-specific instances under `case-studies/local/`.

### Hidden cross-boundary sequencing

The package appears isolated but safe operation still depends on callers
performing cache invalidation, retries, or cleanup in an undocumented order.
Either bring the lifecycle inside, define and verify the integration contract,
or reject Full-Spec placement.

### Fast-lane valve copied incorrectly

External imports are prohibited, making a reusable responsibility impossible
to consume. Full-Spec uses a public import membrane, not Fast lane's
surface-deletion valve.

### Product importance confused with Critical placement

Consequential behavior is kept out of Full-Spec solely because mistakes
would matter. Consequence should raise charter precision, test strength, and
review expectations. Critical placement is required when technical hazards or
non-local invariants prevent safe replacement.

### Hazard tags treated as binary labels

Every tagged responsibility is rejected, or every locally owned tag is treated
as harmless. Hazard compatibility depends on whether the invariant and its
required action can be contained and independently verified.

## Adoption Checklist

Before placing a responsibility cluster in `full_spec/`:

- [ ] It is the sole owner of a short, complete Responsibility Charter.
- [ ] Its responsibilities are cohesive rather than artificially fragmented.
- [ ] Parent and adjacent charters agree about ownership.
- [ ] Its public boundary and supported consumers are explicit.
- [ ] State, writes, side effects, time, randomness, and framework semantics are
      sufficiently specified for the responsibility it owns.
- [ ] External consumers import only the public entry point.
- [ ] Hazard tags are compatible or have an accepted conditional-isolation
      argument and required evidence.
- [ ] Durable state has compatibility, migration, repair, and authorization
      semantics where applicable.
- [ ] Protected contract tests map to every Durable Requirement.
- [ ] A charter-first blind-spot review considered plausible boundary, failure,
      state-transition, integration, and likely or possible user-state defects
      without expanding into implementation-coupled or exhaustive testing.
- [ ] The verification harness covers relevant boundary, failure, integration,
      concurrency, performance, and recovery behavior.
- [ ] The implementation-substitution test can be satisfied without changing
      callers or weakening protected artifacts.
- [ ] The architecture-pressure forecast explains what coordination burden the
      package retains.

After a material implementation replacement:

- [ ] The accepted charter and public contracts remain satisfied.
- [ ] Protected tests were not weakened as an implementation shortcut.
- [ ] Durable state remained compatible or followed the accepted migration.
- [ ] No unsupported consumer or deep import appeared.
- [ ] No new cross-boundary invariant or hazard escaped the package.
- [ ] Actual side effects and state ownership still match the charter.
- [ ] Affected end-to-end journeys received recorded smoke-test coverage when
      automated integration evidence was absent or insufficient.
- [ ] Fragile or materially user-visible UI states have representative
      screenshots available in the repository's gitignored local review area.
- [ ] The package remains cohesive and replacement-feasible.
