# Design Doc Slicing: Parent Doc + Sequence-Completable Slices

> **Prefer a walkthrough first?** Watch **[Video 5: Overnight Relays, Design Doc Slicing & Engineering Director (`12:12`)](https://m4thnerd.github.io/lca_playbook/#engineering-director-overnight)** in the interactive 1080p player.

This guide defines how the LCA turns a large brainstorm (roughly 15-50 user
stories, far more scope than one design doc can carry) into a parent design doc
plus a sequence of child slice docs. Each slice runs the
[Mandatory Requirements Preflights](../lca_playbook.md#mandatory-requirements-preflights)
and `convergence-review` independently; the parent becomes a thin orientation
layer that owns no implementation detail.

First proven on an overnight autonomous shift where one ~50-story brainstorm
became six slices driven to convergence in a single session.

## When To Slice

Slicing is forced by the tool: `convergence-review` hard-caps
`# Essential Requirements` at 1-10 bullets per design doc. A brainstorm that
needs ~35 ERs cannot run as one doc no matter how well it is written.

Slice when any of these hold:

- the estimated ER count exceeds the 10-bullet cap
- the story set spans multiple modules or delivery phases that can ship
  independently
- a single `convergence-review` run would be too large to converge within its
  iteration cap or to validate as one commit gate

Target shape for a 30-50 story brainstorm: 5-6 slices, each carrying 10 or
fewer ERs (ideally fewer), each completable in one-to-few `convergence-review`
runs.

## The Ownership Rule

Every requirement, story, and design detail lives in **exactly one** slice
doc, which is its definitive spec. The parent doc keeps no duplicated
substance: after slicing, scoop each responsibility out of the parent and
replace it with a one-line pointer to the owning slice.

This is drift prevention by construction, not by synchronization. Language
preflights, ER preflights, and mid-run adaptation inevitably mutate each slice
doc. If the parent held a redundant copy of any detail, that copy would
silently fall out of date and contradict the owning slice, and in an autonomous
run there is no human around to notice. With single ownership there is nothing
to keep in sync, so nothing can contradict.

Corollaries:

- A slice that needs a detail owned by another slice references it; it never
  copies it.
- The parent's one-liners describe *what* a slice owns, never *how* the slice
  satisfies it.

## Parent Doc Shape

The parent doc is the orientation surface for the LCA mid-run and for every
reviewer (`convergence-review`, GSR) who looks at a diff and needs the big
picture. It carries only:

- **North Star / Goal**: what this whole effort is about, the epic-scale
  purpose, and the key advances it delivers, written so a fresh reviewer
  understands why the branch exists.
- **Global Non-Goals / Deferred**: scope excluded from the entire effort, so
  no slice quietly re-adopts it.
- **Slice Index**: sequence, name, one-line owned responsibility, link, and
  status per slice. This is what the LCA reads first when resuming.
- **Cross-Slice Interfaces**: the few contracts no single slice owns alone
  (shared data shapes, module boundaries, shared vocabulary). Keep this
  section small; if it grows, a slice boundary is probably wrong.
- **Decisions log pointer**: where the run's decisions log lives.

The original brainstorm stories may remain as an appendix explicitly marked
non-definitive. The definitive, preflight-converged stories live in the slices
that own them.

Template:

```text
# <Effort Name> - Parent Design Doc

## North Star

<What this is all about; the key advances. Epic-scale, a few paragraphs max.>

## Global Non-Goals / Deferred

- ...

## Slice Index

| # | Slice | Owns | Status |
|---|-------|------|--------|
| 1 | [<name>](slice_1_<name>.md) | <one-line responsibility> | Converged |
| 2 | [<name>](slice_2_<name>.md) | <one-line responsibility> | In progress |
| 3 | [<name>](slice_3_<name>.md) | <one-line responsibility> | Not started |

Statuses: Not started | In progress | Converged | Paused (reason)

## Cross-Slice Interfaces

- <contract>: introduced by slice N, consumed by slices M...

## Decisions Log

See <path>.

## Appendix: Original Brainstorm (non-definitive)

<Optional. Raw story list for provenance. The owning slices are definitive.>
```

## Slice Doc Shape

Each slice doc uses the canonical design-doc shape in
[lca_playbook.md](../lca_playbook.md#canonical-design-doc-shape) with a
navigation header on top:

```text
# Slice N: <Name>

Parent: [<effort> parent doc](<parent>.md) - North Star, slice index, interfaces
Previous: [Slice N-1](<prev>.md) | Next: [Slice N+1](<next>.md)

Owns: <one sentence stating the definitive scope of this doc>
Does not own: <pointers to sibling slices for adjacent responsibilities>
```

The up-link lets any agent working the slice recover the big picture; the
prev/next links let it see what earlier slices actually did and what is coming
so it does not pre-build or duplicate future scope.

## Slicing Procedure

1. **Group** the brainstormed stories into candidate slices that are
   *sequence-completable*: ordered so each slice builds only on `main` plus
   earlier slices, never on later ones. Prefer boundaries that follow module
   or responsibility lines; minimize cross-slice contracts.
2. **Check the boundaries**: estimate ERs per slice (must be <= 10, ideally
   fewer) and list the cross-slice interfaces each boundary creates. Many
   interfaces between two slices means merge or re-cut them.
3. **Create the slice docs**, moving every story and all supporting detail
   from the brainstorm into exactly one slice.
4. **Scoop out the parent**: replace all transplanted substance with the thin
   pointer layer described above. When this step is done, the parent contains
   no detail that could drift.
5. **Refine just-in-time**: run each slice's requirements preflight sequence
   (story language preflight -> ERs -> ER preflights) immediately before that
   slice's implementation, not all up front. Later slices should absorb the
   clarity that emerges from earlier slices' convergence, and preflighting them
   early guarantees rework.
6. **Implement in sequence** using the per-slice cadence in
   [lca_overnight_playbook.md](../lca_overnight_playbook.md), updating the
   parent's Slice Index status as each slice changes state.

## Mid-Sequence Adaptation

When work on slice N reveals that a detail owned by slice M must change:

1. Edit the owning doc directly; the owning slice doc is always authoritative,
   even after slice M has converged.
2. Append a dated change note to the owning doc: what changed, why, and which
   slice's work surfaced it.
3. Never copy the adapted detail into slice N; keep the reference.
4. If slice M was already implemented and the change is semantic (behavior,
   not wording), log the decision and schedule the follow-up work (a rerun of
   slice M or scope added to a later slice) in the parent's Slice Index.

Change note format, appended to the owning slice doc:

```text
## Change Notes

- 2026-07-05 (during Slice 4): <what changed and why>.
```

## Autonomous Orientation

The parent doc plus change notes are how an autonomous LCA re-orients mid-run
with no human available: read the parent's North Star and Slice Index to see
what this is all about and what state each slice is in, follow the down-links
into earlier slices' change notes to see what actually happened, then resume
the next slice. Keep the Slice Index current as statuses change; a stale index
costs the next resume far more than the one line it takes to update.
