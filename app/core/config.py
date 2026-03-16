from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "rating-service"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    register_rate_limit: int = 5
    register_window_seconds: int = 60
    score_ip_rate_limit: int = 120
    score_ip_window_seconds: int = 60
    score_username_rate_limit: int = 20
    score_username_window_seconds: int = 60
    database_url: str = Field(
        default="postgresql://app:app@db:5432/app",
        alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )


settings = Settings()
