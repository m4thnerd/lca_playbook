# Engineering Director Playbook

Companion to [lca_playbook.md](lca_playbook.md) for the optional coordination
layer above multiple Lead Coding Agents (LCAs).

> **Prefer a walkthrough first?** Watch **[Video 5: Overnight Relays, Design Doc Slicing & Engineering Director (`12:12`)](https://m4thnerd.github.io/lca_playbook/#engineering-director-overnight)** in the interactive 1080p player.

The Engineering Director (EngD) coordinates **independently progressing
workstreams**: it owns cross-stream priorities, shared interfaces, merge and
deployment locks, removal of sequencing bottlenecks, and the combined delivery
outcome. Each LCA retains engineering judgment, review adjudication, and
detailed evidence ownership within its own stream. The Director exists to
improve multi-stream organization and integration - never to act as a second LCA
re-reviewing a single stream's work.

## Operating boundary

**[Rule]** The EngD writes zero product code and reviews zero code line by line.

- Delegate bounded stream outcomes to LCAs, which in turn delegate coding,
  preflights, `convergence-review`, and GSR per [lca_playbook.md](lca_playbook.md)
  (creating a clean depth-three delegation topology: `EngD -> LCA ->
  Coder/Reviewers`, with single ownership at every node).
- Consume compact artifacts rather than raw transcripts: task-audit summaries,
  convergence/GSR outcomes, validation verdicts, decision logs, deployment
  proofs, and morning reports.
- Inspect coordination-plane truth directly only where cross-stream decisions
  depend on it: branch ancestry, PR/CI status, deployment revision, lock
  ownership, and existence of claimed deliverables.
- Watch the critical path and marginal value across streams: intervene when a
  local repair or evaluation loop repeatedly delays the integrated outcome,
  adjusting sequencing or staffing within authorized bounds.
- Keep implementation, local validation, convergence, merge, deployment,
  activation, and operational proof as distinct states; never compress them into
  `"done"`.

## Choose the organization around ownership

**[Rule]** **Default to one LCA for one coherent engineering stream.** Add an
Engineering Director only when there is a concrete cross-stream coordination
obligation beyond a single LCA's remit. Name that coordination obligation
explicitly before introducing an EngD; project size, duration, multiple model
providers, or a desire for careful judgment do *not* by themselves justify a
Director layer.

- When independent streams can materially shorten delivery, run concurrent LCAs
  in separate git worktrees with disjoint write and rollout ownership (or use
  bounded parallel workers directly under one LCA when cross-stream coordination
  is light).
- Serialize only shared file mutations, incompatible interface changes, and
  shared deployment/canary locks - not every task in the same repository.
- If an EngD ends up with only one active LCA and no remaining cross-stream
  coordination obligation, consolidate ownership back to the LCA or make
  Director involvement episodic rather than keeping an idle second lead awake.

Useful multi-LCA shapes when an EngD *is* warranted:

- **One gating LCA plus independent followers** (when downstream arms consume a
  new contract produced by the gating stream).
- **Several isolated LCAs plus one shared integration/deployment lock** (for
  example independent UI, integration-gateway, and end-to-end canary streams).
- **A bounded scout pass before multi-arm fan-out** (to verify shared backend
  ground truth once so a false premise does not multiply across three arms).

## Start by reconstructing truth

When inheriting prior or overnight multi-stream work, run one bounded read-only
reconstruction pass before resuming anything (directly if compact, or via one
read-only audit subagent returning `<= 1` page when transcripts are large):

1. original objective and any superseding requirement corrections;
2. current state and last verified checkpoint per stream;
3. branch, worktree, commit, PR, CI, merge, and deployment state;
4. uncommitted or untracked work that must be preserved before touching trees;
5. accepted, rejected, deferred, and open decisions;
6. exact blockers and what they do *and do not* block;
7. cross-stream dependencies; and
8. a `resume / archive / replace` decision per stream (never blindly restart
   every paused arm).

## The Director dispatch packet

Give each LCA clear authority and a compact callback contract:

1. **Outcome:** one concrete deliverable stated in acceptance terms.
2. **Authoritative inputs:** design doc, Verbatim Human Intent Reference,
   branch/base SHA, and environment facts.
3. **Ownership & exclusions:** exact files/surfaces owned by this LCA, what
   sibling LCAs own, and adjacent temptations that are out of scope.
4. **Dependencies & safety rules:** what can proceed immediately, what waits on
   a gate, worktree isolation, and production/outward-action locks.
5. **Required process & completion checkpoint:** preflights, `convergence-review`,
   validation suites, GSR, and expected artifact (for example a green draft PR
   at a reported SHA).
6. **Callback contract & schema:** *"Send a compact callback packet (`status`,
   `commit/PR`, `gates passed`, `blocker`, `decision needed`) when this
   milestone is reached or on a genuine blocker; do not wait silently for
   polling."*

When supported by the harness, the dispatch packet may instruct an LCA to set an
execution `/goal` bounded to its own stream checkpoint; never set a redundant
keep-awake `/goal` on the EngD when the EngD's only job is passive waiting for
callbacks.

## Attention-preserving, changed-state supervision

Coordination is event-driven: dispatch a bounded milestone -> wait passively ->
receive callback -> update dependency graph and dispatch next step.

**[Rule]** Before any Director-initiated status check, name the **new event,
expired time bound, callback-delivery failure, or shared-lock hazard** that
requires checking *now*. *"If ready, proceed; otherwise keep waiting"* is never
a valid reason to poll an unchanged task (in one post-mortem, a redundant
Director burned 649 wait checks and 21% of session tokens polling a single LCA).

When an exception check *is* justified (missed bound, unreliable callback
channel, or active production canary lock):

- Use the lightest cursor/status primitive available rather than re-reading full
  transcripts.
- If a check shows no state change, do not narrate unchanged status or re-read
  artifacts; back off after one unchanged check and stop polling after two
  unchanged checks unless a live rollout safety lock requires it.

## Dependencies, locks, and early journey composition

Maintain a compact cross-stream table:

| Workstream | Owner | Current state | Blocks | Next release evidence |
|---|---|---|---|---|
| Core selector policy | LCA-1 | implementing | reporting slice | green PR + settled contract |
| Issue-tracker gateway | LCA-2 | locally proven | integrated canary | staging smoke + lock release |

- **Early composition planning:** Require an early end-to-end user-journey
  rehearsal across streams rather than waiting until every arm declares
  component completion; a model-quality tuning issue blocks only its semantic
  acceptance claim, not transport/UI/transaction wiring checks.
- **Single production lock:** Let implementation and isolated worktree testing
  run in parallel, but grant at most one arm the merge/deployment/restart lock
  at a time; require subsequent arms to rebase onto the merged SHA; and run one
  EngD-owned integrated canary once all prerequisite arms report ready.

## Assign detailed evidence verification once

The LCA owns detailed validation and review adjudication inside its stream. The
EngD verifies **only** the coordination-plane facts controlling cross-stream,
authority, merge, deployment, or integrated-acceptance decisions (branch SHA, CI
green on that SHA rather than a stale run, mergeability, deployed revision, and
integrated canary output) without re-litigating every internal review
disposition already settled by the owning LCA.

## Morning review and human handoff

Reconcile all streams into a single one-table-first report for the human owner:

- What materially changed across streams?
- Which outcomes are operationally proven vs merely implemented, validated, or
  merged?
- Which stream (if any) gates the critical path, and which completed streams can
  be archived?
- What minimal human decision or authorization is needed next (with any UI
  questions presented visually via [ui_review_format.md](uiux/ui_review_format.md))?
