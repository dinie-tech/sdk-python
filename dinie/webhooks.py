"""Public webhook surface — re-exports `extract` from the runtime.

Usage::

    from dinie.webhooks import extract

    event = extract(payload_bytes, headers)
    match event:
        case CustomerCreated():
            handle_new_customer(event)
"""

from __future__ import annotations

from dinie.runtime.webhooks import extract

__all__ = ["extract"]
