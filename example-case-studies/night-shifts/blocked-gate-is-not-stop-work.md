# Case Study: When a Blocked Production Gate Became a Stop-Work Gate

> **Status: mandatory reading before leading an autonomous overnight shift.**

## Executive Finding

An overnight security-hardening shift produced a high-quality `Slice 13`
implementation: it isolated dirty worktrees cleanly, implemented a fail-closed
boundary, drove `convergence-review` to zero findings on a second review-first
run, passed **29 focused tests and 502 full-suite tests** plus migration checks,
dispositioned **7 GSR passes** (ending with two consecutive clean passes), and
verified that local macOS execution failed closed with `sandbox_unavailable`
because the target Linux kernel isolation primitives were absent.

Despite that strong engineering work, the shift was a **major process failure**
for two independent reasons:

1. **Conflating acceptance/activation gates with implementation stop-work
   gates:** Because no Linux staging host was reachable to prove real-host
   isolation, the lead correctly kept activation disabled - and then
   **incorrectly stopped the entire campaign**, leaving authorized `Slice 14`,
   `Slice 15` (inactive cutover code), and independent macOS-compatible fallback
   stories untouched.
2. **Declaring a reviewer CLI globally unavailable from one sandboxed false
   negative:** A single status check inside a restricted outer filesystem
   sandbox returned `Not logged in` for `claude`. Without consulting the machine
   delegation notes or running a task-shaped headless smoke check (`claude
   --print ... --permission-mode plan`) with normal home-directory read access
   (which returned `CLAUDE_OK` immediately the next morning), the lead wrote off
   Claude for the entire night.

## Four States That Must Never Be Conflated

The lead collapsed four distinct engineering states into one binary `"blocked"`:

1. **Portable implementation exists;**
2. **Local/unit/contract validation passes;**
3. **Intended-host / staging acceptance passes;** and
4. **Live activation is enabled.**

Only states `3` and `4` were blocked by the missing Linux host. Both the parent
design doc and `Slice 14` explicitly stated that downstream implementation
waited on `Slice 13` *code convergence* (which had succeeded), while the Linux
host probe gated only final *activation*.

## Expected vs Actual Behavior

| Situation | Expected Lead Behavior | Actual Shift Behavior |
|---|---|---|
| Host lacks target Linux kernel primitives | Keep feature flag off; mark host-acceptance pending | Done correctly |
| One status probe reports `claude` logged out inside an outer sandbox | Run a task-shaped headless smoke with normal CLI auth state before declaring provider loss | Declared `claude` unavailable for the night |
| `Slice 13` converges locally (`502` tests green, `2` clean GSRs) without Linux host proof | Record pending host proof and proceed to `Slice 14` / inactive `Slice 15` implementation | Treated `Slice 14` and `Slice 15` as completely blocked |
| Primary campaign hits a real external gate | Pivot to an explicitly authorized independent fallback slice | Ended the overnight shift early |

## Durable Rules

1. **Scope every blocker to the exact claim it governs.** Missing deployment or
   host-acceptance proof blocks *claiming host acceptance* and *enabling
   activation*; it does not block portable code, unit/contract tests, or
   downstream slices behind a disabled flag.
2. **Test tool availability with a task-shaped smoke in the real execution
   context** before declaring a provider down; distinguish outer-sandbox
   permission denials from real auth or quota failures.
3. **Degrade gracefully on genuine single-provider loss:** record reduced
   reviewer diversity and continue authorized work with remaining configured
   models rather than halting the campaign.
