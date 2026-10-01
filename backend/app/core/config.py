from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "Intelligent Phishing Email Detection Platform"
    API_V1_STR: str = "/api/v1"

    # Security - JWT_SECRET has no default: the app refuses to start without it.
    JWT_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database (SQLite by default; set DATABASE_URL for Postgres)
    DATABASE_URL: str = "sqlite:///./phishing.db"

    # CORS - comma separated list of allowed frontend origins
    FRONTEND_ORIGINS: str = "http://localhost:5173"

    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024

    # Optional external threat intel (only used when set)
    VT_API_KEY: str = ""
    URLHAUS_AUTH_KEY: str = ""
    TI_TIMEOUT_SECONDS: float = 3.0
    TI_CACHE_HOURS: int = 24
    TI_MAX_LOOKUPS_PER_SCAN: int = 10

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]


settings = Settings()
