# Ambitious UX Competition Loop

> **Standing rule:** Never run this multi-round competition loop unless the
> human explicitly requests it by name; when someone asks for "a few quick
> options", default to quick lightweight sketches instead.

A multi-round design competition in which several agents ("competitors") each
independently redesign the same page as ambitiously as they can, a judging panel
scores every entry each round, competitors see competing entries between rounds,
and the loop ends with an HTML report presenting the final designs, live
prototypes, and judge evaluations.

This is the deliberate **opposite** of the
[Low-Risk UX Enhancements Loop](low_risk_ux_enhancements_loop.md). That loop
mines existing pages for easy, safe, frontend-only wins and prunes anything
ambitious. This loop invites full creative freedom: redesign the page from
scratch, think from first principles about what the user actually needs and what
would delight them, and (in Type 2) even invent **new user stories** if they
make the experience more compelling. Entries are design proposals or isolated
worktree builds, so risk is absorbed by the competition format rather than by
timid scope pruning.

## When to use it

- A page (or a tightly connected 2-3 page flow) matters enough that incremental
  polish is not the ceiling you want; you want to see what the page *could* be.
- You want several genuinely different points of view to compare before
  committing to a direction, rather than iterating one agent's first idea.
- The human owner explicitly asked to run an ambitious UX competition.

Do **not** use it for routine polish (use the low-risk loop), when the design
direction is already settled, or when quick 10-minute sketches would answer the
question.

## Competition types

All types judge the user experience; they differ in data and delivery
constraints:

1. **Type 1: Frontend-only, existing data.** Competitors redesign using only
   data already exposed to the frontend today.
2. **Type 1-B: Real-data inventory + shared fixture + ship-intended.** Before
   writing the brief, a sub-agent inventories what backend endpoints/helpers can
   actually serve today (GREEN / YELLOW / RED) so false premises never enter the
   brief. Competitors render against one **single shared, self-validated fixture
   dataset** so entries are directly comparable, and the winning design is
   implemented for real (including a mandatory **real-data render gate** in both
   light and dark themes before opening a PR).
3. **Type 1-C: Templates-only over unchanged backend views.** Competitors work
   in isolated git worktrees restricted to template/CSS/static globs and render
   through the real application views against a seeded test database.
4. **Type 2: Frontend with synthetic data.** Competitors may invent plausible,
   internally consistent synthetic fixture data ("if the backend gave you X,
   what could you do with it?") and must clearly distinguish which elements rely
   on synthetic data so the final report doubles as a ranked backend wishlist.

Pick the competition type in the brief before round 1.

## Default parameters

- **Competitors:** 3 across diverse model families when available (for example
  Claude Opus, GPT/Codex, and Gemini or Grok; use a same-vendor stand-in rather
  than stalling if a foreign CLI auth session is expired at kickoff).
- **Rounds:** 2-3 (3 is the standard balance between cross-pollination and
  diminishing returns).
- **Scope:** 1 focus page (or a cohesive 2-3 page set judged together, or tiered
  pages when covering a whole module).
- **Judging panel:** 2 fresh independent judges per round by default:
  1. a **professional UX critic** (with an explicit **restraint mandate** on
     task/utility pages: score restraint and name what should be cut), and
  2. a **narrow in-character user persona** (for example a time-pressed target
     user on a phone with a concrete question such as *"would I run my morning
     on this tomorrow?"*).
- **Judge-feedback visibility:** entries-only by default, paired with an
  explicit anti-convergence rule in rounds 2+.

## Kickoff & operational checklist

Lessons learned across five production runs:

1. **Inventory backend truth first (Type 1 / 1-B / 1-C):** verify actual fields
   and helper semantics in code before drafting the brief.
2. **Smoke-test every competitor and judge CLI with exact flags and working
   directories** before round 1. Stage all required inputs (`brief.md`, shared
   fixtures, reference files) *inside* each sandboxed competitor's working
   directory using relative paths, and launch judges from the run root so
   sandbox read rules never block inputs.
3. **Never encode the human's review act as a rigid enum** (`approve / revise /
   reject`) in briefs or fixtures when real human review is an open selection
   plus steering notes.
4. **Have the human owner skim the brief opening during round 1** when possible;
   if premises need correction, issue a `brief_addendum_r2.md` before round 2
   without penalizing round 1 entries.
5. **Competitors do not self-screenshot:** have competitors focus on keeping
   their HTML/CSS renderable at every moment (writing CSS before templates so
   timeouts never leave unstyled markup) and writing their designer's note last;
   the orchestrator captures desktop + mobile (light + dark) screenshots
   centrally via `puppeteer-core` (marking the mobile fold line when scroll
   depth matters).
6. **Run long multi-round orchestrators detached** with status files rather than
   fragile foreground shell timeouts.

## Submission format (per competitor, per round)

- **Working HTML deliverable** (standalone prototype or isolated worktree render).
- **Orchestrator-captured screenshots** (desktop and mobile, light and dark
  where applicable, full-size files on disk; judges inspect `<= 5` images per
  call and confirm claimed interactions in the rendered HTML/JS).
- **Short designer's note**: thesis, what sits above the fold and why, (Type 2)
  which elements ride on synthetic data (with internally consistent math),
  (rounds 2+) **what changed and why**, and (final round) **evolution across
  rounds**.

## The round cycle & cross-pollination

1. **Compete:** Round 1 starts from the brief and shared fixture. In rounds 2+,
   include two explicit instructions in the competitor prompt:
   - *Anti-convergence:* "A distinct, well-executed point of view beats the
     second-best version of a rival's page."
   - *Defect movement:* "If your previous entry has an obvious usability or
     layout weakness relative to rivals, fix it; holding a point of view is not
     the same as holding a defect."
2. **Judge concurrently:** Because entries-only cross-pollination means round
   `N+1` competitors need only round `N`'s entries (not judge scores), round `N`
   judging and round `N+1` competing can run concurrently when wall-clock speed
   matters.
3. **Iterative single-branch variant & Borda voting:** If running sequential
   persona-driven rounds on a single branch ending in a blind vote, avoid voting
   across near-identical rounds (Borda saturates into ties; compare only the few
   most distinct candidates or run pairwise comparisons), pre-register
   Architecture Pressure as a secondary tiebreaker, build a per-persona hybrid
   candidate when user groups split (for example customers prefer round 6 while
   providers prefer round 3), and hold panel open/closed state steady after one
   deliberate flip so reviewers do not oscillate. See
   [ui-vote-tie-and-visual-reporting.md](../example-case-studies/night-shifts/ui-vote-tie-and-visual-reporting.md).

## Final report

Produce a reviewable HTML report (following [ui_review_format.md](ui_review_format.md)
where decisions or held story mockups are presented) containing:

- **Direct links to each finalist's live HTML deliverable** (and serve via a
  local HTTP server when presenting locally so links open rendered pages rather
  than raw source).
- Inline screenshot previews at desktop and mobile widths (never folding away
  the primary deliverable that approval acts on).
- Separate scores and concrete region-level commentary from both the UX critic
  and the user-persona judge (including cross-entry hybrid recommendations,
  which frequently beat any single finalist).
- Each finalist's designer's note and (Type 2) the consolidated backend
  capability wishlist.
- When the winning direction is implemented (Type 1-B / 1-C), render the built
  implementation against real dev/staging data in both themes and verify every
  assumed backend field semantic before opening a PR.
