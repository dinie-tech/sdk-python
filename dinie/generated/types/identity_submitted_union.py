# generated — do not edit
from __future__ import annotations

from typing import Any

from .identity_cnh_submitted import IdentityCnhSubmitted
from .identity_rg_submitted import IdentityRgSubmitted

IdentitySubmitted = IdentityCnhSubmitted | IdentityRgSubmitted


def deserialize_identity_submitted(raw: dict[str, Any]) -> IdentitySubmitted:
    """Dispatch on the `evidence_type` field value."""
    _disc = raw.get("evidence_type")
    match _disc:
        case "cnh":
            return IdentityCnhSubmitted.deserialize(raw)
        case "rg":
            return IdentityRgSubmitted.deserialize(raw)

        case _:
            raise ValueError(f"Unknown IdentitySubmitted discriminator value: {_disc!r}")


__all__ = ["IdentitySubmitted", "deserialize_identity_submitted"]
