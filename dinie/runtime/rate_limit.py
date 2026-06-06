"""Rate-limit tracking for the Dinie Python SDK.

Parses the three ``X-RateLimit-*`` response headers and holds the most recent
snapshot for the transport layer to expose as ``client.rate_limit``.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RateLimit:
    """Snapshot of the rate-limit state read from the most recent API response.

    All fields are non-nullable; ``RateLimitTracker.parse`` returns ``None``
    (not a partial) when any header is missing or unparseable.

    Attributes:
        limit: Window ceiling (``X-RateLimit-Limit``).
        remaining: Requests left in the current window (``X-RateLimit-Remaining``).
        reset_at: UTC datetime when the window resets (``X-RateLimit-Reset``).
    """

    limit: int
    remaining: int
    reset_at: datetime


class RateLimitTracker:
    """Parses ``X-RateLimit-*`` headers and caches the most recent snapshot.

    All-or-nothing: a missing or unparseable header makes ``parse`` return ``None``
    and ``update`` keeps the previous snapshot rather than clobbering it.
    """

    LIMIT_HEADER = "x-ratelimit-limit"
    REMAINING_HEADER = "x-ratelimit-remaining"
    RESET_HEADER = "x-ratelimit-reset"

    # ``X-RateLimit-Reset`` values >= this are read as an absolute Unix epoch;
    # anything below is treated as a delta in seconds from now. 1e9 seconds
    # is ~2001-09 — well above any "seconds until reset" while below every real epoch.
    EPOCH_THRESHOLD_SECONDS: float = 1_000_000_000.0

    def __init__(self) -> None:
        self._current: RateLimit | None = None

    @property
    def snapshot(self) -> RateLimit | None:
        """Latest parsed snapshot, or ``None`` before the first valid response."""
        return self._current

    def update(self, headers: Mapping[str, str]) -> None:
        """Fold a response's headers into the snapshot.

        A response without valid ``X-RateLimit-*`` headers leaves the snapshot
        untouched — it does not reset it to ``None``.

        Args:
            headers: Response headers (case-insensitive lookup).
        """
        parsed = self.parse(headers)
        if parsed is not None:
            self._current = parsed

    @classmethod
    def parse(cls, headers: Mapping[str, str]) -> RateLimit | None:
        """Parse the three ``X-RateLimit-*`` headers into a ``RateLimit``, or ``None``.

        Returns ``None`` when any header is absent or contains an unparseable value.

        Args:
            headers: Response headers (case-insensitive lookup).

        Returns:
            A frozen ``RateLimit``, or ``None``.
        """
        limit = cls._parse_count(cls._header_value(headers, cls.LIMIT_HEADER))
        remaining = cls._parse_count(cls._header_value(headers, cls.REMAINING_HEADER))
        reset_at = cls._parse_reset(cls._header_value(headers, cls.RESET_HEADER))
        if limit is None or remaining is None or reset_at is None:
            return None
        return RateLimit(limit=limit, remaining=remaining, reset_at=reset_at)

    @classmethod
    def _parse_count(cls, raw: str | None) -> int | None:
        if raw is None:
            return None
        try:
            value = int(raw.strip())
            return value if value >= 0 else None
        except ValueError:
            return None

    @classmethod
    def _parse_reset(cls, raw: str | None) -> datetime | None:
        if raw is None:
            return None
        try:
            seconds = float(raw.strip())
        except ValueError:
            return None
        if seconds < 0:
            return None
        if seconds >= cls.EPOCH_THRESHOLD_SECONDS:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        return datetime.fromtimestamp(time.time() + seconds, tz=timezone.utc)

    @classmethod
    def _header_value(cls, headers: Mapping[str, str], name: str) -> str | None:
        target = name.lower()
        for key, value in headers.items():
            if key.lower() == target:
                return value
        return None
