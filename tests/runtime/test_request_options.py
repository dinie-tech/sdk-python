"""Tests for dinie.runtime.request_options."""

from __future__ import annotations

import pytest

from dinie.runtime.request_options import RequestOptions


class TestRequestOptionsCoerce:
    def test_passthrough_instance(self) -> None:
        opts = RequestOptions(timeout=5.0)
        assert RequestOptions.coerce(opts) is opts

    def test_none_returns_default(self) -> None:
        opts = RequestOptions.coerce(None)
        assert isinstance(opts, RequestOptions)
        assert opts.timeout is None
        assert opts.idempotency_key is None
        assert opts.headers is None
        assert opts.max_retries is None

    def test_dict_coercion(self) -> None:
        opts = RequestOptions.coerce({"timeout": 10.0, "max_retries": 3})
        assert opts.timeout == 10.0
        assert opts.max_retries == 3
        assert opts.idempotency_key is None

    def test_empty_dict(self) -> None:
        opts = RequestOptions.coerce({})
        assert opts.timeout is None

    def test_frozen_prevents_mutation(self) -> None:
        opts = RequestOptions(timeout=5.0)
        with pytest.raises((TypeError, AttributeError)):
            opts.timeout = 10.0  # type: ignore[misc]


class TestRequestOptionsDefaults:
    def test_all_none_by_default(self) -> None:
        opts = RequestOptions()
        assert opts.timeout is None
        assert opts.idempotency_key is None
        assert opts.headers is None
        assert opts.max_retries is None

    def test_headers_dict(self) -> None:
        opts = RequestOptions(headers={"X-Custom": "value", "Authorization": None})
        assert opts.headers == {"X-Custom": "value", "Authorization": None}
