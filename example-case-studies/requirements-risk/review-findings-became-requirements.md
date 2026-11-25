# Case Study: When Review Findings Became Requirements

> **Status: required calibration reading; apply with the
> [GSR playbook](../../reviews/general_stability_review_playbook.md) and your
> project's operating conditions (see example
> [lean-saas-team.md](../operating-conditions/lean-saas-team.md)).**

## Context

In an Authoring-Studio-to-Platform exact catalog-item-publish implementation,
the authoring studio needed to send one bounded, frozen contract to the learning
platform after an explicit instructor action. The approved design already
specified the important safeguards:

- immutable request-key/body identity;
- exact acknowledgement checks;
- distinct confirmed, conflict, uncertain, and blocked outcomes;
- atomic local finalization after platform success;
- minimal sensitive retention;
- CSV export fallback; and
- no generic integration framework, deployment changes, AI orchestration, or
  caller-selected destination.

The implementation session began from a recommended handoff. Although the
session read earlier mechanism-bloat case studies and the GSR playbook at
startup, it did not read the operating-conditions file and failed to reactivate
requirements-risk scrutiny when review loops hit iteration caps or restarted
churn.

## What Happened

The initial implementation was followed by **12 `convergence-review` runs and 15
GSR passes**. Each capped `convergence-review` run was treated mainly as a queue
of defects to fix and re-review rather than as a signal to ask whether subtle ER
language or review-driven scope expansion was causing churn.

GSR then behaved exactly as its probabilistic sampling model predicts:

- passes 1 and 2 found plausible ordinary defects;
- **passes 3 and 4 were clean** on the corrected candidate;
- later independent samples found different edge cases;
- accepted fixes changed the candidate and reset the clean-pass target; and
- the cycle repeated until pass 15.

**Crucial nuance:** Many findings were *legitimate within the implementation
that existed at the time*. The failure was treating technical validity inside
growing machinery as sufficient authorization for permanent machinery. The LCA
repeatedly described each correction as narrow while the aggregate state
machine, recovery policy, and test matrix kept expanding.

## Cost Signal

The final read-only audit measured:

- **5,561 added lines** in the feature diff (`2,282` production/config/UI lines
  + `3,277` test lines);
- a **1,637-line backend publication service** with **186 decision points**;
- **79 focused backend tests** plus frontend state tests; and
- an estimated **2,000-2,650 removable lines (36-48% of the diff)**, leaving an
  estimated 5-8 hours of simplification and revalidation work.

The 12 `convergence-review` processes consumed ~3.5 hours of machine runtime and
the 15 GSR passes consumed ~1.9 hours across a nearly seven-hour wall-clock
session before the human owner intervened.

Root-task telemetry recorded **~82.2 million cumulative model-context tokens**
(including ~81.9 million cached input tokens). That figure represents repeated
context traffic across reloads - **not** 82.2 million unique tokens or a direct
API billing figure - yet it is an unmistakable efficiency alarm: the LCA
repeatedly reloaded and re-adjudicated a ballooning implementation instead of
stopping to simplify the governing policy.

## How Bloat Entered & The Clean-Pass Trap

Successive findings expanded a one-caller, one-destination publication operation
into generalized recovery policy: post-confirmation re-publication,
historical-state restoration via `prior_state`, endpoint-change recovery,
retries after definitive non-committing failures, multiple overlapping attempt
and payload digests, a signed browser-confirmation protocol, a custom
worker-thread/queue/wall-clock HTTP transport, provenance continuity across
later unrelated imports, duplicated backend/frontend state inference, and a
large permutation test matrix.

Once clean passes 3 and 4 proved core branch reviewability, later marginal
findings deserved a much higher actionability bar. Instead, accepting edge-case
safeguards on pass 6 or pass 12 created a self-reinforcing trap:

1. a fresh sample proposes an edge-case safeguard;
2. the safeguard adds state or policy;
3. later reviewers find real bugs and missing permutations *inside* that new
   machinery;
4. fixes and tests make the machinery more durable and reset the clean-pass
   counter; and
5. further sampling discovers the next hypothetical obligation.

## What Should Have Happened

At the first capped `convergence-review` run, the LCA should have separated:
(1) unfinished work under approved ERs, (2) ambiguous/over-broad ER wording
needing simplification, and (3) unrequested behavior or guarantees.

The proportionate retained core was simply the frozen wire contract and
caption-track canonicalization, immutable request-key/body handling, exact
response verification, identical retry for genuinely uncertain outcomes,
conflict reconciliation via a deliberate new attempt, atomic local finalization,
authorization/redaction/bounds, and CSV export fallback. Generalized
post-confirmation policy, endpoint migration, definitive-failure recovery
permutations, and duplicated client state should have been rejected or deferred.

## Lessons For LCA Sessions

1. Requirements-risk calibration is both a bootstrap requirement (including on
   handoffs) and an active checkpoint at iteration caps, architecture-pressure
   gates, and later GSR rounds.
2. A `convergence-review` iteration cap is a decision point, not an automatic
   rerun trigger.
3. Reviewer findings never amend approved requirements.
4. After early clean GSR samples, raise the marginal-value bar sharply.
5. Evaluate *aggregate* Architecture Pressure across fixes, not just whether
   each single patch sounds small.
6. Track diff, decision-point, review-count, and context-traffic growth as
   stop-and-simplify signals.
7. When newly added machinery generates new defects, consider deleting the
   machinery before perfecting it.
8. The LCA owns the iteration brake before a human has to intervene.

## Calibration Questions

1. Has the reviewer identified a failure of approved behavior, or proposed new
   behavior to prevent a hypothetical future scenario?
2. Would this finding still exist if review-added machinery were removed?
3. Does the proposed fix add a new state, protocol, digest, lock, reconciliation
   rule, migration policy, or permutation test matrix?
4. Did a recent candidate already receive clean GSR samples, and if so, what
   concrete current-system risk justifies resetting the clean-pass count?
5. Is implementation size growing faster than user-visible capability?
6. Has the iteration cap been hit more than once without simplifying the ERs?
7. Can a rare edge case rely on an existing manual fallback (such as CSV export)
   instead of automated recovery state?
8. Did this session read and reapply both the requirements-risk cases and the
   repository's operating conditions at this decision point?
