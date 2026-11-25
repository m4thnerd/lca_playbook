# Example Case Studies & Calibration Library

These case studies are de-identified from real production engineering runs,
preserving their real technical failure mechanics, verbatim before/after
Essential Requirements diffs, quantitative telemetry, and calibration questions
while omitting company, partner, personal, and product-identifying symbols.

Requirements risk and review-driven overbuilding are the most consistent failure
modes in high-autonomy agentic engineering. Treat these files as active
calibration lenses before drafting `# Essential Requirements`, running
preflights, or accepting late-round review machinery.

For your own organization's staffing, traffic, and project-specific incidents,
add private Markdown files under [`../case-studies/local/`](../case-studies/local/README.md).

## Categories

### 1. Operating Conditions (`operating-conditions/`)

- [Lean SaaS Team Operating Conditions](operating-conditions/lean-saas-team.md):
  example organization profile demonstrating how staffing and actual operator
  concurrency prevent reviewers from demanding hyperscale distributed machinery
  for sparse human-paced workflows.

### 2. Requirements Risk & Review-Driven Bloat (`requirements-risk/`)

Active calibration set read by
[ER Justification Preflight](../requirements/convergence_review_preflight_requirements_justification.md):

- [Exception Labels and an Unsupported Completion-ID Protocol](requirements-risk/unsupported-completion-id-protocol.md):
  how locally truthful `[Data Integrity, Maintainability, Reliability]` tags
  laundered an unrequested cross-layer completion-ID and uniqueness-winner
  protocol when extending an existing event field sufficed.
- [Exception Labels and a Perfect-Concurrency Snapshot Protocol](requirements-risk/perfect-concurrency-snapshot-protocol.md):
  how demanding exact concurrent-first-observation ordering spawned row locks,
  deadlock hazards, and cross-request state corruption on a lean learner
  progress sidecar.
- [When Review Findings Became Requirements](requirements-risk/review-findings-became-requirements.md):
  how 12 `convergence-review` runs and 15 GSR passes turned a bounded
  publication contract into 5,561 added lines by treating every plausible
  edge-case finding as a mandate for permanent recovery machinery.
- [When Agent-Authored Essential Requirements Laundered Unrequested Operational Gates](requirements-risk/agent-authored-ers-and-operational-gates.md):
  how unreviewed agent-drafted ERs turned a 2-part deploy guardrail request into
  `INIT_HOST_MODE`, interactive prompts, and stopped-container refusal gates
  that caused three production deploy incidents in five days.
- [Autonomous Preflight Self-Inflation, Runtime Self-Policing, and Follow-Up Snowballs](requirements-risk/preflight-self-inflation-and-follow-up-snowballs.md):
  findings from a 112-PR production audit covering autonomous preflight story
  invention, runtime `ast.parse` import police, 2-phase DB state machines for
  `cache.delete()`, and building explicitly deferred subsystems.

### 3. Essential Requirements Language Clarity (`requirements-language-clarity/`)

Real before/after ER rewrites showing how to satisfy both machine preflights and
clean, noise-free human specification review:

- [Essential Requirements That Passed Preflight but Could Not Be Approved](requirements-language-clarity/dense-ers-after-preflight-rounds.md)
  (601-word jargony preflight survivor -> 240-word human-approved scope anchor).
- [Target Schedule ERs, Touch-Point Inventories, and Transient Names](requirements-language-clarity/target-schedule-ers-inventories-and-transient-names.md)
  (why `"removed in full"` beats stale caller inventories and why removal ERs
  must state the end state).
- [Leaderboard ERs, and How a Shorter Paraphrase Can Invent a Feature](requirements-language-clarity/leaderboard-ers-paraphrase-can-invent.md)
  (how paraphrasing `"leaderboards-enabled gate"` as `"opt-in"` could invite an
  unrequested per-user opt-in feature).
- [When Precise Essential Requirements Become Hard To Understand](requirements-language-clarity/topic-progress-essential-requirements-before-after.md)
  (separating durable scope anchors from detailed formulas, rollout flags, and
  temporary verification checkpoints).

### 4. Full-Spec Lane Judgment Calls (`full-spec-lane-judgment-calls/`)

- [Full-Spec Lane Judgment Calls Index](full-spec-lane-judgment-calls/README.md)
- [When a Mechanically Valid Snapshot Semantics Core Did Not Earn Full-Spec Placement](full-spec-lane-judgment-calls/daily-snapshot-semantics-boundary.md):
  using a disposable comparison branch and independent review to test whether a
  pure core meaningfully owns an outcome or merely freezes helper decomposition.

### 5. Agentic Simplification (`agentic-simplification/`)

- [Agentic Simplification Index](agentic-simplification/README.md): calibration
  template for stories whose Architecture Pressure drops sharply when delivered
  agentically or as a thin hybrid (see worked examples in
  [agentic_delivery_foundations.md](../requirements/agentic_delivery_foundations.md)).

### 6. Autonomous Night Shifts (`night-shifts/`)

- [Night-Shift Case Studies Index](night-shifts/README.md)
  - [A blocked gate is not a stop-work gate](night-shifts/blocked-gate-is-not-stop-work.md)
  - [Continuation requires a controller](night-shifts/continuation-requires-a-controller.md)
  - [Context is evidence, not scope](night-shifts/context-is-evidence-not-scope.md)
  - [Exact-context preflight and explicit continuation](night-shifts/exact-context-preflight-and-continuation.md)
  - [A Four-Way Vote Tie and a Report That Asked UI Questions Without Pictures](night-shifts/ui-vote-tie-and-visual-reporting.md)
