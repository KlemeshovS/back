from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status
from psycopg.errors import UniqueViolation

from app.database import get_connection, init_db
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


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/users/register",
    response_model=StatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(payload: RegisterUserRequest) -> StatusResponse:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (username)
                    VALUES (%s)
                    RETURNING username;
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

    return StatusResponse(status="created", username=user["username"])


@app.post("/users/score", response_model=UserScoreResponse)
def update_score(payload: UpdateScoreRequest) -> UserScoreResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
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
            detail="Username not found",
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
