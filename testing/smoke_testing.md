# Smoke Testing Guide

Smoke tests are short, high-signal checks that prove a user-facing workflow is wired across the stack. They do not replace unit, API, or full regression tests. Use them when the main risk is integration: routing, frontend state handoff, backend payload shape, browser rendering, or post-activity persistence.

## When to Run Smoke Tests

Run a smoke test when a branch changes a cross-stack user story, especially before handing off a broad feature branch for review. Good candidates include:

- A page that combines data from multiple endpoints.
- A workflow that returns from one activity to another page with one-shot state.
- A backend payload consumed immediately by the SPA.
- A feature whose behavior depends on local content, cooldowns, entitlement, or user progress.
- A merge-alignment branch that combines several workstreams.

Keep the smoke small. The goal is to confirm the essential path works, not to prove every edge case.

## Recommended Shape

1. Name the user stories being exercised.
2. Prepare deterministic backend state with a helper script.
3. Start the full stack in the same mode users will hit locally.
4. Drive the real browser UI.
5. Capture screenshots and a structured JSON report.
6. Assert backend state before and after the browser activity.
7. Record caveats separately from failures.

Prefer one focused smoke script per feature area. Store committed documentation in `docs/`, but keep generated screenshots, reports, and throwaway helpers under a gitignored `local/` directory unless there is a deliberate reason to commit them.

## Local Environment

Prefer calling your project's virtualenv binary directly so shell state does not affect imports:

```bash
.venv/bin/python -m pytest path/to/test.py
```

For full-stack browser smoke tests against a backend-served SPA, rebuild the frontend bundle and start the local stack in the same serving mode production uses:

```bash
cd backend
LOCAL=1 DEBUG=1 ./run_local_frontend_rebuild.sh
```

Apply any pending local migrations and explicitly pin deterministic test datasets before running the smoke so local defaults do not point at stale or incomplete fixtures. Stop any dev server started for the smoke before finishing the run.

## Browser Driver

Headless Chrome works well for local full-stack smoke checks. `puppeteer-core` is a good fit for frontend-only state manipulation. Selenium or Playwright with Chrome is practical when testing a backend-served production build because it can log in, navigate, click through real pages, and capture screenshots with minimal SPA-specific setup.

Wait for the app to be fully mounted before interacting. A loaded `#app` or `#app-root` container alone may not mean a Vue/React app is hydrated; wait on framework mount state or a stable `data-test` element. Capture browser console logs, separating known report-only CSP notices from runtime JavaScript errors.

## Test Users and State

Avoid using interactive signup during smoke tests. Bot checks, onboarding modals, email flows, and product gates make signup unreliable as a setup path. Create or reuse deterministic local users through backend helpers, then drive the browser from an authenticated session.

Useful setup helpers typically:

- Create a user with a stable username/email/password.
- Set active workspace or product context and explicit entitlement tier (free vs paid).
- Seed just enough progress, records, cooldowns, or content mappings for the target user story.

Smoke tests are easier to trust when every synthetic mutation is visible in one setup helper.

## Data Realism

Local fixtures are often intentionally small for determinism, which can distort percentages, cooldown counts, or availability totals. Document denominator caveats in the smoke report (for example, completing 1 item out of a 1-item local fixture causes a larger visible percentage jump than production content, while still proving the return path, delta rendering, and payload contract).

## Assertions

Use both backend and browser assertions. Browser-only screenshots are useful evidence, but they can miss whether the right source of truth changed.

Good backend assertions include:

- Endpoint payload shape matches the frontend contract.
- Resource availability and state counts changed as expected.
- Progress or delta fields include prior and updated values.
- One-shot return state is available only for the just-completed activity.
- Persisted snapshots are scoped to the right user and tenant/context.

Good browser assertions include:

- The user lands on the expected page.
- **Every required subresource (`stylesheet`, `script`, `image`, `font`) returns HTTP `200` (zero `4xx`/`5xx` network responses) and required CSS/JS bundles are non-empty.** An HTML `200 OK` or `curl | grep` check is **never** a valid UI or post-deploy smoke test: a misconfigured `STATIC_URL` / CDN path or missing static asset step can return HTTP `200` for the HTML document while `404`ing CSS and rendering a completely unstyled page.
- **Computed styles and visual layout are intact:** Capture a real browser screenshot of the actual modified or deployed surface and delegate a visual inspection check (per [lca_playbook.md](../lca_playbook.md#runtime-and-visual-evidence), the LCA delegates visual review to an independent subagent/reviewer rather than assuming a file on disk looks right) or assert key computed styles (non-default flex/grid layout, expected colors, non-zero image dimensions).
- **The smoke test exercises the actual surface changed:** A local SPA-only smoke script does **not** smoke-test a server-rendered template (such as `marketing_home.html`) or a live staging/production deployment's CDN/static asset pipeline.
- Expected CTAs, copy transitions, deltas, and return routes behave as specified.

## Artifact Conventions

Keep local artifacts predictable:

- `local/<feature>_smoke.py` for a local smoke helper.
- `local/<feature>_smoke_report.json` for structured results (branch, timestamp, scenario, URL, screenshots, backend state before/after, console errors, caveats).
- `local/screenshots/<feature-smoke>/00-baseline.png` and similar for screenshots.

## Review Checklist

Before treating a smoke run as valid evidence, confirm:

- The scenario maps to a named user story.
- Setup did not depend on manual signup.
- The browser exercised the real UI on the actual modified/deployed surface, not only direct API calls, `curl | grep` HTML checks, or an unrelated SPA smoke script.
- Every subresource (`stylesheet`, `script`, `image`, `font`) returned HTTP `200` (zero `4xx`/`5xx` asset failures) and required CSS/JS bundles were non-empty.
- Screenshots were visually inspected (via a delegated subagent/reviewer per [lca_playbook.md](../lca_playbook.md#runtime-and-visual-evidence)) to confirm CSS layout and visual rendering are intact.
- Backend state was checked before and after the activity.
- Screenshots, structured reports, and fixture caveats were saved, and any local server started for the run was stopped.
