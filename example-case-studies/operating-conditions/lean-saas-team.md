# Example Operating Conditions Profile: Lean SaaS Team

> **Example Organization Profile:** Copy this template to
> `case-studies/local/operating-conditions.md` (gitignored) and adapt it to your
> own organization's staffing, traffic, and deployment model. Reviewers use a
> repository's operating conditions to judge whether proposed safeguards and
> concurrency guarantees are proportionate to reality rather than an imagined
> hyperscale enterprise.

This document supplies the real operating scale for requirements justification
and architecture review on a lean SaaS learning platform and its companion
authoring tools. Use it to judge whether proposed guarantees and mechanisms
solve conditions this business actually faces, rather than conditions plausible
only at a giant technology company, multinational airline, or hyperscale
enterprise.

These are situational operating conditions, not universal software laws. Revise
this profile whenever team size, traffic shape, or deployment topology changes.

## Company And Engineering Capacity

- The product is operated by a lean founder-led business.
- Ongoing engineering maintenance capacity consists of one full-time technical
  founder plus one part-time partner engineer who also supports other systems.
- Every retained protocol, abstraction, compatibility path, operational surface,
  and unusual edge-case guarantee must be understood and maintained by this
  small team.
- Maintenance opportunity cost is therefore part of correctness: machinery that
  protects a condition the business does not encounter consumes capacity needed
  for real learner and instructor value.

## Deployment And Administrative Usage

- Each tenant deployment typically has only one instructor or administrator
  actively configuring the system at any given time.
- Multiple administrators do not concurrently perform conflicting administrative
  writes on the same deployment in normal operations.
- The active staff user typically spends less than five minutes per day in a
  deployment's administrative interface.
- Administrative writes are sparse, human-paced events, not a high-throughput
  multi-operator workload.

For staff-side and administrative flows, simultaneous multi-operator races are
not a default design condition. Do not invent them merely because a feature
contains a write, an instructor action, or an administrator action.

## Engineering Consequences

Prefer the simplest implementation that is correct for these conditions and uses
existing framework or repository contracts:

- Do not require locks, distributed coordination, queues, retry protocols,
  deduplication systems, perfect ordering, cross-request state, or elaborate
  idempotency solely to protect hypothetical concurrent instructor or
  administrator actions.
- Do not add enterprise configurability, generalized extension points,
  multi-region assumptions, large-team ownership machinery, or compatibility
  layers without a current user story, observed failure mode, or explicit human
  owner decision that requires them.
- Treat claims such as "two administrators might submit at the exact same
  millisecond" as unsupported unless the design documents a concrete path that
  actually occurs in this operating environment.
- If a direct change should take minutes to read and maintain, but concurrency
  machinery turns it into a multi-hundred-line state machine, re-evaluate the
  premise before engineering the machinery.
- When a rare race can be handled acceptably by ordinary framework behavior,
  database uniqueness constraints, a clear last-writer rule, or a simple retry
  at the boundary, prefer that proportionate behavior over a new subsystem.

The burden of proof belongs to the heavier mechanism. "A hyperscale company
might need this" and "this is theoretically purer" are not sufficient
justification.

## What Lean Scale Does Not Waive

Apply these conditions to the actor and path actually under review. A single
active administrator does not prove that learner traffic, scheduled background
jobs, payment webhooks, browser double-clicks/retries, or external API calls
never overlap. Concurrency protection is justified whenever a real request path,
observed failure, or explicit product requirement establishes it.

Lean scale also never waives authentication, authorization, tenant isolation,
privacy, input validation, migration safety, recoverability, or ordinary
persisted-data correctness. Keep repository-standard safeguards that address
real failure modes; reject speculative machinery for conditions that do not
exist.

## Reviewer Calibration Questions

For each proposed requirement or implemented mechanism, ask:

1. Which actual user, request path, or operating event creates the condition
   this protects?
2. Can that condition realistically occur given our actual operator concurrency
   and traffic profile?
3. Is the safeguard proportionate to its likelihood and consequence for our
   actual engineering maintenance headcount?
4. Would a direct implementation using an existing framework or repository
   contract be correct here?
5. Are we retaining durable machinery for our actual system, or for an imagined
   enterprise?

If the only credible answer is the imagined enterprise, remove or simplify the
requirement or implementation.
