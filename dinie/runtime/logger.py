"""Structured logging for the Dinie Python SDK.

Design
------
* Uses stdlib ``logging`` — no third-party dependency.
* ``DINIE_LOG`` environment variable controls the SDK's own log level:
  ``off`` (default), ``error``, ``warn``, ``info``, ``debug``.
* ``SensitiveDataFilter`` is a ``logging.Filter`` that redacts secrets from
  headers and PII from body fields before the record reaches any handler.
* Body strings longer than ``BODY_TRUNCATE_BYTES`` are truncated; the original
  size is preserved in ``[truncated, full_size=NNN]``.
* Log records may carry ``request_log_id`` and ``retry_of`` extra fields
  (injected by the transport layer).  They appear in the formatted output when
  the ``SensitiveDataFilter`` is attached to a handler that uses a format string
  referencing them.

Usage
-----
Call ``setup_logging()`` early (or let it be called lazily via ``get_logger()``)
to honour the ``DINIE_LOG`` env variable.  Pass a custom ``logging.Logger`` to
``SyncHttpClient`` via story 007's ``Dinie()`` constructor to override the
built-in one.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Environment variable that controls the SDK's log level.
LOG_ENV_VAR = "DINIE_LOG"

#: SDK logger name — ``logging.getLogger("dinie")`` is the root.
SDK_LOGGER_NAME = "dinie"

#: Body payloads longer than this (in characters) are truncated in log output.
BODY_TRUNCATE_CHARS = 2048

#: Redaction placeholder used for sensitive values.
REDACTED = "[REDACTED]"

#: Request headers whose values are always redacted.
SENSITIVE_HEADERS: frozenset[str] = frozenset(
    {
        "authorization",
        "webhook-signature",
        "x-dinie-client-secret",
        "proxy-authorization",
    }
)

#: JSON body keys whose values are always redacted.
#: Only top-level keys are checked (nested PII is out of scope for v1).
SENSITIVE_BODY_KEYS: frozenset[str] = frozenset(
    {
        "cpf",
        "cnpj",
        "account",
        "cvv",
        "password",
        "secret",
        "client_secret",
        "access_token",
        "phone",
    }
)

#: Maps ``DINIE_LOG`` string values to ``logging`` integer levels.
_LEVEL_MAP: dict[str, int] = {
    "off": logging.NOTSET,
    "error": logging.ERROR,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


class SensitiveDataFilter(logging.Filter):
    """Redacts sensitive headers and PII body fields from log records.

    Operates on the ``extra`` dict attached to log records when the transport
    logs request/response details.  Specifically looks for:

    * ``record.request_headers`` — a dict of request headers.
    * ``record.response_headers`` — a dict of response headers.
    * ``record.request_body`` — a JSON string or dict of the request body.
    * ``record.response_body`` — a JSON string or dict of the response body.

    Mutates the attributes in-place before the record is emitted, so no
    sensitive data reaches any handler.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply redaction.  Always returns ``True`` (never drops records)."""
        _redact_headers_attr(record, "request_headers")
        _redact_headers_attr(record, "response_headers")
        _redact_body_attr(record, "request_body")
        _redact_body_attr(record, "response_body")
        return True


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def setup_logging(logger: logging.Logger | None = None) -> logging.Logger:
    """Configure and return the SDK logger according to ``DINIE_LOG``.

    Reads ``DINIE_LOG`` from the environment.  If the value is ``"off"`` or
    the variable is not set, the logger is disabled (``propagate=False``,
    no handlers, level NOTSET).  Otherwise configures a ``StreamHandler`` with
    a ``SensitiveDataFilter`` at the appropriate level.

    Args:
        logger: Logger to configure.  Defaults to the SDK root logger
            ``"dinie"``.

    Returns:
        The configured logger.
    """
    if logger is None:
        logger = logging.getLogger(SDK_LOGGER_NAME)

    raw = os.environ.get(LOG_ENV_VAR, "off").lower().strip()
    level = _LEVEL_MAP.get(raw, logging.NOTSET)

    if level == logging.NOTSET:
        logger.setLevel(logging.NOTSET)
        logger.handlers.clear()
        logger.propagate = False
        return logger

    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def get_logger(name: str = SDK_LOGGER_NAME) -> logging.Logger:
    """Return a (possibly lazy-configured) SDK logger.

    Args:
        name: Logger name.  Defaults to ``"dinie"``.

    Returns:
        A ``logging.Logger`` instance.
    """
    return logging.getLogger(name)


def redact_headers(headers: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``headers`` with sensitive values replaced by ``[REDACTED]``.

    Args:
        headers: HTTP headers dict (string keys, any values).

    Returns:
        A new dict with the same keys; sensitive values replaced.
    """
    return {k: REDACTED if k.lower() in SENSITIVE_HEADERS else v for k, v in headers.items()}


def redact_body(body: str | dict[str, Any] | None) -> str:
    """Redact PII from a body value and truncate if necessary.

    Args:
        body: Raw body string, dict, or ``None``.

    Returns:
        A redacted and possibly truncated string safe to log.
    """
    if body is None:
        return ""
    if isinstance(body, dict):
        body_str = json.dumps(_redact_body_dict(body))
    else:
        body_str = _redact_body_str(body)
    return _truncate(body_str)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _redact_headers_attr(record: logging.LogRecord, attr: str) -> None:
    raw = getattr(record, attr, None)
    if isinstance(raw, dict):
        setattr(record, attr, redact_headers(raw))


def _redact_body_attr(record: logging.LogRecord, attr: str) -> None:
    raw = getattr(record, attr, None)
    if raw is not None:
        setattr(record, attr, redact_body(raw))


def _redact_body_dict(body: dict[str, Any]) -> dict[str, Any]:
    return {k: REDACTED if k.lower() in SENSITIVE_BODY_KEYS else v for k, v in body.items()}


def _redact_body_str(body: str) -> str:
    """Best-effort JSON-parse-and-redact; fallback to regex if not valid JSON."""
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            return json.dumps(_redact_body_dict(parsed))
        return body
    except (json.JSONDecodeError, ValueError):
        # Fallback: regex-based redaction for non-JSON bodies
        for key in SENSITIVE_BODY_KEYS:
            # Match "key": "value" (double or single quote) and "key": <number>
            pattern = re.compile(
                rf'("{re.escape(key)}"\s*:\s*)"[^"]*"',
                re.IGNORECASE,
            )
            body = pattern.sub(rf'\1"{REDACTED}"', body)
        return body


def _truncate(body: str) -> str:
    if len(body) <= BODY_TRUNCATE_CHARS:
        return body
    return body[:BODY_TRUNCATE_CHARS] + f"…[truncated, full_size={len(body)}]"
