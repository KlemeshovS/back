from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from psycopg.errors import UniqueViolation

from app.core.auth import generate_access_token, hash_access_token
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.db.database import get_connection, init_db
from app.domain.schemas import (
    AnonymousAuthResponse,
    LeaderboardResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    RatingParticipationUpdateRequest,
    RegisterUserRequest,
    ScoreUpdateRequest,
    StatusResponse,
    UpdateScoreRequest,
    UserScoreResponse,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Rating Service",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def enforce_rate_limit(key: str, limit: int, window_seconds: int, detail: str) -> None:
    allowed, retry_after = rate_limiter.check(key, limit, window_seconds)
    if allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=detail,
        headers={"Retry-After": str(retry_after)},
    )


def get_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    token = get_bearer_token(authorization)
    token_hash = hash_access_token(token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, score, is_rating_enabled
                FROM users
                WHERE auth_token_hash = %s;
                """,
                (token_hash,),
            )
            user = cur.fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def save_profile(user_id: int, username: str | None, participate_in_rating: bool) -> ProfileResponse:
    if participate_in_rating and not username:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username is required to participate in rating",
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET username = %s,
                        is_rating_enabled = %s,
                        updated_at = NOW(),
                        last_seen_at = NOW()
                    WHERE id = %s
                    RETURNING id, username, is_rating_enabled;
                    """,
                    (username, participate_in_rating, user_id),
                )
                user = cur.fetchone()
            conn.commit()
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from exc

    return ProfileResponse(
        id=user["id"],
        username=user["username"],
        participate_in_rating=user["is_rating_enabled"],
    )


@app.get("/", include_in_schema=False)
def landing_page(request: Request):
    host = request.headers.get("host", "")
    if host.startswith("wobbly.site"):
        return FileResponse(STATIC_DIR / "pages" / "landing.html")

    return HTMLResponse(content="<h1>Wobbly API</h1>", status_code=status.HTTP_200_OK)


@app.get("/privacy", include_in_schema=False)
def privacy_page(request: Request):
    host = request.headers.get("host", "")
    if host.startswith("wobbly.site"):
        return FileResponse(STATIC_DIR / "pages" / "privacy.html")

    return HTMLResponse(content="<h1>Not Found</h1>", status_code=status.HTTP_404_NOT_FOUND)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/swagger", include_in_schema=False)
def swagger_ui() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
    )


@app.get("/docs", include_in_schema=False)
def legacy_swagger_redirect() -> RedirectResponse:
    return RedirectResponse(url="/api/swagger", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/api/docs", include_in_schema=False)
def docs_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "pages" / "api-docs.html")


@app.post(
    "/auth/anonymous",
    response_model=AnonymousAuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_anonymous_user(request: Request) -> AnonymousAuthResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"anonymous-auth:ip:{client_ip}",
        limit=settings.register_rate_limit,
        window_seconds=settings.register_window_seconds,
        detail="Too many account creation attempts. Please try again later.",
    )

    access_token = generate_access_token()
    token_hash = hash_access_token(access_token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (auth_token_hash)
                VALUES (%s)
                RETURNING id;
                """,
                (token_hash,),
            )
            user = cur.fetchone()
        conn.commit()

    return AnonymousAuthResponse(user_id=user["id"], access_token=access_token)


@app.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse(
        id=current_user["id"],
        username=current_user["username"],
        participate_in_rating=current_user["is_rating_enabled"],
    )


@app.patch("/me/profile", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    username = payload.username if payload.username is not None else current_user["username"]
    return save_profile(current_user["id"], username, payload.participate_in_rating)


@app.patch("/me/rating", response_model=ProfileResponse)
def update_my_rating_participation(
    payload: RatingParticipationUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    return save_profile(
        current_user["id"],
        current_user["username"],
        payload.participate_in_rating,
    )


@app.post("/me/score", response_model=UserScoreResponse)
def update_my_score(
    payload: ScoreUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> UserScoreResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"score:ip:{client_ip}",
        limit=settings.score_ip_rate_limit,
        window_seconds=settings.score_ip_window_seconds,
        detail="Too many score updates from this IP. Please try again later.",
    )
    enforce_rate_limit(
        key=f"score:user:id:{current_user['id']}",
        limit=settings.score_username_rate_limit,
        window_seconds=settings.score_username_window_seconds,
        detail="Too many score updates for this user. Please try again later.",
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET score = %s,
                    updated_at = NOW(),
                    last_seen_at = NOW()
                WHERE id = %s
                RETURNING username, score;
                """,
                (payload.score, current_user["id"]),
            )
            user = cur.fetchone()
        conn.commit()

    return UserScoreResponse(**user)


@app.post(
    "/users/register",
    response_model=StatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(payload: RegisterUserRequest, request: Request) -> StatusResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"register:ip:{client_ip}",
        limit=settings.register_rate_limit,
        window_seconds=settings.register_window_seconds,
        detail="Too many registration attempts. Please try again later.",
    )

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username)
                    VALUES (%s)
                    RETURNING id, username;
                    """,
                    (payload.username,),
                )
                user = cur.fetchone()
            conn.commit()
    except UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from exc

    return StatusResponse(status="created", id=user["id"], username=user["username"])


@app.post("/users/score", response_model=UserScoreResponse)
def update_score(payload: UpdateScoreRequest, request: Request) -> UserScoreResponse:
    client_ip = get_client_ip(request)
    enforce_rate_limit(
        key=f"score:ip:{client_ip}",
        limit=settings.score_ip_rate_limit,
        window_seconds=settings.score_ip_window_seconds,
        detail="Too many score updates from this IP. Please try again later.",
    )
    if payload.user_id is not None:
        user_key = f"id:{payload.user_id}"
    else:
        user_key = f"username:{payload.username.lower()}"

    enforce_rate_limit(
        key=f"score:user:{user_key}",
        limit=settings.score_username_rate_limit,
        window_seconds=settings.score_username_window_seconds,
        detail="Too many score updates for this user. Please try again later.",
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            if payload.user_id is not None:
                cur.execute(
                    """
                    UPDATE users
                    SET score = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING username, score;
                    """,
                    (payload.score, payload.user_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE users
                    SET score = %s,
                        updated_at = NOW()
                    WHERE username = %s
                    RETURNING username, score;
                    """,
                    (payload.score, payload.username),
                )
            user = cur.fetchone()
        conn.commit()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserScoreResponse(**user)


def fetch_leaderboard(order: str, score_filter: str, limit: int) -> LeaderboardResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM users
                WHERE is_rating_enabled = TRUE
                  AND username IS NOT NULL
                  AND score {score_filter};
                """
            )
            total_row = cur.fetchone()
            cur.execute(
                f"""
                SELECT username, score
                FROM users
                WHERE is_rating_enabled = TRUE
                  AND username IS NOT NULL
                  AND score {score_filter}
                ORDER BY score {order}, username ASC
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return LeaderboardResponse(
        items=[UserScoreResponse(**row) for row in rows],
        total=total_row["total"],
    )


@app.get("/leaderboard/top", response_model=LeaderboardResponse)
def top_leaderboard(limit: int = Query(default=100, ge=1, le=100)) -> LeaderboardResponse:
    return fetch_leaderboard("DESC", ">= 0", limit)


@app.get("/leaderboard/bottom", response_model=LeaderboardResponse)
def bottom_leaderboard(limit: int = Query(default=100, ge=1, le=100)) -> LeaderboardResponse:
    return fetch_leaderboard("ASC", "< 0", limit)
