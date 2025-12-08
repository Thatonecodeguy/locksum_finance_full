**Project Overview**
- **Backend:** `backend/app` — FastAPI app using SQLAlchemy (v2 style `Mapped` annotations). Main entry: `backend.app.main:app`.
- **Frontend:** `web/src` — React (Vite). Expects backend at `FRONTEND_BASE_URL` (default `http://localhost:5173`).
- **Mobile:** `android/` and `ios/` contain skeleton apps (not required for most backend work).

**High-level architecture & data flow**
- Clients (web/mobile) call the FastAPI backend. Auth uses JWTs (see `backend/app/auth.py`) — login returns a bearer token where `sub` is `user.id`.
- Persistent models live in `backend/app/models.py`. Database sessions are provided with the `get_db` dependency in `backend/app/database.py`.
- External integrations:
  - Plaid: `backend/app/plaid_integration.py` (link token + public token exchange). gated behind plan checks.
  - Stripe: `backend/app/stripe_billing.py` (checkout sessions + webhook handling). Webhook maps Stripe price IDs back to `user.plan`.
- AI logic is implemented in `backend/app/ai.py` and invoked via `/ai/*` endpoints. These functions are pure-ish and accept a DB session / simple args.

**Developer workflows (how to run & debug locally)**
- Install deps listed in `backend/requirements.txt` and `web/package.json`.
- Backend quick run (from repo root) — PowerShell example:
```
$env:JWT_SECRET='dev_secret'; $env:DATABASE_URL='sqlite:///./dev.db'
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- Notes:
  - `backend/app/settings.py` is `pydantic.BaseSettings` — it reads from environment or a `.env` file (supported via `python-dotenv`).
  - Database tables are created automatically on startup (`Base.metadata.create_all` in `main.py`). There is no migration system in-tree.

**Auth & API conventions**
- Login: `POST /auth/login` accepts JSON `email` + `password` (schema `UserCreate`) and returns `{access_token, token_type}`.
- Protect endpoints with the `Authorization: Bearer <token>` header. The FastAPI `get_current_user` dependency decodes JWT `sub` as `user.id`.
- Example curl to list transactions:
```
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/transactions
```

**Plan gating & billing behavior**
- Plan checks use `backend/app/plans.py` (`require_min_plan`). Some endpoints (Plaid, AI) call `require_min_plan(user, "plus")` before proceeding.
- Stripe price IDs are provided via env vars (`STRIPE_PRICE_ID_*`) and webhook behavior updates `user.plan` using those IDs.

**Third-party integration gotchas**
- Plaid: requires `PLAID_CLIENT_ID`, `PLAID_SECRET`, and optionally `PLAID_REDIRECT_URI`. The code constructs a typed Plaid client — missing keys raise HTTP 500.
- Stripe: requires `STRIPE_SECRET` for API calls and optionally `STRIPE_WEBHOOK_SECRET` for webhook signature verification. If webhook secret is missing, events are parsed without signature verification.

**Code patterns & where to look**
- DB models: `backend/app/models.py` — uses SQLAlchemy 2.0 `Mapped` + `mapped_column` and `relationship(back_populates=...)`.
- DB session injection: `backend/app/database.py` provides `get_db()` as a FastAPI dependency (yielding sessions).
- Auth: `backend/app/auth.py` — `oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')`; tokens are JWTs signed with `JWT_SECRET`.
- Routes are defined in `backend/app/main.py` and in subrouters: `plaid_integration.py`, `stripe_billing.py`.
- AI helpers: `backend/app/ai.py` — keep business logic separate from request handling.

**Examples of common changes and where to edit**
- Add a new protected endpoint: edit `backend/app/main.py`, add a route that depends on `get_current_user` and `get_db`.
- Add a new model: edit `backend/app/models.py`, then restart the server (auto-create runs on startup). Consider adding DB migration tooling if persistent schema evolution is needed.

**Files to reference when coding**
- `backend/app/main.py` — API surface and router includes
- `backend/app/models.py` — data model definitions
- `backend/app/schemas.py` — Pydantic request/response shapes
- `backend/app/settings.py` — environment-driven config
- `backend/requirements.txt` — Python dependencies

If anything here looks incomplete or you want more detail (examples for the React frontend, mobile wiring, or Docker development), tell me which area to expand.
