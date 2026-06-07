"""Tests for dinie.runtime.logger.

Coverage:
- SensitiveDataFilter redacts sensitive headers and body PII
- Redacted content never leaks to captured log output
- Body truncation at BODY_TRUNCATE_CHARS with full_size annotation
- setup_logging() respects DINIE_LOG env var
- get_logger() returns the SDK logger
"""

from __future__ import annotations

import json
import logging

import pytest

from dinie.runtime.logger import (
    BODY_TRUNCATE_CHARS,
    LOG_ENV_VAR,
    REDACTED,
    SENSITIVE_BODY_KEYS,
    SENSITIVE_HEADERS,
    SensitiveDataFilter,
    get_logger,
    redact_body,
    redact_headers,
    setup_logging,
)


class TestRedactHeaders:
    def test_authorization_redacted(self) -> None:
        headers = {"Authorization": "Bearer super-secret-token", "Content-Type": "application/json"}
        result = redact_headers(headers)
        assert result["Authorization"] == REDACTED
        assert result["Content-Type"] == "application/json"

    def test_webhook_signature_redacted(self) -> None:
        headers = {"webhook-signature": "v1,abc123=="}
        result = redact_headers(headers)
        assert result["webhook-signature"] == REDACTED

    def test_x_dinie_client_secret_redacted(self) -> None:
        headers = {"x-dinie-client-secret": "my-secret"}
        result = redact_headers(headers)
        assert result["x-dinie-client-secret"] == REDACTED

    def test_proxy_authorization_redacted(self) -> None:
        headers = {"Proxy-Authorization": "Basic dXNlcjpwYXNz"}
        result = redact_headers(headers)
        assert result["Proxy-Authorization"] == REDACTED

    def test_case_insensitive(self) -> None:
        headers = {"AUTHORIZATION": "Bearer tok", "accept": "application/json"}
        result = redact_headers(headers)
        assert result["AUTHORIZATION"] == REDACTED
        assert result["accept"] == "application/json"

    def test_non_sensitive_keys_unchanged(self) -> None:
        headers = {"X-Request-Id": "abc", "Accept": "application/json"}
        result = redact_headers(headers)
        assert result == headers

    def test_empty_headers(self) -> None:
        assert redact_headers({}) == {}

    def test_all_sensitive_headers_covered(self) -> None:
        headers = {h: "value" for h in SENSITIVE_HEADERS}
        result = redact_headers(headers)
        for v in result.values():
            assert v == REDACTED


class TestRedactBody:
    def test_cpf_redacted(self) -> None:
        body = json.dumps({"cpf": "123.456.789-00", "name": "João"})
        result = redact_body(body)
        data = json.loads(result)
        assert data["cpf"] == REDACTED
        assert data["name"] == "João"

    def test_access_token_redacted(self) -> None:
        body = json.dumps({"access_token": "eyJhbGci...", "expires_in": 3600})
        result = redact_body(body)
        data = json.loads(result)
        assert data["access_token"] == REDACTED
        assert data["expires_in"] == 3600

    def test_all_sensitive_keys_redacted(self) -> None:
        body_dict = {k: "value" for k in SENSITIVE_BODY_KEYS}
        body = json.dumps(body_dict)
        result = redact_body(body)
        data = json.loads(result)
        for v in data.values():
            assert v == REDACTED

    def test_non_sensitive_keys_unchanged(self) -> None:
        body = json.dumps({"amount": 100, "currency": "BRL", "description": "test"})
        result = redact_body(body)
        data = json.loads(result)
        assert data["amount"] == 100
        assert data["currency"] == "BRL"

    def test_dict_body_accepted(self) -> None:
        body_dict = {"cpf": "123", "amount": 50}
        result = redact_body(body_dict)
        data = json.loads(result)
        assert data["cpf"] == REDACTED
        assert data["amount"] == 50

    def test_none_body(self) -> None:
        assert redact_body(None) == ""

    def test_truncation_at_limit(self) -> None:
        """Body longer than BODY_TRUNCATE_CHARS is truncated."""
        long_body = "x" * (BODY_TRUNCATE_CHARS + 100)
        result = redact_body(long_body)
        assert "truncated" in result
        assert f"full_size={len(long_body)}" in result
        assert len(result) < len(long_body)

    def test_body_at_limit_not_truncated(self) -> None:
        body = "x" * BODY_TRUNCATE_CHARS
        result = redact_body(body)
        assert "truncated" not in result

    def test_authorization_does_not_leak(self) -> None:
        """Sensitive data must NOT appear in the redacted body string."""
        secret = "super-secret-token-12345"
        body = json.dumps({"access_token": secret, "amount": 99})
        result = redact_body(body)
        assert secret not in result


class TestSensitiveDataFilter:
    def _make_record(self, **extra: object) -> logging.LogRecord:
        record = logging.LogRecord(
            name="dinie",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=(),
            exc_info=None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_request_headers_redacted(self) -> None:
        filt = SensitiveDataFilter()
        record = self._make_record(request_headers={"Authorization": "Bearer tok", "Accept": "*"})
        filt.filter(record)
        assert record.request_headers["Authorization"] == REDACTED  # type: ignore[attr-defined]
        assert record.request_headers["Accept"] == "*"  # type: ignore[attr-defined]

    def test_response_headers_redacted(self) -> None:
        filt = SensitiveDataFilter()
        record = self._make_record(response_headers={"webhook-signature": "v1,sig==", "X-Id": "1"})
        filt.filter(record)
        assert record.response_headers["webhook-signature"] == REDACTED  # type: ignore[attr-defined]

    def test_request_body_pii_redacted(self) -> None:
        filt = SensitiveDataFilter()
        body = json.dumps({"cpf": "123.456.789-00", "amount": 100})
        record = self._make_record(request_body=body)
        filt.filter(record)
        result = json.loads(record.request_body)  # type: ignore[attr-defined]
        assert result["cpf"] == REDACTED
        assert result["amount"] == 100

    def test_response_body_pii_redacted(self) -> None:
        filt = SensitiveDataFilter()
        body = json.dumps({"access_token": "tok", "id": "cust_123"})
        record = self._make_record(response_body=body)
        filt.filter(record)
        result = json.loads(record.response_body)  # type: ignore[attr-defined]
        assert result["access_token"] == REDACTED
        assert result["id"] == "cust_123"

    def test_filter_always_returns_true(self) -> None:
        """Filter never drops records."""
        filt = SensitiveDataFilter()
        record = self._make_record()
        assert filt.filter(record) is True

    def test_no_extra_attrs_is_safe(self) -> None:
        """Records without extra attrs don't raise."""
        filt = SensitiveDataFilter()
        record = self._make_record()
        filt.filter(record)  # must not raise

    def test_captured_log_does_not_contain_authorization(self) -> None:
        """End-to-end: token must not appear in log output."""
        secret = "very-secret-bearer-token"
        logger = logging.getLogger("dinie.test.filter")
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.MemoryHandler(capacity=100)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        logger.propagate = False

        try:
            logger.info(
                "outgoing request",
                extra={"request_headers": {"Authorization": f"Bearer {secret}"}},
            )
            handler.flush()
            record = handler.buffer[-1]
            assert secret not in str(getattr(record, "request_headers", {}))
        finally:
            logger.removeHandler(handler)


class TestSetupLogging:
    def test_off_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(LOG_ENV_VAR, raising=False)
        logger = setup_logging(logging.getLogger("dinie.test.off"))
        assert logger.level == logging.NOTSET
        assert not logger.handlers

    def test_debug_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(LOG_ENV_VAR, "debug")
        logger = setup_logging(logging.getLogger("dinie.test.debug"))
        assert logger.level == logging.DEBUG
        assert logger.handlers

    def test_info_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(LOG_ENV_VAR, "info")
        logger = setup_logging(logging.getLogger("dinie.test.info"))
        assert logger.level == logging.INFO

    def test_warn_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(LOG_ENV_VAR, "warn")
        logger = setup_logging(logging.getLogger("dinie.test.warn"))
        assert logger.level == logging.WARNING

    def test_error_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(LOG_ENV_VAR, "error")
        logger = setup_logging(logging.getLogger("dinie.test.error"))
        assert logger.level == logging.ERROR

    def test_unknown_value_treated_as_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(LOG_ENV_VAR, "verbose")
        logger = setup_logging(logging.getLogger("dinie.test.unknown"))
        assert logger.level == logging.NOTSET


class TestGetLogger:
    def test_returns_dinie_logger(self) -> None:
        logger = get_logger()
        assert logger.name == "dinie"

    def test_custom_name(self) -> None:
        logger = get_logger("dinie.custom")
        assert logger.name == "dinie.custom"


# ---------------------------------------------------------------------------
# Import needed for MemoryHandler
# ---------------------------------------------------------------------------

import logging.handlers  # noqa: E402 — after class definition that uses it
