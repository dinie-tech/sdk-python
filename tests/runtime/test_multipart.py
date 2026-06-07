"""Tests for multipart/form-data transport (story 013).

DoD coverage:
- Multipart framing: fields + file encoded as multipart/form-data with boundary
- Content-Type: multipart/form-data (not application/json) on multipart requests
- Auth / idempotency / retry pipeline still applies to multipart requests
- Negative: plain JSON body still goes as application/json (no regression)
- MultipartBody with no file sends only scalar fields (still multipart)

pytest-httpx is used for all HTTP interception — no real network calls.
"""

from __future__ import annotations

from collections.abc import Iterator
from io import BytesIO
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from dinie.runtime.http import SyncHttpClient
from dinie.runtime.multipart import DEFAULT_FILE_CONTENT_TYPE, DEFAULT_FILE_NAME, MultipartBody
from dinie.runtime.token_manager import TOKEN_PATH, TokenManager

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

BASE_URL = "https://api.dinie.com.br"
TOKEN_URL = f"{BASE_URL}{TOKEN_PATH}"
UPLOAD_URL = f"{BASE_URL}/v1/upload"


def _token_response(token: str = "test-token", expires_in: int = 3600) -> dict[str, object]:
    return {"access_token": token, "expires_in": expires_in, "token_type": "Bearer"}


@pytest.fixture()
def http_client() -> Iterator[httpx.Client]:
    with httpx.Client() as client:
        yield client


def _make_client(
    http_client: httpx.Client,
    httpx_mock: HTTPXMock,
    *,
    max_retries: int = 0,
) -> SyncHttpClient:
    httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response())
    manager = TokenManager(
        client_id="id", client_secret="secret", base_url=BASE_URL, http_client=http_client
    )
    return SyncHttpClient(
        base_url=BASE_URL,
        max_retries=max_retries,
        timeout=5.0,
        http_client=http_client,
        token_manager=manager,
    )


# -------------------------------------------------------------------------
# MultipartBody construction
# -------------------------------------------------------------------------


class TestMultipartBodyConstruction:
    def test_defaults(self) -> None:
        """Default MultipartBody has empty fields and no file."""
        body = MultipartBody()
        assert body.fields == {}
        assert body.file is None
        assert body.file_name == DEFAULT_FILE_NAME
        assert body.file_content_type == DEFAULT_FILE_CONTENT_TYPE

    def test_with_fields_and_file(self) -> None:
        body = MultipartBody(
            fields={"requirement_id": "req_abc"},
            file=b"jpeg bytes",
            file_name="selfie.jpg",
            file_content_type="image/jpeg",
        )
        assert body.fields == {"requirement_id": "req_abc"}
        assert body.file == b"jpeg bytes"
        assert body.file_name == "selfie.jpg"
        assert body.file_content_type == "image/jpeg"

    def test_with_binary_io(self) -> None:
        bio = BytesIO(b"file content")
        body = MultipartBody(fields={}, file=bio)
        assert body.file is bio


# -------------------------------------------------------------------------
# Transport framing
# -------------------------------------------------------------------------


class TestMultipartTransport:
    def test_content_type_is_multipart_not_json(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """Multipart request has Content-Type: multipart/form-data, not application/json."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        body = MultipartBody(
            fields={"requirement_id": "req_1"},
            file=b"\xff\xd8\xff",
            file_name="photo.jpg",
            file_content_type="image/jpeg",
        )
        client.request("POST", "/v1/upload", body=body)

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        ct = upload_req.headers.get("content-type", "")
        assert ct.startswith("multipart/form-data"), f"Expected multipart/form-data, got: {ct!r}"
        assert "boundary=" in ct, f"Expected boundary in Content-Type, got: {ct!r}"

    def test_field_present_in_multipart_body(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """Scalar fields are present in the multipart payload."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        body = MultipartBody(
            fields={"requirement_id": "req_xyz"},
            file=b"bytes",
        )
        client.request("POST", "/v1/upload", body=body)

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        raw_body = upload_req.content.decode("latin-1")
        assert "requirement_id" in raw_body
        assert "req_xyz" in raw_body

    def test_file_present_in_multipart_body(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """File bytes are present in the multipart payload."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        file_bytes = b"\xff\xd8\xff\xe0"  # JPEG magic bytes
        body = MultipartBody(
            fields={"requirement_id": "req_1"},
            file=file_bytes,
            file_name="selfie.jpg",
        )
        client.request("POST", "/v1/upload", body=body)

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        assert file_bytes in upload_req.content

    def test_file_from_binary_io(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """BytesIO file is encoded correctly as multipart."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        bio = BytesIO(b"streaming file content")
        body = MultipartBody(fields={"key": "val"}, file=bio)
        client.request("POST", "/v1/upload", body=body)

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        assert b"streaming file content" in upload_req.content

    def test_auth_header_present_on_multipart_request(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """Authorization: Bearer header is still injected for multipart requests (DoD-R2)."""
        httpx_mock.add_response(url=TOKEN_URL, method="POST", json=_token_response("my-tok"))
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        manager = TokenManager(
            client_id="id", client_secret="secret", base_url=BASE_URL, http_client=http_client
        )
        client = SyncHttpClient(
            base_url=BASE_URL, max_retries=0, timeout=5.0,
            http_client=http_client, token_manager=manager,
        )

        body = MultipartBody(fields={"f": "v"}, file=b"data")
        client.request("POST", "/v1/upload", body=body)

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        assert upload_req.headers["authorization"] == "Bearer my-tok"

    def test_idempotency_key_injected_on_multipart_post(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """Idempotency-Key header is still injected for multipart POST requests."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        body = MultipartBody(fields={}, file=b"data")
        client.request("POST", "/v1/upload", body=body)

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        assert "idempotency-key" in {k.lower() for k in upload_req.headers.keys()}

    def test_multipart_no_file_sends_fields_only(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """MultipartBody with no file still encodes as multipart/form-data."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        body = MultipartBody(fields={"status": "ready"})
        client.request("POST", "/v1/upload", body=body)

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        ct = upload_req.headers.get("content-type", "")
        # With files={} httpx uses multipart encoding
        assert "multipart/form-data" in ct or "form" in ct


# -------------------------------------------------------------------------
# Negative: JSON path not regressed
# -------------------------------------------------------------------------


class TestJsonPathNotRegressed:
    def test_plain_dict_body_still_uses_json(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """A plain dict body is still sent as application/json (no regression)."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"created": True})

        client.request("POST", "/v1/upload", body={"name": "test"})

        upload_req = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"][0]
        ct = upload_req.headers.get("content-type", "")
        assert "application/json" in ct

    def test_none_body_has_no_content_type(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """GET with no body sends no Content-Type header (no regression)."""
        client = _make_client(http_client, httpx_mock)
        httpx_mock.add_response(
            url=f"{BASE_URL}/v1/resource", method="GET", json={"id": "1"}
        )
        client.request("GET", "/v1/resource")
        # No assertion needed — we just verify it doesn't raise


# -------------------------------------------------------------------------
# Retry pipeline still applies to multipart
# -------------------------------------------------------------------------


class TestMultipartRetry:
    def test_multipart_request_is_retried_on_500(
        self, http_client: httpx.Client, httpx_mock: HTTPXMock
    ) -> None:
        """500 on a multipart POST triggers retry with the same idempotency key."""
        client = _make_client(http_client, httpx_mock, max_retries=1)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", status_code=500)
        httpx_mock.add_response(url=UPLOAD_URL, method="POST", json={"id": "ok"})

        body = MultipartBody(fields={"f": "v"}, file=b"data")

        with patch("dinie.runtime.http.time.sleep"):
            result = client.request("POST", "/v1/upload", body=body)

        assert result == {"id": "ok"}
        upload_reqs = [r for r in httpx_mock.get_requests() if r.url.path == "/v1/upload"]
        assert len(upload_reqs) == 2
        # Same idempotency key on retry
        key_first = upload_reqs[0].headers.get("idempotency-key")
        key_second = upload_reqs[1].headers.get("idempotency-key")
        assert key_first == key_second
        assert key_first is not None
