import time
import asyncio
from contextlib import asynccontextmanager
from typing import List


class RateLimiter:
    """
    Асинхронный рейт-лимитер для ограничения количества операций за заданный период.

    Пример:
        limiter = RateLimiter(max_calls=5, period=1.0)
        async with limiter:
            await do_something()
    """

    def __init__(self, max_calls: int, period: float) -> None:
        """
        :param max_calls: максимальное количество вызовов за указанный период
        :param period: длительность периода в секундах (например, 1.0 — это одна секунда)
        """
        if max_calls <= 0:
            raise ValueError("max_calls должен быть больше 0")
        if period <= 0:
            raise ValueError("period должен быть больше 0")

        self.max_calls: int = max_calls
        self.period: float = period
        self._timestamps: List[float] = []
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def __call__(self):
        """
        Асинхронный контекстный менеджер, ограничивающий частоту вызовов.
        """
        async with self._lock:
            now = time.monotonic()

            # Очистка устаревших вызовов
            self._timestamps = [t for t in self._timestamps if now - t < self.period]

            # Если достигнут лимит — ждём
            if len(self._timestamps) >= self.max_calls:
                sleep_time = self.period - (now - self._timestamps[0])
                await asyncio.sleep(sleep_time)
                now = time.monotonic()
                self._timestamps = [t for t in self._timestamps if now - t < self.period]

            # Фиксируем новый вызов
            self._timestamps.append(now)

        yield
