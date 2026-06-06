"""Tests for dinie.runtime.idempotency."""

from __future__ import annotations

import uuid

from dinie.runtime.idempotency import KEY_PREFIX, generate_key


class TestGenerateKey:
    def test_prefix(self) -> None:
        key = generate_key()
        assert key.startswith(KEY_PREFIX)

    def test_suffix_is_uuid4(self) -> None:
        key = generate_key()
        suffix = key[len(KEY_PREFIX) :]
        parsed = uuid.UUID(suffix)
        assert parsed.version == 4

    def test_keys_are_unique(self) -> None:
        keys = {generate_key() for _ in range(100)}
        assert len(keys) == 100

    def test_key_prefix_constant(self) -> None:
        assert KEY_PREFIX == "dinie-sdk-retry-"
