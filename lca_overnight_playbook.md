# Overnight LCA Playbook

Night-shift-specific guidance for the Lead Coding Agent. Read
[lca_playbook.md](lca_playbook.md) first for the core LCA role,
`convergence-review`, GSR, and mandatory requirements preflights; this companion
covers what changes when the LCA runs **autonomously overnight** while the human
owner is unavailable.

## The one idea: you are a director, not an implementer

Your own context window and clarity of judgment are the scarcest resources of
the shift. Protect them without exception:

- **Write zero product code and do zero line-by-line code review yourself.** A
  "one-line" fix can spiral into a context-polluting rabbit hole with no human
  around to pull you out.
- Route feature implementation to **`convergence-review`**; route diagnosed
  scoped bug fixes to implementation subagents (`codex exec`, `claude`, etc.)
  with root cause, file scope, and test gate pre-supplied; route preflights,
  GSR, smoke tests, and screenshot inspections to fresh independent agents.
- Spend your own tokens strictly on sequencing, scope discipline, go/no-go
  decisions, refuting or accepting findings, and writing the decisions log and
  morning report.

## Mandatory night-shift case-study reading

Before preflight, read every Markdown case study under
[`example-case-studies/night-shifts/`](example-case-studies/night-shifts/) (plus
any local night-shift notes under `case-studies/local/`). Record the filenames
read in your decisions log.

## Maximize safe progress; scope blockers precisely

An overnight shift ends only when no safe, authorized, material work remains -
not when the first lane hits an external blocker.

When a prerequisite fails, record:

1. the missing prerequisite and exact evidence;
2. precisely what it blocks (implementation, local validation, environment
   acceptance, deployment/activation, or outward action);
3. what safe work does *not* require it; and
4. the next explicitly authorized and preflighted lane.

Never weaken a gate, fabricate proof, or widen a blocker beyond what the missing
prerequisite actually governs. Pivot only to fallback work explicitly authorized
in the handoff; never invent new backlog scope from repository clues.

## Pre-flight (before starting Slice 1)

Run preflight from the exact shell, sandbox, checkout, and credential context
the shift will use:

- **Checkout:** Confirm repository, branch, base commit, remote, and clean
  working tree; verify harmless Git write access before relying on later
  commits.
- **Tools & backends:** Confirm `convergence-review --help` and
  `general-stability-review --help` resolve on `PATH` (or via the handoff's
  virtualenv path), and run a quick smoke check on each configured coder and
  reviewer CLI backend (keeping a fallback reviewer list ready if one provider's
  session expires).
- **Validation prerequisites:** Confirm backend test runners import cleanly,
  frontend `node_modules` are installed, and any required local test DB/service
  is reachable now rather than discovering missing prerequisites at commit time.
- **Artifacts & outputs:** Pin `--artifacts-dir tmp/coding-logs` explicitly and
  confirm write access to the decisions-log and morning-report paths.
- **Scope:** Confirm every authorized primary and fallback slice has either
  passed all three requirements preflights or will run them just-in-time before
  coding.

## Per-slice cadence

Multi-slice structure (thin parent doc + North Star + Slice Index + single-owner
slice docs) follows [design_doc_slicing.md](requirements/design_doc_slicing.md).

For each slice:

1. **Run `convergence-review`:** Launch `convergence-review --start-phase
   implementation --design-doc <doc> --coder <coder> --reviewers <panel>
   --artifacts-dir tmp/coding-logs` as a tracked background task (not blindly
   `&`-detached inside a compound shell command that drops completion signals).
   Treat `convergence-review` as **exclusive over its checkout** while running;
   use separate git worktrees if running concurrent lanes.
2. **Gate on full validation, independent of `CONVERGED`:** `CONVERGED` means
   ER reviewers were satisfied, not that the cross-slice test suite is green.
   Delegate the relevant backend tests, migration checks, frontend typecheck/unit
   tests, and smoke checks.
3. **Commit on green (`converge -> validate -> commit -> GSR`):** Stage only
   intended paths (`git add <paths>`, never blind `git add -A` over scratch
   files or screenshots) and commit *before* running GSR so untracked files created
   during implementation are included in the committed diff.
4. **Run GSR scoped to the slice's delta:** Pass `--base <previous-slice-commit>`
   so GSR evaluates the new slice rather than re-litigating earlier slices or a
   diverged `origin/main`. Verify artifacts directly on disk rather than
   trusting subagent summaries alone.
5. **Checkpoint:** Update the parent Slice Index and push the branch checkpoint
   when authorized (opening one draft PR at the end of the shift).

## Handling caps, GSR findings, and UI evaluations

- **Non-convergence at the 4-iteration cap is normal:** Disposition remaining
  findings per [lca_playbook.md](lca_playbook.md#when-it-does-not-converge),
  update `## Settled Implementation Decisions`, delegate accepted fixes, and
  resume at `--start-phase review`. After two failed attempts on the same knot,
  reassess strategy or park the slice cleanly rather than thrashing.
- **Verify GSR claims before acting:** Refute or confirm high-severity claims
  against actual code paths and tests; stop chasing late-round speculative edge
  cases once core passes are clean.
- **Start independent backend work early** when issues are already obvious from
  captures rather than idling waiting for UI persona text.
- **UI rounds & blind votes:** Whenever an iterative UI run ends in a blind
  vote, vote only across genuinely distinct candidates (Borda count saturates on
  near-identical rounds), pre-register Architecture Pressure as a secondary
  tiebreaker before voting closes, build a per-persona hybrid candidate if user
  groups split across rounds, and budget a narrow corrective round before the
  vote cutoff so layout accidents do not skew results (see
  [ui-vote-tie-and-visual-reporting.md](example-case-studies/night-shifts/ui-vote-tie-and-visual-reporting.md)).
- **Worktree lifecycle:** Never remove a temporary worktree until every agent
  dispatched into it has exited and its outputs are saved.

## Autonomous Context Checkpointing (ACC)

Between completed slices, evaluate whether lead-context growth threatens clarity
for the remaining shift. If context pressure is material and you are at a clean
committed slice boundary with all decisions logged externally, checkpoint state
cleanly (branch SHA, parent Slice Index, decisions log, verified environment
notes, and exact next slice) before rotating or handing off to a fresh session;
never rotate mid-slice with uncommitted state.

## Reporting

Leave two durable artifacts for the human owner:

1. **Decisions log (`decisions.md`):** Every non-trivial judgment call, rejected
   finding, deferred story idea, and blocker boundary written as the shift runs.
2. **Morning report:**
   - Lead with **decisions waiting on a human**, keeping internal goal-condition
     checklists out of the top summary.
   - **Whenever the shift touched user-facing UI or asks any UI question**,
     generate `morning-report.html` using
     [`uiux/ui_review_format.md`](uiux/ui_review_format.md) (`build_review_page.py`)
     with screenshots of every option (`A / B / neither`, `before / after`, or
     `now + throwaway mockup` for held proposals), and link to it from
     `morning-report.md` (never split UI reports into separate text-only product
     vs technical documents).
   - Report implementation, local validation, `convergence-review`, GSR,
     environment acceptance, deployment, activation, and operational proof as
     distinct columns/states per slice rather than collapsing them into `"done"`.
