"""Tests for dinie.runtime.retry."""

from __future__ import annotations

from email.utils import formatdate
from unittest.mock import patch

import pytest

from dinie.runtime.retry import (
    RETRYABLE_STATUS,
    parse_retry_after,
    retry_delay,
    should_retry,
)


class TestShouldRetry:
    def test_retryable_statuses(self) -> None:
        for status in (408, 429, 500, 502, 503, 504):
            assert should_retry(status), f"{status} should be retryable"

    def test_not_retryable(self) -> None:
        for status in (200, 201, 204, 400, 401, 403, 404, 409, 422):
            assert not should_retry(status), f"{status} should NOT be retryable"

    def test_409_not_retried(self) -> None:
        """409 is explicitly excluded — it is a Dinie semantic conflict."""
        assert not should_retry(409)

    def test_retryable_status_set_exact(self) -> None:
        assert RETRYABLE_STATUS == frozenset({408, 429, 500, 502, 503, 504})


class TestParseRetryAfter:
    def test_delta_seconds(self) -> None:
        result = parse_retry_after("30")
        assert result == pytest.approx(30.0)

    def test_delta_seconds_float(self) -> None:
        result = parse_retry_after("1.5")
        assert result == pytest.approx(1.5)

    def test_capped_at_60(self) -> None:
        """Retry-After: 120 is capped at 60s."""
        result = parse_retry_after("120")
        assert result == pytest.approx(60.0)

    def test_zero_seconds(self) -> None:
        result = parse_retry_after("0")
        assert result == pytest.approx(0.0)

    def test_negative_clamped_to_zero(self) -> None:
        result = parse_retry_after("-5")
        assert result == pytest.approx(0.0)

    def test_retry_after_ms_takes_precedence(self) -> None:
        """Retry-After-Ms wins over Retry-After when both are present."""
        result = parse_retry_after("10", retry_after_ms="5000")
        assert result == pytest.approx(5.0)

    def test_retry_after_ms_only(self) -> None:
        result = parse_retry_after(retry_after_ms="2000")
        assert result == pytest.approx(2.0)

    def test_retry_after_ms_capped(self) -> None:
        result = parse_retry_after(retry_after_ms="120000")
        assert result == pytest.approx(60.0)

    def test_none_both(self) -> None:
        assert parse_retry_after(None) is None
        assert parse_retry_after(None, retry_after_ms=None) is None

    def test_invalid_string_returns_none(self) -> None:
        assert parse_retry_after("not-a-number") is None

    def test_http_date_parseable(self) -> None:
        # Use an HTTP-date 30 seconds in the future
        import time

        future_ts = time.time() + 30.0
        http_date = formatdate(future_ts, usegmt=True)
        result = parse_retry_after(http_date)
        assert result is not None
        assert 0.0 <= result <= 30.0  # capped & non-negative

    def test_http_date_far_future_capped(self) -> None:
        import time

        future_ts = time.time() + 3600.0
        http_date = formatdate(future_ts, usegmt=True)
        result = parse_retry_after(http_date)
        assert result == pytest.approx(60.0)


class TestRetryDelay:
    def test_no_header_uses_backoff(self) -> None:
        """Without a header, delay is in [0, max_backoff]."""
        with patch("dinie.runtime.retry.random.random", return_value=0.5):
            delay = retry_delay(0)
        # 0.5 * 2^0 * (1 - 0.25 * 0.5) = 0.5 * 0.875 = 0.4375
        assert delay == pytest.approx(0.5 * 0.875)

    def test_backoff_increases_with_attempt(self) -> None:
        with patch("dinie.runtime.retry.random.random", return_value=0.0):
            d0 = retry_delay(0)
            d1 = retry_delay(1)
            d2 = retry_delay(2)
        assert d0 < d1 < d2

    def test_backoff_capped_at_max(self) -> None:
        with patch("dinie.runtime.retry.random.random", return_value=0.0):
            # attempt=10: 0.5 * 2^10 = 512 → capped at 8.0
            delay = retry_delay(10)
        assert delay == pytest.approx(8.0)

    def test_retry_after_header_wins(self) -> None:
        delay = retry_delay(0, retry_after="5")
        assert delay == pytest.approx(5.0)

    def test_retry_after_header_capped(self) -> None:
        delay = retry_delay(0, retry_after="120")
        assert delay == pytest.approx(60.0)

    def test_retry_after_ms_header_wins(self) -> None:
        delay = retry_delay(0, retry_after_ms="3000")
        assert delay == pytest.approx(3.0)
