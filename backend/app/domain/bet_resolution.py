from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

# Legacy DrinkLevel int values (совпадают с /me/calendar и с клиентами):
# 0=none, 1=little, 2=medium, 3=heavy, 4=sport, 5=little_sport, 6=medium_sport, 7=heavy_sport
_DRINKING_VALUES = frozenset({1, 2, 3, 5, 6, 7})
_SPORT_VALUES = frozenset({4, 5, 6, 7})

_BONUS_COEFFICIENTS = {0: 1.0, 1: 1.2, 2: 1.5, 3: 1.75}
_BONUS_DEFAULT = 2.0

_PENALTY_COEFFICIENTS = {1: 1.0, 2: 1.5, 3: 2.5, 4: 3.5}
_PENALTY_DEFAULT = 3.0  # каноничная версия — Swift (ProgressCalculator.swift)


def _calendar_key(d: date) -> str:
    # Формат ключа календаря — month 0-based, как на сервере и в Swift-клиенте.
    return f"{d.year}-{d.month - 1}-{d.day}"


def _date_range(start: date, end: date) -> list[date]:
    if end < start:
        return []
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]


def _bonus_coefficient(weeks: int) -> float:
    return _BONUS_COEFFICIENTS.get(weeks, _BONUS_DEFAULT)


def _penalty(base: int, consecutive_days: int) -> int:
    coefficient = _PENALTY_COEFFICIENTS.get(consecutive_days, _PENALTY_DEFAULT)
    return math.ceil(base * coefficient)


def compute_score(calendar_days: dict[str, int], start: date, end: date) -> int:
    """Очки за период [start, end] включительно, начиная с нуля на `start`.

    Портирует day-by-day алгоритм из Wobbly/Managers/ProgressCalculator.swift (calculate()),
    но без findFirstMarkedDate/3650-дневного окна — тут период уже задан извне (стартом пари).
    """
    progress = 0
    consecutive_drink_days = 0
    consecutive_sober_days = 0

    for day in _date_range(start, end):
        level = calendar_days.get(_calendar_key(day), 0)

        if level == 0:  # none
            weeks = consecutive_sober_days // 7
            progress += math.ceil(5.0 * _bonus_coefficient(weeks))
            consecutive_drink_days = 0
            consecutive_sober_days += 1
        elif level == 4:  # sport (без алкоголя)
            weeks = consecutive_sober_days // 7
            progress += math.ceil(20.0 * _bonus_coefficient(weeks))
            consecutive_drink_days = 0
            consecutive_sober_days += 1
        elif level == 1:  # little
            consecutive_drink_days += 1
            consecutive_sober_days = 0
            progress -= _penalty(5, consecutive_drink_days)
        elif level == 5:  # little_sport
            consecutive_drink_days += 1
            consecutive_sober_days = 0
            progress += -_penalty(5, consecutive_drink_days) + 20
        elif level == 2:  # medium
            consecutive_drink_days += 1
            consecutive_sober_days = 0
            progress -= _penalty(20, consecutive_drink_days)
        elif level == 6:  # medium_sport
            consecutive_drink_days += 1
            consecutive_sober_days = 0
            progress += -_penalty(20, consecutive_drink_days) + 5
        elif level == 3:  # heavy
            consecutive_drink_days += 1
            consecutive_sober_days = 0
            progress -= _penalty(35, consecutive_drink_days)
        elif level == 7:  # heavy_sport
            consecutive_drink_days += 1
            consecutive_sober_days = 0
            progress -= _penalty(35, consecutive_drink_days)
        # любое другое (в т.ч. unknown=-1) — не встречается в calendar_data, no-op

    return progress


def count_sport_days(calendar_days: dict[str, int], start: date, end: date) -> int:
    return sum(
        1
        for day in _date_range(start, end)
        if calendar_days.get(_calendar_key(day), 0) in _SPORT_VALUES
    )


def first_drinking_date(calendar_days: dict[str, int], start: date, end: date) -> Optional[date]:
    for day in _date_range(start, end):
        if calendar_days.get(_calendar_key(day), 0) in _DRINKING_VALUES:
            return day
    return None


class BetOutcome:
    """Результат резолюшна: победитель ('challenger'/'opponent'/None=ничья) + числа для снапшота."""

    def __init__(
        self,
        winner: Optional[str],
        challenger_value,
        opponent_value,
    ) -> None:
        self.winner = winner
        self.challenger_value = challenger_value
        self.opponent_value = opponent_value


def resolve_sobriety(
    challenger_days: dict[str, int],
    opponent_days: dict[str, int],
    start: date,
    end: date,
) -> BetOutcome:
    c_break = first_drinking_date(challenger_days, start, end)
    o_break = first_drinking_date(opponent_days, start, end)

    if c_break is None and o_break is None:
        winner = None
    elif c_break is None:
        winner = "challenger"
    elif o_break is None:
        winner = "opponent"
    elif c_break == o_break:
        winner = None
    else:
        winner = "opponent" if c_break < o_break else "challenger"

    return BetOutcome(
        winner=winner,
        challenger_value=c_break.isoformat() if c_break else None,
        opponent_value=o_break.isoformat() if o_break else None,
    )


def resolve_sport(
    challenger_days: dict[str, int],
    opponent_days: dict[str, int],
    start: date,
    end: date,
) -> BetOutcome:
    c = count_sport_days(challenger_days, start, end)
    o = count_sport_days(opponent_days, start, end)
    if c == o:
        winner = None
    else:
        winner = "challenger" if c > o else "opponent"
    return BetOutcome(winner=winner, challenger_value=c, opponent_value=o)


def resolve_score(
    challenger_days: dict[str, int],
    opponent_days: dict[str, int],
    start: date,
    end: date,
    *,
    higher_wins: bool,
) -> BetOutcome:
    c = compute_score(challenger_days, start, end)
    o = compute_score(opponent_days, start, end)
    if c == o:
        winner = None
    elif higher_wins:
        winner = "challenger" if c > o else "opponent"
    else:
        winner = "challenger" if c < o else "opponent"
    return BetOutcome(winner=winner, challenger_value=c, opponent_value=o)


def resolve_bet(
    bet_type: str,
    challenger_days: dict[str, int],
    opponent_days: dict[str, int],
    start: date,
    end: date,
) -> BetOutcome:
    if bet_type == "sobriety":
        return resolve_sobriety(challenger_days, opponent_days, start, end)
    if bet_type == "sport":
        return resolve_sport(challenger_days, opponent_days, start, end)
    if bet_type == "score_up":
        return resolve_score(challenger_days, opponent_days, start, end, higher_wins=True)
    if bet_type == "score_down":
        return resolve_score(challenger_days, opponent_days, start, end, higher_wins=False)
    raise ValueError(f"Unknown bet_type: {bet_type!r}")
