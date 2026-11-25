# Agentic PM User Story Preflight

This guide defines a second, separate preflight for user stories when AI agents
are actors or operators in the workflow. It does not replace
[user_story_preflight_scoring.md](user_story_preflight_scoring.md), which
checks language, source, and scope. This preflight challenges delivery: for
each story, can a capable agent deliver the value with no bespoke software, or
with one thin piece of wiring, instead of the system the story's wording
implies?

Read [agentic_delivery_foundations.md](agentic_delivery_foundations.md) before
scoring, and score using
[agentic_architecture_pressure_scoring.md](agentic_architecture_pressure_scoring.md).

## Core Question

> For each story, what is the smallest thing that must exist in software for
> a capable agent to deliver this value, and could the answer be nothing?

## When To Run

- After the language preflight has passed, or alongside story brainstorming
  with the product owner when the set is still forming.
- Before Essential Requirements are drafted. Stories reclassified here should
  not generate ERs for machinery they no longer need.
- Again whenever a design's ER count or a `convergence-review` loop grows
  without new product value. Bloat often means a story was read as Software
  when it was Agentic.

It is cheap. It reads docs, not code, except to confirm that an access path
the agentic reading depends on already exists.

## Inputs

- the current story set, in-scope and deferred
- the design doc draft and any ER draft
- the relevant module charters and operating conditions (`case-studies/local/operating-conditions.md` when present)
- the foundations guide's lists of what agents deliver for free and what still needs software

## The Challenge, Per Story

Ask these in order. Stop at the first answer that settles the mode:

1. **Could the owner or an operator ask an agent for this in one sentence and
   get it?** If yes and nothing below applies, the story is Agentic.
2. **Does the behavior need to exist when no agent is running?** If yes,
   Software or Hybrid.
3. **Does it cross an authority boundary** (credentials, production writes,
   kill switch, audit)? If yes, that boundary is the Software remainder; the
   rest stays agentic.
4. **Must several agents, systems, or humans query the same facts
   deterministically over time,** beyond what a notes file or an existing field
   can carry? If yes, that state is the remainder.
5. **Is the data already reachable?** If not, the remainder is the thinnest
   exposure of that data, not the feature that consumes it.
6. **Does the story bundle the product outcome with its mechanism?** Rewrite
   to the outcome. "Automatically", "pipeline", "dashboard", "classifier",
   "index", "scheduler", "queue", "config", and "admin UI" are the usual
   smuggled mechanisms.
7. **Is it automating before it has been dogfooded?** A scheduled or
   background version of a task that has never run on demand is premature.
   Demote it to on-demand agentic delivery and let the cadence emerge.

## Scoring Model

Score each story independently.

| Dimension | Values | Meaning |
|---|---|---|
| Naive Reading | 0-5 | Architecture Pressure the story's wording implies under a bespoke-software reading. |
| Delivery Mode | Agentic / Hybrid / Software | The mode the remainder question supports. |
| Software Remainder | phrase or `none` | What must exist in code. For Hybrid, the wiring shape. |
| Software Signal | named condition or `n/a` | Which "still needs software" condition justifies the remainder. |
| Agentic Pressure | 0-5 | Pressure of the remainder only. |
| Disposition | Keep / Rewrite / Fold / Defer | Keep as written; rewrite to the outcome; fold into an instruction (playbook line, not a story); defer. |

A Software mode without a Software Signal is not allowed. An Agentic mode
with any ER attached is a finding.

## Dispositions

- **Keep:** wording already states the outcome and the mode is clear.
- **Rewrite:** the story smuggles a mechanism. Rewrite to the stakeholder
  outcome and let the mode fall out:

  ```text
  Before: As an operator, I want a scheduled weekly capture pipeline that
  snapshots every UI component into an image database with a search index.
  After:  As an operator, I want an up-to-date UI catalog I can ask an agent
  to refresh and search, so that product reasoning stays grounded in the real
  interface.
  Mode: Hybrid. Remainder: well-known Git location + minimal read-only guide
  app for search. Naive 4 -> Agentic 1.
  ```

- **Fold:** the story describes something an agent will simply do when asked
  or when following an existing playbook. It becomes a line in the
  instruction surface, not a story and not an ER.
- **Defer:** value is real but depends on an access path or authority
  boundary that is itself deferred.

## Recommended Output Format

```text
| Story | Naive | Mode | Software Remainder | Signal | Agentic | Disposition | Note |
|---|---:|---|---|---|---:|---|---|
| US-1 short label | 4 | Agentic | none | n/a | 0 | Fold | Agent runs it on request; one playbook line. |
| US-2 short label | 4 | Hybrid | read-only export of X | reachability | 1 | Rewrite | Drop "pipeline"; expose the data. |
| US-3 short label | 3 | Software | idempotent event intake | runs without agent | 3 | Keep | Legitimate remainder. |

Naive total: 11. Agentic total: 4. Simplification headroom: -7.
```

Then list only:

- story rewrites, with before and after text
- stories folded into instruction surface, naming the file
- the software remainder list: every thin piece of wiring, deduplicated
- stories that stay Software, each with its signal
- open product judgments for the human owner, where the mode depends on an
  operating condition only they can confirm

## Readiness Standard

Before ERs are drafted:

- every in-scope story has a Delivery Mode, a Software Remainder, and, for
  Hybrid or Software, a named Software Signal
- no Agentic story is a source for any ER; a Hybrid story is a source only
  for ERs about its named remainder
- every rewritten story has re-passed
  [user_story_preflight_scoring.md](user_story_preflight_scoring.md)
- the naive and agentic totals are reported with the headroom
- the software remainder list is the only thing ERs may describe
- the instruction surface that carries the agentic work is named

Run sequential iterations: review, revise, review again if the story set or
the modes materially changed. Do not run concurrent passes on the same draft.

## Guardrail

This preflight removes unnecessary machinery; it does not remove safeguards that
an operating condition actually requires. When a mode depends on an unverified
condition (who operates it, how often, whether a session will be running),
state the assumption explicitly and ask the human owner to confirm it rather
than choosing the heaviest software mode by default.
