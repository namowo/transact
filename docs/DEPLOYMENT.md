# Deployment

This document describes how TransAct is operated and lists the required environment variables.

## Architecture

- **Backend**: FastAPI application (Python 3.12), runs in a Docker container (see [backend/Dockerfile](../backend/Dockerfile)) via `fastapi run --workers 4 app/main.py`. Package management via `uv`.
- **Frontend**: Vue 3 / Vite SPA, built for production via `npm run build` into a static bundle (`frontend/dist`). The backend can serve this directory via `FRONTEND_DIR`.
- **Database**: PostgreSQL, accessed through SQLAlchemy/psycopg. Schema management via Alembic migrations ([backend/alembic/](../backend/alembic/)).
- **Email delivery**: SMTP for transactional emails (registration, password reset, etc.). Without a configured SMTP host, emails are logged to the console instead of being sent (useful for local development).
- **Auth**: JWT in HttpOnly cookies plus WebAuthn/passkeys as an additional authentication factor.

## Building and running the backend container

```sh
docker build -t transact-backend ./backend
docker run --env-file .env -p 8000:8000 transact-backend
```

Before the first start (or after schema changes), Alembic migrations must be applied:

```sh
uv run alembic upgrade head
```

## Building the frontend

```sh
cd frontend
npm install
npm run build
```

The result is placed in `frontend/dist` and can either be served by the backend (`FRONTEND_DIR`) or hosted separately via a web server/CDN.

## Environment variables

### Backend (`.env`, see [backend/app/core/config.py](../backend/app/core/config.py))

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOSTNAME` | no | `localhost` | PostgreSQL database hostname |
| `DB_PORT` | no | `5432` | PostgreSQL database port |
| `DB_USERNAME` | yes | – | Database username |
| `DB_PASSWORD` | yes | – | Database password |
| `DB_NAME` | yes | – | Database name |
| `JWT_SECRET_KEY` | recommended | randomly generated | Secret key for signing JWTs. Must be set explicitly in production, otherwise restarts invalidate all sessions |
| `VITE_JWT_LIFETIME_SECONDS` | no | `43200` | Access token lifetime in seconds |
| `ACCESS_TOKEN_COOKIE_NAME` | no | `access_token` | Name of the auth cookie |
| `RESET_PASSWORD_TOKEN_SECRET` | yes | – | Secret key for password reset tokens |
| `VERIFICATION_TOKEN_SECRET` | yes | – | Secret key for email verification tokens |
| `EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS` | no | `48` | Validity period of the verification token |
| `PASSWORD_RESET_TOKEN_EXPIRE_HOURS` | no | `2` | Validity period of the password reset token |
| `WEBAUTHN_RP_ID` | no | `localhost` | Relying party ID for WebAuthn/passkeys (usually the domain) |
| `WEBAUTHN_RP_NAME` | no | `TransAct` | Display name of the relying party |
| `WEBAUTHN_ORIGIN` | no | `http://localhost:5173` | Expected origin for WebAuthn requests |
| `WEBAUTHN_CHALLENGE_TTL_SECONDS` | no | `300` | Validity period of a WebAuthn challenge |
| `HOST_URL` | no | `http://localhost:8000` | Publicly reachable URL of the backend |
| `FRONTEND_URL` | no | `http://localhost:5173` | URL of the frontend (used e.g. for links in emails) |
| `FRONTEND_DIR` | no | `../frontend/dist` | Path to the built frontend, if served by the backend |
| `API_V1_STR` | no | `/api/v1` | Prefix for API routes |
| `ENVIRONMENT` | no | `local` | `local`, `staging`, or `production` |
| `BACKEND_CORS_ORIGINS` | no | `[]` | Comma-separated list of additional allowed CORS origins |
| `SMTP_HOST` | no | unset | SMTP server for email delivery. If left empty, emails are only logged |
| `SMTP_PORT` | no | `587` | SMTP port |
| `SMTP_USERNAME` | no | unset | SMTP username |
| `SMTP_PASSWORD` | no | unset | SMTP password |
| `SMTP_USE_TLS` | no | `true` | Whether to use TLS for the SMTP connection |
| `SMTP_FROM_EMAIL` | no | `no-reply@transact.local` | Sender email address |
| `SMTP_FROM_NAME` | no | `TransAct Repository` | Sender display name |

### Frontend

| Variable | File | Description |
|----------|------|--------------|
| `VITE_API_BASE_URL` | `.env.development` / `.env.production` | Base URL of the backend API |
| `VITE_PRIMEVUE_LICENSE_KEY` | `.env.local` (not versioned) | License key for PrimeVue components, if required |

> Secrets (`JWT_SECRET_KEY`, `RESET_PASSWORD_TOKEN_SECRET`, `VERIFICATION_TOKEN_SECRET`, `DB_PASSWORD`, `SMTP_PASSWORD`, `VITE_PRIMEVUE_LICENSE_KEY`) must not be committed to the repository. `.env` files containing real values must be excluded via `.gitignore`.
