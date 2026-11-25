# Choosing a Workflow

Start with the lightest workflow that matches the slice's real risk and scope:

| Situation | Primary Workflow | Add When Warranted |
|---|---|---|
| Bounded feature, bug fix, or refactor (`<= 10` ERs) | [Quickstart](quickstart.md) + [LCA Playbook](../../lca_playbook.md) | [Full-Stack Data Shape Review](../../reviews/full_stack_data_shape_review.md) when payloads change |
| Large epic or brainstorm (`> 10` ERs / 15-50 stories) | [Design Doc Slicing](../../requirements/design_doc_slicing.md) | Independent [Code-Aware LoC Impact Pass](../../requirements/architecture_pressure_scoring.md#enhanced-option-independent-code-aware-impact--loc-estimation) |
| Workflow includes AI agents as actors/operators | [Agentic PM Story Preflight](../../requirements/agentic_pm_user_story_preflight.md) | [Agentic Architecture Pressure](../../requirements/agentic_architecture_pressure_scoring.md) (`Software` vs `Hybrid` vs `Agentic`) |
| Incremental frontend polish across existing pages | [Low-Risk UX Enhancements Loop](../../uiux/low_risk_ux_enhancements_loop.md) | [UX Persona Review](../../uiux/ux_persona_review.md) + [UI Review Format](../../uiux/ui_review_format.md) |
| Evolving one good page with in-character user feedback | [Autonomous Persona Design Loop](../../uiux/autonomous_persona_design_loop.md) | [Standing UI/UX Design Patterns](../../uiux/ui_ux_design_patterns.md) |
| Rethinking a high-leverage page from first principles *(explicitly requested)* | [Ambitious UX Competition Loop](../../uiux/ambitious_ux_competition_loop.md) | Type 1-B shared fixture + real-data render gate |
| Evaluating or creating a spec-replaceable module | [Full-Spec Lane Guide](../../architecture/module_charters_full_spec_lane.md) | [Snapshot Boundary Case Study](../../example-case-studies/full-spec-lane-judgment-calls/daily-snapshot-semantics-boundary.md) |
| Onboarding onto an unfamiliar or complex codebase | [Engineer Architecture Visuals](../../visualizations/engineer_architecture_visuals.md) | [Module Charter Compatibility Review](../../architecture/module_charter_compatibility_review.md) |
| Authorized unattended multi-hour execution | [Overnight LCA Playbook](../../lca_overnight_playbook.md) | [Night-Shift Case Studies](../../example-case-studies/night-shifts/README.md) |
| Multiple independent workstreams sharing locks/contracts | [Engineering Director Playbook](../../engineering_director_playbook.md) | Separate git worktrees + milestone callbacks |

## Early Warning Signs of Over-Engineering

Stop and simplify whenever you spot any of these:

- An autonomous preflight pass adds new `US-*` stories, numeric quotas, or
  unused config columns that the human never asked for.
- Exception tags (`[Reliability]`, `[Data Integrity]`) are used to justify new
  interactive prompts, `INIT_HOST_MODE` flags, or 2-phase DB state machines for
  ordinary cache clears.
- A reviewer edge case on GSR pass 6+ is treated as a mandatory new feature
  rather than deferred or rejected under your operating conditions.
- An entire multi-layer feature is labeled with one lane instead of reasoning by
  architectural position.
- An Engineering Director is sitting above a single LCA polling for status.
