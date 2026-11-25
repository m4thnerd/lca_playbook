# Module Charter Annotations

The mechanics of the lane system introduced in [module_charters.md](module_charters.md): how code positions and annotations declare lanes, how hazard tags are defined and applied, and what CI enforces. This spec is cross-repo; each repo instantiates it with its own taxonomy file (see "Repo Instances").

## The Positional Lane Model

Lanes attach to positions and files, never to whole modules and never to individual functions.

| Lane | How it is declared | Default posture |
|---|---|---|
| Fast | The file lives inside a `fast_lane/` directory | Rewrite freely within the valve rules; lighter review bar |
| Full-Spec | The file lives inside a direct child responsibility package under a `full_spec/` directory | Change against the complete charter, public boundary, and protected verification contract |
| Careful | Any file outside `fast_lane/` and `full_spec/`, with no Critical header | Narrow additions at existing seams; check consumers before changing exported behavior |
| Critical | One-line file header docstring | Human-reviewed with extreme care; never treated as Full-Spec |

**Inheritance principle:** a missing annotation means *inherit the surrounding default* - it never means *safe*.

**The lane map is derived, never maintained.** `grep -rn "Charter-lane:"` plus the lists of `fast_lane/` and `full_spec/` directories reconstructs the full picture. Do not create or maintain a central lane-mapping document; it would only drift.

### Critical file header

First line of the module docstring:

```python
"""Charter-lane: Critical - denormalized mastery state with many consumers.

<rest of module docstring>
"""
```

One clause of *why*, not an essay. A file takes the highest severity of its contents by default; finer distinctions belong to hazard tags. The repo taxonomy names the hazards that make a file **presumptively Critical**. The presumption stands - header required - whenever hazards interlock across symbols, untagged code participates in maintaining a tagged invariant, or the file is dense enough that an edit anywhere risks a distant invariant. It may be rebutted only when the hazard is **localized** - the tagged symbol's required action fully contains the risk and the rest of the file is routine - and never silently: the rebutting file carries an explicit Careful header stating why:

```python
"""Charter-lane: Careful - persisted-shape-contract is localized to TAG_TO_FIELD_MAPPING; rest of file is plain constants."""
```

**When in doubt, the presumption wins.** Files containing no presumptive hazard carry no header at all; any file containing one must carry a `Charter-lane:` header of *either* lane - lint-checkable, so a missing header is always an error, never a considered "no". This keeps the lane map grep-derivable (rebuttals are on the record) while the Critical header stays what it is for: a rare, high-signal declaration that a file is among the most complex and essential, not a checksum of its tags.

### Fast lane directories

- **One-way valve (CI-enforced):** nothing outside a `fast_lane/` directory may import from one. Sole exceptions: the parent module's URL registration include and framework registration glue that the framework requires at module root - including, for Django, the root `models.py` re-export that migration registration requires. Fast-lane code may freely consume seams owned elsewhere.
- **Deletion test (membership criterion):** a fast-lane surface's entire footprint outside its own directory is registration glue - the URL include plus, for stateful surfaces, the framework-required model re-export. Deleting the directory (and that glue) removes the surface's UX and nothing else; re-creating it from its charter touches nothing else outside the directory. Code whose removal would break anything beyond its own surface does not belong there.
- A `fast_lane/` directory may exist inside any module, including Critical-heavy ones - an experimental surface in a platform module is exactly what it is for. No module is required to have one, but fast-lane treatment is available only inside one.

### Durable state in fast lanes: the expendability rule

A model may live in a fast-lane package iff its docstring declares the data **expendable**, stating the recovery cost:

```python
class CohortMembership(models.Model):
    """Expendable-data: hard reset acceptable; recovery = re-entering
    ~30 student emails via the roster form, <5 min."""
```

The declaration is the load-bearing artifact - durable consent to data loss, so no future contributor assumes the table is precious. Migrations are best-effort while the declaration stands; a no-migration rebuild is an accepted outcome. A schema-less JSON field with an explicitly evolving inner schema is the recommended shape for this phase.

**Expendable data never implies expendable access control.** The authorization gate over prototype data is a Careful seam from day one - leaked data cannot be recovered by re-entry.

Contributors who are not software engineers work in the stateless fast-lane subset (views, templates, read-only queries); engineers may additionally use expendable-data models.

## Hazard Tags

Hazard tags mark the specific symbols in sensitive code where a local edit can have non-local consequences. Rules:

1. **Only non-derivable knowledge.** A tag must carry what an agent cannot reconstruct from local code in seconds - invariants, ordering rationale, calibration intent, incident history, external contracts. Never grep-derivable facts ("has many consumers").
2. **Every tag defines a required action.** The canonical definition states the concrete protective step to perform when touching tagged code - so a contributor with attention spread across another task follows the action instead of needing expert recall.
3. **Every tag defines when NOT to use it.** Scarcity is the signal; a tag seen everywhere means nothing.
4. **Annotation budget.** Most functions carry no tag. A repo carries dozens of tags, not hundreds.
5. **Tags explain risk; position determines lane.** No tag promotes or demotes a lane.

### Syntax

Terminal docstring section, one tag per line - canonical kebab-case name, colon, optional one-line local specifics:

```python
def update_data(self, updated_progress):
    """Persist the full _progress payload and refresh its cache copy.

    Hazard-tags:
        sole-write-path: all _progress writes must route through here.
        cache-commit-coupling: cache set deferred to transaction commit.
    """
```

Canonical meanings live once in the repo's taxonomy file; the tag name alone transmits the full contract. Greppable both ways: `grep -rn "Hazard-tags:"` inventories annotated surfaces; `grep -rn "<tag-name>"` finds one tag everywhere. For models, tags go on the class docstring with the affected fields named in the local note.

## Graduation: Triggers Fire a Review, Not a Move

Fast-lane code comes up for graduation review when any of:

- (a) code outside the fast lane imports it in production - CI-detected via the valve;
- (b) a fast-lane model's data stops being expendable;
- (c) the surface becomes an externally consumed contract;
- (d) it acquires a compliance-sensitive datum.

Review outcomes: promote the code out of `fast_lane/`, extract the needed behavior into a deliberate seam owned elsewhere, or decline and remove the dependency. Second use *within* the fast lane is not a trigger.

## Enforcement

Land with the first `fast_lane/` directory, before any wider annotation effort:

- Import-linter (or equivalent) rule for the one-way valve.
- Lint accepting only recognized tag names from the repo taxonomy file.
- Where the repo taxonomy defines presumptive-Critical hazards, a check that every
  file containing one carries a `Charter-lane:` header of either lane.
- Where a repo's taxonomy defines write-exclusivity tags (e.g. `sole-write-path`), an optional check that the guarded state is not written elsewhere.

## Repo Instances

Each adopting repo carries a **self-contained** taxonomy file (e.g. `docs/charters/hazard_tags.md`) that copies the general tags it uses verbatim, adds repo-specific tags, and includes the repo's framework-specific fast-lane mechanics. Self-containment is mandatory: an agent working in the repo must resolve any tag in one file-read, without leaving the repo. The file opens with a one-line conformance pointer naming this spec and a date. That line - not sync automation - is the sync mechanism.

## Starter Tag Set

General tags most codebases can adopt directly; repos copy what applies, adapt definitions with local examples, and add their own.

| Tag | Carries | Required action |
|---|---|---|
| `order-dependent` | Pipeline/step order is load-bearing; reordering silently corrupts persisted state | Read the whole pipeline and its ordering rationale before touching any step; place new steps relative to the documented order; never reorder, parallelize, or partial-run |
| `at-most-once` | Idempotency/claim mechanics against double business effects; which failures keep vs release the claim is policy | Identify the marker and its transaction boundary; determine keep-vs-release semantics before changing any retry or error path |
| `trust-boundary` | Enforces authn/authz, tenant isolation, or signature verification | Inspect and run the authorization/isolation tests; treat any widening of access as a security decision requiring human sign-off |
| `hot-path` | Carries an established latency/query-count envelope | Measure before and after; preserve the envelope or re-measure at production scale |
| `sole-write-path` | Single authorized mutation path for derived/denormalized state | Route every new mutation through this function; never add a parallel write path |
| `denormalized-with-resync` | Incrementally maintained aggregate; drift is silent and permanent | Identify the source of truth and the named from-scratch resync routine; verify resync correctness after changing any write path |
| `persisted-shape-contract` | A shape that is both persisted state and a multi-consumer wire contract | Sweep consumers for compatibility; plan a backfill for stored rows when adding or renaming keys; never change value scales |
| `calibrated-values` | Constants/formulas are product-calibrated, not derived - do not fix what looks like sloppy math | No change without human product sign-off plus a plan for already-persisted downstream values |
| `external-api-contract` | Encodes another company's API behavior, including undocumented quirks | Validate against the provider's actual contract, not just local tests; preserve defensive parsing |
| `pii-egress` | User data/content crosses a boundary (email, chat, LLM provider, logs, public surfaces) | Confirm what is permitted to leave and to whom; apply the documented minimization rules; treat recipient or content changes as privacy decisions |
