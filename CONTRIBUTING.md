# Contributing to the LCA Playbook

Thank you for your interest in the Lead Coding Agent (LCA) Playbook!

## Maintainer Posture

This repository is an active, opinionated engineering playbook maintained by a
single primary author for daily production use and shared openly under
[Apache-2.0](LICENSE) in case it helps other builders and teams.

Thoughtful issues, forks, bug fixes, and pull requests are warmly welcome, with
candid expectations up front:

- There is no guaranteed SLA on issue triage or PR review.
- Changes that add ceremony, generic checklists, or speculative process without
  strong empirical failure-mode evidence will generally be declined to keep the
  playbook lean.

## What Makes a Strong Proposal

Keep proposals reusable across engineering organizations and agent harnesses:

1. **Observed failure mode or bottleneck:** What concretely went wrong in real
   agent-led engineering work?
2. **Minimal fix:** The smallest rule, CLI improvement, or calibration example
   that addresses the root cause.
3. **Empirical evidence:** What real run(s) proved this works, and what remains
   unproven?

## Pre-Submission Checklist

Before opening a pull request:

- Run the Python test suites (`pytest tools/convergence-review/tests tools/general-stability-review/tests`).
- Confirm all relative Markdown links and section anchors resolve cleanly.
- Confirm nothing from gitignored local files (`llm_config.py`,
  `case-studies/local/*`, `AGENTS_LOCAL*`, `local/`) is staged.
- Scan your diff for credentials, personal email addresses, absolute home paths,
  private customer/partner names, or proprietary product details.
- Avoid undated model-vendor rankings in durable guidance (model pins belong in
  `llm_config.example.py` / local `llm_config.py`).
- Preserve explicit distinctions between *implemented*, *validated*, *merged*,
  *deployed*, *activated*, and *operationally proven*.
