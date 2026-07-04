"""
Standalone authentication module for the HRMS hackathon project.

This package is self-contained: it has its own config, DB session,
User model, security helpers, and router. It does not import anything
from the rest of the app, so it can be dropped into any FastAPI project
by just doing:

    from files.router import router as auth_router
    app.include_router(auth_router)

and calling `Base.metadata.create_all(bind=engine)` once at startup
(see README.md in this folder for the 2-line wiring).
"""
