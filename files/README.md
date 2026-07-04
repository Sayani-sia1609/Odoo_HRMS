# HRMS Auth Module

Self-contained authentication package for FastAPI.

This folder is currently named `files/`. All imports are package-relative, so
it also works if you rename it to `auth/` later.

## Module Contents

```
files/
├── config.py         # environment settings (DB, JWT, verification URLs)
├── database.py       # SQLAlchemy engine/session/Base
├── models.py         # User model and RoleEnum
├── schemas.py        # request/response DTOs
├── security.py       # bcrypt + JWT helpers
├── dependencies.py   # current user + role guard dependencies
└── router.py         # auth API routes
```

## Integration in main.py

```python
from fastapi import FastAPI

from files.database import Base, engine
from files.router import router as auth_router

app = FastAPI()

Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
```

This database setup follows the same pattern as your reference `app/database.py`
(engine + SessionLocal + Base + get_db with `pool_pre_ping=True`).

## Environment Variables

### Hackathon / local

```
APP_ENV=development
DATABASE_URL=postgresql+psycopg2://hrms_user:hrms_pass@localhost:5432/hrms_db
SECRET_KEY=dev-only-secret-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=480
EMAIL_VERIFICATION_EXPIRE_MINUTES=1440
DEV_RETURN_VERIFICATION_TOKEN=true
FRONTEND_VERIFY_URL=http://localhost:3000/verify-email
```

### Production

```
APP_ENV=production
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:5432/<db>
SECRET_KEY=<at-least-32-char-random-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=30
EMAIL_VERIFICATION_EXPIRE_MINUTES=60
DEV_RETURN_VERIFICATION_TOKEN=false
FRONTEND_VERIFY_URL=https://your-frontend.com/verify-email
```

In production:
- `SECRET_KEY` must be strong (>= 32 chars)
- `DEV_RETURN_VERIFICATION_TOKEN` must be `false`

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | register user and send/return verification token |
| POST | `/auth/verify-email` | verify email with JSON body `{ "token": "..." }` |
| GET | `/auth/verify-email?token=...` | verify email from frontend link click |
| POST | `/auth/resend-verification` | resend verification token by email |
| POST | `/auth/login` | OAuth2 form login (`username` = email) |
| POST | `/auth/login/json` | frontend JSON login (`email`, `password`) |
| POST | `/auth/refresh` | rotate refresh token and return new access+refresh pair |
| POST | `/auth/logout` | revoke current access token and provided refresh token |
| GET | `/auth/me` | get current authenticated user |

`/auth/login/json` is the easiest endpoint for frontend apps.

## Frontend Integration Contract

### Login request

```http
POST /auth/login/json
Content-Type: application/json

{
    "email": "user@company.com",
    "password": "Strong@123"
}
```

### Login response

```json
{
    "access_token": "<jwt>",
    "token_type": "bearer",
    "expires_in": 28800,
    "refresh_token": "<jwt>",
    "refresh_expires_in": 604800,
    "role": "employee",
    "employee_id": "EMP-001",
    "user_id": "uuid"
}
```

Send the token as:

```http
Authorization: Bearer <jwt>
```

Use `/auth/me` after login to bootstrap frontend user state.

Call `/auth/refresh` before access token expiry to get a new token pair.
Call `/auth/logout` with the refresh token to revoke both active tokens.

## Notes

- Password policy is enforced at signup: min 8 chars, uppercase, lowercase,
    digit, and special character.
- Verification email sending is currently a stub (`print`). Plug this into SMTP,
    SES, or SendGrid for production.
- Add CORS middleware in your main app so your frontend domain can call these routes.
