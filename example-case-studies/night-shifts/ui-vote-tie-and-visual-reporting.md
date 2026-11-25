# Case Study: A Four-Way Vote Tie and a Report That Asked UI Questions Without Pictures

> **Status: calibration reading for autonomous UI/UX shifts and morning reports;
> normative rules live in [ui_review_format.md](../../uiux/ui_review_format.md)
> and [lca_overnight_playbook.md](../../lca_overnight_playbook.md).**

## Executive Finding

An overnight autonomous UI redesign shift ran six iterative polish rounds plus a
baseline (`round 0`) on a two-sided marketplace prototype, gated and tagged
every round cleanly, captured 18 persona screenshots per round (desktop and
phone across customer and service-provider pages), ran eight in-character
persona reviews per round (Gemini and Grok CLIs), and held a blind Borda-count
vote at the end.

Engineering discipline held, but two failures surfaced at the final vote and
morning report:

1. **The blind Borda vote tied four ways (`0 / 13 / 15 / 35 / 35 / 35 / 35` across
   rounds 0-6).** The pre-registered tiebreaker (`"a tie goes to the earlier
   round"`) automatically reverted the branch head to `round 3` - the tied round
   with the least work in it - even though **customer personas favored round 6
   (`21` vs `16`)** while **provider personas favored round 3 (`19` vs `14`)**.
   No secondary tiebreaker (such as Architecture Pressure) had been scored in
   advance, and nobody built the obvious hybrid candidate (customer pages from
   round 6 + provider pages from round 3).
2. **The Markdown morning report was unactionable.** It asked human reviewers
   text-only UI questions (*"keep the preselected checkbox? yes or no"*) with
   zero screenshots of either option, opened with an internal agent
   goal-condition checklist, pitched deferred user stories as prose without
   mockups, and split the report into separate product-text vs technical
   sections instead of giving everyone one visual HTML decision page.

## Timeline Highlights & Operational Wins

- **Director stance held:** The lead agent wrote zero application code,
  delegating 8 raw persona reviews per round to consolidation subagents and
  keeping architectural/product judgment clean.
- **Every round gated, tagged, and archived as captured:** Rounds with visible
  defects were reviewed honestly rather than hidden, turning each defect into
  the top item of the next round's brief, and tagging meant `round 6` remained
  one `git checkout` away despite the tiebreaker picking `round 3`.
- **Corrective pre-vote round saved the evaluation:** In `round 5`, a copied
  navigation bar wrapped the mobile header and pushed two primary choices to
  `983 px` (below the `844 px` mobile fold). The lead caught it and ran a narrow
  11-minute corrective `round 6` (`831 px`) before the vote cutoff so the vote
  would not hinge on a mobile layout accident.
- **Worktree lifecycle mistake (recovered):** Removing a scratch worktree while
  a background review subagent was still reading from it lost stderr logs;
  never remove a worktree until every agent dispatched into it has exited.

## Why the Vote and Report Failed

- **Borda count saturates across near-identical candidates:** Eleven of 18
  screenshots were pixel-identical between rounds 5 and 6. Ranking seven closely
  related rounds on contact sheets blurred real differences.
- **Persona-split verdicts require a hybrid candidate:** Rounds 5-6 improved
  customer pages while two panel moves on provider pages annoyed provider
  personas. Because changes were presentation-only, combining customer `round 6`
  with provider `round 3` was straightforward and strictly better than picking
  one side via a tie rule.
- **Full-page mobile captures hid the fold:** Even after `round 6` brought
  choices above `844 px`, full-page tall mobile screenshots carried no visible
  fold marker, so all four customer personas still assumed they had to scroll.
- **UI questions without pictures cannot be answered:** Asking a human to choose
  between UI options or evaluate held UI stories in Markdown prose stalls
  review. Likewise, splitting a UI report into separate product vs engineering
  documents hides shared context; use one visual HTML report (`morning-report.html`
  built via `uiux/ui_review_format/build_review_page.py`) with screenshots of
  each option and technical details folded into expandable drawers.

## Durable Rules Established by This Case

1. **Every UI change or UI question ships as a visual HTML review page**
   ([ui_review_format.md](../../uiux/ui_review_format.md)) showing screenshots
   of each option (`A`, `B`, `neither`, or `now + throwaway mockup` for held
   proposals), leading with decisions rather than agent checklists.
2. **Vote only on distinct candidates (or pairwise), using full-size images in
   small batches (`<= 5` per call)** rather than giant contact sheets.
3. **Pre-register Architecture Pressure as a secondary tiebreaker** (scored
   before voting closes) and **build a per-persona hybrid candidate** whenever
   distinct user roles split cleanly across rounds.
4. **Budget a narrow corrective round before any final evaluation**, draw the
   viewport fold line on mobile captures when fold position matters, and restore
   matching module-charter prose whenever reverting code to an earlier round tag.
