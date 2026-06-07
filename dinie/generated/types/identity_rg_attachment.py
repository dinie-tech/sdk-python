# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class IdentityRgAttachment:
    attachment_type: Literal["front", "back"]
    submitted: bool

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> IdentityRgAttachment:
        return cls(
            attachment_type=raw["attachment_type"],
            submitted=raw["submitted"],
        )
