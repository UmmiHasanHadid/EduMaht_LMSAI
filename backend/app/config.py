from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings managed via environment variables"""

    # Database
    database_url: str = "sqlite:///./edumaht_lms.db"
    database_url_async: str = "sqlite+aiosqlite:///./edumaht_lms.db"

    # JWT & Security
    secret_key: str = "change-me-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 30

    # API Keys
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    google_api_key: Optional[str] = None

    # AI Tutor
    tutor_retention_days: int = 10

    # Misc
    redis_url: Optional[str] = None
    allowed_origins: str = "*"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = "noreply@edumaht.com"
    sender_password: str = "not-used"
    institution_name: str = "EduMaht"
    institution_email: str = "info@edumaht.com"
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
