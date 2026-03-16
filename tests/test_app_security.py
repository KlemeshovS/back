from fastapi.testclient import TestClient

from app.api.app import create_app


def build_client() -> TestClient:
    app = create_app(init_database=False)
    return TestClient(app)


def test_rejects_untrusted_host_header() -> None:
    client = build_client()

    response = client.get("/health", headers={"host": "evil.example.com"})

    assert response.status_code == 400
    assert response.text == "Invalid host header"


def test_sets_cors_headers_for_allowed_origin() -> None:
    client = build_client()

    response = client.options(
        "/me",
        headers={
            "origin": "https://wobbly.site",
            "access-control-request-method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://wobbly.site"


def test_skips_cors_headers_for_unknown_origin() -> None:
    client = build_client()

    response = client.options(
        "/me",
        headers={
            "origin": "https://evil.example.com",
            "access-control-request-method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
