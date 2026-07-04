"""
End-to-end smoke test for the whole API, run against SQLite so nobody needs
a running Postgres instance just to sanity-check the code.

Run with:  python3 tests/test_api_smoke.py   (from the project root)
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./tests/smoke_test.db"

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch engine creation for sqlite (needs check_same_thread=False)
import sqlalchemy
_orig_create_engine = sqlalchemy.create_engine
def patched_create_engine(url, **kwargs):
    kwargs.pop("pool_pre_ping", None)
    if url.startswith("sqlite"):
        return _orig_create_engine(url, connect_args={"check_same_thread": False})
    return _orig_create_engine(url, **kwargs)
sqlalchemy.create_engine = patched_create_engine

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        raise SystemExit(1)

# Health check
r = client.get("/")
check("health check", r.status_code == 200)

# Signup employee
r = client.post("/auth/signup", json={
    "employee_id": "EMP001",
    "email": "employee1@example.com",
    "password": "Passw0rd!",
    "role": "employee"
})
print(r.status_code, r.json())
check("employee signup", r.status_code == 201)
emp_token_verif = r.json()["verification_token"]

# Signup admin
r = client.post("/auth/signup", json={
    "employee_id": "ADM001",
    "email": "admin1@example.com",
    "password": "AdminPass1!",
    "role": "admin"
})
check("admin signup", r.status_code == 201)
admin_token_verif = r.json()["verification_token"]

# duplicate signup should fail
r = client.post("/auth/signup", json={
    "employee_id": "EMP001",
    "email": "employee1@example.com",
    "password": "Passw0rd!",
    "role": "employee"
})
check("duplicate signup rejected", r.status_code == 400)

# weak password rejected
r = client.post("/auth/signup", json={
    "employee_id": "EMP002",
    "email": "weakpass@example.com",
    "password": "weak",
    "role": "employee"
})
check("weak password rejected", r.status_code == 422)

# login before verify should fail
r = client.post("/auth/login", data={"username": "employee1@example.com", "password": "Passw0rd!"})
check("login before verification blocked", r.status_code == 403)

# verify email
r = client.post("/auth/verify-email", json={"token": emp_token_verif})
check("verify employee email", r.status_code == 200)
r = client.post("/auth/verify-email", json={"token": admin_token_verif})
check("verify admin email", r.status_code == 200)

# login employee
r = client.post("/auth/login", data={"username": "employee1@example.com", "password": "Passw0rd!"})
check("employee login", r.status_code == 200)
emp_token = r.json()["access_token"]
emp_headers = {"Authorization": f"Bearer {emp_token}"}

# login admin
r = client.post("/auth/login", data={"username": "admin1@example.com", "password": "AdminPass1!"})
check("admin login", r.status_code == 200)
admin_token = r.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# wrong password
r = client.post("/auth/login", data={"username": "employee1@example.com", "password": "WrongPass1!"})
check("wrong password rejected", r.status_code == 401)

# get my profile
r = client.get("/profile/me", headers=emp_headers)
check("get my profile", r.status_code == 200)

# update my profile (allowed field)
r = client.put("/profile/me", json={"phone": "9999999999", "address": "123 Street"}, headers=emp_headers)
check("update my profile", r.status_code == 200 and r.json()["profile"]["phone"] == "9999999999")

# employee cannot edit job_title via employee-only schema (field simply ignored/not present)
r = client.put("/profile/me", json={"phone": "1234567890"}, headers=emp_headers)
check("update my profile again", r.status_code == 200)

# employee tries to access admin-only list -> forbidden
r = client.get("/profile/", headers=emp_headers)
check("employee blocked from listing all profiles", r.status_code == 403)

# admin lists all profiles
r = client.get("/profile/", headers=admin_headers)
check("admin lists profiles", r.status_code == 200 and len(r.json()) == 2)

emp_user_id = [u["user"]["id"] for u in r.json() if u["user"]["employee_id"] == "EMP001"][0]

# admin edits employee profile fully
r = client.put(f"/profile/{emp_user_id}", json={"job_title": "Software Engineer", "department": "Engineering"}, headers=admin_headers)
check("admin edits employee profile", r.status_code == 200 and r.json()["profile"]["job_title"] == "Software Engineer")

# attendance check-in
r = client.post("/attendance/checkin", json={}, headers=emp_headers)
check("employee check-in", r.status_code == 201)

# duplicate check-in blocked
r = client.post("/attendance/checkin", json={}, headers=emp_headers)
check("duplicate check-in blocked", r.status_code == 400)

# check-out
r = client.post("/attendance/checkout", json={}, headers=emp_headers)
check("employee check-out", r.status_code == 200)

# get my attendance
r = client.get("/attendance/me?view=weekly", headers=emp_headers)
check("get my attendance", r.status_code == 200 and len(r.json()) == 1)

# employee blocked from all-attendance admin route
r = client.get("/attendance/", headers=emp_headers)
check("employee blocked from admin attendance list", r.status_code == 403)

# admin views employee attendance
r = client.get(f"/attendance/{emp_user_id}", headers=admin_headers)
check("admin views employee attendance", r.status_code == 200 and len(r.json()) == 1)

# apply for leave
r = client.post("/leave/apply", json={
    "leave_type": "sick",
    "start_date": "2026-08-01",
    "end_date": "2026-08-02",
    "remarks": "Fever"
}, headers=emp_headers)
check("apply for leave", r.status_code == 201)
leave_id = r.json()["id"]

# invalid date range
r = client.post("/leave/apply", json={
    "leave_type": "sick",
    "start_date": "2026-08-05",
    "end_date": "2026-08-01",
}, headers=emp_headers)
check("invalid leave date range rejected", r.status_code == 400)

# get my leaves
r = client.get("/leave/me", headers=emp_headers)
check("get my leaves", r.status_code == 200 and len(r.json()) == 1)

# employee blocked from admin leave list
r = client.get("/leave/", headers=emp_headers)
check("employee blocked from admin leave list", r.status_code == 403)

# admin approves leave
r = client.put(f"/leave/{leave_id}/decision", json={"status": "approved", "admin_comment": "Get well soon"}, headers=admin_headers)
check("admin approves leave", r.status_code == 200 and r.json()["status"] == "approved")

# employee payroll view (read-only, auto-created)
r = client.get("/payroll/me", headers=emp_headers)
check("employee views own payroll", r.status_code == 200)

# employee blocked from updating payroll (no such route exists for employee, admin-only route requires admin)
r = client.put(f"/payroll/{emp_user_id}", json={"basic_salary": 50000}, headers=emp_headers)
check("employee blocked from updating payroll", r.status_code == 403)

# admin updates payroll
r = client.put(f"/payroll/{emp_user_id}", json={"basic_salary": 50000, "allowances": 5000, "deductions": 1000}, headers=admin_headers)
check("admin updates payroll", r.status_code == 200 and r.json()["net_salary"] == 54000)

# employee sees updated payroll
r = client.get("/payroll/me", headers=emp_headers)
check("employee sees updated payroll", r.status_code == 200 and r.json()["net_salary"] == 54000)

# dashboards
r = client.get("/dashboard/employee", headers=emp_headers)
check("employee dashboard", r.status_code == 200)

r = client.get("/dashboard/admin", headers=admin_headers)
check("admin dashboard", r.status_code == 200)

# unauthenticated access blocked
r = client.get("/profile/me")
check("unauthenticated request blocked", r.status_code == 401)

print("\nALL SMOKE TESTS PASSED")
