# HRMS API (FastAPI)

This is the **API layer only** for the Human Resource Management System, built
with FastAPI + SQLAlchemy + PostgreSQL. Auth is JWT-based (`python-jose`),
passwords are hashed with bcrypt (`passlib`).

Tested with a full smoke-test suite (`tests/test_api_smoke.py`, 34 checks, all
passing) covering auth, RBAC, profile, attendance, leave, and payroll flows.

## 1. Setup

```bash
cd hrms_api
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env
# edit .env -> set DATABASE_URL to your Postgres instance, and a real SECRET_KEY
```

Create the Postgres database (if it doesn't exist yet):

```sql
CREATE DATABASE hrms_db;
CREATE USER hrms_user WITH PASSWORD 'hrms_pass';
GRANT ALL PRIVILEGES ON DATABASE hrms_db TO hrms_user;
```

## 2. Run

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Tables are auto-created on startup via `Base.metadata.create_all` (fine for a
hackathon — swap for Alembic migrations later if needed).

## 3. Run the smoke test (no Postgres required, uses SQLite)

```bash
python3 tests/test_api_smoke.py
```

## 4. Auth flow

1. `POST /auth/signup` — creates a user (role: `employee` or `admin`).
   Password must be 8+ chars with an uppercase, lowercase, digit, and special
   character. Response includes `verification_token` (only because
   `DEV_RETURN_VERIFICATION_TOKEN=True` in `.env` — turn this off once real
   email sending is wired up; right now the "email" is just printed to the
   server console).
2. `POST /auth/verify-email` — body `{"token": "..."}` marks the account
   verified.
3. `POST /auth/login` — **form data** (not JSON), fields `username` (=email)
   and `password`. Returns a JWT `access_token`.
4. Send `Authorization: Bearer <access_token>` on every subsequent request.

## 5. Endpoints

| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/auth/signup` | public | Register (employee/admin) |
| POST | `/auth/verify-email` | public | Verify email with token |
| POST | `/auth/login` | public | Login, get JWT |
| GET | `/profile/me` | any | View own profile |
| PUT | `/profile/me` | any | Edit own profile (phone, address, picture) |
| GET | `/profile/` | admin | List all employees |
| GET | `/profile/{user_id}` | admin | View one employee's profile |
| PUT | `/profile/{user_id}` | admin | Edit any field of any employee |
| POST | `/attendance/checkin` | any | Check in for today |
| POST | `/attendance/checkout` | any | Check out for today |
| GET | `/attendance/me?view=daily\|weekly\|monthly` | any | Own attendance |
| GET | `/attendance/` | admin | All attendance (optional `?target_date=`) |
| GET | `/attendance/{user_id}` | admin | One employee's attendance |
| POST | `/attendance/{user_id}/manual` | admin | Manually set/correct attendance |
| POST | `/leave/apply` | any | Apply for leave |
| GET | `/leave/me` | any | Own leave requests |
| DELETE | `/leave/{leave_id}` | any | Cancel own pending leave |
| GET | `/leave/` | admin | All leave requests |
| PUT | `/leave/{leave_id}/decision` | admin | Approve/reject a leave request |
| GET | `/payroll/me` | any | View own payroll (read-only) |
| GET | `/payroll/` | admin | List all payroll records |
| GET | `/payroll/{user_id}` | admin | One employee's payroll |
| PUT | `/payroll/{user_id}` | admin | Update salary structure |
| GET | `/dashboard/employee` | any | Quick-access dashboard data |
| GET | `/dashboard/admin` | admin | Admin dashboard summary counts |

"any" = any logged-in user (employee or admin), scoped to their own data.

## 6. Project structure

```
hrms_api/
├── app/
│   ├── main.py            # FastAPI app, CORS, router registration
│   ├── config.py          # env-based settings
│   ├── database.py        # SQLAlchemy engine/session
│   ├── models.py          # User, Profile, Attendance, Leave, Payroll
│   ├── schemas.py         # Pydantic request/response models
│   ├── security.py        # password hashing + JWT
│   ├── dependencies.py    # get_current_user, RBAC guards
│   └── routers/
│       ├── auth.py
│       ├── profile.py
│       ├── attendance.py
│       ├── leave.py
│       ├── payroll.py
│       └── dashboard.py
├── tests/
│   └── test_api_smoke.py
├── requirements.txt
├── .env.example
└── README.md
```

## 7. Notes for the team

- **Frontend (React)**: point axios/fetch base URL at this service (e.g.
  `http://localhost:8000`), and CORS is already wide open (`CORS_ORIGINS=*`)
  for local dev — lock it down before any public deployment.
- **Django backend**: this FastAPI service owns auth + the endpoints above
  directly against Postgres. If Django needs to read the same data, point it
  at the same `hrms_db` database, or expose an internal endpoint here — let's
  sync on which approach before merging.
- **Database**: all tables/columns are defined in `app/models.py`. If you
  need extra fields, add them there and they'll be auto-created on next
  startup (dev only — no destructive migrations exist yet).
- IDs are UUID strings, not integers — keep that in mind on the frontend.
