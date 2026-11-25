# Agentic Architecture Pressure Scoring

This guide is the sister rubric to
[architecture_pressure_scoring.md](architecture_pressure_scoring.md) for
designs in which AI agents are participants in the workflow. It assumes
[agentic_delivery_foundations.md](agentic_delivery_foundations.md).

Use it when an agent (an LCA session, an overnight shift, a role-scoped
management agent, or an operator working through agents) is a stakeholder or an
actor in the stories being scored. Keep using the standard rubric alone for
customer-facing product runtime paths that must behave identically with no
agent present.

The standard rubric's definitions are unchanged. This guide adds a pressure-0
tier, a delivery-mode field, and an Agentic Pressure Delta so that the
simplification headroom in a design becomes a number reviewers can see.

## Core Question

> After the smallest correct implementation has landed, how much of this
> story's durable surface is bespoke software, versus what a capable agent
> session with the right access already provides?

Score the smallest correct implementation under the delivery mode that the
remainder question in the foundations guide actually supports, not the
delivery mode the story's wording implies.

## Scoring Table

| Score | Meaning |
|---|---|
| 0 | No retained bespoke software. The story is delivered by a capable agent through existing access, existing tools, and plain-English instructions. Any durable artifact is instruction text. |
| 1-5 | As defined in [architecture_pressure_scoring.md](architecture_pressure_scoring.md), applied only to the software remainder. |

A score of 0 is not a claim that nothing is maintained. It is a claim that
nothing in the codebase is maintained for this story.

## Required Fields

For each story or ER, report:

- **Delivery Mode:** `Agentic`, `Hybrid`, or `Software`.
- **Software Remainder:** one phrase naming what must exist in code, or
  `none`. For Hybrid, name the wiring shape from the foundations guide.
- **Software Signal:** for Hybrid and Software, which condition from "What
  Still Needs Software" applies. A Software mode with no named signal is a
  scoring error.
- **Agentic Architecture Pressure:** 0-5 for the remainder.
- **Instruction Surface:** the playbook, prompt, or notes file that carries the
  agentic part, or `none`.

## Agentic Pressure Delta

Report the difference between the naive software reading and the agentic
delivery:

```text
agentic-delivery Architecture Pressure - naive-software-reading Architecture Pressure
```

This is the simplification headroom. It is always zero or negative. A design
whose stories sum to a large negative delta had a large bloat exposure; record
it so the pattern becomes visible across designs.

Do not confuse this with the standard Architecture Pressure Delta, which
compares current codebase state with target state for refactors.

## Pressure Reducers Specific To Agentic Delivery

Reduce the remainder when the design:

- lets the agent read the source data instead of building an ingest or sync
  pipeline
- lets the agent write into an existing text or JSON field instead of adding
  schema
- lets the agent render a report or view on demand instead of maintaining a
  dashboard
- lets the agent classify or triage instead of building a classifier service
  or rules engine
- uses a well-known file location instead of a table
- uses the existing harness or scheduled-request capability instead of a
  scheduler
- expresses policy as a plain-English playbook instead of a config system or
  admin UI
- keeps fluid product heuristics in agent instructions instead of encoding
  them as rigid code that must be re-released to change
- runs on demand first, and adds a scheduler or daemon only after on-demand
  invocation has been dogfooded and the cadence is known
- satisfies an investigation, inventory, or reconnaissance story by doing it
  once rather than building a feature that does it repeatedly

## Pressure Raisers To Challenge Before Accepting

Treat these as findings, not scores, until the design justifies them with a
named software signal:

- new columns, enums, or state tables whose only job is to hold an agent's
  classifications, intermediate thoughts, or handoff notes
- a scheduler, daemon, or job queue built before on-demand agent invocation
  has been tried
- validation or formatting logic duplicated in code that the agent, or an
  existing boundary, already handles
- a tool catalog, registry, or policy engine built ahead of the slices that
  would use it

## Pressure Raisers That Remain Legitimate

Keep the remainder, and score it with the standard rubric, when the design:

- must run with no agent present
- enforces an authority boundary: credentials, production writes, kill
  switches, audit
- holds shared durable state that several agents, systems, or humans query
  deterministically over time
- runs at a volume, latency, or cost where per-run inference is wrong
- exposes a contract another system depends on
- must give a deterministic answer

Durable, idempotent inbound event acceptance (recording origin before returning)
and mediated authority (business credentials and external write actions enforced
outside the agent process) are reference examples of remainder that stays
Software on purpose.

## Scoring Discipline

- Score the agentic design honestly: if the agent must re-derive something
  expensive on every run that software would compute once, say so and weigh
  it under volume and cost.
- Do not score instruction text as code pressure, but do name it. An unnamed
  playbook is how agentic surface silently sprawls.
- A story reclassified to Agentic contributes no ERs. If an ER remains, either
  the story is Hybrid or the ER is bloat.
- Report naive and agentic readings side by side. The gap is the finding.

## Output Language

Useful agentic note:

```text
Delivery Mode: Agentic. Software Remainder: none. Software Signal: n/a.
Agentic Architecture Pressure: 0 (naive reading 4, delta -4). Instruction
Surface: playbook section "weekly content health report". The operator asks
for the report; the agent reads the existing analytics tables and renders it.
```

Useful hybrid note:

```text
Delivery Mode: Hybrid. Software Remainder: read-only conversation retrieval
tool behind existing deployment auth. Software Signal: reachability +
authority boundary. Agentic Architecture Pressure: 2 (naive reading 4, delta
-2). Instruction Surface: manager-role playbook. The role does the analysis;
the tool only exposes the conversation.
```

Useful software note:

```text
Delivery Mode: Software. Software Remainder: idempotent inbound event
acceptance with recorded origin. Software Signal: runs without an agent +
external contract. Agentic Architecture Pressure: 3 (naive reading 3, delta
0). Instruction Surface: none.
```

Avoid notes that assign a delivery mode without naming the remainder and the
signal.
