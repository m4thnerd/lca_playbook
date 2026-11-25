# Engineer Architecture Visuals

A repeatable, agent-agnostic skill for turning an unfamiliar codebase into a
small set of dense infographic posters that give a senior software engineer, at
a glance, deep ground-truth understanding of the system without reading every
file first.

Proven on multi-service production codebases using four parallel research agents
in ~4 hours wall clock, surfacing doc-vs-code divergences alongside topology and
review-lane posture.

## When to use

- Meeting a codebase you have never read (onboarding, consulting engagement,
  technical due diligence, inherited system, or agent-built services where you
  want a rapid ground-truth map).
- Refreshing a team's shared mental model after a major refactor wave.

## Audience dial (what makes this ENGINEER-facing)

Maximum signal; never shy away from real system complexity. If a nuance would
make a senior engineer say "good to know", it belongs on the poster or in its
companion spec. Do not oversimplify into generic marketing boxes; the practical
ceiling is rendered text legibility, not the reader's appetite.

## The standard suite

Adapt to the repository, defaulting to up to four posters. Each poster must
answer one **central question** whose verdict shapes how an engineer approaches
future changes:

1. **Backend**: modules, dependencies, review-lane classification, topology.
   Central question: *hub-and-spoke or constellation?* If code lives in one
   monolithic app/package, decompose it into its real internal domains (cluster
   models, view families, services, commands); framework app lists are often a
   facade. Include scale cues (LOC/model counts) so box size reflects gravity.
2. **Frontend**: pages, routing, components, composables/hooks.
   Central question: *where does state live?* (global store vs component-local
   vs URL vs server-fetch-per-page vs cache layer). Map which pages consume
   which API families, plus sharp edges (god components, duplicated fetch
   skeletons, hand-mirrored types).
3. **Full stack**: HTTP (or RPC/queue) surface and data flow.
   Central question: *one fat payload or a constellation of per-page endpoints?*
   Group endpoints into families with auth mechanism per family; map page to
   endpoint; distinguish browser surfaces from machine/agent surfaces.
4. **System boundary** (only when there is a sibling repo, sister service, or
   control-plane / execution-plane split). Central question: *what belongs on
   which side, and through which documented seams?* Read both codebases; docs
   describe intent, while code reveals who actually calls what and with which
   credentials.

## Where outputs live

Default: `local/engineer_visuals/` inside the target repository when a
gitignored `local/` directory exists. If there is no gitignored scratch area,
ask the human owner where outputs should go before writing; never commit
generated posters into a repository unprompted.

Layout:

```text
local/engineer_visuals/
  README.md            # master plan: visual list, briefs, shared visual language,
                       # medium + prompt-craft rules, iteration log
  specs/NN_name.md     # one per visual: findings + verbatim PROMPT block
  codex/NN_name.png    # render per engine so engines can be compared
  gemini/NN_name.png
```

## Orchestration (the LCA pattern)

1. **Orchestrator writes the master `README.md` first**: the shared visual
   language and briefs bind all research agents; write them before spawning
   workers.
2. **One research agent per visual, run in parallel.** Each agent:
   - reads the master `README.md`, then the repo's docs tree for *intent*;
   - establishes **ground truth in code** (where docs and code disagree, the
     poster shows code truth and footnotes the divergence);
   - writes its `specs/NN_name.md` file (exclusive write ownership; read sibling
     specs freely for cross-visual consistency);
   - generates, verifies, and logs the renders.
3. Ensure research agents wait for long image-generation calls to finish rather
   than ending their turn early.
4. **Final orchestrator pass**: deliver renders as they land, synthesize
   cross-cutting findings (independent agents converging on the same sharp edge
   is high-signal), and update the iteration log.

### Research quality bar (non-negotiable)

- **Extract names programmatically**: endpoint paths from router/URLconf scripts,
  page names from directory listings, store names from `grep`. Never hand-type
  an identifier into a prompt; hand-typing is how a poster lies.
- Verify every module, page, and endpoint name letter-for-letter against source
  before it enters the `PROMPT` block.
- Classify modules into review lanes per
  [module_charters.md](../architecture/module_charters.md) and
  [module_charters_full_spec_lane.md](../architecture/module_charters_full_spec_lane.md)
  (`critical`, `careful`, `full-spec`, `fast`); flag genuinely ambiguous ones
  rather than forcing a lane.
- State a clear verdict on the visual's central question in the spec's opening
  section, and record docs-vs-code divergences in a dedicated section.

## Shared visual language (binding across the suite)

- **Style register**: dense modern technical infographic (dark slate
  blueprint/forensic-poster aesthetic, 16:9 landscape, 6-9 numbered zones around
  a central topology diagram, side callout boxes for nuances, legend, crisp
  sans-serif labels, upright monospace paths/identifiers).
- **Lane colors**: critical = red `#dc2626`, careful = amber `#d97706`,
  full-spec = blue `#2563eb`, fast = green `#16a34a`, unclassifiable/infra =
  slate. Include the legend on every poster.
- **Edges**: external services get dashed borders; solid edge = synchronous
  call/import, dashed edge = async/batch/queue; **label every edge with its
  mechanism** (`HTTP POST`, `FK`, `CLI command`, `webhook + header`,
  `presigned URL`).
- **Verification stamp**: `Verified against code @ <git short sha>, <date>`.

## Medium: AI image generation

Modern agentic image generation renders dense technical text reliably when
prompted with discipline:

- **Self-contained verbatim `PROMPT` block**: enumerate *every* rendered text
  string verbatim (titles, zone headings, module/endpoint labels, callouts,
  legend, stamp). Anything left unenumerated invites hallucinated text.
- **Density ceiling**: 6-9 numbered zones + legend + callouts; put the full
  endpoint inventory in the companion `specs/NN_name.md` file.
- **Guards**: include "leave incidental surfaces blank" and "upright monospace;
  do not render prompt meta-labels (`TITLE:`, `STAMP:`) as literal text".
- **Letter-by-letter verification**: delegate an un-anchored full-resolution
  visual QA check (`<= 5` images per reviewer call, cropping dense zones if
  needed) to verify every title, identifier, and digit; version retries (`_v1`,
  `_v2`) so a retry never overwrites an earlier cleaner render.

### Headless CLI engine notes

- **Codex CLI headless** (`codex exec --sandbox workspace-write
  --skip-git-repo-check`, prompt piped to stdin asking to generate and save
  `<name>.png` in cwd): strong text fidelity via self-verification; verify only
  after the process exits because intermediate renders overwrite the file.
- **Gemini image generation via `agy` CLI**: invoke `agy --mode accept-edits
  --print-timeout 10m --print="<prompt>"` beginning with *"Please use your
  generate_image tool to create this image natively. Do not use terminal
  commands, Python, or external APIs. After generating, state the absolute path
  of the saved file."* Copy the saved image from stdout into
  `local/engineer_visuals/gemini/` as `_v1`, `_v2`, etc.

## Spec file template (`specs/NN_name.md`)

1. Headline verdict on the central question
2. Ground-truth findings (zoom-in companion inventory)
3. Docs-vs-code divergences
4. Sharp edges footnoted on the visual
5. Poster design rationale (zone layout, what was cut and why)
6. `PROMPT` block (self-contained, all rendered text verbatim)
7. Iteration levers (what to cut first if too dense / what to never cut)
8. Generation + verification log (attempts, garbles found, retries, engine verdict)
9. Verification stamp (`git short sha` + date)
