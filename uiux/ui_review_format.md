# UI Review Format: Decisions You Can See

Any change or question that affects what a user sees ships with a reviewable
HTML page. A Markdown report may exist as the record, but the HTML page is what
the human reads.

This exists because a morning report about six UI redesign rounds came back
unactionable: it asked questions about pages the reader could not see. Being
asked about a UI without seeing the UI leaves the reviewer stuck; they cannot
pick option A or option B without seeing both. Every UI question comes with
screenshots of the UI in question, one per option, and supporting detail stays
folded away until someone wants it (except the deliverable that approval acts on,
which must never be hidden when it is the primary thing being judged).

Tools live beside this file:

- [ui_review_format/build_review_page.py](ui_review_format/build_review_page.py)
  turns a JSON manifest into one static HTML page. Python 3.10+, standard
  library only, no network.
- [ui_review_format/manifest_schema.md](ui_review_format/manifest_schema.md)
  is the manifest contract.
- [ui_review_format/example/](ui_review_format/example/) is a two-card example
  you can build and open.

## When this applies

- Any task, branch, or night shift whose result changes a user-facing page.
- Any question to a human about a UI: which variant, keep or revert, whether a
  held proposal is worth building.
- Any morning report that mentions UI work. For a night shift that touched UI,
  the deliverable is `morning-report.html`, built per this document, and the
  Markdown morning report links to it.

It does not apply to changes with no visible effect. Do not invent screenshots
for a pure backend refactor.

## What one card holds

Each item on the page is one card. A reviewer should be able to decide from the
card alone, without opening anything else.

1. **The plain question or change**, as a title a non-engineer understands.
2. **Status**, one line: built and merged, built but not at the head, held,
   mockup only.
3. **Summary**, one to three plain sentences: what the page does now, what it
   did before, who asked, why it matters.
4. **The ask**, in its own box: exactly what reply is wanted, with the choices
   spelled out (`Keep it? A (keep) · B (revert) · neither`). If the card only
   reports a change, there is no ask box.
5. **Score**, if the item came out of a scored review, with one line on why.
6. **Options**, folded by default: one column per option, each with a label,
   a title saying which round or state the images come from, the screenshots
   at the device sizes that matter, and a caption under each image naming the
   page, the device, and the state.
7. **Details**, folded by default: technical background, policy references,
   commit ids, test names, links. Long is fine here; nobody has to read it.

The summary and the ask are the only things a reader must read. Everything
else is there to support a decision, not to be skimmed.

## Choosing the shape of the options

Pick the shape that matches the decision:

- **A / B / neither.** A real choice between alternatives. Show every option,
  including the current page if it is one of them. Add a "neither" option
  without images when "none of these" is a legitimate answer; it keeps the
  reviewer from being cornered.
- **Before / after.** A change already made, shown so the reviewer can object.
  Use the same page, device, and state on both sides so the only difference is
  the change.
- **Now plus mockup.** A held proposal that was not built. Do not describe it in
  prose. Build a throwaway mockup in a scratch worktree, capture it, and throw
  the worktree away. Title the option "mockup, not built". A rough picture
  beats a precise paragraph.
- **Now only.** One option, for "this is what it looks like at the head". Use
  it for tour notes and changes nobody needs to choose between.

An item with no visual at all, such as a process note, may have no options.
Keep those rare on a UI review page.

## Images

**Sources, in order of preference:**

- Screenshots already archived by the round or review that produced the change
  (see [ui_screenshot_review.md](ui_screenshot_review.md)). Reuse them rather
  than re-capturing what you already have.
- A fresh full-page walk of the head of the branch, for the "now" state.
- Mockups captured from a scratch worktree, for held proposals. Never commit
  mockup code to the branch under review.

**Devices.** Show the device sizes that matter for the question. Most pages
need desktop and phone. A phone-only layout change needs only phone images, and
the caption should say so.

**Format and size.**

- JPEG for screenshots, quality around 80. PNG only for small, flat images.
- Capture desktop at up to 1440 px wide and phone at its device pixel width.
  The page shows desktop images at up to 560 px and phone images at up to
  260 px, and the reviewer can click to see the full file.
- Never upsample. Capture at the size you need instead of stretching a small
  image. The generator never displays an image wider than its file.
- Crop very tall full-page captures to the part the question is about, or say
  in the caption that it is the full page.
- Budget: aim for under about 300 KB per image. A page sent with `--inline`
  should stay under about 15 MB; if it exceeds that, cut images, not cards.

**No change.** If an option's image is identical to another option's, say "no
change" rather than showing two identical pictures as if they were a choice.
The generator marks byte-identical images automatically. Reuse the same file
on purpose when nothing changed, so the mark appears.

**Captions.** Every image names the page, the device, and the state:
"Onboarding, phone, round 2". A screenshot without its state is a guess.

Never split a UI review into separate text-only vs technical reports by role:
keep one visual page and use tags (or optional `owner` labels when a multi-lead
team wants them) to filter.

## Building the page

1. Collect the facts and images for each item.
2. Write a manifest per [the schema](ui_review_format/manifest_schema.md).
   Image paths are relative to where the HTML file will live.
3. Build:

   ```bash
   python build_review_page.py manifest.json morning-report.html
   python build_review_page.py manifest.json morning-report-inline.html --inline
   ```

   The script prints one line: items, images, files, and missing files. A
   missing image is an error that names the item and the path, and the page is
   not written. A missing required key fails the build and names the item.
4. Open the page in a browser and check it at desktop width and at phone width
   (about 420 px). Options must stack on the phone and the page must never
   scroll sideways.

The page is one static file: inline CSS, an explicit page background, a light
theme with a dark-mode variant, a sticky table of contents built from the
sections, a tag filter, expand all / collapse all, and click-to-enlarge.
Without `--inline` it references the images by relative path and stays small;
keep it next to its images in the repository. With `--inline` every image is
embedded, so the single file can be attached to a message or opened outside the
repository.

**Vendoring.** Copy `build_review_page.py` into a project's tooling directory
unchanged and keep it byte-identical to the playbook copy. Project-specific
wording belongs in the manifest (`legend_html`, `owner_labels`), not in a
forked script.

## Optional annotation layer: lavish-axi

[lavish-axi](https://github.com/kunchenguid/lavish-axi) opens agent-written
local HTML in a sandboxed frame so a human can point at elements and send
feedback to the agent. Pages built here already follow its conventions: one
self-contained HTML file with an explicit page background, local assets by
relative path next to the file, and no design-system dependency. A manifest may
add `lavish_revisions`, emitted as
`<script type="application/json" data-lavish-revisions>`, and `lavish_revision`
on an item, emitted as `data-lavish-revision="<id>"` on its card, to mark what
changed between versions of the page. This is optional; the page renders
identically when opened directly in any browser.

## What not to do

- **No Markdown-only reports for UI work.** If it changes what a user sees,
  the reader gets pictures.
- **No prose that assumes the reader saw the pages.** "The round-3 treatment
  of the hero" means nothing to someone who was not there. Show it.
- **No goal-condition checklists** in the summary ("Goal 4 met, goal 5
  partially met").
- **No commit ids, file names, or test names in the summary or the ask.** They
  go in Details.
- **No question without its options.** If you cannot show what the choices
  look like, build a mockup or do not ask yet.
- **No unlabeled images.** Every image says which round or state it is from.
- **No hundred-page scroll.** Options and details are folded by default.

## Reading guide

Pages can reuse this paragraph as their legend (`legend_html`). The generator
uses a version of it when no legend is given:

> Each card is one change or one question. Read the summary and the yellow
> box: that is the ask. Open **Options** to see a screenshot of each choice, at
> the device sizes that matter, with the state each image comes from under it;
> click an image to enlarge it. **Details** holds technical background and
> links and is optional.

## Worked example

- Small and synthetic:
  [ui_review_format/example/](ui_review_format/example/). Run
  `python ../build_review_page.py manifest.json example.html` inside it.
- Case study background:
  [ui-vote-tie-and-visual-reporting.md](../example-case-studies/night-shifts/ui-vote-tie-and-visual-reporting.md).

## Related

- [ui_screenshot_review.md](ui_screenshot_review.md): how screenshots are
  captured and scored. Its outputs are the inputs to these pages.
- [low_risk_ux_enhancements_loop.md](low_risk_ux_enhancements_loop.md) and
  [ambitious_ux_competition_loop.md](ambitious_ux_competition_loop.md): loops
  that change UI. Their reports to a human follow this format.
