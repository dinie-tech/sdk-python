"""Retry policy — pure decision + delay functions (no I/O, no state).

The retry loop itself (sleeping, attempt counting, ``X-Dinie-Retry-Count`` header,
401 one-shot re-auth) lives in ``http.py``. These functions are pure so they are
trivially testable with a mocked ``random``.
"""

from __future__ import annotations

import random
from email.utils import parsedate_to_datetime

#: HTTP status codes the SDK retries.
#:
#: Exactly ``{408, 429, 500, 502, 503, 504}``. 409 (Dinie semantic conflict) is
#: intentionally excluded — it signals an idempotency-key reuse or a state-machine
#: violation, not a transient failure. 401 is a one-shot re-auth handled separately
#: in the transport, orthogonal to this set.
RETRYABLE_STATUS: frozenset[int] = frozenset({408, 429, 500, 502, 503, 504})

#: Cap for ``Retry-After`` / ``Retry-After-Ms`` in seconds.
#: Any server-supplied value above this is clamped to prevent abusive wait times.
RETRY_AFTER_CAP_SECONDS: int = 60

#: Base delay for the first retry attempt (``attempt = 0``), in seconds.
INITIAL_BACKOFF_SECONDS: float = 0.5

#: Maximum backoff ceiling, in seconds (reached at ``attempt ≈ 4``).
MAX_BACKOFF_SECONDS: float = 8.0

#: Subtractive jitter fraction: the computed delay is reduced by up to this share.
JITTER_RATIO: float = 0.25


def should_retry(status: int) -> bool:
    """Return ``True`` only for the retryable status set.

    Args:
        status: HTTP status code from the response.

    Returns:
        ``True`` when the status is in ``{408, 429, 500, 502, 503, 504}``.
    """
    return status in RETRYABLE_STATUS


def retry_delay(
    attempt: int,
    *,
    retry_after: str | None = None,
    retry_after_ms: str | None = None,
) -> float:
    """Compute the seconds to wait before the next attempt.

    A parseable ``Retry-After`` / ``Retry-After-Ms`` header wins (already clamped
    to ``[0, 60]`` by ``parse_retry_after``). Otherwise uses exponential backoff
    with subtractive jitter:

        ``min(0.5 × 2^attempt, 8) × (1 − 0.25 × random())``

    Args:
        attempt: Zero-based index of the attempt just completed.
        retry_after: Value of the ``Retry-After`` response header (if present).
        retry_after_ms: Value of the ``Retry-After-Ms`` response header (if present).

    Returns:
        Seconds to sleep (a float ≥ 0).
    """
    from_header = parse_retry_after(retry_after, retry_after_ms=retry_after_ms)
    if from_header is not None:
        return from_header
    base: float = min(INITIAL_BACKOFF_SECONDS * (2.0**attempt), MAX_BACKOFF_SECONDS)
    return base * (1.0 - JITTER_RATIO * random.random())


def parse_retry_after(
    retry_after: str | None = None,
    *,
    retry_after_ms: str | None = None,
) -> float | None:
    """Parse ``Retry-After`` / ``Retry-After-Ms`` headers to seconds, capped at 60.

    Precedence (mirrors the Ruby/JS peers):

    1. ``Retry-After-Ms`` (non-standard milliseconds field) → convert to seconds.
    2. ``Retry-After`` as a delta-seconds float.
    3. ``Retry-After`` as an HTTP-date (delta from now).
    4. Returns ``None`` when nothing is parseable.

    Args:
        retry_after: Value of the ``Retry-After`` header.
        retry_after_ms: Value of the ``Retry-After-Ms`` header.

    Returns:
        Wait in seconds in ``[0, 60]``, or ``None``.
    """
    seconds = _retry_after_ms_seconds(retry_after_ms) or _retry_after_seconds(retry_after)
    if seconds is None:
        return None
    return max(0.0, min(float(seconds), float(RETRY_AFTER_CAP_SECONDS)))


def _retry_after_ms_seconds(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        ms = float(raw.strip())
        return ms / 1000.0
    except ValueError:
        return None


def _retry_after_seconds(raw: str | None) -> float | None:
    if raw is None:
        return None
    stripped = raw.strip()
    try:
        return float(stripped)
    except ValueError:
        pass
    # Try HTTP-date
    try:
        import time

        dt = parsedate_to_datetime(stripped)
        delta = dt.timestamp() - time.time()
        return max(0.0, delta)
    except Exception:  # noqa: BLE001
        return None
