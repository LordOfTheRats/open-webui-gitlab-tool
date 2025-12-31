"""Concurrency control utilities."""

import asyncio
from typing import Optional


class ConcurrencyLimiter:
    """Semaphore-based concurrency limiter for Ollama requests."""

    def __init__(self, max_concurrent: int):
        """Initialize limiter with maximum concurrent requests."""
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_concurrent = max_concurrent

    async def __aenter__(self):
        """Acquire semaphore."""
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release semaphore."""
        self._semaphore.release()

    @property
    def available(self) -> int:
        """Get number of available slots."""
        return self._semaphore._value

    @property
    def max_concurrent(self) -> int:
        """Get maximum concurrent requests."""
        return self._max_concurrent


# Global limiter instance
_limiter: Optional[ConcurrencyLimiter] = None


def get_limiter() -> ConcurrencyLimiter:
    """Get global concurrency limiter instance."""
    global _limiter
    if _limiter is None:
        from gitlab_tool.config import get_settings

        settings = get_settings()
        _limiter = ConcurrencyLimiter(settings.max_concurrent_requests)
    return _limiter


def set_limiter(limiter: ConcurrencyLimiter) -> None:
    """Set global concurrency limiter instance."""
    global _limiter
    _limiter = limiter
