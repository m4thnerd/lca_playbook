# Low-Risk UX Enhancements Loop

An autonomous, repeatable loop that mines a set of pages for **easy,
frontend-only UX/usability wins**, ships them in small verified slices, and
stops itself when a round comes up empty. It pairs the
[UI/UX screenshot review process](ui_screenshot_review.md) with the
[Mandatory Requirements Preflights](../lca_playbook.md#mandatory-requirements-preflights)
and `convergence-review`.

First proven on an overnight autonomous shift where three rounds shipped ~22
small wins across five pages with no backend changes, each round a self-verified
slice, with visible diminishing returns by round 3.

For the deliberate opposite (an ambitious, think-big, redesign-from-scratch
competition on a single page), see the
[Ambitious UX Competition Loop](ambitious_ux_competition_loop.md).

## When to use it

- After a batch of pages reaches feature-complete and you want to systematically
  raise polish without a human driving each fix.
- When "make the new UX nicer" is the goal but the specific fixes are unknown;
  the loop discovers them.

Do **not** use it for behavior/bugs (use tests + GSR), for changes that need
backend/API/data work (out of scope by construction), or for large redesigns.

## The cycle (one round)

1. **Capture**: boot the app on the current branch and capture real screenshot
   *files* (desktop + mobile) of every target page. Delegate this: it is fiddly
   (compose quirks, MFA, self-signed certs, asset allowlists) and is the highest
   rabbit-hole risk in the loop. Give the capture agent the known-environment
   notes and a `puppeteer-core` harness (inline-only browser tools cannot
   produce the files reviewers need). Leave the stack running so later rounds
   re-capture cheaply via HMR.
2. **Review**: fan out **>= 3 diverse reviewers** in different framings
   (round 1: first-time / power-user / accessibility; round 2: visual-hierarchy /
   microcopy / interaction-mobile; round 3: consistency / error-prevention /
   empty-state). Rotate framings each round to surface fresh signal. Each
   reviewer gets full-size screenshots (at most 5 images per call, never contact
   sheets), brief app context, the list of known empty/absent seed-data states
   (so they are not reported as bugs), and from round 2 on **the cumulative list
   of what earlier rounds already fixed**, so they hunt new issues instead of
   re-flagging resolved ones. Use an open-ended "walk in the user's shoes,
   suggest simple improvements" prompt without a defect checklist; skip formal
   rubric scoring.
3. **Consolidate & filter (LCA judgment)**: dedupe across reviewers, resolve
   contradictions against the pages' purpose, and **filter to easy frontend-only
   wins**. Keep a **pruning log** of everything deferred (needs-backend,
   moderate effort, layout restructures, product-judgment calls) so it does not
   re-emerge each round. This step is the go/no-go gate (see stop condition).
4. **Design doc + requirements preflights**: write a small `ux{N}-...` doc
   (Goal / User Stories / ERs / Non-Goals / Validation), then run user-story
   preflight and ER preflights, revising until clean. For pure-polish slices the
   ER *scoring* preflight consistently catches unbounded scope and mechanism
   lock-in. Skip independent code-aware LoC impact estimation: architecture
   pressure is trivially low for presentation-only work.
5. **`convergence-review` -> validate -> re-capture -> GSR -> commit**: same
   discipline as any slice (see [lca_overnight_playbook.md](../lca_overnight_playbook.md)).
   Re-capturing after the fixes both verifies they rendered and produces the
   next round's input.

Then repeat from step 1.

## The stop condition

**Pause the loop after a round that yields no easy/clear wins.** Make it
detectable rather than guessing:

- Instruct every reviewer to say **"No worthwhile new wins"** explicitly for any
  page with nothing left, and to self-filter marginal nitpicks. When most
  page-by-lens cells return that, the well is dry.
- Watch the trend: rounds shrink (round 1 is typically rich; round 3 has
  multiple no-win pages and mostly consistency items). When the consolidated
  in-scope list is empty or trivial, stop and write it up rather than
  manufacturing churn.

## Tips that worked

- **Filter hard; prune explicitly.** The value is in *not* doing the moderate /
  backend / product-judgment items. A visible pruning log keeps scope honest and
  prevents re-litigating the same deferrals.
- **Bound ER scope to named surfaces and state outcomes, not mechanisms.** The
  scoring preflight will otherwise (correctly) flag "across pages" invariants and
  "use one shared component" mandates. Pre-empting these in the draft makes the
  preflights converge in one pass.
- **GSR still finds real bugs in "simple" UI work.** A round that touched video
  playback introduced a real fallback regression the ER reviewers missed;
  scoped GSR caught it. Do not skip GSR just because the slice is cosmetic.
- **Reviewer "remove vendor/jargon names" suggestions must exempt domain
  identifiers.** A named identifier (for example `MuxAssetID` on an internal
  operator screen) is *disambiguating*, not jargon: renaming it to a generic
  "Video ID" forces operators to guess which of several video-id types it is.
  Treat internal operator identifier labels as protected unless the human owner
  says otherwise.
- **Later rounds refine earlier rounds.** Some of the best round-3 items
  completed a round-1 deferral (gating an always-on scroll affordance on actual
  overflow) or extended a round-1 fix (applying no-data treatment to an
  aggregate series).
- **Re-capture every round.** Fresh screenshots on the improved UI are both the
  verification of the last round and the input to the next.

## Gemini and Grok as screenshot reviewers (validated 2026-10-19)

Both work headlessly on screenshot files through their subscription CLIs with no
per-call API key in the loop:

- **Gemini via `agy`:** `cd <dir with screenshots> && agy --model
  <gemini-model-id> --mode plan --print-timeout 15m --print="<prompt>"
  < /dev/null` (run `agy models` to list current model IDs). Prefix the prompt
  with "Please use your file/image viewing tool
  to look at each image file listed below natively at full size. Do not use
  terminal commands, Python, or external tools to inspect them." and list paths
  relative to the working directory (at most 5 images per call).
- **Grok via `grok` CLI** (preferred over OpenRouter, which if
  used must carry `"provider": {"data_collection": "deny"}`): `timeout 900 grok
  -m <grok-model-id> --permission-mode plan --disable-web-search --no-subagents
  --disallowed-tools run_terminal_command --output-format plain --prompt-file
  <prompt>.md < /dev/null`, run from a directory holding only the screenshots
  and the prompt; the prompt's first line asks it to inspect each listed image
  with its file tool. Verify `git status` afterwards because `grok` plan mode
  does not hard-block edit tools on all versions.

Reviewer personas written in character and asked whether anything feels annoying
or over-styled are an effective alternative to generic lenses when a page has
too much ceremony rather than too little; see
[design patterns, DP-001](ui_ux_design_patterns.md#dp-001-never-put-a-marketing-hero-on-an-internal-page).
