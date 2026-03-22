from fastapi import APIRouter, Query

from app.domain.schemas import LeaderboardResponse
from app.services import user_service

router = APIRouter()


@router.get("/leaderboard/top", response_model=LeaderboardResponse)
def top_leaderboard(limit: int = Query(default=100, ge=1, le=100)) -> LeaderboardResponse:
    return user_service.fetch_leaderboard("DESC", ">= 0", limit)


@router.get("/leaderboard/bottom", response_model=LeaderboardResponse)
def bottom_leaderboard(limit: int = Query(default=100, ge=1, le=100)) -> LeaderboardResponse:
    return user_service.fetch_leaderboard("ASC", "< 0", limit)
