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
| `REGISTRATION_ENABLED` | no | `true` | Whether people may sign up on the registration page. Set to `false` (with invitations on) for an invite-only instance |
| `INVITATIONS_ENABLED` | no | `true` | Whether admins and lab admins may invite people by email. When `false`, pending invitation links stop working too |
| `TWO_FACTOR_REQUIRED` | no | `false` | Require two-factor authentication: password + one-time code from an authenticator app, or a passkey (with fingerprint, face or PIN). Users without a second factor must set one up right after signing in |
| `TOTP_ISSUER` | no | `TransAct` | Name shown for the account in authenticator apps |
| `TWO_FACTOR_LOGIN_TTL_SECONDS` | no | `300` | How long the one-time code step may take after a correct password |
| `TWO_FACTOR_ENCRYPTION_KEY` | recommended | `JWT_SECRET_KEY` | Encrypts the authenticator app secrets in the database (any long random string). Changing it makes the stored secrets unreadable: affected users can still sign in with a recovery code, or need a two-factor reset |
| `MAX_FAILED_LOGIN_ATTEMPTS` | no | `10` | Wrong passwords in a row before the account is locked. An admin has to unlock it. `0` turns locking off |
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

#### Sign-up and two-factor authentication

| Setup | `REGISTRATION_ENABLED` | `INVITATIONS_ENABLED` |
|-------|------------------------|-----------------------|
| Open sign-up and invitations (default) | `true` | `true` |
| Invite only | `false` | `true` |
| Open sign-up, no invitations | `true` | `false` |
| Closed (existing accounts only) | `false` | `false` |

The first administrator can always be created on the setup page of a fresh instance.

With `TWO_FACTOR_REQUIRED=true`, a sign-in only counts once a second factor was used. Sessions
from before it was turned on have to set one up (users without one) or sign in again (users who
have one). Users who lost their authenticator app and recovery codes can be reset by an admin
under *Settings → Admin → Users → Reset two-factor*. API keys are unaffected.

Accounts locked after `MAX_FAILED_LOGIN_ATTEMPTS` wrong passwords are unlocked under
*Settings → Admin → Users → Unlock account*. Existing sessions of a locked account keep working;
only new sign-ins are refused. If no admin can sign in any more, unlock one on the server:

```sh
cd backend
python -m app.unlock_user admin@example.com            # add --reset-two-factor if needed
```

### Frontend

| Variable | File | Description |
|----------|------|--------------|
| `VITE_API_BASE_URL` | `.env.development` / `.env.production` | Base URL of the backend API |

> Secrets (`JWT_SECRET_KEY`, `RESET_PASSWORD_TOKEN_SECRET`, `VERIFICATION_TOKEN_SECRET`, `DB_PASSWORD`, `SMTP_PASSWORD`) must not be committed to the repository. `.env` files containing real values must be excluded via `.gitignore`.
