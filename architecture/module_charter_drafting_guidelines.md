# Module Charter Drafting Guidelines

This guide adds only the practices around charter drafts that are not already
covered by [module_charters.md](module_charters.md) and
[convergence_review_essential_requirements.md](../requirements/convergence_review_essential_requirements.md).

## Best Practices

1. Read both reference documents above before drafting or revising a charter; their guidance is canonical and remains so.
2. Keep draft charters in `docs/charters/<module>_draft.md` until the charter operating model is approved; do not add root-level module `charter.md` files yet.
3. Treat `External Contracts` as a required (not optional) section so the module's seam with the rest of the codebase is always declared.
4. Lead `Essential User Stories` with the most user-facing voice the module legitimately serves (learner if applicable; otherwise the module's primary internal stakeholder).
5. Apply the [Essential Requirements drafting standards](../requirements/convergence_review_essential_requirements.md) to `Durable Requirements` - the same exclusions, name-pinning warnings, and outcome-over-mechanism preference.
6. Module charters are not limited to the 10-bullet Essential Requirements cap used by convergence-review design docs. Keep every durable requirement compact, but include all long-term behaviors the module must preserve.
7. The `External Contracts` section names the boundary and must not restate any rule that another module's charter already owns.
8. Before submitting a draft that references another module, re-read every referenced charter to confirm each requirement has exactly one authoritative owner, and close `External Contracts` with a one-line disclaimer pointing readers elsewhere for behaviors owned by those modules.
9. Exclude what the [Essential Requirements guide](../requirements/convergence_review_essential_requirements.md) says to exclude.
10. Watch for the failure modes listed in that guide; they apply to charters too.
11. Any PR that materially shifts what a module promises - new user-facing capability, new external contract, removed responsibility - should include a `docs/charters/<module>_draft.md` update so reviewers can compare against the current draft before deciding whether the shift is merited.
12. **Preserve human sign-off provenance:** Never append agent-drafted clauses directly beneath an existing `"Human-Approved as of <date>"` attestation header without placing them in an explicit `## Pending Agent-Drafted Additions (Unreviewed)` section or updating the charter's sign-off status.
13. **Keep `CHARTER.md` and public boundaries clean-room ready:** Never paste PR commit diaries, reconstruction timer logs, test-fix histories, or internal formula tuning constants into `CHARTER.md` `Durable Requirements` (place tuning parameters in a separate calibration table if needed), and keep `full_spec/` (`rebuildable/`) `__init__.py` `__all__` restricted to the minimal public entry points (`1-4` symbols) rather than exporting internal helpers for white-box tests.

## Reference Examples

Each adopting repository should maintain its own reviewed charter examples near
the modules they describe. Do not copy a charter from another system as though
its ownership boundaries were universal.
