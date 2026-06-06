"""Tests for dinie.runtime.errors."""

from __future__ import annotations

import pytest

from dinie.runtime.errors import (
    ERROR_REGISTRY,
    ApiError,
    AuthenticationError,
    BadGatewayError,
    ConflictError,
    DinieError,
    GatewayTimeoutError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    UnprocessableEntityError,
    from_response,
    register_error,
)

_EMPTY_HEADERS: dict[str, str] = {}


class TestErrorHierarchy:
    def test_api_error_is_dinie_error(self) -> None:
        err = ApiError("msg", status=400, body=None, headers={})
        assert isinstance(err, DinieError)
        assert isinstance(err, Exception)

    @pytest.mark.parametrize(
        "cls",
        [
            AuthenticationError,
            PermissionDeniedError,
            NotFoundError,
            ConflictError,
            UnprocessableEntityError,
            RateLimitError,
            InternalServerError,
            BadGatewayError,
            ServiceUnavailableError,
            GatewayTimeoutError,
        ],
    )
    def test_named_errors_are_api_errors(self, cls: type[ApiError]) -> None:
        err = cls("msg", status=999, body=None, headers={})
        assert isinstance(err, ApiError)
        assert isinstance(err, DinieError)

    def test_attributes(self) -> None:
        err = ApiError("bad", status=404, body={"detail": "x"}, headers={"x": "y"})
        assert err.status == 404
        assert err.body == {"detail": "x"}
        assert err.headers == {"x": "y"}
        assert str(err) == "bad"

    def test_repr(self) -> None:
        err = ApiError("not found", status=404, body=None, headers={})
        assert "404" in repr(err)
        assert "not found" in repr(err)


class TestFromResponse:
    def test_401_authentication(self) -> None:
        err = from_response(status=401, body=None, headers={})
        assert isinstance(err, AuthenticationError)

    def test_403_permission(self) -> None:
        err = from_response(status=403, body=None, headers={})
        assert isinstance(err, PermissionDeniedError)

    def test_404_not_found(self) -> None:
        err = from_response(status=404, body=None, headers={})
        assert isinstance(err, NotFoundError)

    def test_409_conflict(self) -> None:
        err = from_response(status=409, body=None, headers={})
        assert isinstance(err, ConflictError)

    def test_422_unprocessable(self) -> None:
        err = from_response(status=422, body=None, headers={})
        assert isinstance(err, UnprocessableEntityError)

    def test_429_rate_limit(self) -> None:
        err = from_response(status=429, body=None, headers={})
        assert isinstance(err, RateLimitError)

    def test_500_internal(self) -> None:
        err = from_response(status=500, body=None, headers={})
        assert isinstance(err, InternalServerError)

    def test_502_bad_gateway(self) -> None:
        err = from_response(status=502, body=None, headers={})
        assert isinstance(err, BadGatewayError)

    def test_503_unavailable(self) -> None:
        err = from_response(status=503, body=None, headers={})
        assert isinstance(err, ServiceUnavailableError)

    def test_504_gateway_timeout(self) -> None:
        err = from_response(status=504, body=None, headers={})
        assert isinstance(err, GatewayTimeoutError)

    def test_generic_5xx(self) -> None:
        err = from_response(status=599, body=None, headers={})
        assert isinstance(err, InternalServerError)

    def test_unknown_4xx_fallback(self) -> None:
        err = from_response(status=418, body=None, headers={})
        assert type(err) is ApiError

    def test_message_from_detail(self) -> None:
        err = from_response(status=404, body={"detail": "resource gone"}, headers={})
        assert str(err) == "resource gone"

    def test_message_from_message_key(self) -> None:
        err = from_response(status=400, body={"message": "invalid"}, headers={})
        assert str(err) == "invalid"

    def test_message_from_error_key(self) -> None:
        err = from_response(status=400, body={"error": "oops"}, headers={})
        assert str(err) == "oops"

    def test_message_from_title_key(self) -> None:
        err = from_response(status=400, body={"title": "Bad Request"}, headers={})
        assert str(err) == "Bad Request"

    def test_message_fallback_to_http_status(self) -> None:
        err = from_response(status=503, body=None, headers={})
        assert str(err) == "HTTP 503"

    def test_message_from_string_body(self) -> None:
        err = from_response(status=500, body="internal error", headers={})
        assert str(err) == "internal error"

    def test_type_url_registry_lookup(self) -> None:
        """ERROR_REGISTRY lookup takes precedence over status map."""

        class InsufficientBalanceError(ApiError):
            pass

        url = "https://errors.dinie.com.br/test-insufficient-balance"
        original = ERROR_REGISTRY.get(url)
        try:
            register_error(url, InsufficientBalanceError)
            err = from_response(
                status=422,
                body={"type": url, "detail": "no funds"},
                headers={},
            )
            assert isinstance(err, InsufficientBalanceError)
            assert str(err) == "no funds"
        finally:
            if original is None:
                ERROR_REGISTRY.pop(url, None)
            else:
                ERROR_REGISTRY[url] = original
