from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/course_select"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API Keys
    MIMO_API_KEY: str = ""
    MIMO_API_BASE_URL: str = "https://api.mimo.example.com/v1"
    MIMO_MODEL: str = "mimo-v2-pro"
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""

    # Application
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = False
    LOG_LEVEL: str = "info"

    # Session
    SESSION_EXPIRE_SECONDS: int = 86400


settings = Settings()
