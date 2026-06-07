"""Standard Webhooks v1 verification and event dispatch for the Dinie Python SDK.

Verification pipeline
---------------------
1. Extract ``webhook-id``, ``webhook-timestamp``, ``webhook-signature`` headers
   (case-insensitive).
2. Verify timestamp is within the bidirectional tolerance window.
3. Build ``signed_payload = "{webhook_id}.{webhook_timestamp}.{body}"``.
4. For each ``secret`` (supports rotation via ``list[str]``), decode the secret
   bytes, compute ``HMAC-SHA256``, base64-encode, and compare against every
   ``v1,<sig>`` token in the signature header using **``hmac.compare_digest``**
   (constant-time — no timing oracle).
5. If verified, deserialise the body JSON and look up ``body["type"]`` in
   ``EVENT_DESERIALIZERS``.
6. Return the typed ``WebhookEvent`` (or a raw one when the type is unregistered
   but ``allow_unknown`` is requested — default is to raise).

**Never** returns an unverified event; the deserialization step only runs after
the cryptographic check passes.

Registry
--------
``EVENT_DESERIALIZERS`` is populated by ``generated/events/__init__.py`` via
``register_event()`` at import time. The runtime carries only the mechanism;
domain names live in the generated layer.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Callable, Mapping
from typing import Any

from dinie.runtime.errors import DinieError

# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class WebhookError(DinieError):
    """Base class for all webhook-related errors."""


class WebhookSignatureError(WebhookError):
    """Raised when no provided secret produces a valid signature."""


class WebhookTimestampError(WebhookError):
    """Raised when the ``webhook-timestamp`` is outside the tolerance window."""


class UnknownWebhookEventError(WebhookError):
    """Raised when ``body["type"]`` is not registered in ``EVENT_DESERIALIZERS``.

    Attributes:
        event_type: The unrecognised type string from the event body.
    """

    def __init__(self, event_type: str) -> None:
        super().__init__(f"Unknown webhook event type: {event_type!r}")
        self.event_type = event_type


# ---------------------------------------------------------------------------
# Event registry
# ---------------------------------------------------------------------------

#: Maps ``body["type"]`` → deserializer callable.
#:
#: Populated by ``dinie/generated/events/__init__.py`` at import time via
#: :func:`register_event`. The runtime has no knowledge of concrete event names.
EVENT_DESERIALIZERS: dict[str, Callable[[dict[str, Any]], Any]] = {}


def register_event(
    event_type: str,
    deserializer: Callable[[dict[str, Any]], Any],
) -> None:
    """Register a generated event deserializer.

    Called by ``dinie/generated/events/<name>.py`` at module import time.

    Args:
        event_type: The ``type`` field from the event body,
            e.g. ``"credit_offer.created"``.
        deserializer: Callable that accepts the raw body dict and returns the
            typed event object.
    """
    EVENT_DESERIALIZERS[event_type] = deserializer


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WEBHOOK_ID_HEADER = "webhook-id"
WEBHOOK_TIMESTAMP_HEADER = "webhook-timestamp"
WEBHOOK_SIGNATURE_HEADER = "webhook-signature"

#: Signature prefix per Standard Webhooks v1.
SIGNATURE_VERSION = "v1"
SIGNATURE_PREFIX = f"{SIGNATURE_VERSION},"

#: Default bidirectional tolerance in seconds (5 minutes).
DEFAULT_TOLERANCE_SECONDS: int = 300

#: Optional secret prefix (Standard Webhooks convention).
_WHSEC_PREFIX = "whsec_"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract(
    *,
    headers: Mapping[str, str],
    body: str | bytes,
    secret: str | list[str],
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
) -> Any:
    """Verify and deserialise an incoming Dinie webhook event.

    This is the **only** public entry point — no partially-verified state is
    exposed.

    Args:
        headers: Request headers (case-insensitive lookup performed internally).
        body: Raw request body — ``str`` or ``bytes`` (decoded as UTF-8).
        secret: Webhook secret as a Base64-encoded string (optionally prefixed
            with ``"whsec_"``).  Pass a ``list[str]`` to support secret rotation:
            the event is accepted if **any** secret produces a matching signature.
        tolerance_seconds: Bidirectional clock-skew tolerance.  Timestamps
            outside ``[now − tolerance, now + tolerance]`` are rejected.
            Pass ``0`` to disable timestamp validation (not recommended).

    Returns:
        The deserialised typed event object, as returned by the registered
        deserializer, or a raw ``dict`` when ``body["type"]`` is in
        ``EVENT_DESERIALIZERS``.

    Raises:
        WebhookTimestampError: Timestamp header is absent or outside the
            tolerance window.
        WebhookSignatureError: No secret produces a matching signature.
        UnknownWebhookEventError: The event ``type`` is not registered.
        ValueError: A required header is missing.
    """
    body_str = body if isinstance(body, str) else body.decode("utf-8")
    secrets = [secret] if isinstance(secret, str) else secret

    # 1. Extract required headers
    webhook_id = _header(headers, WEBHOOK_ID_HEADER)
    webhook_ts_raw = _header(headers, WEBHOOK_TIMESTAMP_HEADER)
    webhook_sig_raw = _header(headers, WEBHOOK_SIGNATURE_HEADER)

    if not webhook_id:
        raise ValueError(f"Missing required webhook header: {WEBHOOK_ID_HEADER!r}")
    if not webhook_ts_raw:
        raise ValueError(f"Missing required webhook header: {WEBHOOK_TIMESTAMP_HEADER!r}")
    if not webhook_sig_raw:
        raise ValueError(f"Missing required webhook header: {WEBHOOK_SIGNATURE_HEADER!r}")

    # 2. Timestamp validation (bidirectional)
    try:
        webhook_ts = int(webhook_ts_raw)
    except ValueError:
        raise WebhookTimestampError(
            f"webhook-timestamp is not a valid integer: {webhook_ts_raw!r}"
        ) from None

    if tolerance_seconds > 0:
        now = int(time.time())
        delta = abs(now - webhook_ts)
        if delta > tolerance_seconds:
            raise WebhookTimestampError(
                f"webhook-timestamp {webhook_ts!r} is outside the "
                f"{tolerance_seconds}s tolerance window (delta={delta}s)"
            )

    # 3. Build signed payload
    signed_payload = f"{webhook_id}.{webhook_ts_raw}.{body_str}"

    # 4. Parse expected signatures from header
    #    Format: "v1,<sig1> v1,<sig2>" — space-separated
    expected_sigs = [
        token[len(SIGNATURE_PREFIX) :]
        for token in webhook_sig_raw.split()
        if token.startswith(SIGNATURE_PREFIX)
    ]
    if not expected_sigs:
        raise WebhookSignatureError(
            f"webhook-signature header contains no {SIGNATURE_VERSION!r} signatures"
        )

    # 5. Cryptographic verification — try every (secret, expected_sig) pair
    payload_bytes = signed_payload.encode("utf-8")
    verified = False
    for raw_secret in secrets:
        key = _decode_secret(raw_secret)
        computed_digest = base64.b64encode(
            hmac.new(key, payload_bytes, hashlib.sha256).digest()
        ).decode("ascii")
        for expected_sig in expected_sigs:
            if hmac.compare_digest(computed_digest, expected_sig):
                verified = True
                break
        if verified:
            break

    if not verified:
        raise WebhookSignatureError("webhook signature verification failed — no secret matched")

    # 6. Deserialise and dispatch
    body_dict: dict[str, Any] = json.loads(body_str)
    event_type = body_dict.get("type")

    if not isinstance(event_type, str):
        raise UnknownWebhookEventError("<missing>")

    deserializer = EVENT_DESERIALIZERS.get(event_type)
    if deserializer is None:
        raise UnknownWebhookEventError(event_type)

    return deserializer(body_dict)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _decode_secret(secret: str) -> bytes:
    """Decode a secret string to raw bytes for HMAC.

    Strips the optional ``"whsec_"`` prefix, then Base64-decodes.  If the
    string is not valid Base64 after prefix stripping, it is used as raw UTF-8
    bytes (allows plain-string secrets in test environments).

    Args:
        secret: Raw or ``whsec_``-prefixed Base64-encoded secret.

    Returns:
        Raw bytes to use as the HMAC key.
    """
    s = secret.removeprefix(_WHSEC_PREFIX)
    try:
        # Standard Webhooks spec: secret is base64-encoded
        return base64.b64decode(s)
    except Exception:
        # Fallback: treat as raw UTF-8 (test environments / plain secrets)
        return secret.encode("utf-8")


def _header(headers: Mapping[str, str], name: str) -> str:
    """Case-insensitive header lookup.

    Args:
        headers: Request headers mapping.
        name: Header name (lowercase canonical form).

    Returns:
        Header value, or ``""`` if not found.
    """
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return ""
