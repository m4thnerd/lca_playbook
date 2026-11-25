# UI/UX Screenshot Review Process

A repeatable process for evaluating the UI/UX of a page or component view
across the full range of states a real user will encounter. Combines
scenario-driven screenshot capture with multi-reviewer scoring against the
page's own user stories, plus open-ended un-anchored visual feedback.

Screenshots from this process feed the reviewable HTML pages built per
[ui_review_format.md](ui_review_format.md) whenever a human must see or decide
a UI change.

The process is designed for pages whose visual feel changes meaningfully
depending on user state (first-time users, free-tier users, paid users, power
users on their hundredth visit, users hitting edge cases) where a single "happy
path" screenshot does not represent the experience.

A formal generic UI/UX rubric is intentionally **not** part of this process.
See [Intentionally deferred: formal UI/UX rubric](#intentionally-deferred-formal-uiux-rubric)
at the bottom for rationale.

## When to use this process

Run a screenshot review when:

- A new page or major component view is approaching feature-complete and you
  want a structured pre-ship review.
- An existing page has accumulated changes and you want to confirm it still
  holds up across all user scenarios.
- You suspect the page reads differently than intended for a specific user
  segment (new vs returning, free vs paid, etc.).

Do **not** run this process for:

- Small, scoped UI tweaks (a button color change, a copy edit). Screenshot
  reviews are expensive in reviewer time; reserve them for surfaces where
  scenario coverage is the actual question.
- Pages where behavior, not appearance, is the open question. Run behavioral
  tests instead.

## Inputs required

Before starting Phase 1, you need:

1. **The page's user stories**, typically in the page's design doc under a
   `## User Stories` heading. These drive scenario enumeration and are the
   scoring axis used in Phase 2.
2. **A way to render the page in each scenario**, typically by editing the
   page's frontend fixtures or mock state locally. Phase 1 cannot begin until
   fixture-driven scenario rendering works locally.
3. **A browser-automation path that produces files on disk.** See
   [Capture tooling notes](#capture-tooling-notes).

## Phase 1: Scenario sweep

**Deliverable:** a directory of named screenshots covering every identified
scenario in both desktop and mobile form factors.

### Step 1a: Enumerate scenarios from user stories

Working from the page's user stories, list every distinct user state worth
testing. A scenario is worth its own screenshot when at least one of these
changes between it and the closest existing scenario:

- The user's progression stage on the page's primary axis (for example zero
  progress vs partial vs crossing a milestone).
- The user's account tier or entitlement (free vs paid).
- The availability of resources the page depends on (items remaining, items on
  cooldown, zero items of a given type).
- The presence or absence of an optional UI region.

Add each scenario to the page's design doc under a **Scenario backlog** section,
with a one-line description of what the scenario stresses.

### Step 1b: Add edge-case scenarios

User stories describe happy paths; edge cases live in the gaps between them:

- **Boundary states**: `0`, `1`, and "many" of each variable quantity.
- **Approaching transitions**: just below a threshold, at it, and just above.
- **Exhaustion states**: every available item completed, free-tier quota
  exhausted, or every item on cooldown.
- **Absent optional regions**: rendered for a context lacking optional cards or
  affordances.
- **Extremes that test layout**: longest realistic label, largest realistic
  list, smallest realistic dataset.

### Coupled-mock-state discipline

Most pages render from at least two mock surfaces (for example a dynamic
per-page fixture plus global mock database counts). **A scenario that updates
only one of them produces a screenshot that visibly contradicts itself**, which
reviewers flag as implementation bugs rather than mock-state bugs (for example a
left column saying "Take your first quiz!" beside a right column showing "32
questions completed").

**Rule:** before capturing, enumerate every mock-state source the page reads
from, and write the scenario's data state for *all* of them in the capture
script.

### Step 1c: Capture screenshots

For each scenario:

1. Modify all coupled mock-state sources to render that scenario and reload the
   page.
2. **Desktop capture: one image per scenario, tall enough to fit the whole page
   in a single viewport** (1280px width default, bumping viewport height until
   full content fits without clipping). If above-the-fold framing is itself
   under review, add a single real-aspect viewport capture for that scenario.
3. **Mobile capture: same tall-viewport principle at a realistic mobile width**
   (for example 375px). When above-the-fold scroll pressure is under review,
   either draw the fold line on the capture or include a viewport-height
   first-screen image.
4. **Capture dark theme selectively**, not 1:1 across every scenario: capture
   light for every scenario, identify theme-sensitive components (dark overrides,
   contrast hazards, badges, banners, gradients), and pick the 2-3 scenarios
   whose dark captures exercise every theme-sensitive component at least once.

#### File naming convention

```text
{page-slug}__{scenario-id}__{form-factor}[__{theme}].png
```

Store screenshots under `local/screenshots/{page-slug}/` (gitignored).

## Phase 2: Multi-reviewer scoring and visual QA discipline

**Deliverable:** raw scores and open-ended feedback from at least 3 diverse
reviewers (different frontier models or distinct user/framing personas).

### Visual QA prompting discipline (anti-anchoring rules)

Empirical A/B testing across visual QA sessions established four hard rules for
prompting image and screenshot reviewers:

1. **Ask for an unprompted general review; never list specific defects to look
   for.** Giving a model a checklist of visual defect categories (or even "look
   for issues including, but not limited to: ...") narrows its search to those
   examples and causes it to pass blatant visual defects outside the list. Give
   at most one general sentence about what the page is meant to show and ask it
   to report anything wrong, odd, inconsistent, confusing, or unconvincing.
2. **Full-size images only, never contact sheets, and at most 5 images per
   reviewer session.** Contact-sheet thumbnails hide layout, text, and anatomy
   defects, and sending dozens of screenshots in one call spreads reviewer
   attention thin so obvious defects get rationalized away. Split larger sweeps
   into batches of `<= 5` full-size images per fresh independent reviewer call.
3. **Coordinators never open screenshot batches in their own context.** The LCA
   delegates visual inspection to fresh independent reviewer sessions with no
   author reasoning in context.
4. **Never fix a slipped defect by adding it to a checklist.** When a visual bug
   slips past review, check whether the reviewer could see it (full resolution,
   `<= 5` images per call, final rendered composite) and whether the prompt
   stayed un-anchored rather than checking items off against a detailed
   description.

### What each reviewer receives

1. A batch of at most 5 full-size screenshots.
2. When scoring story fit, the page's user stories lifted verbatim from the
   design doc (never the full design doc, whose rationale and implementation
   notes pull reviewers away from visual judgment). For pure visual defect QA,
   run the un-anchored open review first before any story-match check.
3. The reviewer prompt template below.

### Reviewer prompt template

```text
You are reviewing full-size screenshots of a page in our application. Do not run
shell commands or edit files; inspect each listed image file directly at full
size and answer in text.

For each screenshot, produce:

1. Open visual review: tell me anything that looks wrong, broken, odd,
   inconsistent, cluttered, or confusing in what a real user sees, judged by
   common sense.

2. User-story scores (1-5 per user story, or N/A): how effectively does the
   screenshot serve each listed user story? Mark N/A when the story does not
   apply to the scenario depicted. For every score below 5, include one short
   sentence naming the specific gap.

Output your review screenshot by screenshot. Do not output overall page-level
averages.
```

## Phase 2 postprocessing: Consolidation

Build a single Markdown consolidation table with one row per screenshot:

- **Scenario**: short label.
- **User-story scores**: one column per user story showing raw per-reviewer
  scores as `R1/R2/R3` (for example `4/3/4`). Never collapse to averages; raw
  triples surface `5/2/4` disagreements immediately.
- **Top findings / suggestions**: up to three deduplicated items ranked by
  reviewer convergence.

When reviewers disagree:

- **Two-vs-one score split**: inspect via a targeted check; dissenters often
  catch real layout or state defects.
- **Contradictory suggestions** ("make the banner louder" vs "banner is too
  aggressive"): resolve against the page's user stories, and record settled
  panel/visibility choices so later rounds do not oscillate.
- **Out-of-scope suggestions**: record in a short **pruning log** with the
  reason so they do not re-emerge in later iterations.

## Iteration loop

1. Resolve contradictions and pick the highest-impact fixes addressing low
   user-story scores or blatant visual defects.
2. Implement those changes.
3. Re-capture affected scenarios (full-size) and re-run reviewers on batches of
   `<= 5` images.
4. Stop when the lowest user-story score reaches 4 across reviewers or marginal
   suggestions stop being load-bearing (typically 2-3 iterations).

## Capture tooling notes

- **Produce real files on disk:** Use a small `puppeteer-core` script driving
  system Chrome (`executablePath`, `defaultViewport` set to width x tall-height,
  `page.waitForSelector('<stable data-test marker>')`,
  `page.screenshot({ path, fullPage: false })`). Avoid Chrome's standalone
  `--headless --screenshot` CLI flag on SPAs, and avoid inline-only browser
  tools that do not write files.
- **Dev server HTTPS + self-signed certs:** Prefer plain HTTP on localhost
  (`DEVSERVER_HTTPS=false`) during capture runs to avoid headless cert-verifier
  errors.
- **Mock state prep:** Pre-populate onboarding/modal dismissal flags in mock
  data rather than clicking through modals at capture time; back up mutable
  fixture files and restore them in a `finally` block; restart mock servers that
  cache JSON in memory at startup; terminate child servers on exit.
- **Capture sweeps are exclusive:** Never run two fixture-mutating capture
  sweeps concurrently against the same checkout and ports; they silently
  overwrite each other's mock state mid-capture.
- **Sanity-check captures before fan-out:** Delegate a quick visual sanity check
  on one desktop and one mobile capture before launching the full reviewer panel
  to catch blank renders, broken asset URLs, or unserved icon fonts (such as
  worktree symlink allowlist issues, where a server-only `DEV_` allowlist env
  var should be used rather than client-exposed `VITE_*` vars).
- **SPAs with internal scroll containers:** Because `fullPage: true` does not
  expand inner scroll containers (such as fixed-height `<div class="inner-scroll-pane">`
  panels), setting a tall viewport height in Step 1c is the reliable default.

## Intentionally deferred: formal UI/UX rubric

An earlier draft scored every screenshot 1-5 across six generic SaaS rubric
categories. It was removed because:

- Un-anchored open visual review surfaces obvious layout, copy, and hierarchy
  defects without anchoring models on a narrow checklist.
- Multi-category rubrics double the surface area reviewers feel obligated to
  invent nitpicks in, driving unproductive iteration churn (the same dynamic
  documented in
  [convergence_review_essential_requirements.md](../requirements/convergence_review_essential_requirements.md)).
- If a domain rubric is ever added inside a product repo, keep dimensions broad
  and tailored to that product's UX principles rather than generic checklists.
