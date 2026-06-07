# generated — do not edit
from __future__ import annotations

from .client import Dinie
from .errors import (
    ERROR_REGISTRY_BY_STATUS,
    ERROR_REGISTRY_BY_TYPE,
    SERVER_ERROR_CLASS,
)
from .events import EVENT_DESERIALIZERS, WebhookEvent
from .types import *  # noqa: F401, F403

__all__ = [
    "Dinie",
    "ERROR_REGISTRY_BY_TYPE",
    "ERROR_REGISTRY_BY_STATUS",
    "SERVER_ERROR_CLASS",
    "EVENT_DESERIALIZERS",
    "WebhookEvent",
]
