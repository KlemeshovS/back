from collections import defaultdict, deque
from threading import Lock
from time import time


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time()

        with self._lock:
            events = self._events[key]

            while events and now - events[0] >= window_seconds:
                events.popleft()

            if len(events) >= limit:
                retry_after = max(1, int(window_seconds - (now - events[0])))
                return False, retry_after

            events.append(now)
            return True, 0


rate_limiter = SlidingWindowRateLimiter()
