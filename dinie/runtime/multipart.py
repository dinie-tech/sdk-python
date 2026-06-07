"""Multipart/form-data transport wrapper for the Dinie Python SDK.

Peer of ``Dinie::Internal::Multipart`` (Ruby sdk-ruby story 009) and the
``FormData`` / ``PassThroughBody`` path in the TypeScript runtime.

The generated resource layer constructs a ``MultipartBody`` and passes it
as the ``body=`` argument to ``SyncHttpClient.request()``. The transport
detects it in ``_raw_request()`` and routes through ``httpx``'s
``files=`` / ``data=`` path instead of ``json=``, letting ``httpx`` set
the ``Content-Type: multipart/form-data; boundary=…`` header.

Architecture
------------
Lives in ``runtime/`` (CODEOWNER: humans). Transport-aware so the
generated layer stays transport-agnostic: a resource method constructs a
``MultipartBody`` (fields + opaque file) and the HTTP client encodes it.

── runtime ↔ generated boundary (architecture §4) ──
Generated code imports this class; the transport (``http.py``) drives the
``httpx`` encoding. Nothing in ``generated/`` knows about ``httpx``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import IO

#: Fallback MIME type used when the caller does not specify one.
DEFAULT_FILE_CONTENT_TYPE = "application/octet-stream"

#: Fallback filename used when the caller does not specify one.
DEFAULT_FILE_NAME = "upload"


@dataclass
class MultipartBody:
    """Multipart/form-data request body.

    Holds scalar form fields and an optional binary file part.  Pass an
    instance as the ``body=`` argument to ``SyncHttpClient.request()``;
    the transport encodes it as ``multipart/form-data`` and lets
    ``httpx`` append the boundary.

    Attributes:
        fields: Scalar form fields (``str`` key → ``str`` value).
        file: Binary file content — raw ``bytes`` or an open binary IO
            object.  ``None`` sends only the scalar fields (as
            ``multipart/form-data`` with no file part).
        file_name: Filename hint for the ``file`` part in the
            ``Content-Disposition`` header.
        file_content_type: MIME type for the ``file`` part.

    Example — KYC selfie upload::

        from dinie.runtime.multipart import MultipartBody

        body = MultipartBody(
            fields={"requirement_id": "req_abc123"},
            file=open("selfie.jpg", "rb"),
            file_name="selfie.jpg",
            file_content_type="image/jpeg",
        )
        client.request("POST", "/customers/c1/kyc-attachments", body=body)
    """

    fields: dict[str, str] = field(default_factory=dict)
    file: bytes | IO[bytes] | None = None
    file_name: str = DEFAULT_FILE_NAME
    file_content_type: str = DEFAULT_FILE_CONTENT_TYPE
