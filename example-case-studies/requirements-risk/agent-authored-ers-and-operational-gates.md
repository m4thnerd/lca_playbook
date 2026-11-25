# Case Study: When Agent-Authored Essential Requirements Laundered Unrequested Operational Gates

> **Status: required calibration reading; apply with
> [lca_playbook.md](../../lca_playbook.md),
> [architecture_critic.md](../../reviewers/architecture_critic.md), and
> [convergence_review_essential_requirements.md](../../requirements/convergence_review_essential_requirements.md).**

## Context

After a routine deployment swept in a frontend framework upgrade that rendered
icon ligatures as raw text and `scripts/activate_image.sh` overwrote
`previous_release_image.txt` three seconds after startup, the human owner asked
for two focused guardrails:

1. a fast, path-gated compiled-SPA Chrome smoke test in CI and pre-commit to
   verify that the app shell mounts and icons render as glyphs rather than raw
   text; and
2. printing the git commit range being deployed and preserving the currently
   serving container image as the rollback target before switching containers.

Because the request was straightforward, the human defined the intent up front
and did not review the agent-drafted `# Essential Requirements`.

## What Happened

Across the first five design-doc revisions, the human owner pared back scope so
the 110-line design doc had **zero mention** of `INIT_HOST_MODE`,
`ensure_containers_up.sh`, `os_patch_reboot.sh`, clean-worktree gates, or
refusing to run `deploy_release.sh` when containers were stopped.

The drift happened in three rapid autonomous commits (`Commits 6 -> 7 -> 8`)
once the agent drafted `# Essential Requirements` and entered review loops:

1. **Commit 6 (Self-Authored ER Overreach):** The agent wrote an ER stating:
   > *"`deploy_release.sh` must be the sole supported production deployment
   > entry point... Before a build can move a mutable application tag, the
   > canonical path must resolve the immutable image ID actually serving...
   > Deployment must stop when the serving image identity cannot be preserved."*

   To satisfy its own ER literally, the agent made `deploy_release.sh` abort on
   any untracked file (`git status --porcelain --untracked-files=all`), abort if
   the `web` container was not currently running, abort on non-fast-forward git
   commits (`--is-ancestor`), pause for an unrequested interactive `Type
   CONFIRM` prompt, and rewrote `ensure_containers_up.sh` and
   `os_patch_reboot.sh` so no other script could create containers.

2. **Commit 7 (19 minutes later - Reviewers Enforce the Self-Authored ER and
   Spawn `INIT_HOST_MODE`):** Downstream reviewers never saw the human's
   original prompt; they only saw the design doc and `# Essential Requirements`.
   They flagged a contradiction created by Commit 6: if `deploy_release.sh`
   requires a running `web` container and every other script only runs `docker
   start`, a fresh host can never be deployed. Instead of deleting the
   stopped-container refusal, the agent invented `INIT_HOST_MODE` and made
   `deploy_release.sh` refuse to run whenever a stopped `web` container, any
   application image, or `rollback_target.state` existed without a running `web`
   container.

3. **Commit 8 (16 minutes later - Second-Order Repair Inside Unrequested
   Machinery):** Reviewers found an edge case *inside* `INIT_HOST_MODE` (a
   failed preflight after building `:latest` blocked retries), so the agent
   added 36 lines of `EXIT` trap cleanup (`cleanup_failed_init_image_tag`) and
   257 lines of tests locking in every branch of the state machine.

## Production Consequence

When the PR merged, `deploy_release.sh` had grown from **114 lines to 362
lines** and caused **three separate operational incidents inside five days**:

- the unrequested interactive `Type CONFIRM` prompt blocked unattended deploys;
- `git log` without `--no-pager` froze deployments inside `less`; and
- after a routine OS security update and host reboot left containers stopped,
  `deploy_release.sh` refused to bring production back online because `web` was
  not running, while `ensure_containers_up.sh` failed to restart the stopped
  containers because Commit 6 hardcoded the wrong Docker Compose project label.

## Why Existing Safeguards Missed It (And What Changed)

1. **Missing provenance distinction between human intent and agent-drafted
   ERs:** Reviewers treated unreviewed `# Essential Requirements` as
   human-approved law. (Fixed by requiring a
   [Verbatim Human Intent Reference](../../requirements/verbatim_human_intent_reference_playbook.md)
   plus `ER Sign-Off Status: Agent-Drafted (Unreviewed)`.)
2. **Padding the ER list:** Turning a 2-bullet operational tweak into 6 heavy
   contract bullets.
3. **Architecture Critic gag rule:** Previously, the Architecture Critic was
   told never to challenge mechanisms written into `# Essential Requirements`;
   it is now explicitly authorized to flag unrequested refusal gates, prompts,
   and state machines whenever ERs are `Agent-Drafted (Unreviewed)`.
4. **Exception-label laundering:** Tagging `[US-2; Maintainability, Reliability]`
   turned "preserve the previous image when one is running" into hard pre-build
   refusal gates when containers were stopped.

## Calibration Questions

1. Were `# Essential Requirements` explicitly `Human-Approved`, or are they
   `Agent-Drafted (Unreviewed)`?
2. Does the count and weight of the ERs match the simplicity of the human's
   request (for example 1-2 minimal ERs for a 2-part operational guard)?
3. Did an exception label (`Reliability`, `Data Integrity`, `Maintainability`)
   turn a best-effort safeguard into a hard refusal gate, interactive prompt, or
   multi-mode state machine that the human never asked for?
4. When a reviewer finds a bug inside an agent-invented refusal gate or
   host-init mode, should you add cleanup traps and tests, or delete the
   unrequested refusal gate?
