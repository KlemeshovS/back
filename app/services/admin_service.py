from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import status
from psycopg.errors import UniqueViolation

from app.core.admin_auth import (
    generate_admin_access_token,
    hash_admin_access_token,
    hash_password,
    verify_password,
)
from app.core.errors import ApiError, ApiErrorCode
from app.db.database import get_connection
from app.domain.schemas import (
    AdminAuditLogEntryResponse,
    AdminAuditLogListResponse,
    AdminAuthResponse,
    AdminLoginRequest,
    AdminLogoutResponse,
    AdminMeResponse,
    AdminOverviewResponse,
    AdminRole,
    AdminUserCreateRequest,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
    ManagedUserListResponse,
    ManagedUserResponse,
    ManagedUserUpdateRequest,
)


def bootstrap_owner(login: str, password: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM admin_users
                WHERE role = 'owner'
                LIMIT 1;
                """
            )
            existing_owner = cur.fetchone()
            if existing_owner is not None:
                return

            cur.execute(
                """
                INSERT INTO admin_users (login, password_hash, role, is_active)
                VALUES (%s, %s, %s, TRUE);
                """,
                (login, hash_password(password), AdminRole.OWNER.value),
            )
        conn.commit()


def authenticate_admin(payload: AdminLoginRequest) -> AdminAuthResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, login, password_hash, role, is_active
                FROM admin_users
                WHERE login = %s;
                """,
                (payload.login,),
            )
            admin = cur.fetchone()

            if admin is None or not verify_password(payload.password, admin["password_hash"]):
                raise ApiError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code=ApiErrorCode.ADMIN_INVALID_CREDENTIALS,
                    message="Invalid admin credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if not admin["is_active"]:
                raise ApiError(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code=ApiErrorCode.ADMIN_INACTIVE,
                    message="Admin account is inactive",
                )

            access_token = generate_admin_access_token()
            token_hash = hash_admin_access_token(access_token)

            cur.execute(
                """
                UPDATE admin_users
                SET auth_token_hash = %s,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (token_hash, admin["id"]),
            )
            _insert_audit_log(
                cur,
                admin_id=admin["id"],
                admin_login=admin["login"],
                action="admin.login",
                target_type="admin_user",
                target_id=admin["id"],
                details={"role": admin["role"]},
            )
        conn.commit()

    return AdminAuthResponse(
        access_token=access_token,
        role=admin["role"],
    )


def get_admin_by_token_hash(token_hash: str) -> dict[str, Any]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, login, role, is_active
                FROM admin_users
                WHERE auth_token_hash = %s;
                """,
                (token_hash,),
            )
            admin = cur.fetchone()

    if admin is None:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.INVALID_TOKEN,
            message="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin["is_active"]:
        raise ApiError(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.ADMIN_INACTIVE,
            message="Admin account is inactive",
        )

    return admin


def build_admin_me_response(admin: dict[str, Any]) -> AdminMeResponse:
    return AdminMeResponse(
        id=admin["id"],
        login=admin["login"],
        role=admin["role"],
        is_active=admin["is_active"],
    )


def logout_admin(current_admin: dict[str, Any]) -> AdminLogoutResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE admin_users
                SET auth_token_hash = NULL,
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (current_admin["id"],),
            )
            _insert_audit_log(
                cur,
                admin_id=current_admin["id"],
                admin_login=current_admin["login"],
                action="admin.logout",
                target_type="admin_user",
                target_id=current_admin["id"],
                details={"role": current_admin["role"]},
            )
        conn.commit()

    return AdminLogoutResponse()


def get_admin_overview() -> AdminOverviewResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM users) AS total_users,
                    (
                        SELECT COUNT(*)
                        FROM users
                        WHERE is_rating_enabled = TRUE
                    ) AS rating_enabled_users,
                    (SELECT COUNT(*) FROM admin_users) AS total_admins,
                    (SELECT COUNT(*) FROM admin_users WHERE is_active = TRUE) AS active_admins,
                    (SELECT COUNT(*) FROM admin_audit_log) AS audit_log_entries;
                """
            )
            row = cur.fetchone()

    return AdminOverviewResponse(
        total_users=row["total_users"],
        rating_enabled_users=row["rating_enabled_users"],
        total_admins=row["total_admins"],
        active_admins=row["active_admins"],
        audit_log_entries=row["audit_log_entries"],
    )


def list_managed_users(search: Optional[str], limit: int, offset: int) -> ManagedUserListResponse:
    search_term = f"%{search.strip()}%" if search else None

    with get_connection() as conn:
        with conn.cursor() as cur:
            if search_term:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM users
                    WHERE username ILIKE %s;
                    """,
                    (search_term,),
                )
                total = cur.fetchone()["total"]
                cur.execute(
                    """
                    SELECT
                        id,
                        username,
                        score,
                        is_rating_enabled,
                        created_at,
                        updated_at,
                        last_seen_at
                    FROM users
                    WHERE username ILIKE %s
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s;
                    """,
                    (search_term, limit, offset),
                )
            else:
                cur.execute("SELECT COUNT(*) AS total FROM users;")
                total = cur.fetchone()["total"]
                cur.execute(
                    """
                    SELECT
                        id,
                        username,
                        score,
                        is_rating_enabled,
                        created_at,
                        updated_at,
                        last_seen_at
                    FROM users
                    ORDER BY id DESC
                    LIMIT %s OFFSET %s;
                    """,
                    (limit, offset),
                )
            rows = cur.fetchall()

    return ManagedUserListResponse(
        items=[_build_managed_user(row) for row in rows],
        total=total,
    )


def get_managed_user(user_id: int) -> ManagedUserResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    score,
                    is_rating_enabled,
                    created_at,
                    updated_at,
                    last_seen_at
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

    if user is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.USER_NOT_FOUND,
            message="User not found",
        )

    return _build_managed_user(user)


def update_managed_user(
    user_id: int,
    payload: ManagedUserUpdateRequest,
    current_admin: dict[str, Any],
) -> ManagedUserResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, score, is_rating_enabled
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            existing_user = cur.fetchone()
            if existing_user is None:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.USER_NOT_FOUND,
                    message="User not found",
                )

            username = existing_user["username"] if payload.username is None else payload.username
            score = existing_user["score"] if payload.score is None else payload.score
            participate = (
                existing_user["is_rating_enabled"]
                if payload.participate_in_rating is None
                else payload.participate_in_rating
            )

            if participate and not username:
                raise ApiError(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    code=ApiErrorCode.USERNAME_REQUIRED_FOR_RATING,
                    message="Username is required to participate in rating",
                )

            try:
                cur.execute(
                    """
                    UPDATE users
                    SET username = %s,
                        score = %s,
                        is_rating_enabled = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING
                        id,
                        username,
                        score,
                        is_rating_enabled,
                        created_at,
                        updated_at,
                        last_seen_at;
                    """,
                    (username, score, participate, user_id),
                )
                updated_user = cur.fetchone()
            except UniqueViolation as exc:
                raise ApiError(
                    status_code=status.HTTP_409_CONFLICT,
                    code=ApiErrorCode.USERNAME_ALREADY_EXISTS,
                    message="Username already exists",
                ) from exc
            _insert_audit_log(
                cur,
                admin_id=current_admin["id"],
                admin_login=current_admin["login"],
                action="user.update",
                target_type="user",
                target_id=user_id,
                details={
                    "before": {
                        "username": existing_user["username"],
                        "score": existing_user["score"],
                        "participateInRating": existing_user["is_rating_enabled"],
                    },
                    "after": {
                        "username": updated_user["username"],
                        "score": updated_user["score"],
                        "participateInRating": updated_user["is_rating_enabled"],
                    },
                },
            )
        conn.commit()

    return _build_managed_user(updated_user)


def list_admin_users() -> AdminUserListResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, login, role, is_active, created_at, updated_at
                FROM admin_users
                ORDER BY id ASC;
                """
            )
            rows = cur.fetchall()

    return AdminUserListResponse(
        items=[_build_admin_user(row) for row in rows],
        total=len(rows),
    )


def create_admin_user(
    payload: AdminUserCreateRequest,
    current_admin: dict[str, Any],
) -> AdminUserResponse:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO admin_users (login, password_hash, role, is_active)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING id, login, role, is_active, created_at, updated_at;
                    """,
                    (
                        payload.login,
                        hash_password(payload.password),
                        AdminRole.ADMIN.value,
                    ),
                )
                admin = cur.fetchone()
                _insert_audit_log(
                    cur,
                    admin_id=current_admin["id"],
                    admin_login=current_admin["login"],
                    action="admin_user.create",
                    target_type="admin_user",
                    target_id=admin["id"],
                    details={
                        "login": admin["login"],
                        "role": admin["role"],
                        "isActive": admin["is_active"],
                    },
                )
            conn.commit()
    except UniqueViolation as exc:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code=ApiErrorCode.ADMIN_ALREADY_EXISTS,
            message="Admin login already exists",
        ) from exc

    return _build_admin_user(admin)


def update_admin_user(
    admin_id: int,
    payload: AdminUserUpdateRequest,
    current_admin: dict[str, Any],
) -> AdminUserResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, login, role, is_active, created_at, updated_at
                FROM admin_users
                WHERE id = %s;
                """,
                (admin_id,),
            )
            existing_admin = cur.fetchone()
            if existing_admin is None:
                raise ApiError(
                    status_code=status.HTTP_404_NOT_FOUND,
                    code=ApiErrorCode.ADMIN_NOT_FOUND,
                    message="Admin not found",
                )

            is_active = existing_admin["is_active"]
            if payload.is_active is not None:
                is_active = payload.is_active

            if current_admin["id"] == admin_id and not is_active:
                raise ApiError(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code=ApiErrorCode.FORBIDDEN,
                    message="Owner cannot deactivate themselves",
                )

            updates = ["is_active = %s", "updated_at = NOW()"]
            values: list[Any] = [is_active]

            if payload.password:
                updates.append("password_hash = %s")
                values.append(hash_password(payload.password))

            cur.execute(
                f"""
                UPDATE admin_users
                SET {", ".join(updates)}
                WHERE id = %s
                RETURNING id, login, role, is_active, created_at, updated_at;
                """,
                (*values, admin_id),
            )
            updated_admin = cur.fetchone()
            _insert_audit_log(
                cur,
                admin_id=current_admin["id"],
                admin_login=current_admin["login"],
                action="admin_user.update",
                target_type="admin_user",
                target_id=admin_id,
                details={
                    "before": {
                        "isActive": existing_admin["is_active"],
                    },
                    "after": {
                        "isActive": updated_admin["is_active"],
                        "passwordChanged": bool(payload.password),
                    },
                },
            )
        conn.commit()

    return _build_admin_user(updated_admin)


def list_audit_logs(limit: int, offset: int) -> AdminAuditLogListResponse:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM admin_audit_log;")
            total = cur.fetchone()["total"]
            cur.execute(
                """
                SELECT
                    id,
                    admin_id,
                    admin_login,
                    action,
                    target_type,
                    target_id,
                    details,
                    created_at
                FROM admin_audit_log
                ORDER BY id DESC
                LIMIT %s OFFSET %s;
                """,
                (limit, offset),
            )
            rows = cur.fetchall()

    return AdminAuditLogListResponse(
        items=[_build_audit_log_entry(row) for row in rows],
        total=total,
    )


def _build_managed_user(row: dict[str, Any]) -> ManagedUserResponse:
    return ManagedUserResponse(
        id=row["id"],
        username=row["username"],
        score=row["score"],
        participate_in_rating=row["is_rating_enabled"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_seen_at=row["last_seen_at"],
    )


def _build_admin_user(row: dict[str, Any]) -> AdminUserResponse:
    return AdminUserResponse(
        id=row["id"],
        login=row["login"],
        role=row["role"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _build_audit_log_entry(row: dict[str, Any]) -> AdminAuditLogEntryResponse:
    return AdminAuditLogEntryResponse(
        id=row["id"],
        admin_id=row["admin_id"],
        admin_login=row["admin_login"],
        action=row["action"],
        target_type=row["target_type"],
        target_id=row["target_id"],
        details=row["details"] or {},
        created_at=row["created_at"],
    )


def _insert_audit_log(
    cur,
    *,
    admin_id: int,
    admin_login: str,
    action: str,
    target_type: str,
    target_id: Optional[int],
    details: dict[str, Any],
) -> None:
    cur.execute(
        """
        INSERT INTO admin_audit_log (
            admin_id,
            admin_login,
            action,
            target_type,
            target_id,
            details
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb);
        """,
        (
            admin_id,
            admin_login,
            action,
            target_type,
            target_id,
            json.dumps(details),
        ),
    )
