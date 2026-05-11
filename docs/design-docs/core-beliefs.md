# Core Beliefs

Non-negotiable principles that govern every decision in ParchMark.

## Domain Safety — The Seven Invariants

Each rule below was derived from current code (Phase 4 of `/keel-adopt`),
stress-tested by a multi-model roundtable (`challenge` + `hivemind`), and
locked in. Every invariant is grep-detectable and evidence-backed — the
codebase already honours it.

A violation of any of these is a bug or a security issue, not a style
preference. The safety-auditor scans every diff against these rules and
refuses to pass work that violates them.

### 1. Tenant isolation on every Note ORM operation

Every SQLAlchemy statement that touches the `Note` table — `select(Note)`,
`select_from(Note)`, `update(Note)`, `delete(Note)`, `db.query(Note)` — in
`backend/app/routers/**` and `backend/app/services/**` must include
`Note.user_id == <user_id>` (or equivalent ownership filter) in the same
statement.

`<user_id>` is either `current_user.id` from request scope or a trusted
argument passed to an explicitly named internal helper.

Rationale: ParchMark is multi-tenant; a missing `user_id` filter is a direct
IDOR / cross-user data leak. This is the single highest-stakes rule in the
codebase.

### 2. Auth required on every non-public route

Every `@router.(get|post|put|patch|delete)` endpoint in
`backend/app/routers/**` must either:

**(a)** declare `Depends(get_current_user)` on its handler (directly, or
transitively via a router-level `dependencies=[...]`), **OR**

**(b)** match one of these exact public routes:

| Method | Path |
|-|-|
| `GET` | `/api/health` |
| `GET` | `/api/auth/health` |
| `POST` | `/api/auth/login` |
| `POST` | `/api/auth/refresh` |
| `GET` | `/api/notes/health/check` |

Any new public endpoint requires an explicit update to this list and the
safety-auditor rule — public routes don't become public by accident.

### 3. No raw SQL outside the one whitelisted site

Raw SQL via `text(...)` is allowed only at:

- `backend/app/services/health_service.py` — `SELECT 1` connectivity probe

Every other database access must go through the SQLAlchemy 2.0 async ORM
(`db.execute(select(...))`, `update(...)`, `delete(...)`). No string
concatenation, no f-strings in queries.

Normal `db.execute(select/update/delete/insert)` is **not** restricted —
it's the intended async ORM entry point.

### 4. Typed-or-bodyless mutations

Request-body parameters on `@router.post`, `@router.put`, `@router.patch`
handlers must be either:

**(a)** typed as a `pydantic.BaseModel` subclass imported from
`app.schemas`, **OR**

**(b)** absent — the endpoint takes no body (e.g. `/logout`).

Forbidden: `dict`, `Any`, `Request`, `Body(...)` with a non-`BaseModel`
type. Pydantic at the boundary is the only validation layer; bypassing it
loses `min_length`, type coercion, and OpenAPI doc parity.

### 5. No secrets in logs

No log statement (`logger.*`, `logging.*`, `print`) in `backend/app/**` may
interpolate any of:

- `password`, `current_password`, `new_password`, `password_hash`
- `refresh_token`, `access_token`
- `secret`
- A variable named `credentials`, `user_credentials`, or `request` that
  holds an auth or settings schema instance
- The `.model_dump()` of any `app.schemas` class whose name contains
  `Password`, `Login`, `Token`, or `Credential`

Password / token leakage in logs is a compliance-level incident. The
codebase is currently clean; this rule keeps it that way.

### 8. Passwords never stored raw

Every assignment to `.password_hash` in `backend/app/**` must have a
right-hand side of either:

- `get_password_hash(...)` (the bcrypt helper from `backend/app/auth/auth.py`), or
- `None` (used for OIDC-sourced users who never had a local password)

No other RHS is permitted. This rule does **not** apply to test code,
scripts, or migrations, which may use pre-hashed fixture values.

### 9. OIDC identity binding by `sub`, not username or email

OIDC user lookup and creation in `backend/app/auth/dependencies.py` must
key on `oidc_sub` (the `sub` claim from the IdP). `preferred_username`
and `email` may only be copied as profile attributes on first creation —
never used as lookup keys.

Rationale: usernames and email addresses in Authelia can be changed or
reassigned; the `sub` claim is the stable, globally-unique identity token.
Keying on a mutable attribute is an account-linking vulnerability.

## Source of Truth

- **Repository is the system of record.** If a decision is not captured in
  this repo, it does not exist for Claude. Slack threads, verbal sync,
  tacit knowledge — all must be encoded here as markdown, code, config, or
  committed test output.
- **Two authoritative data stores:** PostgreSQL for persistent state
  (users, notes), browser `localStorage` for ephemeral client
  state (auth tokens, UI preferences, sort order). No other stores.
- **Server owns markdown rendering decisions.** When frontend and backend
  disagree about note metadata (e.g. extracted title), the backend's
  interpretation wins and the frontend re-fetches. See the shared
  `markdownTestCases` fixture for the common contract.

## Design Philosophy

Drawn from [design-context.md](./design-context.md):

1. **Content is king.** The user's writing is the interface. UI elements
   recede; text takes center stage.
2. **Speed over spectacle.** Perceived and actual performance matter more
   than visual polish. Never add decoration that slows things down.
3. **Quiet confidence.** Design choices should feel deliberate but not
   showy. The burgundy accent, the serif headings — each detail earns its place.
4. **Click-first, scan-friendly.** Design for visual scanning and direct
   manipulation. The notes list is home base; the Command Palette is a
   quick-jump tool, not the front door.
5. **Reduce, don't add.** When in doubt, remove. Fewer elements, fewer
   colors, fewer borders. Let whitespace do the work.

## Container / Runtime

- Docker is the production packaging format (multi-stage `Dockerfile.prod`;
  k3s deploy).
- Local development does **not** require Docker — `make dev` runs UI + API
  natively, with PostgreSQL as the only containerized dependency
  (`docker-compose.dev.yml`).
- Tests that need real PostgreSQL use `testcontainers` (backend
  `pytest-xdist` gives each worker its own DB) or Vitest in-process (UI).

## Claude Is The Builder

- Claude is responsible for design, development, testing, documentation,
  maintenance.
- The human steers. Claude executes.
- Every decision must be traceable to a document in this repo.
- The KEEL pipeline (`/keel-pipeline`) is the default path for any feature
  or bug larger than a one-line typo; see
  [docs/process/THE-KEEL-PROCESS.md](../process/THE-KEEL-PROCESS.md).

## Testing Strategy: Spec-Driven Testing

Tests enforce spec conformance, not discover design. Every spec assertion
has a corresponding test. When specs change, tests change first.

### Layer 0: Spec Consistency

Docs must not contradict each other. Before writing tests, verify that
product-specs, design-docs, exec-plans, and ARCHITECTURE.md agree.
`spec-reviewer` agent runs this check.

### Layer 1: Safety Invariants (the seven)

The rules in this document. **Must be enforced against real I/O** —
mocking safety means testing your mock.

| Invariant | Real-I/O requirement |
|-|-|
| #1 Tenant isolation | Integration test in `backend/tests/integration/` that creates two users, posts notes as A, and verifies B's `GET /notes/` returns only B's data. |
| #2 Auth allowlist | Integration test that hits every router endpoint unauthenticated and asserts `401` for non-allowlisted paths. |
| #3 Raw SQL | Grep-based audit in CI. |
| #4 Typed body | Integration test posts `{"extra": "field"}` to a mutation endpoint and asserts rejection (enforced by Pydantic `extra="forbid"` where configured). |
| #5 Secrets in logs | Unit test captures `caplog` during a login/password-change flow and asserts no log record contains the plaintext. |
| #8 Password-hash write | Unit test against `User.set_password`/equivalents — rejects non-hashed input. |
| #9 OIDC sub | Unit test in `test_oidc_validator.py` verifies lookup uses `oidc_sub`, not `preferred_username`. |

### Layer 2a: Integration (Slow)

Real DB, real FastAPI app, real HTTP client via `testcontainers` + httpx.
Tagged slow — skipped from the fast loop. Lives in
`backend/tests/integration/`.

### Layer 2b: Pure Domain Logic (Fast)

No I/O. Tests for derived fields (e.g. `extractTitle`), pure functions
(date grouping), business rules. Lives in
`backend/tests/unit/` (Python) and `ui/src/**/__tests__/` (TypeScript).

### Layer 3: Service / Process Behavior

Service behavior with mocked external dependencies (HTTP calls to Authelia).
Python uses `unittest.mock`; TypeScript uses Vitest's `vi.mock`.

### Layer 4: UI / Component Behavior

UI behavior with mocked service layer. Uses `render` from
`ui/test-utils/render.tsx` (wraps Chakra, Router, Zustand providers).
Form tests use `fireEvent.submit()`, not button clicks.

### Layer 5: Acceptance + Container Smoke

Validates the full stack boots correctly inside the container:

- `docker-compose.yml` builds successfully
- `make test` passes inside the backend container
- Backend responds to `/api/health` with status 200 and reports DB connected
- Frontend (via nginx) serves `index.html` and proxies `/api/*`

### Testing Infrastructure

| Concern | Parchmark choice |
|-|-|
| Fixture helper | `backend/tests/conftest.py` provides `client`, `sample_user`, `auth_headers`. UI side uses `test-utils/render.tsx`. |
| Mock framework | Python `unittest.mock`; TypeScript Vitest `vi.mock`; MSW intercepts fetch in UI tests. |
| Test tags | Pytest markers: `slow`, `integration`, `oidc`; Vitest tags by file convention (`.integration.test.ts`). |
| Coverage floor | **90%** both sides, enforced by config (`pyproject.toml` `--cov-fail-under=90`, `vitest.config.ts` threshold). |
