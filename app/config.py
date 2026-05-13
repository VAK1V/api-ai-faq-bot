"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    # Database
    postgres_user: str = "faq_user"
    postgres_password: str = "faq_password"
    postgres_db: str = "faq_db"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Model
    model_repo: str = "t-tech/T-lite-it-2.1-GGUF"
    model_file: str = "T-lite-it-2.1-Q4_K_M.gguf"
    max_text_length: int = 500
    max_tokens: int = 256
    n_threads: int = 4
    n_ctx: int = 4096
    temperature: float = 0.7

    # Security
    api_key: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
