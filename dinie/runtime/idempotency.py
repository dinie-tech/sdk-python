"""Idempotency-key generation for the Dinie Python SDK.

Single responsibility: mint a fresh auto-generated key. The transport policy
around the key (when to generate, which methods, how to thread it through retries)
lives in ``http.py``, not here.
"""

from __future__ import annotations

import uuid

#: Prefix that marks a key as SDK-auto-generated (vs. partner-supplied).
#: Lets the Dinie backend distinguish auto-gen from explicit keys in logs.
KEY_PREFIX = "dinie-sdk-retry-"


def generate_key() -> str:
    """Return a fresh auto-generated idempotency key: ``'dinie-sdk-retry-<uuid4>'``.

    The key is minted ONCE before the retry loop, so every attempt of the same
    logical request reuses the same key — a retry never creates a duplicate resource.

    Returns:
        A string of the form ``"dinie-sdk-retry-<uuid4>"``.
    """
    return f"{KEY_PREFIX}{uuid.uuid4()}"
