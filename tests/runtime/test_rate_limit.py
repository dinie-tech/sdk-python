"""Tests for dinie.runtime.rate_limit."""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from dinie.runtime.rate_limit import RateLimit, RateLimitTracker

LIMIT_H = RateLimitTracker.LIMIT_HEADER
REMAINING_H = RateLimitTracker.REMAINING_HEADER
RESET_H = RateLimitTracker.RESET_HEADER


def _headers(limit: str = "100", remaining: str = "42", reset: str = "120") -> dict[str, str]:
    return {LIMIT_H: limit, REMAINING_H: remaining, RESET_H: reset}


class TestRateLimitTrackerParse:
    def test_parse_delta_seconds(self) -> None:
        before = time.time()
        rl = RateLimitTracker.parse(_headers(reset="120"))
        after = time.time()
        assert rl is not None
        assert rl.limit == 100
        assert rl.remaining == 42
        # reset_at is approximately now + 120s
        expected_ts = before + 120.0
        actual_ts = rl.reset_at.timestamp()
        assert expected_ts <= actual_ts <= after + 121.0

    def test_parse_epoch_timestamp(self) -> None:
        epoch_ts = 1_700_000_000  # well above threshold
        rl = RateLimitTracker.parse(_headers(reset=str(epoch_ts)))
        assert rl is not None
        assert rl.reset_at == datetime.fromtimestamp(epoch_ts, tz=timezone.utc)

    def test_missing_header_returns_none(self) -> None:
        assert RateLimitTracker.parse({LIMIT_H: "100", REMAINING_H: "42"}) is None
        assert RateLimitTracker.parse({LIMIT_H: "100", RESET_H: "120"}) is None
        assert RateLimitTracker.parse({REMAINING_H: "42", RESET_H: "120"}) is None

    def test_invalid_count_returns_none(self) -> None:
        assert RateLimitTracker.parse(_headers(limit="not-a-number")) is None
        assert RateLimitTracker.parse(_headers(remaining="nan")) is None

    def test_negative_count_returns_none(self) -> None:
        assert RateLimitTracker.parse(_headers(limit="-1")) is None

    def test_invalid_reset_returns_none(self) -> None:
        assert RateLimitTracker.parse(_headers(reset="bad")) is None

    def test_case_insensitive_headers(self) -> None:
        headers = {
            "X-RateLimit-Limit": "50",
            "X-RateLimit-Remaining": "10",
            "X-RateLimit-Reset": "30",
        }
        rl = RateLimitTracker.parse(headers)
        assert rl is not None
        assert rl.limit == 50
        assert rl.remaining == 10


class TestRateLimitTrackerUpdate:
    def test_update_sets_snapshot(self) -> None:
        tracker = RateLimitTracker()
        assert tracker.snapshot is None
        tracker.update(_headers())
        assert tracker.snapshot is not None
        assert tracker.snapshot.limit == 100

    def test_invalid_headers_preserve_previous(self) -> None:
        tracker = RateLimitTracker()
        tracker.update(_headers(limit="100", remaining="42", reset="60"))
        previous = tracker.snapshot
        tracker.update({})  # no valid headers
        assert tracker.snapshot is previous  # unchanged


class TestRateLimitDataclass:
    def test_frozen(self) -> None:
        rl = RateLimit(limit=10, remaining=5, reset_at=datetime.now(tz=timezone.utc))
        with pytest.raises((TypeError, AttributeError)):
            rl.limit = 99  # type: ignore[misc]
