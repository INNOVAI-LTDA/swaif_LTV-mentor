# Batch C (Backend CORS) - Current State (Brownfield)

Scope: document the current backend CORS configuration and what it implies for localhost, preview, and production deployments.

## Current Backend CORS Config

The backend configures CORS in [backend/app/main.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/main.py) via `fastapi.middleware.cors.CORSMiddleware`.

Runtime origin resolution lives in [backend/app/config/runtime.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/config/runtime.py):

- `APP_ENV` is required at process start (`get_app_env()` raises if missing).
- `CORS_ALLOW_ORIGINS` is parsed by `resolve_cors_origins()`.
- If `CORS_ALLOW_ORIGINS` is empty:
  - Production-like `APP_ENV` (anything not in `{local, development, dev, test}`) fails fast with `RuntimeError("CORS_ALLOW_ORIGINS is required when APP_ENV is production-like.")`.
  - Local-like `APP_ENV` falls back to `LOCAL_CORS_ORIGINS`:
    - `http://localhost:5173`
    - `http://127.0.0.1:5173`
    - `http://localhost:4173`
    - `http://127.0.0.1:4173`
    - `http://localhost:3000`
    - `http://127.0.0.1:3000`

## Wildcard Origin Behavior

If the resolved origin list contains `"*"`, [backend/app/main.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/main.py) switches to:

- `allow_origins=["*"]`
- `allow_credentials=False` (because wildcard + credentials is invalid)

Otherwise it uses:

- `allow_origins=<explicit origins list>`
- `allow_credentials=True`

Note: wildcard patterns like `https://*.vercel.app` are not supported; use `CORS_ALLOW_ORIGIN_REGEX` instead of `"*"`.

## Origin Normalization Rules (Operator-Facing Contract)

Each comma-separated entry in `CORS_ALLOW_ORIGINS` is normalized by `normalize_cors_origin()`:

- Must be an absolute `http` or `https` origin with a host.
- Must not contain credentials (`https://user:pass@host` is rejected).
- Must not contain a path, query string, or fragment.
- Trailing `/` is tolerated (normalized to bare origin).

This means `CORS_ALLOW_ORIGINS=https://example.com/app` is invalid; you must configure `CORS_ALLOW_ORIGINS=https://example.com`.

## Localhost vs Preview vs Production Handling (Current)

There is no special-casing for Vercel Preview or Production in code. Deployment reality must be handled through environment values:

- Local dev without extra env:
  - CORS allows the fixed `LOCAL_CORS_ORIGINS` list (includes Vite dev/preview ports `:5173` and `:4173`, plus `:3000`).
- Preview deployments:
  - If the frontend is deployed to multiple dynamic origins (example: per-PR `*.vercel.app` URLs), the backend can only support that by either:
    - explicitly listing every preview origin in `CORS_ALLOW_ORIGINS`, or
    - configuring a regex via `CORS_ALLOW_ORIGIN_REGEX` (preferred; avoids `"*"`).
- Production deployments:
  - The intended contract is a short explicit list of the real hosted frontend origin(s) in `CORS_ALLOW_ORIGINS`.

### Operator Examples (Current Intended Contract)

- Production: `APP_ENV=production CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br`
- Preview: `APP_ENV=production CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br CORS_ALLOW_ORIGIN_REGEX=^https://.*\\.vercel\\.app$`
- Local: defaults allow `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:4173`, `http://127.0.0.1:4173`, `http://localhost:3000`, `http://127.0.0.1:3000`

Warning: Wildcard `*` is rejected in production-like environments; keep `CORS_ALLOW_ORIGINS` explicit and use `CORS_ALLOW_ORIGIN_REGEX` for preview patterns instead.

## Cookies / Credentials Status

Backend auth is Bearer-token based (see [backend/app/api/routes/auth.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/api/routes/auth.py)) and no `set_cookie` usage was found in `backend/app` during this scan.

Implication: today, CORS `allow_credentials` is not required for the current auth flow. If you later introduce cookie-based auth, `"*"` origins will break cross-origin usage.

## Files Likely Affected By Batch C

- [backend/app/config/runtime.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/config/runtime.py)
  - env var contract, origin parsing/normalization, local defaults
- [backend/app/main.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/app/main.py)
  - `CORSMiddleware` wiring (`allow_origins`, `allow_credentials`)
- [backend/tests/test_cors_config.py](/c:/Users/dmene/Projetos/innovai/repos/swaif_LTV-mentoria/backend/tests/test_cors_config.py)
  - expected behavior around required envs and origin validation

## Validation Steps Needed (Current)

Automated:

1. `cd backend`
2. `python -m pytest tests/test_cors_config.py`
3. `python -m pytest tests/test_runtime_config.py`

Manual (preflight sanity check against a running backend):

1. Start backend with explicit env:
   - Local-like: `APP_ENV=local CLIENT_CODE=<client> CORS_ALLOW_ORIGINS=http://127.0.0.1:4173 ...`
   - Production-like: `APP_ENV=production CLIENT_CODE=<client> CORS_ALLOW_ORIGINS=https://accmed.innovai-solutions.com.br ...`
2. Send a preflight request with an `Origin` header matching your frontend origin and confirm the response includes:
   - `access-control-allow-origin: <exact origin>` (or `*` only if configured)
   - `access-control-allow-methods` and `access-control-allow-headers` allowing the SPA’s requests
