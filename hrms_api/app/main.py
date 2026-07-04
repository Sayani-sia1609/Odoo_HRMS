"""
HRMS API - FastAPI application entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.config import settings
from app.routers import auth, profile, attendance, leave, payroll, dashboard

# Creates tables if they don't exist yet. Fine for a hackathon; swap for
# Alembic migrations if the project grows beyond the hackathon.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HRMS API",
    description="API for the Human Resource Management System (auth, profile, attendance, leave, payroll).",
    version="1.0.0",
)

origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [
    o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(attendance.router)
app.include_router(leave.router)
app.include_router(payroll.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "HRMS API"}
