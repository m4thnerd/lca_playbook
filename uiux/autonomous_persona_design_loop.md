# Autonomous Persona Design Loop

One agent, acting as product manager and lead designer, improves a single
page over a few versions. Between versions the project's reference personas
review the current state in character, and the agent decides what to do with
what they said. Once set up it runs without the owner, and it stops itself.

Use it when a design is already in a good place and the open question is
whether a few more rounds of user feedback, taken seriously but not
literally, land it somewhere better. It is not the
[competition loop](ambitious_ux_competition_loop.md) (many designers, one
judge, proposals rather than one evolving page) and not the
[low-risk loop](low_risk_ux_enhancements_loop.md) (small safe polish mined
from many pages). Here one design evolves, and the agent's own product
judgment is the filter.

## Setup (the owner, once)

- Save the starting design as checkpoint `v0`, so the whole run can be undone.
- Name the personas: the relevant set from the project's `docs/ux_personas/`,
  chosen per that README. How a persona review is run (persona file, shared
  review ask, headless reviewer routes, at most 5 full-size images per call) is
  in [UX persona review](ux_persona_review.md); nothing here changes it.
- Declare the hard guardrails and the scope in a few lines. These are the
  things the agent may not trade away no matter who asks (for example: no new
  quiz types, frontend-only changes using data the page already has, and keep
  invariants settled in earlier rounds).
- Set the cap: about five versions.

Anything the owner already knows they would say no to belongs in the
guardrails up front, because the agent will not ask mid-run.

## The loop

1. The personas review the current version, in character, with no fixes.
   Same personas, same review ask, same set of screenshots each round, run
   the way the project's persona README says. Fresh and unsteered: the
   reviewers do not see earlier rounds' feedback or the agent's triage.
2. The agent triages as PM and lead designer. It reads everything, decides
   what it believes, and writes down what it accepts, what it declines, and
   why. Declining is normal; a persona is one user reacting, not a
   requirement. Where personas pull in opposite directions, resolve the
   confusion underneath rather than splitting the difference. Anything that
   crosses a guardrail is declined without further discussion.
3. The agent implements the next version as a new checkpoint. Every version
   stays viewable side by side; nothing is overwritten.
4. Review the new version the same way, then check for convergence.

## Convergence (stop when any one holds)

- Diminishing returns, by the agent's judgment: the page is strong and what
  the personas still ask for would not improve it, or is out of bounds.
- Consensus: the personas have nothing material left to say.
- Oscillation: a persona asks to undo a change made in an earlier version.
  The loop has started chasing its tail; stop.

Otherwise continue to the cap.

## Final report

Short: what changed in each version and why; which version the agent recommends
(an earlier version is a legitimate answer; that is what checkpoints are for);
why it stopped; and the persona asks that were declined, with the reason. Present
visual comparisons per [ui_review_format.md](ui_review_format.md). The owner
decides from there.

## What this is not

Not a vote: persona counts decide nothing, the agent does. Not a rubric: no
scores, no weighted criteria. Not a reason for more process: the owner's
guardrails and the cap are the only controls. And as everywhere in this
playbook, no model or vendor name reaches a product page or an end user.

## Operational notes from pilot run (2026-10-30)

- Keep the kickoff prompt short: roles, guardrails, the three stopping
  conditions, checkpoint `v0`, and the version cap. Over-specifying viewport
  constants or artificial consensus formulas adds ceremony without improving
  decisions.
- Write the triage rationale (what was accepted vs declined and why) to a
  visible round note before implementing `vN+1`, rather than leaving it only in
  ephemeral model reasoning, so the final report can accurately summarize
  declined persona asks.
