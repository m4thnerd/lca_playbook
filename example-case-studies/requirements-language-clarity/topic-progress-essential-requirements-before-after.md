# Case Study: When Precise Essential Requirements Become Hard To Understand

## Context

A Topic Progress Recalibration design needed a compact `# Essential
Requirements` section to guide implementation and `convergence-review`. The
first draft contained the right product decisions, carried valid source tags,
and passed formal scoring, yet failed a casual human engineering read: by the
fourth bullet, sentence length and interacting clauses made it harder to parse
than the detailed design itself.

## Before: Technically Explicit, Practically Opaque

- `[US-4, US-6; Maintainability]` One deployment-level tenant configuration selection must choose the legacy or recalibrated implementation for every course. Normal MCQ, track-specific graded-practice, review-card-triggered topic refresh, and score-repair calculation paths must use the same Scoring-owned dispatch boundary; no course, learner, track-specific handler, or caller may independently select or reconstruct either formula.
- `[Maintainability]` Changing the deployment selection must preserve the existing lazy-recomputation contract: it must not proactively rewrite stored SK or topic scores, reads must continue to return stored scores, and the next existing authoritative score-refresh path must calculate and store affected values with the selected implementation. A submission's prior score must remain the stored value from before that activity.
- `[US-1; Maintainability]` Recalibrated SK score must equal the lesser of the existing recency-weighted accuracy estimate and the effective cap for the `SkillRecord`'s total direct accuracy impacts. The site-default caps must be `0.63` at one impact, `0.82` at two, `0.95` at three, and `1.00` at four or more, with the existing all-or-nothing per-course calibration override retained; zero impacts must produce `0.0`. The total must include the existing standard and track-specific correct and incorrect impact counts, including repeats, so wrong answers affect accuracy and no new distinct-question or submission-identity mechanism is introduced.
- `[US-1, US-3]` Recalibrated topic progress must use all score-eligible SKs and return `0.0` when none exist; for at most 10 eligible SKs it must divide their summed stored scores by the eligible count, and for more than 10 it must divide the sum of assessed SKs' stored scores by the greater of 10 and the assessed count, where assessed means the total direct-impact count is greater than zero. The recalibrated path must not apply the legacy attempt-volume ceiling or weak-SK penalty; it must retain the fixed `0.95` graded-practice ceiling followed by the existing review-card lift and final `1.0` bound.
- `[US-2]` For an assessed SK, the backend must use the SK's stored score and the same total-impact count used for SK scoring to calculate `clip(0.10 + 0.57 * n^-0.75, 0.10, 0.67)`, raise the result to at least `0.40` when score is below `0.25`, at least `0.30` when score is from `0.25` through less than `0.50`, and at least `0.15` when score is at least `0.80` with 20 or more impacts, then expose the result rounded to two decimals as `score_confidence_band`. It must return `null` for an unassessed SK or while recalibration is disabled, and the band must not be persisted as learner state.
- `[US-2]` The current-state Topic Progress detail response must associate each confidence band with its SK. Version 1 must print each non-null value as plain text beside that SK and print nothing for a null value; it must not add band values to the post-answer delta or require band animation, explanatory labels, or a settled visual treatment.
- `[US-5; Maintainability]` Legacy-only scoring formulas and constants must remain production-supported in a dedicated legacy module while any deployment uses them. Shared persistence, eligibility, configuration, and dispatch behavior must not be duplicated merely to isolate legacy code; any legacy-only symbol that cannot be moved into that module without disproportionate complexity must be listed in a focused deprecation guide for removal after every deployment migrates.
- `[US-6; Maintainability:CriticalLane]` Scoring must remain the sole owner of score formulas while LearnerData continues to own `SkillRecord` and topic-progress state and its existing write/cache paths. The recalibrated scoring and band policy must form one narrow Full-Spec responsibility inside Scoring, protected at its public behavioral contract without making its internal file layout or helper structure part of that contract.

## Two Category Errors Caught During Rewrite + Human Review

After rewriting into plain short sentences and running independent clarity and
justification reviews, a final human read caught two classic category errors:

1. **Operational rollout state vs durable requirement:** A reviewer proposed
   requiring `"Tenant A enabled; Tenant B disabled"` in the ERs so an
   implementation could not leave both tenants on legacy. That is temporary
   deployment configuration (often stored in environment/parameter-store config),
   not a code requirement. Code owns the selection *capability*, not today's
   per-tenant flag position.
2. **Temporary verification scaffold vs product requirement:** Printing the raw
   confidence band beside each SK was a temporary internal checkpoint that must
   never ship to learners; it belonged in the *Verification Plan*, not `#
   Essential Requirements`.

## Final Approved Essential Requirements (6 Bullets)

- `[US-4, US-6]` Each deployment must use one deployment-level setting to choose either the legacy or recalibrated score calculation. All SK and topic score calculations in that deployment must use the selected implementation.
- `[Maintainability]` Turning on recalibration must not immediately change stored scores. Scores change only through the normal practice-driven refreshes used today; simply reading a score does not recalculate it.
- `[US-1]` Recalibrated SK score must use the existing recency-weighted accuracy score. By default, cap it at `0.63` after one evidence impact, `0.82` after two, `0.95` after three, and leave it uncapped at four or more. An unassessed SK remains `0.0`. Count all existing standard and track-specific correct and incorrect impacts, including repeats.
- `[US-1, US-3; Maintainability]` Recalibrated topic score is `0.0` when no eligible SKs exist. With 10 or fewer eligible SKs, average all of them. With more than 10, sum the assessed SK scores and divide by at least 10, or by the assessed count when it is higher. Do not apply the legacy volume ceiling or weak-SK penalty. Keep the existing `0.95` graded-practice ceiling and review-card lift.
- `[US-2; Maintainability]` Topic Progress detail must return the Section 7 confidence band for each assessed SK in recalibrated mode. Return a null band when the SK is unassessed or recalibration is disabled. Calculate the band from current stored score and evidence; do not store it as learner state.
- `[US-5, US-6; Maintainability]` During rollout, keep the legacy and recalibrated calculations separate within Scoring and behind the same selection point. The legacy path and selection setting must remain removable after every deployment migrates.

## Key Takeaways

1. **Point to a focused design section for lengthy math** (`Section 7`) rather
   than pasting multi-threshold clip formulas into an ER bullet.
2. **Never turn today's per-tenant rollout toggle positions into software ERs.**
3. **Never put temporary debug/verification UI checkpoints into `# Essential
   Requirements`.**
