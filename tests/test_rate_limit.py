from app.core.rate_limit import SlidingWindowRateLimiter


def test_rate_limiter_allows_until_limit_is_reached() -> None:
    limiter = SlidingWindowRateLimiter()

    allowed_first, retry_first = limiter.check("user", limit=2, window_seconds=60)
    allowed_second, retry_second = limiter.check("user", limit=2, window_seconds=60)
    allowed_third, retry_third = limiter.check("user", limit=2, window_seconds=60)

    assert allowed_first is True
    assert retry_first == 0
    assert allowed_second is True
    assert retry_second == 0
    assert allowed_third is False
    assert retry_third >= 1
