# Case Study: Exact-Context Preflight, Pre-Authorized Continuation, and Watchdogs

> **Status: calibration reading from two successful overnight continuations and
> their morning Engineering Director syntheses.**

## What Actually Ran

Direct task telemetry across two parallel programs demonstrated how explicit
preflight and continuation controls eliminated the prior night's stall and
stop-work failure modes:

| Workstream | Active Window | Elapsed | Outcome |
|---|---:|---:|---|
| Platform simulation-management LCA | `20:29-07:06` | `10h 37m` | Uninterrupted active controller: preflighted design, converged implementation, captured clean-room and browser proof, and opened draft PR (morning EngD isolated 1 lint/unused-param check in `3m 24s`; LCA pushed green CI fix in `11m`). |
| Agent-workspace Conversations LCA (initial + pre-authorized continuation) | `21:52-01:12` + `01:12-01:45` | `3h 52m` | Delivered screenshot-backed draft PR at `01:12`, then consumed the human's queued `22:08` pre-authorized autonomy instruction to merge, deploy, run a live production canary, and clean temporary state by `01:45`. |
| Conversations `30-minute` watchdog | `01:45-morning` | Seconds/check | Fired every 30 minutes and performed clean **no-ops** because the durable goal was already satisfied. |
| Issue-tracker security LCA | `20:39-23:47` | `3h 08m` | Merged and deployed a safely default-off read seam, then parked cleanly on the exact missing external service credential without blocking sibling streams. |
| Morning Engineering Director syntheses | `07:56-08:02` | `3-6 min` | Reconciled actual branches, PR checks, and deployed state into one dependency sequence per program without asking LCAs to retell transcripts. |

Two tempting misreads were refuted by the trace:

- **"Finishing at `01:45` wasted the rest of the night":** False. **Empty
  wall-clock consumption is never a success metric.** Once an autonomous run has
  genuinely completed and verified every authorized objective, clean watchdog
  no-ops and leaving production undisturbed is the exact right behavior.
- **"Every fallback in the repo is overnight capacity":** Only fallback slices
  that are *already preflighted and free of open product questions* count as
  real overnight capacity.

## Seven Load-Bearing Controls Behind the Success

1. **One named must-exist morning payload** plus explicit non-goals and
   authority bounds in the handoff.
2. **Exact-context preflight before Slice 1:** verifying writable `.git` index
   (catching stale `index.lock` or sandboxed credential-cache denials early),
   provider CLIs, browser capture, test runners, and artifact directories from
   the *same* shell/sandbox the shift uses.
3. **Proven continuation:** either an uninterrupted active controller loop or a
   durable `/goal` paired with a periodic (`30-minute`) no-op-safe watchdog.
4. **Pre-authorized continuation instructions:** queued human clarifications
   unlocking merge/canary steps once local gates pass without mid-night live
   chat.
5. **Narrow blocker scoping:** missing external credentials parked only the
   live-canary claim on that one arm while sibling arms shipped.
6. **Isolated worktrees + single-writer `convergence-review` checkouts** with
   commits at every green slice boundary.
7. **Compact morning Engineering Director verification** (`3-6 minutes`)
   checking actual remote SHA/CI/deployment truth before waking only the one LCA
   needed for a `1-line` CI cleanup.
