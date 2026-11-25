# Case Study: Target Schedule ERs, Touch-Point Inventories, and Transient Names

> **Status: calibration reading for drafting and preflighting Essential
> Requirements. Companion to
> [dense-ers-after-preflight-rounds.md](dense-ers-after-preflight-rounds.md),
> the same design's first slice.**

## Context

The second slice of the same adaptive learning platform design moved the
Dashboard's Target Schedule card onto real progress data across five
owner-approved stories (`US-1` through `US-5`) and removed the card's two-tab
schedule view and stored tab preference.

## Before (207 Words)

```text
- [US-1, US-2, US-3, US-4] The Active Plan view must render its count, journey chart, day details
  and last-7-days change from the slice 1 learner progress data for the learner's active
  course, with no topic-target schedule on its face.
- [US-2, US-4; Maintainability] The backend schedule pacing module must compute the pace values the
  card shows (the steady line from the reference start date to the Proficient target date
  the module already derives, today's point on that line, and the weekly rate needed) from the
  slice 1 course total and today's demonstrated count. The card draws these values and never
  computes schedule math.
- [US-5] A free learner must see their own count and schedule line over a chart labelled as an
  example, and the example must contain no learner's real data.
- [Maintainability; Data Integrity] The Schedule from today tab must be removed in full, including
  the stored schedule mode preference and every place that reads or writes it (model, API, admin,
  contracts, assistant prompt context, frontend). The column leaves through the first release of the
  two-release removal in `docs/deployment/partner_releases.md` (a database default, then a
  state-only removal); dropping the column is not part of this slice. Setup and Final Wrap-Up must
  not change.
```

## After: Owner-Approved (~115 Words)

```text
- [US-1, US-2, US-3, US-4] The Active Plan view shows the learner's own count, journey chart, day
  details and last-7-days change from slice 1's progress data, with no topic-target schedule on its
  face.
- [US-2, US-4; Maintainability] The schedule shown for the learner's target date comes from the
  backend schedule pacing module. The card draws it and does not compute it.
- [US-5] A free learner sees their own count and schedule line over a chart labelled as an example.
- [Maintainability; Data Integrity] The Active Plan view has no tabs, and the stored tab preference
  is removed in full. The database column itself is dropped in a later release. Setup and Final
  Wrap-Up do not change.
```

## What Changed, and Why

1. **Parenthetical formula moved to Proposed Approach:** The ER's real promise
   is *who* computes schedule values (the backend, not the card), not the exact
   steady-line formula.
2. **Touch-point inventory became `"removed in full"`:** Listing `(model, API,
   admin, contracts, assistant prompt context, frontend)` is a grep result that
   goes stale the moment a seventh reader exists and looks falsely exhaustive.
3. **Runbook steps became one boundary fact:** `"The database column itself is
   dropped in a later release"` keeps the slice constraint without duplicating a
   deployment runbook.
4. **Unsourced clause deleted:** `"The example must contain no learner's real
   data"` had no story behind it on a static synthetic chart.
5. **End-state wording replaced transient UI labels:** An intermediate rewrite
   said `"The Schedule from today tab is removed"`, which preflight caught
   because on `main` the tabs were named `"Projected Schedule"` and
   `"Historical Schedule"`. Stating the end state (`"The Active Plan view has no
   tabs"`) eliminated the trap.

## Lessons

1. **State who owns a value, not how it is computed.**
2. **`"Removed in full"` beats a caller inventory.**
3. **Keep deployment runbook mechanics in runbooks**, stating only the boundary
   fact this slice must respect.
4. **Describe the end state of a removal** rather than anchoring on transient
   branch or UI labels.
