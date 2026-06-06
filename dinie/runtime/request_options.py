"""Per-call request options for the Dinie Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RequestOptions:
    """Normalized per-call overrides, accepted as the trailing ``request_options``
    argument by every public SDK method.

    A ``None`` header value removes the matching default (mirrors Ruby's nil-to-remove
    behaviour). Validation is minimal: the generated client layer validates user inputs;
    here we only freeze and expose.
    """

    #: Per-call timeout in seconds. ``None`` inherits the client default.
    timeout: float | None = None
    #: Explicit idempotency key (overrides the auto-generated one).
    idempotency_key: str | None = None
    #: Per-call header overrides. A ``None`` value removes the matching default header.
    headers: dict[str, str | None] | None = None
    #: Per-call retry budget override. ``None`` inherits the client default.
    max_retries: int | None = None

    @classmethod
    def coerce(cls, value: RequestOptions | dict[str, Any] | None) -> RequestOptions:
        """Return a RequestOptions, accepting an instance, a plain dict, or None.

        Args:
            value: ``RequestOptions`` (pass-through), ``dict`` (unpacked into the
                constructor), or ``None`` (returns a default-filled instance).

        Returns:
            A frozen ``RequestOptions``.
        """
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(**value)
        return cls()
