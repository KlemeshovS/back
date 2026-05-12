from __future__ import annotations

from fastapi import status
from psycopg.errors import UniqueViolation

from app.core.errors import ApiError, ApiErrorCode
from app.core.usernames import normalize_public_username
from app.db.database import get_connection
from app.domain.schemas import FriendListResponse, FriendResponse, FriendshipStatus
from app.services.user_service import build_avatar_url

_FRIENDS_LIMIT = 200


def _build_friend_response(row: dict, current_user_id: int) -> FriendResponse:
    is_requester = row["requester_id"] == current_user_id
    other_username = row["requester_username"] if not is_requester else row["addressee_username"]
    other_avatar = row["requester_avatar"] if not is_requester else row["addressee_avatar"]
    other_id = row["requester_id"] if not is_requester else row["addressee_id"]
    return FriendResponse(
        user_id=other_id,
        username=other_username,
        avatar_url=build_avatar_url(other_avatar),
        friendship_id=row["id"],
        status=FriendshipStatus(row["status"]),
        is_requester=is_requester,
        created_at=row["created_at"],
    )


_FRIENDSHIP_SELECT = """
    SELECT
        f.id,
        f.requester_id,
        f.addressee_id,
        f.status,
        f.created_at,
        ru.username  AS requester_username,
        ru.avatar_path AS requester_avatar,
        au.username  AS addressee_username,
        au.avatar_path AS addressee_avatar
    FROM friendships f
    JOIN users ru ON ru.id = f.requester_id
    JOIN users au ON au.id = f.addressee_id
"""


def send_friend_request(current_user_id: int, target_username: str) -> FriendResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # resolve target user
            cur.execute(
                "SELECT id, username FROM users WHERE username = %s AND account_status = 'active';",
                (target_username,),
            )
            target = cur.fetchone()
            if target is None or not normalize_public_username(target["username"]):
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.USER_NOT_FOUND,
                    message="User not found",
                )

            if target["id"] == current_user_id:
                raise ApiError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ApiErrorCode.CANNOT_ADD_SELF,
                    message="Cannot send friend request to yourself",
                )

            # check if any relationship already exists in either direction
            cur.execute(
                """
                SELECT id, status, requester_id
                FROM friendships
                WHERE (requester_id = %s AND addressee_id = %s)
                   OR (requester_id = %s AND addressee_id = %s);
                """,
                (current_user_id, target["id"], target["id"], current_user_id),
            )
            existing = cur.fetchone()
            if existing:
                if existing["status"] == "accepted":
                    raise ApiError(
                        status_code=status.HTTP_409_CONFLICT,
                        code=ApiErrorCode.ALREADY_FRIENDS,
                        message="Already friends with this user",
                    )
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.FRIEND_REQUEST_ALREADY_SENT,
                    message="Friend request already exists",
                )

            # check limit
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM friendships
                WHERE (requester_id = %s OR addressee_id = %s)
                  AND status = 'accepted';
                """,
                (current_user_id, current_user_id),
            )
            if cur.fetchone()["cnt"] >= _FRIENDS_LIMIT:
                raise ApiError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ApiErrorCode.FRIENDS_LIMIT_REACHED,
                    message=f"Friends limit of {_FRIENDS_LIMIT} reached",
                )

            try:
                cur.execute(
                    """
                    INSERT INTO friendships (requester_id, addressee_id, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id, requester_id, addressee_id, status, created_at;
                    """,
                    (current_user_id, target["id"]),
                )
                row = cur.fetchone()
            except UniqueViolation as exc:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.FRIEND_REQUEST_ALREADY_SENT,
                    message="Friend request already exists",
                ) from exc

        conn.commit()

        # fetch full row with usernames
        with conn.cursor() as cur:
            cur.execute(
                _FRIENDSHIP_SELECT + " WHERE f.id = %s;",
                (row["id"],),
            )
            full_row = cur.fetchone()

    return _build_friend_response(full_row, current_user_id)


def get_friends(current_user_id: int, status_filter: str | None = None) -> FriendListResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            query = (
                _FRIENDSHIP_SELECT
                + """
                WHERE (f.requester_id = %s OR f.addressee_id = %s)
                """
            )
            params: list = [current_user_id, current_user_id]

            if status_filter:
                query += " AND f.status = %s"
                params.append(status_filter)

            query += " ORDER BY f.created_at DESC;"
            cur.execute(query, params)
            rows = cur.fetchall()

    items = [_build_friend_response(r, current_user_id) for r in rows]
    return FriendListResponse(items=items, total=len(items))


def respond_to_friend_request(
    current_user_id: int,
    friendship_id: int,
    action: str,
) -> FriendResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, requester_id, addressee_id, status
                FROM friendships
                WHERE id = %s;
                """,
                (friendship_id,),
            )
            friendship = cur.fetchone()

            if friendship is None or friendship["addressee_id"] != current_user_id:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.FRIEND_REQUEST_NOT_FOUND,
                    message="Friend request not found",
                )

            if friendship["status"] != "pending":
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.FRIEND_REQUEST_NOT_FOUND,
                    message="Friend request is no longer pending",
                )

            new_status = "accepted" if action == "accept" else "declined"
            cur.execute(
                """
                UPDATE friendships
                SET status = %s, updated_at = NOW()
                WHERE id = %s;
                """,
                (new_status, friendship_id),
            )

        conn.commit()

        with conn.cursor() as cur:
            cur.execute(_FRIENDSHIP_SELECT + " WHERE f.id = %s;", (friendship_id,))
            full_row = cur.fetchone()

    return _build_friend_response(full_row, current_user_id)


def remove_friend(current_user_id: int, friendship_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM friendships
                WHERE id = %s
                  AND (requester_id = %s OR addressee_id = %s)
                RETURNING id;
                """,
                (friendship_id, current_user_id, current_user_id),
            )
            if cur.fetchone() is None:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.NOT_FRIENDS,
                    message="Friendship not found",
                )
        conn.commit()
