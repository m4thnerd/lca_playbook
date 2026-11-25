# Review-Page Manifest Schema

The contract between `build_review_page.py` and the agent writing the content.
The generator owns layout, CSS, the collapsible option panels, the tag filter,
and the lightbox. The manifest owns every word and every image path. Extra keys
are ignored. A missing required key fails the build and names the item id.
The guide to using it is [ui_review_format.md](../ui_review_format.md); a
working example is [example/manifest.json](example/manifest.json).

```json
{
  "title": "Morning report - plain-UI redesign, 2026-10-20",
  "subtitle": "What was built overnight, what needs a decision, and what each option looks like",
  "generated": "2026-10-20 13:10 UTC",
  "source": {"branch": "night/2026-10-19-plain-ui", "commit": "0000000", "pr": "https://github.com/owner/repo/pull/41"},
  "legend_html": "<p>optional one-paragraph legend: how to read the cards</p>",
  "sections": [
    {
      "id": "decisions",
      "heading": "Decisions waiting",
      "intro_html": "<p>optional</p>",
      "items": [
        {
          "id": "PE-1",
          "title": "Onboarding pre-ticks 'send weekly summary emails'",
          "status": "built round 2 (at the head)",
          "tags": ["customer", "policy exploration", "built round 1"],
          "summary_html": "<p>One to three plain sentences: what the page does now, what it did before, who asked, why it matters. No ids, no file names.</p>",
          "ask": "Keep it? A (keep) · B (back to no preselection) · neither",
          "score": 2,
          "score_note": "optional one line: why this score",
          "options": [
            {
              "label": "A",
              "title": "Pre-ticked, behind a link (round 2 onward)",
              "note_html": "<p>optional one line under the images</p>",
              "images": [
                {"src": "screens/onboarding-r2-desktop.jpg", "caption": "Onboarding, desktop, round 2", "kind": "desktop"},
                {"src": "screens/onboarding-r2-phone.jpg", "caption": "Onboarding, phone, round 2", "kind": "phone"}
              ]
            },
            {"label": "B", "title": "No preselection (round 0)",
             "images": [{"src": "screens/onboarding-r0-desktop.jpg", "caption": "Onboarding, desktop, round 0", "kind": "desktop"}]},
            {"label": "neither", "title": "Something else; say what in the reply"}
          ],
          "details_html": "<p>Collapsed by default. Technical detail, policy references, commit ids, test names. May be long.</p>",
          "links": [{"text": "PE-1 in policy-explorations.md", "href": "policy-explorations.md#pe-1"}],
          "lavish_revision": "r2"
        }
      ]
    }
  ],
  "lavish_revisions": [{"id": "r2", "label": "Round 2 wording"}]
}
```

## Required keys

- Page: `title`, `sections`.
- Section: `id`, `heading`, `items`.
- Item: `id`, `title`, `summary_html`, `ask`. `ask` may be the empty
  string for an item that only reports a change; the ask box is then omitted.
- Option: `label`, `title`.
- Image: `src`, `caption`, `kind`.

Everything else is optional: `subtitle`, `generated`, `source`, `legend_html`
(a default reading guide is used when absent), `owner_labels`, `intro_html`,
`status`, `owner`, `tags`, `score`, `score_note`, `options`, `images`,
`note_html`, `details_html`, `links`.

## Field rules

- `owner` (optional) renders a role badge when set (`either`, `product`, or
  `engineering` by default, customizable via top-level `owner_labels`). Omit
  `owner` when role badges are unnecessary.
- `tags` are short free strings. They render as pills, and the filter bar is
  built from the set of all tags on the page. A filter shows items carrying any
  selected tag.
- `options` may be empty (an item with no visual, such as a tour note). One
  option is a plain "what it looks like now" card. `label` is `A`, `B`, `C`,
  `neither`, or `before` / `after` / `now`. `title` always says which round or
  state the images come from. An option may have no images (a "neither" choice).
- `images[].src` is a path relative to the output HTML file's directory.
  Absolute paths, `file://`, `http(s)://`, and `data:` are rejected. Only
  `.jpg`, `.jpeg`, and `.png` are accepted. A missing file is an error naming
  the item, the option, the image, and the resolved path; the page is not
  written.
- `kind` is `desktop` or `phone`. Desktop images are shown at most 560 px wide
  and phone images at most 260 px, never wider than the file itself.
- An image whose bytes are identical to one in an earlier option of the same
  item gets a "no change: same image as <label>" note automatically.
- `summary_html` and `ask` are the only things a reader must read. Everything
  in `details_html` is optional.
- All `*_html` fields are trusted fragments written by the content agent and are
  inserted as is. Plain-text fields are escaped.
- `lavish_revisions` (any JSON) is emitted as
  `<script type="application/json" data-lavish-revisions>`, and an item's
  `lavish_revision` becomes `data-lavish-revision` on its card. Both are optional
  and change nothing when the page is opened directly in a browser.
