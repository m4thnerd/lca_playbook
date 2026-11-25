# Case Study: Leaderboard ERs, and How a Shorter Paraphrase Can Invent a Feature

> **Status: calibration reading for drafting and preflighting Essential
> Requirements. Companion to
> [dense-ers-after-preflight-rounds.md](dense-ers-after-preflight-rounds.md)
> and [target-schedule-ers-inventories-and-transient-names.md](target-schedule-ers-inventories-and-transient-names.md).**

## Context

The third slice of the same adaptive learning platform design replaced legacy
Practice XP points with two anonymous weekly boards across four owner-approved
stories:

- **US-1:** The learner sees what was credited this week, beside last week's count.
- **US-2:** The learner sees their run, recent weeks, and how close this week is on each route.
- **US-3:** An anonymous weekly velocity board.
- **US-4:** An anonymous streak board.

## Before (146 Words)

```text
- [US-1, US-2] The learner's own velocity, credited Competencies, run and recent weeks must
  come from the slice 1 learner progress data.
- [US-3, US-4] Board entries are learner-course pairs with a target completion date, across all
  tracks. The velocity board holds pairs with a Competency credited this week or last,
  ranked by this week's credited count then last week's; the streak board holds pairs with a run
  of at least 1, ranked by the run. The 10-pair minimum counts pairs on either board. Aliases, the
  leaderboards-enabled gate and the board size stay as today, except that the five-entry reduced
  board keeps only its streak condition.
- [Maintainability] Practice XP point scoring of velocity and streak must be removed in full: the
  scoring module, the 7-day and 30-day boards, the points copy and legend, and the old boards in
  the admin preview.
```

## First Rewrite (Rejected by Preflight)

```text
- [US-3, US-4] Both boards rank learners across all tracks and keep today's aliases, opt-in and
  minimum board size.
```

Both scoring and justification preflights caught two subtle defects introduced by
that simplification:

- **`"Opt-in"` did not exist:** There was no per-learner leaderboard opt-in,
  only a site-wide `leaderboards-enabled` setting. A reviewer could read `"keep
  today's opt-in"` as a requirement to build a per-learner opt-in feature.
- **`"Rank learners across all tracks"` became ambiguous:** It could mean
  summing one learner's credits across multiple courses into one row, whereas
  each board entry is one `(learner, course)` pair.

## After: Owner-Approved (~100 Words)

```text
- [US-1, US-2] The learner's own credited Competencies, run, recent weeks and progress on
  each route come from slice 1's progress data.
- [US-3] The velocity board ranks learners by Competencies credited this week, then last
  week, so it reads as a full board early in the week.
- [US-4] The streak board ranks learners by their run of earned weeks.
- [US-3, US-4] Both boards rank one entry per learner and course, from all tracks together, as
  today, and keep today's aliases, leaderboards-enabled setting and minimum board size.
- [Maintainability] Practice XP point scoring is removed in full, with its boards and copy.
```

## Lessons

1. **Shortening by paraphrase can invent features.** When an ER preserves
   existing behavior, use the system's real concept name (`leaderboards-enabled
   setting`), never a casual synonym (`opt-in`) that implies a different
   feature.
2. **Check `"across all X"` for unit-of-row ambiguity** (one entry per learner
   vs one entry per learner-and-course).
3. **Always re-run preflights after a plain-language rewrite.** Both bugs above
   were introduced during simplification and caught by preflight.
4. **Welcome preflight findings that fix a wrong word; suspect findings that
   append long clauses.**
