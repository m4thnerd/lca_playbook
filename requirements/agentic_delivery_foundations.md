# Agentic Delivery Foundations

This guide corrects one of the most expensive blind spots in agent-written
designs: assuming that a user story needs bespoke software when a capable AI
agent, given access to the right context, already delivers it.

It is upstream of
[agentic_architecture_pressure_scoring.md](agentic_architecture_pressure_scoring.md)
and
[agentic_pm_user_story_preflight.md](agentic_pm_user_story_preflight.md).
Read it before either.

## Core Question

> What does this story need that a capable agent session, with access to the
> right context, cannot already do? Only that remainder is software.

## The Blind Spot

Pretraining-era software intuition assumes software does the work and humans
operate it. Under that model every capability needs a mechanism: a pipeline to
ingest, a table to hold, a classifier to label, a dashboard to show, a
scheduler to run, a config system to tune, an admin UI to operate.

In an agent-assisted organization the operator is itself a capable reader,
analyst, classifier, writer, and coder working orders of magnitude faster than
human read speed. Many of those mechanisms now exist only to replace an
intelligence that is already present in the session. Agents still propose them
by reflex because pretraining assumes software must perform every cognitive step
at runtime. That shows up as requirements bloat: pages of Essential Requirements
describing machinery whose only job is to do what an agent would do by being
asked.

The corrective first question is not "what tables, endpoints, and jobs must
exist for the software to do this?" but "if an agent starts a session with the
relevant context today, what stops it from just doing this?"

**[Observed]** On a 143-story internal agent-workspace backlog, a naive
bespoke-software reading scored roughly 850 total Architecture Pressure points;
on reclassification, roughly 50-60% of the stories carried pressure 0 because
an informed agent delivers them outright, and most of the rest became thin
hybrids.

## The Three Delivery Modes

Every user story resolves into one of three delivery modes.

| Mode | Meaning | Typical Architecture Pressure |
|---|---|---|
| **Agentic** | A capable agent with access to the relevant context delivers the whole story on request or on its own cadence. No bespoke code, schema, or UI is retained. The durable artifact, if any, is plain-English instructions. | 0 |
| **Hybrid** | The agent delivers most of the value (typically 80-90%), while one thin piece of wiring must exist: data made reachable, a place to write, a credential boundary, or a trigger. | 1-2 |
| **Software** | The behavior must exist as code because of a condition an agent session cannot satisfy (see below). Score with the standard rubric. | 1-5 |

The classification is per story, and it is a product and architecture
judgment, not a language check. A story's wording often implies Software
("the system automatically generates a weekly report") when its value is
Agentic ("an operator can ask for the report and get it").

## What Agents Deliver For Free

Treat the following as already available in any session with context access.
A story that only needs these is Agentic:

- reading any volume of documents, logs, code, tickets, threads, or data
- classifying, triaging, ranking, and labeling items
- summarizing, drafting, rewriting, and reporting in any format
- cross-system lookup when read access already exists
- ad-hoc analysis and on-demand visualization
- writing results into an existing text, JSON, or notes field
- following a plain-English playbook, including multi-step procedures
- deciding when a step is not needed, and saying so
- investigating and fixing a defect through the normal LCA delegation path
- keeping its own working notes in a well-known file location

## What Still Needs Software

A story earns the Software or Hybrid mode only when at least one of these
holds. Name which one:

- **Runs without an agent.** The behavior must happen when no session is
  running: a customer-facing request path, a hard real-time trigger, or a
  guarantee that cannot wait for an agent to be invoked.
- **Authority boundary.** Credentials, write permissions to production,
  kill switches, or audit records must be enforced outside the agent so that a
  compromised or mistaken agent cannot bypass them.
- **Shared durable state.** Multiple agents, systems, or humans must query the
  same facts deterministically over time, and a notes file or existing field
  cannot carry them.
- **Volume, latency, or cost.** The operation runs at a frequency or scale
  where paying for inference each time is wrong, or where a deterministic
  answer is required.
- **External contract.** Another system depends on a stable API, payload,
  event, or schema.
- **Reachability.** The agent cannot currently read or write what it needs.
  This usually yields Hybrid, not Software: expose the data, do not build the
  feature.

If none apply, the story is Agentic, however much its wording sounds like a
system.

## The Hybrid Shape

Hybrid wiring is almost always one of a short list of shapes. Prefer them in
this order:

1. a well-known file or directory location every agent knows
2. an existing text or JSON field on an existing model
3. a read-only endpoint, export, or tool that exposes data already stored
4. an existing feature flag, settings entry, or admin pattern
5. a minimal write path behind an existing authorization boundary

A Hybrid story whose wiring is not on this list probably hides a Software story
or an unexamined assumption. Make it explicit.

## Worked Examples

Each example records the naive reading and the delivered mode:

- **UI catalog.** Naive: capture daemon, image database, weekly scheduler,
  generated guide, agent retrieval index (pressure 4). Delivered: capture
  instructions plus curated fixtures in a well-known Git location, snapshots on
  demand; the only software is a minimal read-only guide app that serves search
  (Hybrid, pressure 1-2).
- **Bounded local workspace.** Naive: a local tool catalog and a policy
  platform. Delivered: expose approved source roots and one role workspace;
  the agent does the investigation (Hybrid, pressure 1).
- **Tool inventory.** Naive: a speculative 100-tool catalog before dogfood.
  Delivered: inventory tools incrementally as each slice needs them (Agentic,
  pressure 0).
- **Reconnaissance stories.** Naive: runtime features. Delivered: substantially
  satisfied by agent reconnaissance passes before implementation began (Agentic,
  pressure 0).
- **Agent working state.** Naive: new columns, enums, or a state table to hold
  an agent's classifications, intermediate notes, and handoffs (pressure 3).
  Delivered: the agent writes structured text into an existing text field or a
  `notes/<id>.md` file that any other agent can read (Agentic, pressure 0).
- **Session dashboard prototype.** Naive: web app, session table, annotation
  model, per-model comment schema, admin. Delivered: one Python script listing
  pinned sessions, headless CLI calls for briefs, and shared agent notes as
  `notes/<id>.md` Markdown files that any model appends to (Hybrid, pressure 1).
- **Admin bulk-grant button.** Naive: concurrency locking across three modules
  against simultaneous operators. Delivered: a plain write; one human operates
  it, rarely (Software, pressure 1).

What the examples share: the agent was not short on capability; it was short on
the operating context showing that the condition it was engineering for does not
exist.

## Counter-Blind Spot

Do not over-rotate. Agentic delivery has real costs: non-determinism, inference
cost per run, latency, dependence on context access, and no guarantee while no
session runs. Customer-facing product behavior at scale, authority boundaries,
and contracts other systems depend on stay Software. Promote an agentic or
hybrid delivery to heavier software only when a named signal applies or when
the agentic delivery was dogfooded and observed to fail, not because software
feels safer.

## Instruction Surface

Agentic delivery moves durable surface from code to instructions: a playbook
section, a prompt file, an `AGENTS.md` note. That surface is not zero; it is
maintained, reviewed by reading, model-agnostic, and cheap to change. Report
it by name so it stays visible, and keep it as lean as the code it replaced.

## Building Durable Knowledge

Designs simplified by applying this model can be recorded in
[`example-case-studies/agentic-simplification/`](../example-case-studies/agentic-simplification/)
(or in your local `case-studies/local/` directory).
