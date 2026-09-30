from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Database
    database_url: str = "postgresql+asyncpg://llmsync:llmsync@localhost:5432/llmsync"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "llmsync"
    minio_secret_key: str = "llmsync123"
    minio_bucket: str = "llmsync-files"
    minio_secure: bool = False

    # App
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_origins: list[str] = ["http://localhost:3000"]

    # OAuth
    oauth_google_client_id: Optional[str] = None
    oauth_google_client_secret: Optional[str] = None
    oauth_github_client_id: Optional[str] = None
    oauth_github_client_secret: Optional[str] = None

    # Email
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@llmsync.local"

    # Retention
    retention_enabled: bool = True
    retention_days_messages: int = 90
    retention_days_files: int = 30
    retention_grace_period_days: int = 7

    # Monitoring
    sentry_dsn: Optional[str] = None

settings = Settings()
