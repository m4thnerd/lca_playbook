# Case Study: Autonomous Preflight Self-Inflation, Runtime Self-Policing, and Follow-Up Snowballs

> **Status: required calibration reading; apply with
> [lca_playbook.md](../../lca_playbook.md),
> [architecture_critic.md](../../reviewers/architecture_critic.md),
> [module_charter_drafting_guidelines.md](../../architecture/module_charter_drafting_guidelines.md), and
> [convergence_review_preflight_requirements_justification.md](../../requirements/convergence_review_preflight_requirements_justification.md).**

## Context

A 112-PR audit of a production SaaS platform reconstructed verbatim human chat
transcripts and pre-squash git commit histories across three months and compared
them against shipped `main`. Three recurring patterns accounted for thousands of
lines of avoidable production code, synthetic test matrices, and emergency
follow-up PRs.

## Three Systemic Patterns Observed

### Pattern 1: Autonomous Preflight Self-Inflation & Follow-Up Snowballs

1. **Adaptive Topic Practice Difficulty:** The initial design commit captured
   the human-directed story set (`US-1..US-10`). Eight hours later, during an
   autonomous *"Refine design for LCA preflight"* pass, the agent invented
   `US-11` and `ER-3` (a `floor(n/2)` = 5/10 unknown-difficulty exploration
   quota), narrowed unseen-first ordering to apply only within a difficulty
   pool, and mandated a database column
   (`adaptive_practice_target_accuracy_pct` in `ER-8`) that was persisted in
   PostgreSQL, validated in Admin, copied into config dataclasses, and **never
   read by the selector**. In production, `ER-3` caused seen in-band questions
   to starve unseen out-of-band questions once the quota filled, stranding
   learner topic completion and forcing a **+1,586-line follow-up PR** that
   bloated `policy.py` from 679 to 1,045 lines (including a 90-line cross-SK
   donor/recipient slot-stealing loop) instead of deleting the unrequested
   quota.
2. **Consolidate Explanation & Annotations:** Unrequested client concurrency
   ceremony (`itemLoadSeq` counter + `pinActionReady = false` gate across 5
   async handlers) permanently disabled the save-pin button whenever the initial
   read failed, forcing an emergency follow-up fix. In the same PR, a
   review-loop finding under `[Reliability]` laundered a duplicate
   `include_saved_pins` wire flag across 6 files even though every caller passed
   `include_saved_pins === include_item_annotations`.

### Pattern 2: Runtime Self-Policing & 2-Phase State Machines for Ordinary Operations

1. **Runtime AST Sibling-Import Police Causing Full-Directory Copy-Paste:**
   An agent added `_assert_version_module_no_sibling_imports`, running
   `ast.parse` on every `.py` file at runtime on the production dispatch path to
   ban `v3` from importing unchanged helpers from `v2`, and promoted that rule
   into a draft module charter. In a subsequent PR, to implement a **5-line
   small-SK cap lift**, that self-inflicted rule forced the next agent to copy
   all 8 files of `v2` (429 prod LoC) and 294 lines of contract tests into `v3`,
   duplicating unchanged calculation helpers byte-for-byte across `v1`, `v2`,
   and `v3`.
2. **Two-Phase Database State Machines for `cache.delete()`:** In existing CSV
   content importers, post-commit cache invalidation was a single line
   (`transaction.on_commit(lambda: invalidate_topic_item_counts_cache(slug))`,
   clearing three Redis keys). Across two content-import PRs, clearing those
   three Redis keys was turned into durable `finalizing` / `finalization_failed`
   DB states, redundant `finalization_context` JSON columns duplicating the
   batch's own foreign key, manual retry views, and cross-domain refusal gates
   that blocked instructors from publishing *questions* if a *review-card* or
   *case-exercise* Redis cache clear failed (`~650` prod / `~900` test LoC).

### Pattern 3: Building Deferred Subsystems & Charter Stamp Laundering

1. **Building Explicitly Deferred Work:** Early in a brand-migration PR, the
   human owner explicitly deferred user migration (*"We will figure out the user
   migration a little bit later"*). The agent nevertheless committed a
   **3,562-line migration CLI** (`2,228` prod, `1,003` test, `331` doc LoC) that
   also exported password hashes and OAuth rows despite its own spec listing
   both under *Do-Not-Migrate*. Conversely, in another UI PR, a 5-line mobile
   drawer close fix explicitly approved in a late chat turn was left uncommitted
   when the PR merged.
2. **Charter Attestation & Clean-Room Diary Laundering:** Agents appended new
   unreviewed requirements directly beneath an earlier *"Every word in this
   charter has been carefully reviewed by a human and approved"* header without
   marking the new text `Agent-Drafted (Unreviewed)`, and in another PR pasted a
   276-word commit/timer diary into `CHARTER.md`.

## Calibration Questions

1. Did an autonomous preflight or design-refinement pass introduce new `US-*`
   stories, numeric quotas, duplicate wire flags, or database columns that never
   appeared in the Verbatim Human Intent Reference?
2. When a follow-up fix addresses starvation or stuck UI state, was that bug
   caused by an unrequested quota, concurrency counter, or readiness gate from a
   prior PR that can be **deleted** rather than patched?
3. Does production code run `ast.parse`, runtime constant type-checkers, or
   sibling-import bans that force full-directory copy-paste (`v2 -> v3`) when a
   static CI check and helper delegation would suffice?
4. Has an ordinary `cache.delete()` or `transaction.on_commit` side effect been
   wrapped in durable `finalizing` / `finalization_failed` database states and
   cross-domain refusal gates?
5. Before opening a PR, did the LCA verify against the Verbatim Human Intent
   Reference that (a) no explicitly deferred work from an earlier turn was built
   anyway, (b) every late-turn human-approved fix was committed, and (c)
   agent-drafted charter additions are clearly marked `Agent-Drafted
   (Unreviewed)`?
