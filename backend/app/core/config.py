from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "StockPilot - Inventory & POS SaaS"
    # Database connection string - MUST be set via environment variable
    # MySQL ex: mysql+pymysql://user:password@localhost:3306/dbname
    # Postgres ex: postgresql+psycopg2://user:password@localhost:5432/dbname
    database_url: str
    secret_key: str  # MUST be set via environment variable
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # Reduced from 60 for production security
    refresh_token_expire_days: int = 7
    upload_dir: str = "./uploads"

    # --- CORS ---
    cors_origins: str = "*"  # Comma-separated list; "*" for dev

    # --- Rate limiting ---
    redis_url: str | None = None  # If None, uses in-memory storage
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "5/minute"  # Stricter for login/register

    # --- Database pool ---
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800  # seconds

    # --- Logging ---
    log_level: str = "INFO"
    json_logs: bool = True

    # --- Environment ---
    environment: str = "development"  # development, staging, production

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
