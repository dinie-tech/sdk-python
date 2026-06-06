"""Model base class and OMIT sentinel for the Dinie Python SDK.

The OMIT sentinel recovers the Python distinction between "not provided" and
``None``. Generated ``serialize_*`` functions drop fields whose value IS OMIT
while serialising explicit ``None`` as JSON ``null``.

The ``Model`` base is a plain marker class; generated response models are
``@dataclass(frozen=True, slots=True)`` subclasses of it.
"""

from __future__ import annotations

from typing import Any


class _OmitType:
    """Sentinel: this optional field was not provided.

    Compare by identity (``value is OMIT``), never by equality.
    There is exactly one instance — the module-level ``OMIT`` constant.
    """

    _instance: _OmitType | None = None

    def __new__(cls) -> _OmitType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "OMIT"

    def __str__(self) -> str:
        return "OMIT"

    def __bool__(self) -> bool:
        return False


#: The single OMIT sentinel instance.
#: Use as a default for optional keyword arguments:
#:   ``def create(*, name: str | OmitType = OMIT) -> ...: ...``
OMIT: _OmitType = _OmitType()

#: Public alias for use in type annotations.
OmitType = _OmitType


class Model:
    """Base marker for every generated response model.

    Generated subclasses are decorated with ``@dataclass(frozen=True, slots=True)``.
    This base enables ``isinstance(obj, Model)`` checks across the SDK and provides
    a common anchor for any shared utilities added in future stories.
    """


def serialize_request(data: dict[str, Any]) -> dict[str, Any]:
    """Drop fields whose value IS the OMIT sentinel.

    Used by generated ``serialize_*`` functions for request params.
    An explicit ``None`` value is kept (serialised as JSON ``null``).

    Args:
        data: raw field dict, possibly containing ``OMIT`` values.

    Returns:
        A new dict with all OMIT-valued entries removed.
    """
    return {k: v for k, v in data.items() if v is not OMIT}
