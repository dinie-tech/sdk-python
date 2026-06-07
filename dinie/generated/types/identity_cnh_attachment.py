# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class IdentityCnhAttachment:
    attachment_type: Literal["front", "back", "file"]
    submitted: bool

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> IdentityCnhAttachment:
        return cls(
            attachment_type=raw["attachment_type"],
            submitted=raw["submitted"],
        )
