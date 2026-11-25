# Case Study: Continuation Requires a Controller (The 900-Second Idle-Timer Race)

> **Status: mandatory reading before leading an autonomous overnight shift.**

## Executive Finding

An overnight shift produced four clean commits in its first 27 minutes (`22:12`
to `22:36`), delegated three background agents (capture harness, inventory, and
shared fixture builder), and ended its turn cleanly waiting on the fixture
builder's completion notification.

At **`23:08:24`**, the fixture agent completed and its notification **did wake
the lead**, which began its next active turn. **Fourteen seconds into that
active turn (`23:08:38`), the desktop harness killed the turn on an unreset
idle timeout.**

When the workstation display had turned off at `22:38`, the desktop app's
`WarmLifecycle` subsystem (`arm=when-hidden`) armed a **900-second idle timer**
(`22:53:38 + 900s = 23:08:38` to the second). Neither the arriving subagent
notification nor the newly started model turn reset that timer. It fired
mid-turn (`"[Request interrupted by user]"`, `"interruptedByShutdown": true`),
leaving the desktop app running all night while the paused session sat frozen
for roughly **9 hours 40 minutes**.

At `07:16` (four seconds after the display woke), the app wrote a synthetic
bookkeeping pair into the transcript (`"Continue from where you left off."` ->
`"No response requested."`, `"model": "<synthetic>"`, **zero input tokens and
zero output tokens**). Real inference resumed only when a human messaged at
`08:48`.

## Factual Timeline

| Local Time | Event | Verified Source |
|---|---|---|
| `22:12-22:36` | Four commits; brief completed; three subagents delegated (`capture`, `inventory`, `fixture`) | `git log`, session transcript |
| `22:36:42` | Lead ends turn waiting for the delegated fixture build | session transcript |
| `22:38` | Display turns off; desktop `WarmLifecycle` arms (`arm=when-hidden`) | OS power log, harness `main.log` |
| `22:53:38` | `WarmLifecycle` starts a `900s` session idle timeout | harness `main.log` |
| `23:08:24` | Fixture subagent finishes; `<task-notification>` wakes the lead, which starts writing analysis | session transcript, `main.log` |
| `23:08:38` | **`900s` idle timer fires mid-turn; harness pauses the active session (`idle_timeout`)** | `main.log`, transcript |
| `23:08-07:16` | Machine stays awake all night (`1,617` app log lines), with the shift session frozen | `main.log`, OS power log |
| `07:16:26` | Display wakes; app warms session and writes a `0`-token `<synthetic>` bookkeeping pair (no LLM call) | transcript, `main.log` |
| `08:48:18` | Human messages the session; real model inference resumes immediately | transcript |

## Secondary Finding: Preparation Outranked Payload

Even before the `23:08` harness pause, the first 27 minutes spent effort on a
broad codebase inventory (`inventory.md`) and fixture scaffolding before
shipping the smallest visible deliverable. When a run is interrupted early, only
already-committed user-visible slices retain value.

## Durable Rules

Before calling a shift unattended, prove all three in the **exact** execution
harness that will run overnight:

1. **Capability:** repositories, CLIs, credentials, and test runners work in the
   actual execution context.
2. **Continuity under display-off / idle lifecycle:** a durable `/goal` loop,
   cron/scheduler watchdog, or headless CLI runner will keep driving turns past
   desktop window-hidden idle timers until the stopping condition is met, and an
   observer/watchdog can distinguish a paused session from a working one.
3. **Payload before broad inventory:** land the smallest valuable, verifiable
   slice before optional reconnaissance or polish.

## Calibration Questions

- What concrete controller or `/goal` loop creates the next turn if a desktop
  idle timer interrupts an active callback turn when the screen turns off?
- Has that continuation mechanism been tested with the display hidden/idle,
  rather than assumed from interactive daytime turns?
- If the shift were killed 30 minutes in, would the committed state hold a
  valuable vertical slice or only preparatory notes?
