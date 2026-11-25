# Full-Stack Data Shape & Field Existence Review

Use this focused review when a branch adds or changes API payloads, backend
serializers/DTOs/prompt contexts, frontend TypeScript contract types, Pinia/state
stores, or cross-stack mocks and fixtures.

General Stability Review (`GSR`) and the Staff Engineer Reviewer can miss quiet
contract drift when both sides look locally plausible in isolation. This pass
enforces two properties before a branch is marked ready for human review:

1. **Every new or retained field earns its existence** by tracing to a real
   terminal consumer (not just a type definition, wrapper, or test fixture).
2. **Producers and consumers agree across the wire and across every runtime
   initialization path** on field names, requiredness, nullability, and units.

## When To Trigger This Check

Run or delegate this check whenever a diff touches any of:

- backend endpoint responses, serializers, `TypedDict`s, DTOs, or prompt-context builders;
- frontend TypeScript interfaces/types representing API or persisted state;
- store state, session objects, route-handoff objects, or reset/hydration paths;
- request payloads sent from frontend to backend; or
- mock server responses and test fixtures standing in for cross-stack data.

---

## Part 1: Field Existence Audit (`Keep / Move / Remove`)

Once an unused or speculative field lands in types, payloads, and fixtures,
future coding agents preserve it forever because it looks intentional. Audit new
fields while the branch is still unpublished.

### The Terminal-Consumer Rule

Every new backend-emitted field and every new frontend-typed/stored field must
trace past intermediate copies to **real terminal behavior**:

- renders visible UI text, layout, chart data, or state;
- gates a CTA, disabled state, route, validation rule, or backend decision;
- persists required user, domain, or audit state;
- builds a validated request payload or formats text actually included in a model prompt; or
- satisfies an explicit, time-bounded compatibility bridge with a named removal condition.

**Not sufficient on their own:** appearing in a TypeScript interface, serializer,
or mock; being copied from one object to another; making a payload look
symmetrical; `"for future use"`; `Record<string, unknown>` hedging; or a test
that only asserts the field exists without testing behavior.

### Deterministic Verdicts

Assign each new or expanded field path one verdict (never `"keep if used"`):

- **`Keep`**: proven terminal consumer, and the current layer is the right owner
  (for example, backend owns access-controlled DB counts; frontend owns unsaved
  UI overlay state or display formatting).
- **`Move`**: real terminal consumer exists, but another layer should own the
  derivation or rule (for example, moving duplicated threshold logic to one
  backend source, or deriving pure display copy in the component instead of
  widening the API).
- **`Remove`**: no terminal consumer, or existing fields already carry the same
  fact more cleanly. Default to `Remove` on unshipped branches when no consumer
  exists.
- **`Defer`**: blocked on an explicit product question (state the exact question).

---

## Part 2: Cross-Stack Shape & Initialization Agreement

Screenshots and green unit tests with mocked stores do not prove that backend
and frontend contracts match. Trace every changed cross-stack field end to end.

### 1. Backend Producer -> Wire Contract

Inspect the view/endpoint, serializer/builder, model fields, cache overlays, and
conditional branches:

- **Presence across all branches:** Is a field marked required in TypeScript
  actually emitted on *every* response variant (including empty, locked,
  unauthenticated, or error-adjacent states)?
- **No dual-shape hedging:** Do not emit the same fields both flat and nested
  just to avoid choosing one contract.
- **Exact units and identifiers:** Verify ratio (`0..1`) vs percent (`0..100`),
  seconds vs milliseconds, slug vs primary key, and UTC ISO timestamp vs local
  calendar date string.
- **Loud failures over silent lies:** Do not mask missing required domain data
  behind silent `0` or `""` defaults that make the UI render plausible-looking
  wrong numbers.

### 2. Wire Contract -> Frontend Types, Stores, & Mocks

Inspect TypeScript interfaces, store initializers, composables, components, and
test fixtures side by side with the backend builder:

- **Exact names and optionality:** TypeScript required/optional modifiers must
  match what the server actually sends (avoid blanket `Partial<T>` erasure).
- **Nullish-coalescing traps:** Confirm `?? 0` or falsy checks (`if (!val)`) do
  not turn valid `0` into "missing" or turn `undefined`/`null` into misleading
  zeros or `NaN`.
- **Every runtime construction path:** When adding a required field to a store
  or session object, check *every* place that object is created or reset:
  initial store state, API hydration, `init*` actions, reset/clear handlers,
  localStorage/sessionStorage rehydration, and unit-test store mocks.
- **Fixture parity:** Update mock server payloads and frontend test fixtures to
  match the real backend shape so tests cannot pass against an imaginary API.

---

## Compact Audit Output

For non-trivial cross-stack diffs, record a short table in the review notes or a
local scratch file (`tmp/<feature>_data_shape_review.md`):

| Field path | Producer | Terminal consumer trace | Nullability & units | Verdict / status |
| --- | --- | --- | --- | --- |
| `summary.items[].score_ratio` | `api.py::build_summary` | `SummaryCard.vue -> formattedScore` | `number \| null`, `0..1` ratio | `Keep` - verified on locked & active responses |
| `summary.legacy_total` | `api.py::build_summary` | Type + test fixture only | `number` | `Remove` - no behavioral consumer |
