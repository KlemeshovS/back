from fastapi.testclient import TestClient

from app.api.app import create_app


def build_client() -> TestClient:
    return TestClient(create_app(init_database=False))
