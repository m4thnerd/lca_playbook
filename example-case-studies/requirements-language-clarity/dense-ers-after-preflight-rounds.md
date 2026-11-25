# Case Study: Essential Requirements That Passed Preflight but Could Not Be Approved

> **Status: calibration reading for drafting or preflighting Essential
> Requirements; apply with
> [convergence_review_essential_requirements.md](../../requirements/convergence_review_essential_requirements.md)
> and
> [preflight-self-inflation-and-follow-up-snowballs.md](../requirements-risk/preflight-self-inflation-and-follow-up-snowballs.md).**

## Context

An LCA drafted a sliced design doc for an adaptive learning platform. The first
slice gave learners a daily history of the Competencies they had demonstrated
and a weekly streak run, extending a daily progress snapshot table in a
Critical-lane module.

The slice had six user stories, which the product owner approved with no
changes:

- **US-1:** Each Competency that the learner's own graded activity brings above the bar
  during a week is credited once, and stays credited after a slip.
- **US-2:** Case-response exercises count as question attempts toward a streak week.
- **US-3:** A day-by-day history of demonstrated, newly demonstrated, and slipped
  Competencies.
- **US-4:** History restarts after a progress reset.
- **US-5:** Per-course threshold values that can be changed without a release.
- **US-6:** A week is earned through either route, and the run counts earned weeks in a row.

The LCA drafted eight Essential Requirements. They went through two rounds of ER
scoring preflight and ER justification preflight, and every finding was applied.
Each round made them longer.

## Before: What the Preflights Passed (601 Words)

```text
- [US-1, US-3, US-6; Maintainability:CriticalLane] Per-day Competency progress must come
  from the existing daily course progress snapshot rows, extended in place. Each changed
  Competency entry also keeps the highest score it reached that study day, recorded at the
  existing SK scoring seam; entries written before that field existed read as the higher of their
  starting and current values. Every new write goes through the snapshot module's sole write path.
  Add no new table, event ledger or per-day copy of every Competency.
- [US-2, US-6] Each snapshot row must hold its study day's question attempt count. On the live
  path, shared question-attempt ingestion adds the question attempts saved in each submission, and
  each CFP case-response exercise submission adds one. A one-off fill sets (never adds to) the count
  on stored rows from stored question attempts plus, through one new track-handler APPEND hook whose
  default adds none, stored track-specific attempts, each on that row's own study timezone.
- [US-3] For each study day from the learner's first unarchived row, the read must give how many of
  the course's Competencies with graded content are demonstrated at day end (score above the
  threshold, or in a topic at Proficient on that day's recorded topic levels), and the newly
  demonstrated and slipped ones by name and topic against the previous study day, or for the
  first row against its own starting values (each entry's starting value and the row's starting
  topic levels). A Competency's value on a past day is its latest recorded value on or
  before that day, else its first later entry's starting value, else its current score. Today
  uses live score and live topic levels. Nothing is reconstructed before the first row.
- [US-1; Slice 3 US-1] A Competency is credited in a Monday-to-Sunday week on the learner's
  study dates when the starting value of its first entry that week was not above the threshold and
  its daily peak went above it on a day of that week. It is credited once, on the first such day,
  stays credited after a slip, and is never credited through the topic rule. Each credited
  Competency carries its name, topic, credited day and whether it is demonstrated today.
- [US-6] A Weekly Streak week is earned when its question attempts or its credited Competencies
  reach their per-course value. The run is earned weeks in a row, read over at most the
  last 26 weeks, and the week in progress never ends it.
- [US-4] Both progress reset paths (single-course and full) must keep the learner's snapshot rows for
  the reset courses and mark them archived. The progress read and the snapshot module's
  lookups of a learner's current or latest row (including the latest row's SK changes) must ignore
  archived rows, and study after a reset, including later on the reset day, must be recorded and
  shown.
- [US-5] The threshold and the two streak values must be per-course values on the existing
  layered scoring configuration with its change log. Rows store no demonstrated, credited or
  earned outcome; these values are applied when reading.
- [US-3, US-6; Slice 3 US-1, Slice 3 US-2; Maintainability] One backend module must own the
  demonstrated, newly demonstrated, slipped, credited, earned-week and run rules. The learner
  endpoint, the Target Schedule calculation and the Leaderboard board build must take those
  outcomes from it and never recompute them. One endpoint serves the learner's own values for one
  course: the three per-course values, the course total, the daily series, the recent weeks
  the Leaderboard shows, the run, and this week's credited Competencies.
```

The product owner's reaction: *"The essential requirements sound like bloated
complexity. It's hard to approve these as is. They read as highly jargony and
overly dense."*

## After: What the Owner Approved (~240 Words)

```text
- [US-1] A Competency that the learner's own graded activity brings above the threshold
  during a week is credited once that week, and stays credited if it slips before the week ends.
- [US-2] Track-specific content types (for example CFP case-response exercises) count toward a
  Weekly Streak week through a track handler contract that returns the question attempts they
  contributed in a date range, counting each graded answer inside them as one.
- [US-3] For each study day since daily progress began, the learner can see how many Competencies
  they had demonstrated, as goal 3 defines it, and which were newly demonstrated or slipped that
  day. Today's count matches the Topic Progress page.
- [US-4] After a progress reset, the learner's history starts again from the reset. Earlier
  history is kept but no longer shown.
- [US-5] The threshold and the two Weekly Streak values are set per course and can be changed
  without a release. A change re-scores past days and weeks.
- [US-6] A Weekly Streak week is earned when its question attempts or its credited Competencies
  reach their per-course value. The run is earned weeks in a row, read over at most the
  last 26 weeks, and the week in progress never ends it.
- [Maintainability:CriticalLane] Daily progress is recorded on the existing daily progress
  snapshot rows, through their one write path, with no new table.
- [Maintainability] One backend module decides demonstrated, credited and earned. Target Schedule and
  the Leaderboard show its results and never recompute them.
```

## What Moved, and Where It Went

Nothing was lost. Every removed detail was already in the slice's Proposed
Approach, where a coder reads it anyway:

| Removed from the ERs | Where it lives now |
|---|---|
| Daily peak field, the SK scoring seam, the fallback for older entries | Proposed Approach, Storage |
| Live-path counting, "sets (never adds to)" backfill, study timezones | Proposed Approach, Storage and Backfill |
| Three-step value-on-a-past-day rule, first-row rule | Proposed Approach, read module |
| The definition of demonstrated, including the topic-at-Proficient rule | The product foundation's goal 3 doc, which already owned it |
| Archive field, conditional unique constraint, which lookups skip archived rows | Proposed Approach, Storage |
| Scoring config model, change log | Proposed Approach, Config |
| The endpoint and its field list | Proposed Approach, endpoint section |

## Why the "Before" Set Failed

- **Each ER did several jobs:** The `US-3` ER held a product outcome, a
  definition owned by another document, a three-step storage fallback, a
  first-row edge case, and a live-vs-stored rule.
- **Mechanism posing as obligation:** `"Sets (never adds to)"`, `"APPEND hook
  whose default adds none"`, and lookup inventories bound the coder and review
  loop to one mechanism.
- **Preflights rewarded clause accretion over human readability:** Each
  preflight finding asked for an edge case, and fixing it appended another
  clause until every machine reviewer passed and the human could not approve.
- **Single-track wording in a shared rule:** `"Each CFP case-response exercise
  submission adds one"` baked one track's rule into a general requirement (and
  under-credited multi-part case exercises, which the owner corrected by stating
  the general track-handler contract instead).

## Lessons

1. **One outcome per ER, in words the product owner uses.** If an ER needs a
   parenthetical to define its own terms, point to the document that owns the
   term.
2. **Mechanism goes in Proposed Approach.** An ER can say `"on the existing
   snapshot rows, with no new table"` as a boundary constraint without listing
   fields, lookups, fallbacks, or backfill mechanics.
3. **Treat preflight findings as questions, not clauses to append.** If the
   design doc body already covers an edge case, keep the ER short.
4. **Shared requirements state the shared contract**, naming specific content
   types only as examples.
5. **Approval is the test.** An ER set that passes machine preflights but that
   the product owner cannot read in one pass has not converged.

## Postscript: US-2 Changed Again Same Day (Why Short ERs Survive Design Pivots)

Later the same day, the owner changed the `US-2` design to store case-exercise
practice on the daily snapshot (accepting a slightly slower write for a much
faster read). Because the ERs stated contracts rather than storage mechanics,
updating `US-2` took a single sentence rather than rewriting three interlocking
ERs:

```text
- [US-2] Track-specific content types (for example CFP case-response exercises) count toward a
  Weekly Streak week through a track handler contract that takes one track-specific content
  instance and returns how many practice questions it is equivalent to.
```

The separate field, computed sum, and backfill stayed in *Proposed Approach*.
Running ER scoring preflight on the earlier read-only revision had also caught a
subtle wording collision (`"Daily progress is recorded on the existing daily
progress snapshot rows"` -> tightened to `"New stored daily progress facts go on
the existing daily progress snapshot rows"`): short ERs still benefit from
checking every word against the latest design decision.
