from app.core.config import Settings


def test_settings_read_env_names_without_using_model_field_aliases() -> None:
    settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/app_test",
        TRUSTED_HOSTS="example.com, api.wobbly.site",
        CORS_ALLOWED_ORIGINS="https://example.com, https://wobbly.site",
        ADMIN_BOOTSTRAP_LOGIN="owner",
        ADMIN_BOOTSTRAP_PASSWORD="secret-password",
    )

    assert settings.database_url == "postgresql://user:pass@localhost:5432/app_test"
    assert settings.trusted_hosts == "example.com, api.wobbly.site"
    assert settings.cors_allowed_origins == "https://example.com, https://wobbly.site"
    assert settings.admin_bootstrap_login == "owner"
    assert settings.admin_bootstrap_password == "secret-password"


def test_settings_parse_csv_lists() -> None:
    settings = Settings(
        TRUSTED_HOSTS="example.com, api.wobbly.site, , localhost",
        CORS_ALLOWED_ORIGINS="https://example.com, , https://wobbly.site",
    )

    assert settings.trusted_hosts_list == [
        "example.com",
        "api.wobbly.site",
        "localhost",
    ]
    assert settings.cors_allowed_origins_list == [
        "https://example.com",
        "https://wobbly.site",
    ]
