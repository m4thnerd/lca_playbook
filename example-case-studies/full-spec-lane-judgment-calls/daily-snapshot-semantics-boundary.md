# Case Study: When a Mechanically Valid Snapshot Semantics Core Did Not Earn Full-Spec Placement

> **Status: required calibration reading; the normative rules live in the
> [Full-Spec Lane guide](../../architecture/module_charters_full_spec_lane.md).**

## Decision In One Sentence

A fully implemented, structurally valid Full-Spec alternative was declined
because it froze a 10-function interface around deterministic fragments while
the consequential daily-snapshot lifecycle, state, hazards, and ownership
remained in a Critical ORM service; the ~900-line net expansion in charters,
protected contracts, and translation adapters did not buy enough replacement
value for the organization.

## Surrounding Critical Hazards & Pre-Implementation Seam Isolation

Daily Course Progress Snapshots preserve one learner's starting and latest
course progress per local study date, sparse Sub-Skill (SK) changes, and
immutable creation-time scoring provenance (after concurrency bloat was stripped
in the
[perfect-concurrency snapshot protocol case](../requirements-risk/perfect-concurrency-snapshot-protocol.md)).

The adjacent `backend/learner_data/models.py` module sits in the **Critical**
lane because it carries interlocking hazards:

- `persisted-shape-contract` (deeply consumed progress tree and durable
  snapshot JSON);
- `sole-write-path` for canonical progress mutation;
- `cache-commit-coupling` between persisted and cached progress;
- `order-dependent` processing;
- `denormalized-with-resync` aggregates; and
- `calibrated-values` used by scoring math.

Before coding, the design fixed a closed 4-seam integration map (bootstrap read,
topic update seam, SK scoring seam, and Topic Detail read projection) and
forbade touching `CourseProgress` or `learner_data/cache.py`. The first
implementation landed cleanly as a **333-line Critical lifecycle service** +
**40-line validator** + PostgreSQL integration tests.

## Why Full-Lifecycle Placement Failed & Testing the Pure-Core Split

Moving the entire service into a Full-Spec package hit static import cycles
through conventional Django models and Scoring dependencies; breaking them
would have required dynamic lookups or dependency-injection adapters built
purely for the lane checker.

To test a narrower hypothesis - keeping a Critical ORM shell while extracting
plain-value snapshot rules into a Full-Spec child package - the team built a
**disposable comparison branch from the exact same baseline** (complete with
Responsibility Charter, manifest, protected entry point, and 431-line contract
suite, passing all structural and PostgreSQL integration checks) and evaluated
it with both the lead agent and a context-light independent reviewer.

## Six Problems Revealed by Comparing Both Real Implementations

1. **The consequential outcome still lived outside the package:** Row selection,
   same-date reuse vs creation, `get_or_create`/save, and the actual
   immutable-start persistence lifecycle stayed in the Critical shell. The child
   package could replace dictionary transformations, not the daily-snapshot
   outcome.
2. **The public boundary protected helper decomposition rather than one
   result:** The entry point froze one dataclass plus 10 low-level functions
   (timezone resolution, validation, creation dicts, copying, normalization,
   merging, metadata, and two projections), turning ordinary internal refactors
   into protected contract changes.
3. **Boundary ceremony:** Two public operations were one-line `deepcopy`
   wrappers, and the shell translated ORM fields into a dataclass and back
   purely so the child looked pure while the shell held the state and risk.
4. **Runtime boundary tax:** Instead of decorating an already-built progress
   tree in place, the pure boundary deep-copied the entire tree on common reads,
   and protected contract tests locked in incidental non-aliasing behavior that
   no user story required.
5. **Assurance surface exceeded replaceable benefit:** Roughly **+900 net lines**
   (+200 prod Python, 158-line charter, 431-line protected contract suite,
   parent charter glue) to make ~227 lines of straightforward deterministic code
   blindly replaceable while the risky ORM lifecycle still required Critical
   review.
6. **The architecture had become its own requirement:** The comparison branch's
   Essential Requirements ended up mandating a Critical ORM shell plus Full-Spec
   child under `Maintainability` and `Performance` tags. Applying the
   mechanism-removal counterfactual exposed the flaw: deleting the Full-Spec
   package, manifest, and protected interface left every learner, research,
   persistence, and seam requirement satisfied by the 333-line service.

## Twelve Lessons For Full-Spec Lane Judgment

1. **Full-Spec is an economic specification-completeness trade, not a badge.**
2. **The boundary must contain the hard part**, not leave lifecycle and hazards
   in an outer shell.
3. **Protect result-oriented outcomes, never a 10-helper decomposition.**
4. **Functional purity is optional evidence, not eligibility**; wrapping ORM
   lifecycle in copy adapters just to look pure is architecture theater.
5. **Mechanical checker validity is necessary, never sufficient.**
6. **Apply the mechanism-removal counterfactual to lane machinery itself.**
7. **Count permanent coordination surfaces** (charters, manifests, protected
   tests, parent/child prose), not only runtime LoC.
8. **A charter cannot launder distributed ownership** when the shell still makes
   the lifecycle decisions.
9. **Critical adjacency does not automatically disqualify Full-Spec**, provided
   the meaningful outcome boundary can actually be contained cleanly.
10. **Use a disposable same-baseline comparison branch** when a boundary
    trade-off feels abstract in prose.
11. **Pair the lead's synthesis with a context-light independent reviewer** once
    both branches exist.
12. **Every lane rejection is local and revisable** if the responsibility later
    grows into an independently consumed outcome.

## Calibration Questions

Before accepting a Full-Spec responsibility, ask:

1. What named user or system outcome becomes cheaply replaceable?
2. Does the package own that outcome's consequential state, lifecycle, side
   effects, and failure semantics, or do adapters retain them?
3. Is the public API result-oriented, or does it freeze current helper
   decomposition?
4. Could a materially different implementation satisfy the protected contract,
   or do contract tests freeze incidental copying, object identity, or internal
   steps?
5. What present or likely future rebuild justifies the protected surface?
6. How many production, charter, manifest, test, and parent-ownership files must
   move during ordinary maintenance?
7. Does the split add runtime copying, translation, or duplicate verification
   that an unsplit implementation avoids?
8. If the lane machinery disappeared, which independently justified user story
   or system constraint could no longer be met?
9. Would a disposable same-baseline comparison branch settle the question faster
   and more honestly than abstract debate?
