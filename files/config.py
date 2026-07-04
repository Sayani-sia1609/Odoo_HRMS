"""
Configuration for the auth module.

Reads from environment variables / a `.env` file. Kept separate from the
main app's config on purpose so this module has zero dependency on the
rest of the project.
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    APP_ENV: str = "development"

    # Point this at the SAME database as the rest of the app so the
    # `users` table is shared. Example for Postgres:
    # postgresql+psycopg2://hrms_user:hrms_pass@localhost:5432/hrms_db
    DATABASE_URL: str = "postgresql+psycopg2://hrms_user:hrms_pass@localhost:5432/hrms_db"

    # JWT settings
    SECRET_KEY: str = "dev-only-secret-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email verification token expiry
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # If True, /auth/signup returns the verification token directly in the
    # JSON response, so you can test the flow without a real mail server.
    # Flip to False once real email sending is wired up.
    DEV_RETURN_VERIFICATION_TOKEN: bool = False

    # Frontend URL that handles email verification links.
    FRONTEND_VERIFY_URL: str = "http://localhost:3000/verify-email"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"prod", "production"}

    @model_validator(mode="after")
    def validate_security_settings(self):
        if self.is_production:
            if self.SECRET_KEY == "dev-only-secret-change-this" or len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be set to a strong random value in production")
            if self.DEV_RETURN_VERIFICATION_TOKEN:
                raise ValueError("DEV_RETURN_VERIFICATION_TOKEN must be false in production")
        return self


auth_settings = AuthSettings()
