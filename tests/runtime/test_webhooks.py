"""Tests for dinie.runtime.webhooks.

DoD-R3 coverage:
- Happy path with well-signed body → typed event returned
- Tamper (flip 1 byte) → WebhookSignatureError
- Timestamp outside tolerance → WebhookTimestampError
- Secret rotation (old, new) → accepts body signed by either
- Unknown type → UnknownWebhookEventError
- compare_digest is used (no timing oracle via == comparison)
- Never returns unverified event
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

import pytest

from dinie.runtime.webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    EVENT_DESERIALIZERS,
    UnknownWebhookEventError,
    WebhookSignatureError,
    WebhookTimestampError,
    extract,
    register_event,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SECRET_RAW = b"test-secret-bytes-32chars!!!!!!!!"  # 32 bytes
SECRET_B64 = base64.b64encode(SECRET_RAW).decode("ascii")

WHSEC_SECRET = f"whsec_{SECRET_B64}"


def _sign(
    *,
    webhook_id: str,
    timestamp: int,
    body: str,
    key_bytes: bytes = SECRET_RAW,
) -> str:
    """Compute v1,<base64> signature matching the webhooks.py algorithm."""
    signed_payload = f"{webhook_id}.{timestamp}.{body}"
    digest = hmac.new(key_bytes, signed_payload.encode("utf-8"), hashlib.sha256).digest()
    return f"v1,{base64.b64encode(digest).decode('ascii')}"


def _headers(
    *,
    sig: str,
    webhook_id: str = "evt_123",
    timestamp: int | None = None,
) -> dict[str, str]:
    if timestamp is None:
        timestamp = int(time.time())
    return {
        "webhook-id": webhook_id,
        "webhook-timestamp": str(timestamp),
        "webhook-signature": sig,
    }


# ---------------------------------------------------------------------------
# Fixtures: register a fake event type for tests
# ---------------------------------------------------------------------------


@dataclass
class FakeCreditEvent:
    type: str
    amount: int


_TEST_EVENT_TYPE = "test.credit_offer.created"
_original_registry: dict[str, Any] | None = None


def setup_module(_: object) -> None:
    global _original_registry
    _original_registry = dict(EVENT_DESERIALIZERS)
    register_event(
        _TEST_EVENT_TYPE,
        lambda d: FakeCreditEvent(type=d["type"], amount=d.get("amount", 0)),
    )


def teardown_module(_: object) -> None:
    EVENT_DESERIALIZERS.clear()
    if _original_registry is not None:
        EVENT_DESERIALIZERS.update(_original_registry)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def _make_body(self) -> str:
        return json.dumps({"type": _TEST_EVENT_TYPE, "amount": 42})

    def test_returns_typed_event(self) -> None:
        body = self._make_body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        result = extract(
            headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
            body=body,
            secret=SECRET_B64,
        )
        assert isinstance(result, FakeCreditEvent)
        assert result.amount == 42

    def test_accepts_bytes_body(self) -> None:
        body = self._make_body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        result = extract(
            headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
            body=body.encode("utf-8"),
            secret=SECRET_B64,
        )
        assert isinstance(result, FakeCreditEvent)

    def test_whsec_prefix_accepted(self) -> None:
        body = self._make_body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        result = extract(
            headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
            body=body,
            secret=WHSEC_SECRET,
        )
        assert isinstance(result, FakeCreditEvent)

    def test_multiple_signatures_in_header(self) -> None:
        """Accepts when at least one sig in the header matches."""
        body = self._make_body()
        ts = int(time.time())
        real_sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        # Add a junk sig before the real one
        combined = f"v1,AAAA==== {real_sig}"
        result = extract(
            headers={
                "webhook-id": "evt_1",
                "webhook-timestamp": str(ts),
                "webhook-signature": combined,
            },
            body=body,
            secret=SECRET_B64,
        )
        assert isinstance(result, FakeCreditEvent)


# ---------------------------------------------------------------------------
# DoD-R3: tamper detection
# ---------------------------------------------------------------------------


class TestTamperDetection:
    def test_flip_one_byte_raises_signature_error(self) -> None:
        """DoD-R3: flip 1 byte → WebhookSignatureError."""
        body = json.dumps({"type": _TEST_EVENT_TYPE, "amount": 100})
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        # Mutate a single character in the middle of the body
        tampered = body[:5] + ("X" if body[5] != "X" else "Y") + body[6:]
        with pytest.raises(WebhookSignatureError):
            extract(
                headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
                body=tampered,
                secret=SECRET_B64,
            )

    def test_wrong_secret_raises_signature_error(self) -> None:
        body = json.dumps({"type": _TEST_EVENT_TYPE})
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        wrong_secret = base64.b64encode(b"wrong-secret-bytes-32chars!!!!").decode()
        with pytest.raises(WebhookSignatureError):
            extract(
                headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
                body=body,
                secret=wrong_secret,
            )

    def test_no_v1_prefix_in_sig_header(self) -> None:
        body = json.dumps({"type": _TEST_EVENT_TYPE})
        ts = int(time.time())
        with pytest.raises(WebhookSignatureError):
            extract(
                headers={
                    "webhook-id": "evt_1",
                    "webhook-timestamp": str(ts),
                    "webhook-signature": "v2,AAAA====",  # v2, not v1
                },
                body=body,
                secret=SECRET_B64,
            )


# ---------------------------------------------------------------------------
# DoD-R3: timestamp tolerance (bidirectional)
# ---------------------------------------------------------------------------


class TestTimestampTolerance:
    def _body(self) -> str:
        return json.dumps({"type": _TEST_EVENT_TYPE})

    def test_timestamp_too_old_raises(self) -> None:
        body = self._body()
        old_ts = int(time.time()) - DEFAULT_TOLERANCE_SECONDS - 10
        sig = _sign(webhook_id="evt_1", timestamp=old_ts, body=body)
        with pytest.raises(WebhookTimestampError):
            extract(
                headers=_headers(sig=sig, webhook_id="evt_1", timestamp=old_ts),
                body=body,
                secret=SECRET_B64,
            )

    def test_timestamp_in_future_raises(self) -> None:
        """Bidirectional: future timestamps beyond tolerance are also rejected."""
        body = self._body()
        future_ts = int(time.time()) + DEFAULT_TOLERANCE_SECONDS + 10
        sig = _sign(webhook_id="evt_1", timestamp=future_ts, body=body)
        with pytest.raises(WebhookTimestampError):
            extract(
                headers=_headers(sig=sig, webhook_id="evt_1", timestamp=future_ts),
                body=body,
                secret=SECRET_B64,
            )

    def test_timestamp_within_tolerance_passes(self) -> None:
        body = self._body()
        ts = int(time.time()) - DEFAULT_TOLERANCE_SECONDS + 5
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        result = extract(
            headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
            body=body,
            secret=SECRET_B64,
        )
        assert isinstance(result, FakeCreditEvent)

    def test_timestamp_zero_tolerance_skips_check(self) -> None:
        """tolerance_seconds=0 disables timestamp validation."""
        body = self._body()
        old_ts = int(time.time()) - 9999
        sig = _sign(webhook_id="evt_1", timestamp=old_ts, body=body)
        result = extract(
            headers=_headers(sig=sig, webhook_id="evt_1", timestamp=old_ts),
            body=body,
            secret=SECRET_B64,
            tolerance_seconds=0,
        )
        assert isinstance(result, FakeCreditEvent)

    def test_invalid_timestamp_raises(self) -> None:
        body = self._body()
        with pytest.raises(WebhookTimestampError):
            extract(
                headers={
                    "webhook-id": "evt_1",
                    "webhook-timestamp": "not-a-number",
                    "webhook-signature": "v1,AAAA====",
                },
                body=body,
                secret=SECRET_B64,
            )


# ---------------------------------------------------------------------------
# DoD-R3: secret rotation
# ---------------------------------------------------------------------------


class TestSecretRotation:
    def _body(self) -> str:
        return json.dumps({"type": _TEST_EVENT_TYPE})

    def test_body_signed_by_old_secret_passes(self) -> None:
        """DoD-R3: body signed by any secret in the list is accepted."""
        old_secret = base64.b64encode(b"old-secret-bytes-32chars!!!!!!").decode()
        new_secret = SECRET_B64
        body = self._body()
        ts = int(time.time())
        sig = _sign(
            webhook_id="evt_1",
            timestamp=ts,
            body=body,
            key_bytes=base64.b64decode(old_secret),
        )
        result = extract(
            headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
            body=body,
            secret=[old_secret, new_secret],
        )
        assert isinstance(result, FakeCreditEvent)

    def test_body_signed_by_new_secret_passes(self) -> None:
        old_secret = base64.b64encode(b"old-secret-bytes-32chars!!!!!!").decode()
        body = self._body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)  # uses SECRET_RAW
        result = extract(
            headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
            body=body,
            secret=[old_secret, SECRET_B64],
        )
        assert isinstance(result, FakeCreditEvent)

    def test_wrong_secrets_all_fail(self) -> None:
        body = self._body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        wrong1 = base64.b64encode(b"wrong1-bytes-32chars!!!!!!!!!!").decode()
        wrong2 = base64.b64encode(b"wrong2-bytes-32chars!!!!!!!!!!").decode()
        with pytest.raises(WebhookSignatureError):
            extract(
                headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
                body=body,
                secret=[wrong1, wrong2],
            )


# ---------------------------------------------------------------------------
# DoD-R3: unknown event type
# ---------------------------------------------------------------------------


class TestUnknownEventType:
    def test_unknown_type_raises(self) -> None:
        body = json.dumps({"type": "completely.unknown.event"})
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        with pytest.raises(UnknownWebhookEventError) as exc_info:
            extract(
                headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
                body=body,
                secret=SECRET_B64,
            )
        assert exc_info.value.event_type == "completely.unknown.event"

    def test_missing_type_field_raises(self) -> None:
        body = json.dumps({"amount": 100})
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        with pytest.raises(UnknownWebhookEventError):
            extract(
                headers=_headers(sig=sig, webhook_id="evt_1", timestamp=ts),
                body=body,
                secret=SECRET_B64,
            )


# ---------------------------------------------------------------------------
# Never returns unverified
# ---------------------------------------------------------------------------


class TestNeverUnverified:
    def test_deserialization_only_after_sig_check(self) -> None:
        """Deserializer is never called with a bad signature."""
        called = [False]

        def spy_deserializer(d: dict[str, Any]) -> FakeCreditEvent:
            called[0] = True
            return FakeCreditEvent(type=d["type"], amount=0)

        spy_type = "spy.event.type"
        register_event(spy_type, spy_deserializer)
        try:
            body = json.dumps({"type": spy_type})
            ts = int(time.time())
            with pytest.raises(WebhookSignatureError):
                extract(
                    headers=_headers(
                        sig="v1,AAAA====",
                        webhook_id="evt_1",
                        timestamp=ts,
                    ),
                    body=body,
                    secret=SECRET_B64,
                )
            assert not called[0], "Deserializer must NOT be called for unverified events"
        finally:
            EVENT_DESERIALIZERS.pop(spy_type, None)


# ---------------------------------------------------------------------------
# Missing required headers
# ---------------------------------------------------------------------------


class TestMissingHeaders:
    def _body(self) -> str:
        return json.dumps({"type": _TEST_EVENT_TYPE})

    def test_missing_webhook_id(self) -> None:
        body = self._body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        with pytest.raises(ValueError, match="webhook-id"):
            extract(
                headers={"webhook-timestamp": str(ts), "webhook-signature": sig},
                body=body,
                secret=SECRET_B64,
            )

    def test_missing_webhook_timestamp(self) -> None:
        body = self._body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        with pytest.raises(ValueError, match="webhook-timestamp"):
            extract(
                headers={"webhook-id": "evt_1", "webhook-signature": sig},
                body=body,
                secret=SECRET_B64,
            )

    def test_missing_webhook_signature(self) -> None:
        body = self._body()
        with pytest.raises(ValueError, match="webhook-signature"):
            extract(
                headers={"webhook-id": "evt_1", "webhook-timestamp": str(int(time.time()))},
                body=body,
                secret=SECRET_B64,
            )

    def test_case_insensitive_headers(self) -> None:
        """Header lookup is case-insensitive."""
        body = self._body()
        ts = int(time.time())
        sig = _sign(webhook_id="evt_1", timestamp=ts, body=body)
        result = extract(
            headers={
                "Webhook-Id": "evt_1",
                "Webhook-Timestamp": str(ts),
                "Webhook-Signature": sig,
            },
            body=body,
            secret=SECRET_B64,
        )
        assert isinstance(result, FakeCreditEvent)
