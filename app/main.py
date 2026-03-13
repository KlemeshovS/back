from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, status
from psycopg.errors import UniqueViolation

from app.config import settings
from app.database import get_connection, init_db
from app.rate_limit import rate_limiter
from app.schemas import (
    LeaderboardResponse,
    RegisterUserRequest,
    StatusResponse,
    UpdateScoreRequest,
    UserScoreResponse,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Rating Service", lifespan=lifespan)


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


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


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


def fetch_leaderboard(order: str, limit: int) -> LeaderboardResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM users;")
            total_row = cur.fetchone()
            cur.execute(
                f"""
                SELECT username, score
                FROM users
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
    return fetch_leaderboard("DESC", limit)


@app.get("/leaderboard/bottom", response_model=LeaderboardResponse)
def bottom_leaderboard(limit: int = Query(default=100, ge=1, le=100)) -> LeaderboardResponse:
    return fetch_leaderboard("ASC", limit)
