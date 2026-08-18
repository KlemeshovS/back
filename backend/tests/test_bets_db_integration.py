from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from psycopg import connect
from psycopg.rows import dict_row

from app.core.errors import ApiError, ApiErrorCode
from app.services import bets_service

pytestmark = pytest.mark.integration_db


def _key_for(d) -> str:
    return f"{d.year}-{d.month - 1}-{d.day}"


def _insert_user(conn, username: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, is_rating_enabled, account_status)
            VALUES (%s, TRUE, 'active')
            RETURNING id;
            """,
            (username,),
        )
        user_id = cur.fetchone()["id"]
    conn.commit()
    return user_id


def _make_mutual_friends(conn, user_a: int, user_b: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s), (%s, %s);",
            (user_a, user_b, user_b, user_a),
        )
    conn.commit()


def _set_calendar(conn, user_id: int, days: dict[str, int]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET calendar_data = %s::jsonb WHERE id = %s;",
            (json.dumps(days), user_id),
        )
    conn.commit()


def _force_bet_timing(
    conn,
    bet_id: int,
    *,
    created_at: datetime | None = None,
    respond_by: datetime | None = None,
    accepted_at: datetime | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> None:
    fields, values = [], []
    for name, value in (
        ("created_at", created_at),
        ("respond_by", respond_by),
        ("accepted_at", accepted_at),
        ("start_at", start_at),
        ("end_at", end_at),
    ):
        if value is not None:
            fields.append(f"{name} = %s")
            values.append(value)
    values.append(bet_id)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE bets SET {', '.join(fields)} WHERE id = %s;", values)
    conn.commit()


@pytest.fixture()
def two_friends(migrated_test_database: str):
    with connect(migrated_test_database, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
        conn.commit()
        challenger_id = _insert_user(conn, "challenger")
        opponent_id = _insert_user(conn, "opponent")
        _make_mutual_friends(conn, challenger_id, opponent_id)
    return challenger_id, opponent_id


def _connect(migrated_test_database: str):
    return connect(migrated_test_database, row_factory=dict_row)


class TestCreateBet:
    def test_creates_pending_bet_between_mutual_friends(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sobriety", "period", 14, None)

        assert bet.status == "pending"
        assert bet.challenger.user_id == challenger_id
        assert bet.opponent.user_id == opponent_id
        assert bet.bet_type == "sobriety"

    def test_rejects_challenge_to_non_mutual_friend(self, migrated_test_database):
        with connect(migrated_test_database, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE users RESTART IDENTITY CASCADE;")
            conn.commit()
            a = _insert_user(conn, "a")
            b = _insert_user(conn, "b")
            # только одностороннее — не взаимное
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s);", (a, b)
                )
            conn.commit()

        with pytest.raises(ApiError) as exc_info:
            bets_service.create_bet(a, b, "sport", "period", 7, None)
        assert exc_info.value.code == ApiErrorCode.BET_NOT_MUTUAL_FRIEND

    def test_rejects_self_challenge(self, two_friends):
        challenger_id, _ = two_friends
        with pytest.raises(ApiError) as exc_info:
            bets_service.create_bet(challenger_id, challenger_id, "sport", "period", 7, None)
        assert exc_info.value.code == ApiErrorCode.BET_CANNOT_CHALLENGE_SELF


class TestAcceptLifecycle:
    def test_accept_starts_the_clock_and_sets_end_at(self, two_friends, migrated_test_database):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 14, None)

        accepted = bets_service.accept_bet(opponent_id, bet.id)

        assert accepted.status == "active"
        assert accepted.start_at is not None
        assert accepted.end_at is not None
        assert (accepted.end_at - accepted.start_at) >= timedelta(days=13)

    def test_only_opponent_can_accept(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        with pytest.raises(ApiError) as exc_info:
            bets_service.accept_bet(challenger_id, bet.id)
        assert exc_info.value.code == ApiErrorCode.BET_FORBIDDEN

    def test_cannot_accept_twice(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)
        bets_service.accept_bet(opponent_id, bet.id)

        with pytest.raises(ApiError) as exc_info:
            bets_service.accept_bet(opponent_id, bet.id)
        assert exc_info.value.code == ApiErrorCode.BET_INVALID_STATE


class TestDeclineCancelForfeit:
    def test_opponent_can_decline_pending_bet(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        declined = bets_service.decline_bet(opponent_id, bet.id)

        assert declined.status == "resolved"
        assert declined.resolution_type == "declined"
        assert declined.winner_id is None

    def test_challenger_cannot_decline_own_bet(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        with pytest.raises(ApiError) as exc_info:
            bets_service.decline_bet(challenger_id, bet.id)
        assert exc_info.value.code == ApiErrorCode.BET_FORBIDDEN

    def test_challenger_can_cancel_pending_bet(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        cancelled = bets_service.cancel_bet(challenger_id, bet.id)

        assert cancelled.status == "resolved"
        assert cancelled.resolution_type == "cancelled"

    def test_opponent_cannot_cancel_bet_they_did_not_create(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        with pytest.raises(ApiError) as exc_info:
            bets_service.cancel_bet(opponent_id, bet.id)
        assert exc_info.value.code == ApiErrorCode.BET_FORBIDDEN

    def test_forfeit_in_active_bet_awards_win_to_the_other_side(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)
        bets_service.accept_bet(opponent_id, bet.id)

        result = bets_service.forfeit_bet(challenger_id, bet.id)

        assert result.status == "resolved"
        assert result.resolution_type == "forfeit"
        assert result.forfeited_by == challenger_id
        assert result.winner_id == opponent_id

    def test_cannot_forfeit_a_pending_bet(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        with pytest.raises(ApiError) as exc_info:
            bets_service.forfeit_bet(challenger_id, bet.id)
        assert exc_info.value.code == ApiErrorCode.BET_INVALID_STATE


class TestLazyExpiration:
    def test_pending_bet_expires_once_respond_by_has_passed(
        self, two_friends, migrated_test_database
    ):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        with _connect(migrated_test_database) as conn:
            _force_bet_timing(
                conn, bet.id, respond_by=datetime.now(timezone.utc) - timedelta(seconds=1)
            )

        fetched = bets_service.get_bet(challenger_id, bet.id)
        assert fetched.status == "resolved"
        assert fetched.resolution_type == "expired"
        assert fetched.winner_id is None

    def test_expired_pending_bet_can_no_longer_be_accepted(
        self, two_friends, migrated_test_database
    ):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)

        with _connect(migrated_test_database) as conn:
            _force_bet_timing(
                conn, bet.id, respond_by=datetime.now(timezone.utc) - timedelta(seconds=1)
            )

        with pytest.raises(ApiError) as exc_info:
            bets_service.accept_bet(opponent_id, bet.id)
        assert exc_info.value.code == ApiErrorCode.BET_INVALID_STATE


class TestLazyResolutionSport:
    def test_active_sport_bet_resolves_naturally_once_end_at_passes(
        self, two_friends, migrated_test_database
    ):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)
        bets_service.accept_bet(opponent_id, bet.id)

        # Сдвигаем весь период пари в прошлое (7 дней, уже полностью истекших),
        # чтобы можно было честно расставить календарные дни внутри окна.
        now = datetime.now(timezone.utc)
        forced_start = now - timedelta(days=10)
        forced_end = now - timedelta(days=3)

        with _connect(migrated_test_database) as conn:
            _force_bet_timing(conn, bet.id, start_at=forced_start, end_at=forced_end)

            window_days = [(forced_start + timedelta(days=i)).date() for i in range(7)]
            # challenger: 3 спортивных дня, opponent: 1 — challenger должен выиграть
            _set_calendar(
                conn,
                challenger_id,
                {_key_for(window_days[i]): 4 for i in (0, 1, 2)},
            )
            _set_calendar(conn, opponent_id, {_key_for(window_days[0]): 4})

        resolved = bets_service.get_bet(challenger_id, bet.id)
        assert resolved.status == "resolved"
        assert resolved.resolution_type == "natural"
        assert resolved.winner_id == challenger_id
        assert resolved.result_snapshot == {"challengerValue": 3, "opponentValue": 1}

    def test_active_sport_bet_exposes_live_snapshot_before_it_resolves(
        self, two_friends, migrated_test_database
    ):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sport", "period", 7, None)
        accepted = bets_service.accept_bet(opponent_id, bet.id)

        start = accepted.start_at.date()
        with _connect(migrated_test_database) as conn:
            _set_calendar(conn, challenger_id, {_key_for(start): 4})
            _set_calendar(conn, opponent_id, {})

        live = bets_service.get_bet(challenger_id, bet.id)
        assert live.status == "active"
        assert live.live_snapshot == {"challengerValue": 1, "opponentValue": 0}
        assert live.result_snapshot is None

    def test_active_sobriety_bet_has_no_live_snapshot(self, two_friends):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sobriety", "period", 30, None)
        bets_service.accept_bet(opponent_id, bet.id)

        live = bets_service.get_bet(challenger_id, bet.id)
        assert live.status == "active"
        assert live.live_snapshot is None


class TestLazyResolutionSobriety:
    def test_sobriety_bet_resolves_early_on_first_break_before_end_at(
        self, two_friends, migrated_test_database
    ):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sobriety", "period", 30, None)
        accepted = bets_service.accept_bet(opponent_id, bet.id)

        with _connect(migrated_test_database) as conn:
            start = accepted.start_at.date()
            # opponent срывается в первый же день пари — задолго до конца 30-дневного окна.
            # (нельзя проставить "будущий" день — резолюшн честно не видит того, что ещё
            # не могло случиться: последний рассматриваемый день ограничен текущей датой)
            _set_calendar(conn, opponent_id, {_key_for(start): 1})

        # end_at всё ещё в будущем (30 дней), но резолюшн должен произойти немедленно
        resolved = bets_service.get_bet(challenger_id, bet.id)
        assert resolved.status == "resolved"
        assert resolved.resolution_type == "natural"
        assert resolved.winner_id == challenger_id

    def test_sobriety_bet_draws_if_neither_breaks_by_end_at(
        self, two_friends, migrated_test_database
    ):
        challenger_id, opponent_id = two_friends
        bet = bets_service.create_bet(challenger_id, opponent_id, "sobriety", "period", 7, None)
        bets_service.accept_bet(opponent_id, bet.id)

        with _connect(migrated_test_database) as conn:
            _force_bet_timing(
                conn, bet.id, end_at=datetime.now(timezone.utc) - timedelta(seconds=1)
            )

        resolved = bets_service.get_bet(challenger_id, bet.id)
        assert resolved.status == "resolved"
        assert resolved.winner_id is None
