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
        validation_alias="DATABASE_URL",
    )
    trusted_hosts: str = Field(
        default=(
            "api.wobbly.site,staging-api.wobbly.site,wobbly.site,admin.wobbly.site,localhost,127.0.0.1,85.239.57.243,testserver"
        ),
        validation_alias="TRUSTED_HOSTS",
    )
    cors_allowed_origins: str = Field(
        default=(
            "https://wobbly.site,https://api.wobbly.site,https://admin.wobbly.site,http://localhost,http://127.0.0.1"
        ),
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    admin_bootstrap_login: str = Field(default="", validation_alias="ADMIN_BOOTSTRAP_LOGIN")
    admin_bootstrap_password: str = Field(
        default="",
        validation_alias="ADMIN_BOOTSTRAP_PASSWORD",
    )
    google_client_ids: str = Field(default="", validation_alias="GOOGLE_CLIENT_IDS")
    apple_client_ids: str = Field(default="", validation_alias="APPLE_CLIENT_IDS")
    yandex_client_ids: str = Field(default="", validation_alias="YANDEX_CLIENT_IDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        items = [item.strip() for item in value.split(",")]
        return [item for item in items if item]

    @property
    def trusted_hosts_list(self) -> list[str]:
        return self._parse_csv(self.trusted_hosts)

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return self._parse_csv(self.cors_allowed_origins)

    @property
    def google_client_ids_list(self) -> list[str]:
        return self._parse_csv(self.google_client_ids)

    @property
    def apple_client_ids_list(self) -> list[str]:
        return self._parse_csv(self.apple_client_ids)

    @property
    def yandex_client_ids_list(self) -> list[str]:
        return self._parse_csv(self.yandex_client_ids)


settings = Settings()
