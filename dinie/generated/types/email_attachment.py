# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class EmailAttachment:
    attachment_type: Literal["email"]
    submitted: bool

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EmailAttachment:
        return cls(
            attachment_type=raw["attachment_type"],
            submitted=raw["submitted"],
        )
