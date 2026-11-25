# Local Calibration & Operating Conditions (`case-studies/local/`)

Everything in `case-studies/local/` except this `README.md` is ignored by Git
(`.gitignore`). Put your organization's real operating constraints and
repository-specific calibration case studies here so agents calibrate their
proportionate-engineering judgment to *your* team rather than an imagined
hyperscale enterprise.

## Recommended First File: `operating-conditions.md`

Copy
[`../../example-case-studies/operating-conditions/lean-saas-team.md`](../../example-case-studies/operating-conditions/lean-saas-team.md)
to `case-studies/local/operating-conditions.md` and edit it to describe your
actual engineering headcount, deployment topology, concurrent admin/operator
traffic, and maintenance opportunity cost.

## Adding Local Case Studies

Whenever an autonomous session, preflight loop, or review pass overbuilds an
unrequested mechanism, invents a refusal gate, or misses a domain-specific
trap, drop a short Markdown post-mortem into `case-studies/local/` (for example
`case-studies/local/2026-11-avoidable-webhook-queue.md`). Both
[`lca_playbook.md`](../../lca_playbook.md) and
[`convergence_review_preflight_requirements_justification.md`](../../requirements/convergence_review_preflight_requirements_justification.md)
instruct agents to check `case-studies/local/` alongside the tracked
[`example-case-studies/`](../../example-case-studies/).

### Sharing Across Multiple Workstations or Teammates

Because `case-studies/local/` is gitignored here:

- **Solo across multiple laptops/workstations:** symlink `llm_config.py` and
  individual files inside `case-studies/local/` into a folder synced via
  Syncthing, iCloud Drive, Dropbox, or Google Drive.
- **Shared across an engineering team:** commit your org's operating conditions
  and case studies inside a `docs/lca/` folder in your private product repo and
  symlink those files into `case-studies/local/` (`ln -s
  ~/dev/your-repo/docs/lca/*.md case-studies/local/`).
