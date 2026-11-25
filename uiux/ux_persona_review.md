# Optional Persona Review of Screenshots

This guide covers running in-character user persona reviews during UI/UX design
workflows and LCA visual polish loops.

Persona review is optional. Many designs move fast and skip it. When a page risks
drifting into internal jargon or decorative clutter, in-character persona
critique catches friction early at near-zero cost.

A project's reference personas live in that project's own `docs/ux_personas/`,
indexed by its `README.md`, with one subfolder per user group and
`_template.md` as the one-page shape. Follow the project's README to choose
personas; do not assume particular persona file names. Where the index offers
personas for a specific domain or workflow context, use the relevant set.

Paste the whole persona file as the reviewer's system prompt, followed by the
review ask using the shared instructions in
[ui_screenshot_review.md](ui_screenshot_review.md). Supply full-size screenshots
(at most 5 images per reviewer call, never contact sheets) and the relevant user
stories as that guide describes. Keep the persona's in-character, no-fixes
instruction in force when using the shared ask.

Use the validated headless routes in
[Gemini and Grok as screenshot reviewers (validated 2026-10-19)](low_risk_ux_enhancements_loop.md#gemini-and-grok-as-screenshot-reviewers-validated-2026-10-19).
That section gives the image-reading instructions and invocation details for
each route.

Critics stay in character. They report the experience and the why from the
user's chair, naming the exact moment attention or trust was lost. They do
not propose fixes or design the solution. Ask what felt annoying or
unnecessarily fancy and which element caused it, as described in
[design patterns, DP-001](ui_ux_design_patterns.md#dp-001-never-put-a-marketing-hero-on-an-internal-page).

Put what the personas said in the review card's notes like any other note,
using the generator's existing `note_html` and `details_html` fields per
[ui_review_format.md](ui_review_format.md). There is no separate persona field,
manifest change, or generator change.

Never show a model or vendor name on a product page or to an end user. Any
drafting metadata in a persona file is for maintainers only.
