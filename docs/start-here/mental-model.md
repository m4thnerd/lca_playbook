# Mental Model

The LCA Playbook organizes agent-led software engineering around three verbs:
**Bound**, **Converge**, and **Stabilize**.

## 1. Bound

High-speed code generation is safe only when the codebase makes the lasting cost
of change legible:

- **[Module Charters](../../architecture/module_charters.md)** record the durable
  intent and ownership boundaries that source code alone cannot explain cheaply.
- **Four positional lanes** (**Critical**, **Careful**,
  **[Full-Spec](../../architecture/module_charters_full_spec_lane.md)**, and
  **Fast**) match review and specification rigor to actual blast radius.
- **[Hazard annotations](../../architecture/module_charter_annotations.md)**
  attach non-local invariants directly to the code lines where an agent would
  otherwise trip.
- **[Architecture Pressure Scoring](../../requirements/architecture_pressure_scoring.md)**
  prices steady-state maintenance burden *before* coding so teams see early
  whether an idea genuinely warrants Pressure 4-5 system-owner buy-in or whether
  a Pressure-2 design delivers nearly the same value with far less permanent
  surface.

*Critical* does not mean important to the business; *Fast* powers rapid-iteration
internal tools and isolated surfaces (including prototype database tables marked
`Expendable-data`); *Full-Spec* (formerly *Rebuildable*) means every material
behavioral requirement is captured in a concise Responsibility Charter and
protected contract suite so both humans and AI agents can evolve and refactor
internals cleanly without tiptoeing around historical accidents.

## 2. Converge

The Lead Coding Agent's context window is a leadership resource, not a scratchpad
for raw diffs and test logs. The LCA writes zero product code:

- Three fast [requirements preflights](../../lca_playbook.md#mandatory-requirements-preflights)
  clean up user stories and `# Essential Requirements` while edits cost seconds.
- [`convergence-review`](../../tools/convergence-review/README.md) encapsulates
  the iterative coder + multi-model reviewer (`core` + `architecture` critic)
  loop and returns consolidated findings to the LCA.
- Between runs, the LCA exercises product and architectural judgment, promoting
  durable boundary calls into `## Settled Implementation Decisions` rather than
  treating every reviewer suggestion as law.

## 3. Stabilize

Passing `# Essential Requirements` proves the slice built what was asked; it
does not prove absence of ordinary regressions, missing payload fields, or
deployment traps:

- **[General Stability Review (GSR)](../../reviews/general_stability_review_playbook.md)**
  and **[Staff Engineer Review](../../reviewers/staff_engineer_reviewer.md)**
  sample the frozen candidate from independent model perspectives.
- A clean pass is one probabilistic sample, not mathematical proof; accepting a
  code fix creates a new candidate and restarts the clean-pass count, while
  late-round speculative edge cases are declined so review never becomes an
  unbounded requirements generator.
- Code surviving preflights, convergence, smoke tests, and GSR often needs only
  light human diff review on routine bounded slices, while deep architectural
  changes or major new machinery warrant human inspection of the deepest
  load-bearing files in a Draft PR.

## Keep Organizational Depth Minimal

**One LCA leading one coherent engineering stream is the default.** Introduce an
[Engineering Director](../../engineering_director_playbook.md) or multiple
worktree-isolated LCAs only when independently progressing streams have a
genuine cross-stream interface or deployment-lock obligation. More agent layers
without separate ownership only add polling noise.
