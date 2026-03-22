from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.db.database import get_connection

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check() -> dict[str, str]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
    except Exception as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Service not ready",
        ) from exc

    return {"status": "ok"}
