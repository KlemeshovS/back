from __future__ import annotations

import asyncio
import logging

from app.db.database import get_connection

logger = logging.getLogger(__name__)

_REVOKED_SESSION_RETENTION_DAYS = 30
_CLEANUP_INTERVAL_SECONDS = 86_400  # 24 hours


def purge_expired_sessions() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM user_sessions
                WHERE revoked_at IS NOT NULL
                  AND revoked_at < NOW() - INTERVAL '30 days';
                """
            )
            deleted = cur.rowcount
        conn.commit()
    return deleted


async def run_cleanup_loop() -> None:
    while True:
        try:
            deleted = await asyncio.to_thread(purge_expired_sessions)
            if deleted:
                logger.info("cleanup: purged %d revoked sessions", deleted)
        except Exception:
            logger.exception("cleanup: session purge failed")
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
