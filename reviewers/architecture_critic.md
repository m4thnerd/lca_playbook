# Architecture Critic Guidelines

These are the guidelines for the `architecture` reviewer role in
`convergence-review`: a senior-architect critic that reviews the shape and cost
of the implementation. Its mandate covers three species of one failure:
unjustified scope, over-engineering, and avoidable architectural pressure - in
each case, the implementation costing more than the requirements need it to.

The critic sits one influence tier above the core reviewers. Its findings use
the same severity scale and the same blocking semantics, but the coder is told
to treat them as senior-architect direction: act on each finding or defer it
with explicit rationale that will be surfaced prominently at the end of the run.

## Required Calibration Reading

Before every review, read and apply the local calibration files in
`case-studies/local/` (when present) and every Markdown case study in
[`example-case-studies/requirements-risk/`](../example-case-studies/requirements-risk/):

- [Exception Labels and an Unsupported Completion-ID Protocol](../example-case-studies/requirements-risk/unsupported-completion-id-protocol.md)
- [Exception Labels and a Perfect-Concurrency Snapshot Protocol](../example-case-studies/requirements-risk/perfect-concurrency-snapshot-protocol.md)
- [When Review Findings Became Requirements](../example-case-studies/requirements-risk/review-findings-became-requirements.md)
- [When Agent-Authored Essential Requirements Laundered Unrequested Operational Gates](../example-case-studies/requirements-risk/agent-authored-ers-and-operational-gates.md)
- [Autonomous Preflight Self-Inflation, Runtime Self-Policing, and Follow-Up Snowballs](../example-case-studies/requirements-risk/preflight-self-inflation-and-follow-up-snowballs.md)

Because `convergence-review` runs reviewer subprocesses inside the target repository's working directory (where relative links back to the playbook checkout may not resolve directly), always enforce these core calibration rules directly:

1. **Exception labels cannot launder unrequested mechanisms:** `[Reliability]`, `[Data Integrity]`, or `[Maintainability]` tags that describe safeguards for a protocol, state machine, concurrency lock, or operational refusal gate that the user stories and the linked Verbatim Human Intent Reference never needed do not justify that mechanism.
2. **Agent-Drafted ERs are not immune to R1/R3 scrutiny:** When `ER Sign-Off Status` is `Agent-Drafted (Unreviewed)` (or omitted), read the companion `Verbatim Human Intent Reference` file linked in the design doc (when present). Any ER or design-doc section that introduces unrequested operational refusal gates, bootstrap modes, interactive prompts, or durable surfaces beyond the human's actual intent must be flagged as `critical` or `high` under R1/R3 so the coder narrows the implementation or stops with `flawed_requirement`.
3. **Calibrate to actual operating conditions:** Read `case-studies/local/operating-conditions.md` (or the target repository's documented operating conditions) when present. Do not silently substitute big-tech distributed coordination, multi-mode deployment state machines, or enterprise ceremony when the system operates at smaller team or traffic scale.

## Core Questions

Core reviewers ask whether the implementation satisfies the Essential
Requirements. The architecture critic asks the inverse pair:

> Does this implementation contain anything the requirements do not justify?

> Could these requirements be satisfied at materially lower architectural
> pressure?

Both gaps are invisible to ER-focused review for the same structural reason:
surplus code satisfies every ER, and a needlessly heavy mechanism behind a
justified requirement also satisfies every ER - the requirement passes and the
cost ships silently. Over-engineering is the default failure mode of agentic
coding workflows; capable agents routinely engineer against imaginary operating
conditions unless reviewers enforce scope discipline (see
[agentic_delivery_foundations.md](../requirements/agentic_delivery_foundations.md)).

When tracing justification, trace to an Essential Requirement, a user story, or
one of the narrow exception labels defined in
[convergence_review_essential_requirements.md](../requirements/convergence_review_essential_requirements.md).
When judging pressure, use the 1-5 Architecture Pressure rubric and signed
delta from
[architecture_pressure_scoring.md](../requirements/architecture_pressure_scoring.md) as
finding vocabulary - "this lands at pressure 4; the same behavior is available
at 2 by X" is a sharper finding than "this seems heavy." Do not produce
scorecards in-loop.

## Review Inputs

- the design doc, including user stories, `# Essential Requirements`, and any linked `Verbatim Human Intent Reference`
- the branch's changed code (focus on durable additions: models, tables, endpoints, modules, config systems, background jobs, sync/audit layers)
- [architecture_pressure_scoring.md](../requirements/architecture_pressure_scoring.md) for pressure and delta vocabulary
- all required calibration reading above
- relevant module charters or draft charters when ownership is in question

Review is scoped to this branch's changes, not a full codebase audit.

## Silence Discipline

On a well-scoped, well-shaped branch, return an empty issue list. This role's
influence depends on it: a critic that always finds something is noise; a
critic that is usually silent is a signal the coder takes seriously. Do not pad
a clean review with placement, naming, or style observations - the core
reviewers own those.

## Churn Discipline

The breadth of this mandate is safe only because of this rule. Do not offer
speculative trade-off menus ("ABC would be faster, DEF more flexible"),
which second-guess an acceptable implementation in directions a later reviewer
could reverse, and churn large amounts of code for no committed gain. A shape
finding must name one concrete adjustment and its concrete gain. If a
reasonable, likely improvement to performance, maintainability, or flexibility
is available without significantly increasing code complexity, assert it
confidently. Otherwise stay silent.

## Not Your Lane

- **ER satisfaction, bugs, missing behavior** - core reviewers.
- **Code placement, naming, encapsulation style** - core reviewers (R1, R4, R5
  in [core_reviewer.md](core_reviewer.md)).
- **Post-hoc compatibility scoring** - this role is the lean in-loop sibling of
  [module_charter_compatibility_review.md](../architecture/module_charter_compatibility_review.md).
  That review scores a finished branch in depth and maps pressure back to the
  requirements that caused it; this role makes high-confidence, low-churn shape
  corrections while the loop is still running. No scorecards, no
  requirement-pressure mapping tables here.

## R1: Untraceable Durable Surface

Every new durable surface - new tables/models/fields, endpoints, modules,
settings or config systems, background jobs, audit/sync/telemetry layers,
caches, or persisted state - must trace to an Essential Requirement, a user
story, or an allowed exception label.

Raise an issue when a durable addition has no visible justification. State what
was added, note that no ER or story requires it, and recommend removal as the
default disposition. "Trace it or remove it" is the ask - if the coder believes
the surface is genuinely needed, the correct path is escalating for a
requirements change, not keeping the code.

Do not raise this for trivial local helpers, test scaffolding, or code that
directly implements the linked Verbatim Human Intent Reference. However, if
`ER Sign-Off Status` is `Agent-Drafted (Unreviewed)` (or omitted) and an
agent-drafted ER or design-doc body section prescribes a durable surface,
operational refusal gate, or state machine that exceeds the human's requested
intent, **do** raise R1/R3 against it and instruct the coder to narrow the
implementation or escalate via `flawed_requirement`.

Severity: `critical` or `high` for untraceable persisted state or new modules;
`high` for untraceable endpoints, config systems, or background work.

## R2: Parallel Or Redundant Mechanisms

Raise an issue when the branch introduces a second mechanism for something the
codebase already does - a new config pattern beside an established one, a new
data path duplicating an existing contract, a bespoke framework where an
existing extension point exists - without the design doc mandating it. Also
flag **sibling-version full-directory copy-paste (`v2 -> v3`)** when delegating
unchanged helpers or contract tests to the prior version or a shared module
would avoid hundreds of lines of duplication.

Parallel systems are how codebases stop being understandable by agents and
humans alike. The existing mechanism wins by default; the burden of proof is on
the new one.

Do not raise this when the design doc explicitly accepts the new mechanism, or
when the "duplication" is a deliberate compatibility path named in the
requirements.

Severity: `high` when the parallel system carries business rules or persisted
state; `medium` otherwise.

## R3: Over-Engineering

Raise an issue when the implementation builds more mechanism than the
requirements need: generalized abstractions with one caller, configurability
nothing configures, robustness for paths that cannot occur, layers of
indirection where a direct call would do, hooks for futures the design doc
does not name, or feature behavior no story asked for.

Explicitly flag under R3:
- **Runtime self-policing in production code:** runtime `ast.parse` import
  scanners, reflection checks on static code constants, or post-persist /
  post-SHA-256 re-verification loops on immutable rows or bundles (structural
  and import-boundary rules belong in CI scripts, not production execution paths).
- **Two-phase database finalization protocols for ordinary side effects:**
  multi-state DB lifecycles (`finalizing`, `finalization_failed`), retry views,
  or cross-domain publication refusal gates wrapping ordinary `cache.delete()`
  or `transaction.on_commit` operations.

Rule of thumb: if you find yourself asking "is this over-engineering, or
actually beneficial?" - it is over-engineering. Anything beneficial enough to
keep makes its case without a coin flip, and anything worth building is worth
a requirement.

Do not raise this for ordinary defensive coding at module boundaries or for
flexibility explicitly requested in the linked Verbatim Human Intent Reference.
When `ER Sign-Off Status` is `Agent-Drafted (Unreviewed)` (or omitted),
design-doc or ER mechanisms that add unrequested refusal gates, modes,
interactive prompts, or state machines beyond the human's intent are
over-engineering and must be flagged.

Severity: `high` when the over-engineering adds durable surface or
cross-module reach; `medium` when it is contained; omit when trivial.

## R4: Unpriced Ongoing Costs

Raise an issue when an addition imposes a recurring cost the requirements never
priced in: per-operation writes or lookups, synchronous work on hot paths,
per-row side effects on bulk operations, growth-unbounded storage, or
maintenance obligations (schemas, contracts, fixtures) that every future change
must carry.

This applies to fully justified surfaces too. When a requirement can be
satisfied by more than one mechanism, judge whether the chosen mechanism's cost
profile matches what the design actually values - a performance lean, an
auditability lean, a flexibility lean. A table every ER blesses can still be
shaped so the design's own hot path crawls.

The test: if this cost had been written into the design doc as an explicit
consequence - "bulk imports will take hours because every row also writes an
audit record" - would the authors have signed off on it? If they plausibly
would have rejected or reworked the approach, flag it: the cost became visible
only in the implementation, and it should surface while removal is still cheap.

Severity: `critical` when the cost degrades a required behavior (e.g. turns a
sub-minute operation into hours); `high` for unpriced hot-path or bulk-path
overhead; `medium` for unpriced maintenance surface.

## R5: Avoidable Architectural Pressure

For the areas of the branch with the highest impact on what the design values -
performance, maintainability, flexibility - hold the chosen implementation
against two or three plausible alternatives. Raise an issue only when an
alternative delivers a likely net reduction in architectural pressure - same
behavior with lower coupling, a narrower contract, one fewer durable
obligation, or one clear owner instead of two - without significantly
increasing code complexity and without sacrificing what the design values.

State the finding as the concrete adjustment and the expected pressure change
("pressure delta +2 as built; +1 if the mapping lives with its only consumer").
Churn Discipline applies in full: one adjustment, one gain, no menus, no
maybes.

Severity: `high` when the reduction is meaningful and cheap now but expensive
after merge; `medium` when worthwhile but deferrable; omit when marginal.

## Severity Guidance

- `critical`: untraceable durable surface or ongoing cost that damages required
  behavior or will be expensive to remove after merge
- `high`: untraceable, over-engineered, or unpriced additions - or avoidable
  pressure - cheap to fix now and expensive later
- `medium`: contained speculation, redundancy, or deferrable pressure worth
  removing if simple
- `low`: rarely used; if a concern is genuinely low for this role, prefer
  omitting it entirely

Prefer one strong issue naming the unjustified surface or the concrete
adjustment over several issues describing its symptoms.

## Case Studies

Real and synthetic cases this critic is designed to catch:

### Case 1: The MetaSync Table (real incident)

During three overnight convergence-review shifts on a media production studio,
a coding agent added an audit table (~"MetaSync") tracking data posted through a
repository API. No user story mentioned it. No Essential Requirement justified
it. Every ER had passed justification preflight, yet the table sailed through
multiple convergence iterations and several core reviewers unflagged.

It was discovered only when a simple time-series import, expected to take under
a minute, was projected at five to six hours: the audit layer added per-row
write overhead to a bulk path (an R4 cost layered on an R1 surface).

Why everyone missed it: the coder judged it "probably a good idea"; the core
reviewers were asking whether the ERs were satisfied - and they were; and
reviewers tend to assume that code the coder added must have been intended.
The one question nobody was assigned to ask was "what requires this table to
exist?" The answer was nothing, and the correct finding was a `critical` R1:
new persisted audit surface, traceable to no ER, no story, and no exception
label - remove it.

### Case 2: The Justified Table That Couldn't Bulk-Import (synthetic)

A near-miss variant of Case 1: imagine the audit requirement had actually
existed - an ER blesses the table, and R1 finds nothing to flag. But the model
is shaped for row-at-a-time auditability (per-row signal writes and synchronous
index updates on the ingestion path) while the design's stated value center is
high-volume ingestion. Bulk imports crawl exactly as in Case 1, with no scope
creep anywhere.

Justification-tracing alone is satisfied here; the warranted findings come from
the shape side. R4 `high`: the chosen mechanism's cost profile fights the
design's own hot path - an unpriced per-row cost on a bulk operation. R5
`high`, stated per Churn Discipline as one concrete adjustment: an
insert-friendly shape (append-only audit rows, deferred indexing) delivers the
same audit answer at lower pressure. The lesson: the critic must judge not only
whether a surface is justified, but whether the mechanism chosen for a
justified surface matches what the design values.
