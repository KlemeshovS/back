from __future__ import annotations

from fastapi import status
from psycopg.errors import UniqueViolation

from app.core.errors import ApiError, ApiErrorCode
from app.core.usernames import normalize_public_username
from app.db.database import get_connection
from app.domain.schemas import FollowListResponse, FollowResponse
from app.services.user_service import build_avatar_url

_FOLLOWS_LIMIT = 500

_FOLLOW_SELECT = """
    SELECT
        f.follower_id,
        f.followed_id,
        f.created_at,
        u.username,
        u.avatar_path,
        EXISTS(
            SELECT 1 FROM follows r
            WHERE r.follower_id = f.followed_id
              AND r.followed_id = f.follower_id
        ) AS is_mutual
    FROM follows f
    JOIN users u ON u.id = f.followed_id
"""

_FOLLOWER_SELECT = """
    SELECT
        f.follower_id,
        f.followed_id,
        f.created_at,
        u.username,
        u.avatar_path,
        EXISTS(
            SELECT 1 FROM follows r
            WHERE r.follower_id = f.followed_id
              AND r.followed_id = f.follower_id
        ) AS is_mutual
    FROM follows f
    JOIN users u ON u.id = f.follower_id
"""


def _build_follow_response(row: dict, perspective_user_id: int) -> FollowResponse:
    is_follower = row["follower_id"] == perspective_user_id
    other_id = row["followed_id"] if is_follower else row["follower_id"]
    return FollowResponse(
        user_id=other_id,
        username=row["username"],
        avatar_url=build_avatar_url(row["avatar_path"]),
        is_mutual=row["is_mutual"],
        created_at=row["created_at"],
    )


def follow_user(current_user_id: int, target_username: str) -> FollowResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username FROM users WHERE username = %s AND account_status = 'active';",
                (target_username,),
            )
            target = cur.fetchone()
            if target is None or not normalize_public_username(target["username"]):
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.USER_NOT_FOUND,
                    message="Пользователь не найден",
                )

            if target["id"] == current_user_id:
                raise ApiError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ApiErrorCode.CANNOT_FOLLOW_SELF,
                    message="Нельзя подписаться на себя",
                )

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM follows WHERE follower_id = %s;",
                (current_user_id,),
            )
            if cur.fetchone()["cnt"] >= _FOLLOWS_LIMIT:
                raise ApiError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ApiErrorCode.FOLLOWS_LIMIT_REACHED,
                    message=f"Достигнут лимит подписок ({_FOLLOWS_LIMIT})",
                )

            try:
                cur.execute(
                    """
                    INSERT INTO follows (follower_id, followed_id)
                    VALUES (%s, %s)
                    RETURNING follower_id, followed_id, created_at;
                    """,
                    (current_user_id, target["id"]),
                )
                row = cur.fetchone()
            except UniqueViolation as exc:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.ALREADY_FOLLOWING,
                    message="Вы уже подписаны на этого пользователя",
                ) from exc

        conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                _FOLLOW_SELECT + " WHERE f.follower_id = %s AND f.followed_id = %s;",
                (row["follower_id"], row["followed_id"]),
            )
            full_row = cur.fetchone()

    return _build_follow_response(full_row, current_user_id)


def unfollow_user(current_user_id: int, target_user_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM follows
                WHERE follower_id = %s AND followed_id = %s
                RETURNING follower_id;
                """,
                (current_user_id, target_user_id),
            )
            if cur.fetchone() is None:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.NOT_FOLLOWING,
                    message="Вы не подписаны на этого пользователя",
                )
        conn.commit()


def get_follows(current_user_id: int) -> FollowListResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _FOLLOW_SELECT + " WHERE f.follower_id = %s ORDER BY f.created_at DESC;",
                (current_user_id,),
            )
            rows = cur.fetchall()
    items = [_build_follow_response(r, current_user_id) for r in rows]
    return FollowListResponse(items=items, total=len(items))


def get_followers(current_user_id: int) -> FollowListResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _FOLLOWER_SELECT + " WHERE f.followed_id = %s ORDER BY f.created_at DESC;",
                (current_user_id,),
            )
            rows = cur.fetchall()
    items = [
        FollowResponse(
            user_id=r["follower_id"],
            username=r["username"],
            avatar_url=build_avatar_url(r["avatar_path"]),
            is_mutual=r["is_mutual"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
    return FollowListResponse(items=items, total=len(items))


def get_mutual_follows(current_user_id: int) -> FollowListResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT f.followed_id AS user_id, u.username, u.avatar_path, f.created_at
                FROM follows f
                JOIN users u ON u.id = f.followed_id
                WHERE f.follower_id = %s
                  AND EXISTS(
                      SELECT 1 FROM follows r
                      WHERE r.follower_id = f.followed_id
                        AND r.followed_id = f.follower_id
                  )
                ORDER BY f.created_at DESC;
                """,
                (current_user_id,),
            )
            rows = cur.fetchall()
    items = [
        FollowResponse(
            user_id=r["user_id"],
            username=r["username"],
            avatar_url=build_avatar_url(r["avatar_path"]),
            is_mutual=True,
            created_at=r["created_at"],
        )
        for r in rows
    ]
    return FollowListResponse(items=items, total=len(items))
