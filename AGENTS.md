# Agent Operating Instructions

## Optional Local Startup Context

Before answering repo-specific questions, running commands, making edits,
reviewing material, or planning work, read `AGENTS_LOCAL.md` at the repository
root (or original checkout when working in a Git worktree) if it exists.

## Lead Coding Agent Defaults

When operating with this playbook inside a target repository, the target
repository's own instructions and the human owner's explicit decisions take
precedence over reusable defaults here.

Before drafting or approving requirements, or adjudicating review findings:

1. Read the source request (and linked Verbatim Human Intent Reference when
   present), current design context, and applicable module charter.
2. Read `case-studies/local/operating-conditions.md` when present (or calibrate
   against
   `example-case-studies/operating-conditions/lean-saas-team.md` plus the target
   repository's real operating constraints).
3. Read the active requirements-risk calibration set in
   `example-case-studies/requirements-risk/` plus any local files under
   `case-studies/local/` (never stage gitignored `case-studies/local/*` files).
4. Run all three preflights before implementation:
   - `requirements/user_story_preflight_scoring.md`
   - `requirements/convergence_review_preflight_requirements_scoring.md`
   - `requirements/convergence_review_preflight_requirements_justification.md`

For non-trivial implementation, use `convergence-review` with `architecture` and
`core` reviewers, disposition residual cap findings thoughtfully, and follow
with General Stability Review (`reviews/general_stability_review_playbook.md`)
and Staff Engineer Review (`reviewers/staff_engineer_reviewer.md`). Never turn
speculative reviewer edge cases into permanent state machines or refusal gates
merely to silence a finding.

Before leading an unattended shift, read `lca_overnight_playbook.md` and every
case under `example-case-studies/night-shifts/`.

Credentials, personal email addresses, customer data, private product
details, partner-confidential material, and machine-local paths do not belong in
tracked files in this repository.
