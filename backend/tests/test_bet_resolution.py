from __future__ import annotations

from datetime import date

from app.domain.bet_resolution import (
    compute_score,
    count_sport_days,
    first_drinking_date,
    resolve_bet,
    resolve_score,
    resolve_sobriety,
    resolve_sport,
)

_START = date(2026, 1, 1)


def _key(d: date) -> str:
    return f"{d.year}-{d.month - 1}-{d.day}"


class TestComputeScore:
    def test_all_sober_days_accrue_base_plus_bonus(self):
        # 7 трезвых дней — бонус ещё x1.0 (0 полных недель на момент каждого дня).
        # none-дни вообще не хранятся как ключи в реальном calendar_data (только non-zero
        # значения когда-либо пушатся) — формула должна одинаково работать с пустым словарём.
        score = compute_score({}, _START, date(2026, 1, 7))
        assert score == 5 * 7  # 7 дней по +5, бонус x1.0 весь период

    def test_week_two_bonus_kicks_in_on_eighth_day(self):
        # Дни 1-7: consecutive_sober_days идёт 0..6 -> weeks=0 -> x1.0 каждый день (+5)
        # День 8: consecutive_sober_days=7 -> weeks=1 -> x1.2 -> ceil(5*1.2)=6
        score = compute_score({}, _START, date(2026, 1, 8))
        assert score == 5 * 7 + 6

    def test_single_little_drink_day_penalty(self):
        days = {_key(_START): 1}  # little
        score = compute_score(days, _START, _START)
        assert score == -5  # base=5, coefficient x1.0 на первый день подряд

    def test_penalty_escalates_then_caps_at_3x_after_five_days(self):
        # 5 дней подряд heavy (base=35): коэффициенты 1.0,1.5,2.5,3.5,3.0(!) — каждый день
        # ceil'ится отдельно (это то, что переносит "падение" коэффициента с 3.5 до 3.0
        # на пятый день — расхождение, которое мы намеренно фиксируем как канон Swift).
        import math

        days = {_key(_START.replace(day=d)): 3 for d in range(1, 6)}
        score = compute_score(days, _START, date(2026, 1, 5))
        per_day_coefficients = [1.0, 1.5, 2.5, 3.5, 3.0]
        expected = -sum(math.ceil(35 * c) for c in per_day_coefficients)
        assert score == expected
        # Явно фиксируем канон: 5й день подряд штрафуется МЯГЧЕ, чем 4й (3.0x < 3.5x).
        four_days_score = compute_score(
            {_key(_START.replace(day=d)): 3 for d in range(1, 5)}, _START, date(2026, 1, 4)
        )
        fifth_day_marginal_penalty = score - four_days_score
        assert fifth_day_marginal_penalty == -math.ceil(35 * 3.0)

    def test_little_sport_reduces_penalty_by_sport_bonus(self):
        days = {_key(_START): 5}  # little_sport
        score = compute_score(days, _START, _START)
        assert score == -5 + 20  # penalty(5,1)=5, +20 спорт-бонус

    def test_heavy_sport_sport_bonus_is_fully_zeroed(self):
        days = {_key(_START): 7}  # heavy_sport
        score = compute_score(days, _START, _START)
        assert score == -35  # penalty(35,1)=35, +0 спорт-бонус (полностью обнулён)

    def test_score_resets_to_zero_at_range_start_regardless_of_history(self):
        # История ДО start не должна влиять — функция ничего не знает про дни раньше `start`.
        days_before = {_key(date(2025, 12, 31)): 3}  # heavy день ДО периода
        days_in_range = {_key(_START): 0}
        score = compute_score({**days_before, **days_in_range}, _START, _START)
        assert score == 5  # один трезвый день = +5, история до периода не в счёт

    def test_drink_streak_breaks_sober_streak_bonus(self):
        # 8 трезвых дней (бонус x1.2 включается на 8й), потом один пьяный день сбрасывает
        # consecutive_sober_days, следующий трезвый день снова считается с x1.0.
        days = {_key(_START.replace(day=9)): 1}  # 9й день — little, остальные трезвые
        score = compute_score(days, _START, date(2026, 1, 10))
        # дни 1-7: +5*7 (x1.0..x1.0, недели 0..0)
        # день 8: consecutive_sober=7 -> weeks=1 -> ceil(5*1.2)=6
        # день 9: little, penalty(5,1)=5 -> -5
        # день 10: трезвый, но consecutive_sober сброшен на 8м дне -> weeks=0 -> +5
        assert score == (5 * 7) + 6 - 5 + 5


class TestCountSportDays:
    def test_counts_pure_sport_and_sport_plus_alcohol_days(self):
        days = {
            _key(_START): 4,  # sport
            _key(_START.replace(day=2)): 5,  # little_sport
            _key(_START.replace(day=3)): 1,  # little, no sport
        }
        assert count_sport_days(days, _START, date(2026, 1, 3)) == 2


class TestFirstDrinkingDate:
    def test_finds_earliest_drinking_day_in_range(self):
        days = {
            _key(_START.replace(day=5)): 1,
            _key(_START.replace(day=3)): 2,
        }
        assert first_drinking_date(days, _START, date(2026, 1, 10)) == _START.replace(day=3)

    def test_none_when_no_drinking_day_in_range(self):
        days = {_key(_START.replace(day=3)): 4}  # sport, not drinking
        assert first_drinking_date(days, _START, date(2026, 1, 10)) is None


class TestResolveSobriety:
    def test_challenger_wins_when_opponent_breaks_first(self):
        challenger = {}
        opponent = {_key(_START.replace(day=3)): 1}
        outcome = resolve_sobriety(challenger, opponent, _START, date(2026, 1, 10))
        assert outcome.winner == "challenger"

    def test_opponent_wins_when_challenger_breaks_first(self):
        challenger = {_key(_START.replace(day=2)): 1}
        opponent = {_key(_START.replace(day=5)): 1}
        outcome = resolve_sobriety(challenger, opponent, _START, date(2026, 1, 10))
        assert outcome.winner == "opponent"

    def test_draw_when_neither_breaks(self):
        outcome = resolve_sobriety({}, {}, _START, date(2026, 1, 10))
        assert outcome.winner is None

    def test_draw_when_both_break_same_day(self):
        challenger = {_key(_START.replace(day=4)): 1}
        opponent = {_key(_START.replace(day=4)): 2}
        outcome = resolve_sobriety(challenger, opponent, _START, date(2026, 1, 10))
        assert outcome.winner is None


class TestResolveSport:
    def test_more_sport_days_wins(self):
        challenger = {_key(_START.replace(day=d)): 4 for d in range(1, 4)}  # 3 дня
        opponent = {_key(_START.replace(day=1)): 4}  # 1 день
        outcome = resolve_sport(challenger, opponent, _START, date(2026, 1, 5))
        assert outcome.winner == "challenger"
        assert outcome.challenger_value == 3
        assert outcome.opponent_value == 1

    def test_equal_sport_days_is_draw(self):
        challenger = {_key(_START): 4}
        opponent = {_key(_START): 4}
        outcome = resolve_sport(challenger, opponent, _START, date(2026, 1, 5))
        assert outcome.winner is None


class TestResolveScore:
    def test_higher_wins_mode(self):
        challenger = {}  # весь период трезвый -> положительные очки
        opponent = {_key(_START.replace(day=d)): 3 for d in range(1, 6)}  # 5 дней heavy
        outcome = resolve_score(challenger, opponent, _START, date(2026, 1, 5), higher_wins=True)
        assert outcome.winner == "challenger"

    def test_lower_wins_mode_flips_winner(self):
        challenger = {}
        opponent = {_key(_START.replace(day=d)): 3 for d in range(1, 6)}
        outcome = resolve_score(challenger, opponent, _START, date(2026, 1, 5), higher_wins=False)
        assert outcome.winner == "opponent"  # тот, кто больше пил, "выигрывает" реверс-пари

    def test_equal_score_is_draw(self):
        outcome = resolve_score({}, {}, _START, date(2026, 1, 5), higher_wins=True)
        assert outcome.winner is None


class TestResolveBetDispatch:
    def test_dispatches_by_bet_type(self):
        assert resolve_bet("sobriety", {}, {}, _START, _START).winner is None
        assert resolve_bet("sport", {}, {}, _START, _START).winner is None
        assert resolve_bet("score_up", {}, {}, _START, _START).winner is None
        assert resolve_bet("score_down", {}, {}, _START, _START).winner is None

    def test_unknown_bet_type_raises(self):
        import pytest

        with pytest.raises(ValueError):
            resolve_bet("not_a_real_type", {}, {}, _START, _START)
