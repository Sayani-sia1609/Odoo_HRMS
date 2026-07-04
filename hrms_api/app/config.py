"""
Application configuration.
Reads settings from environment variables (or a .env file placed in the
project root, next to this `app` folder).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL connection string, e.g.
    # postgresql+psycopg2://hrms_user:hrms_pass@localhost:5432/hrms_db
    DATABASE_URL: str = "postgresql+psycopg2://hrms_user:hrms_pass@localhost:5432/hrms_db"

    # JWT settings
    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Email verification token expiry
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # If True, /auth/signup returns the verification token directly in the
    # JSON response so you can test the flow before a real email service is
    # wired up. Set to False once real email sending is added.
    DEV_RETURN_VERIFICATION_TOKEN: bool = True

    # Comma separated list of allowed frontend origins, e.g.
    # "http://localhost:3000,https://myapp.vercel.app"
    # Use "*" for all origins (fine for a hackathon demo).
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
