from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.error_handlers import (
    api_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.routes import admin, auth, docs, health, leaderboard, profile, site
from app.core.config import settings
from app.core.errors import ApiError
from app.db.database import init_db


@asynccontextmanager
async def db_lifespan(_: FastAPI):
    init_db()
    yield


@asynccontextmanager
async def noop_lifespan(_: FastAPI):
    yield


def create_app(init_database: bool = True) -> FastAPI:
    app = FastAPI(
        title="Rating Service",
        lifespan=db_lifespan if init_database else noop_lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts_list,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Staging-Key"],
    )

    static_dir = Path(__file__).resolve().parents[1] / "static"
    app.state.static_dir = static_dir
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    app.mount("/og", StaticFiles(directory=static_dir / "og"), name="og")
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(site.router)
    app.include_router(health.router)
    app.include_router(docs.router)
    app.include_router(admin.router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(leaderboard.router)

    return app
