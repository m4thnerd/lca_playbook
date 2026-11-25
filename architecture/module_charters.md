# Module Charters

## The Velocity Asymmetry

AI coding agents can read and write code far faster than humans can review it
line by line. If we spend the bulk of human attention on every implementation
line, we waste that leverage. Moving human attention up a level - to intent,
requirements, boundaries, and verification - makes rapid implementation more
useful without pretending that architecture or judgment disappeared.

## The Module Charter

Every meaningful module gets a **Module Charter** - a short, durable file with two named sections, *Essential User Stories* at the top and *Durable Requirements* below. A charter is the first thing a human, AI coder, or AI reviewer reads when working on the module.

The "Durable Requirements" name comes from `convergence-review`, our AI-assisted implementation and review workflow: humans define requirements, an AI coder implements, multiple independent AI reviewers evaluate against those requirements, and the loop iterates until it converges. Each design doc carries a `# Essential Requirements` section - a small, strict list of behaviors any acceptable implementation must satisfy. That section is *transient*: drafted per PR, used, archived after merge. The Module Charter promotes it to durable, and pairs it with durable user stories that name the *why* the requirements exist to serve.

That single shift - from transient ER to durable Charter - is the unlock. Charters land incrementally as modules and cohesive responsibility clusters are next touched. Fast-lane surfaces and Full-Spec responsibility clusters depend especially strongly on precise charter language; for other sensitive code, a charter still aids understanding without requiring a comprehensive retroactive documentation campaign.

## A Concrete Example

Consider a fictional internal content-availability policy implemented across a
large application diff.

For most stakeholders, what matters is three user stories and a short section of internal nuances around initial assessment question selection:

**Durable user stories**

- As a site administrator, I need to adjust which learning activities are
  available to trial users, so I can manage the trial experience without code
  changes.
- As a free trial learner, I want minimal disruption to my learning experience when the amount of free content available is reduced, so I'm not unnecessarily frustrated when content availability shifts.
- As a learner taking an initial assessment, I want a diverse question set so
  that the result reflects my prior knowledge.

For most stakeholders, the concern ends there. The implementation may be much
larger than the charter, but the human review surface that matters most is the
accepted user value, durable behavior, boundaries, and verification - not choosing
among every equally acceptable internal detail.

## Why the Charter Is the Unlock

A Module Charter replaces *"re-derive the spec from the code"* with *"read the spec, then change the code."* That shift makes large refactors cheap and AI-assisted implementation changes tractable. It is the core of **Spec-Driven Development (SDD)**: the accepted specification directs the code instead of being reconstructed from it.

### User stories first

User stories do more than break ties between equivalent implementations. They shape what *better* means at every fork in the work. With user stories at the top of the Charter, every naming decision, every refactoring choice, every shape-of-the-API question gets pulled toward what users actually need - instead of toward whatever local optimum the coder or reviewer happens to notice next.

They also tell `convergence-review` what *doesn't* matter. Anything not named in the user stories or Durable Requirements should generally be treated as out of scope for feature expansion unless it violates engineering, security, performance, or contract baselines. The loop converges faster when reviewers know which directions to stop chasing.

### What the absence costs

- A payment module takes longer to change when every branch must re-derive which
  pricing behaviors are essential versus incidental.
- A messaging module takes longer to simplify when no durable document records
  which behaviors must survive and which implementation choices may be replaced.

A Module Charter gives `convergence-review` (and humans) a stable target to refactor against, instead of forcing the team to reconstruct the spec on every pass.

## Key Mindset Shifts

### #506,151 vs #720,881

There may be 1,000,000+ ways to implement a given feature. For a well-isolated module, **at least 250,000 of them are roughly equally fine** if they satisfy the user stories, meet the durable requirements, pass tests, and remain easy to modify. Spending scarce human attention picking between #506,151 and #720,881 is inefficiency to avoid.

### Requirements are much smaller than the code

The essential requirements of many modules fit in a few user stories plus a few
sections of internal nuance. The production code that satisfies them is often
substantially longer. With the Charter durably capturing the requirements, the
highest-value human review surface is the Charter, the external contracts, and
the high-risk paths - not every line of the implementation.

### The role shift

> Humans define the durable requirements, intent, contracts, risk boundaries, and verification bar - and stay deeply knowledgeable in the most critical areas of the codebase. AI agents do most of the implementation and most of the line-level review.

## Coupling Is The Main Risk Multiplier

The dangerous thing about AI-assisted coding is not volume - it is **coupling**: hidden dependencies, unclear contracts, complexity leaking across module boundaries. The Charter makes coupling visible by forcing every surface to declare what it promises and what it owns. The lane system below makes the most important boundary *enforceable*. Classic encapsulation, made legible - then made checkable.

## Lanes: Different Kinds of Good

Lanes are not a linear scale from safe to dangerous, and product importance alone does not determine a lane. Critical, Full-Spec, and Fast lanes are affirmative architectural designs with different benefits. Careful is the honest default when code has not earned one of those more explicit postures.

- **Critical lanes are good because they make technically hazardous engineering safer to maintain.** They enable complicated, high-performance, or deeply interdependent functionality - denormalized state, cache protocols, trust boundaries, calibrated domain math, and cross-module sequencing - without pretending that those hazards can be designed away. File declarations, sparse hazard tags, and required actions preserve the non-local knowledge that maintainers need. This makes critical code safer to change than the same functionality would be in a traditional uncategorized codebase, while retaining the performance and capability that simpler isolation cannot provide.
- **Full-Spec lanes (formerly called Rebuildable lanes) are good because they capture the complete material specification for broad classes of essential product behavior outside the implementation, making the code safely rebuildable from its spec.** Each cluster is the sole owner of a short, complete Responsibility Charter, exposes a stable public boundary, contains or explicitly contracts for its state and side effects, and has a protected verification system strong enough to evaluate materially different implementations against the same accepted behavior. "Full" means that all identified material behavior, constraints, boundaries, and invariants are specified; it does not mean restating every implementation line or claiming formal verification. This moves humans' and agents' attention from incidental implementation details to plain-English user stories, Durable Requirements, boundaries, and verification - often a 10x-30x smaller attention surface than the code. Full-Spec code may own durable state, framework interactions, and high-consequence behavior; business importance is not itself a Critical-lane hazard.
- **Fast lanes are good because their stronger isolation makes iteration even cheaper.** They retain the SDD benefits of small attention surfaces and implementation freedom, but own isolated, removable surfaces that nothing outside depends on except narrow registration glue. This permits a lighter review bar and rapid evolution where exact implementation or presentation is less durable than the capability - for example, internal instructor or administrator workflows whose required task must remain available while the page's appearance may change frequently. Contributors who are not software engineers can ship real user stories safely. A healthy module can keep a Fast lane forever; Fast-lane code is not failed code waiting to graduate.
- **Careful lanes are the necessary but least leveraged default.** Their responsibilities may be important, but their ownership, consumers, hazards, or replacement boundary have not been isolated enough to justify Critical, Full-Spec, or Fast treatment. Contributors investigate those relationships and make narrow changes at established seams. Careful is not a claim that code is bad or unsafe; it is an explicit statement that the code has neither Critical's mapped hazard protections nor the specification and substitution guarantees of Full-Spec or Fast. It is often a useful holding posture, but usually not the architectural destination to optimize for.

### Two SDD lane styles

Full-Spec and Fast both put accepted specifications ahead of incidental implementation choices, but they earn their postures through different tests:

- **Fast uses the deletion test.** Deleting the surface removes its own UX and nothing more; no production code outside the directory depends on it except permitted registration glue.
- **Full-Spec uses the implementation-substitution test.** Other production code may depend on the responsibility through its declared public boundary, but the internal implementation can be replaced without changing accepted charter language, callers, durable contracts, or externally observable behavior. Compatible data migrations may follow an explicitly accepted plan.

Fast-lane code is surface-removable. Full-Spec code is specification-complete and implementation-substitutable. The detailed eligibility, placement, charter, verification, implementation-change, and review rules are in [module_charters_full_spec_lane.md](module_charters_full_spec_lane.md).

The failure mode is treating everything as one lane: Critical process everywhere kills iteration speed; Fast process everywhere corrupts the core; and declaring code Full-Spec without sufficient ownership and verification merely disguises Careful or Critical risks.

## Lanes Are Positional

Lanes are properties of *where code sits*, not labels on modules. Modules have **shapes** - an admin module might be 80% Fast lane around a small Careful nucleus; a platform module might be mostly Critical files with a Full-Spec responsibility island and an experimental Fast-lane surface.

- **Fast Lane is a directory.** Code is Fast-lane iff it lives inside a `fast_lane/` package. CI enforces the one-way valve: nothing outside a `fast_lane/` directory may import from one. The deletion test defines membership: a Fast-lane surface's entire footprint outside its directory is registration glue (the URL include plus, for stateful surfaces, the framework-required model re-export), so it can be deleted and rebuilt from its charter without touching anything else. Durable state is permitted only under an explicit expendable-data declaration.
- **Full-Spec Lane is a directory near the responsibility's legitimate owner.** Any `full_spec/` directory may contain direct child packages, each of which is the sole owner of one cohesive Responsibility Charter. Production consumers may import only the package's declared public entry point; implementation deep imports are prohibited. Specification completeness, the implementation-substitution test, protected verification contract, hazard compatibility, and durable-state rules define membership. Full-Spec directories may appear at different depths across a codebase rather than being collected into one global dumping ground.
- **Files outside `fast_lane/` and `full_spec/` default to Careful** (e.g. a utilities file with simple dependencies). No marker needed. A missing annotation means *inherit the default*, never *safe*.
- **Critical is declared per file** with a one-line header docstring naming the reason (e.g. a denormalized hot-path with nuanced cache sequencing). A hazard the repo taxonomy names as presumptively Critical requires the header unless the file explicitly rebuts the presumption with a Careful header stating why the hazard is localized (mechanics in [module_charter_annotations.md](module_charter_annotations.md)); per-function nuance is carried by hazard tags.
- **The lane map is derived, never maintained.** Grepping the Critical headers plus listing `fast_lane/` and `full_spec/` directories reconstructs the full picture on demand. The reader who needs a lane label is the person or agent already editing the file - so the label lives exactly where their attention already is.

Existing file-header and Fast-lane mechanics are in [module_charter_annotations.md](module_charter_annotations.md). Full-Spec placement, protection, and enforcement rules are in [module_charters_full_spec_lane.md](module_charters_full_spec_lane.md); adopting repositories implement the applicable checks described there.

## Hazard Tags

Within sensitive code, a small canonical set of **hazard tags** marks the specific functions and models where local edits can have non-local consequences - the sole write path for denormalized state, the cache write that must follow commit, the constant that only looks like sloppy math. A tag carries knowledge an agent cannot reconstruct from the local code, and every tag definition includes a **required action**: the concrete protective step to take when touching tagged code, spelled out so no one has to rely on expert recall mid-task. Most functions carry no tag; that scarcity is what keeps each tag a real signal.

## Change Process

For non-trivial PRs: map each new responsibility to one owning module and define the narrowest integration seam into Careful or Critical code before writing final Essential Requirements, update the affected surface's Charter if the change shifts what it promises, run `convergence-review` against it, and link the evidence in the PR. Changes that add Fast-lane surfaces, introduce or materially change Full-Spec responsibility clusters, touch hazard-tagged code, or cross a lane boundary deserve explicit boundary decisions before coding begins.

## Longer-Term Operating Model

Over time this style of work extends beyond implementation. AI agents can review customer support interactions for likely defects, convert them into structured Jira tickets with reproduction context, draft or update Module Charters, and produce an implementation through `convergence-review`.

In that future, software engineers are more essential, not less - deciding what should be true, where boundaries should exist, what risks matter, and how the system stays coherent as it grows.
