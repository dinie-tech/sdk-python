"""Cursor-based pagination for the Dinie Python SDK.

``SyncCursorPage[T]`` is the return type for all list/paginate resource
methods.  It models a single page of results and knows how to advance to the
next page using the ``has_more`` / ``starting_after`` cursor protocol.

Dinie pagination contract (D#1 / DoD-R5)
-----------------------------------------
* ``has_more`` is the **only** stop signal.  An empty page or a page shorter
  than the requested ``limit`` does **not** indicate the end — ``has_more``
  must be ``False``.
* The cursor is the ``id`` of the **last item** in the current page.  It is
  passed as ``starting_after`` on the next request.
* Items yielded by ``__iter__`` are the raw typed objects; ``iter_pages()``
  yields one page at a time for callers that need page-level metadata.

Async support
-------------
An ``AsyncCursorPage`` (future) would be structurally identical but with
``async def __aiter__`` / ``async def iter_pages``.  No logic changes needed
in the generated resource methods — only the page class swaps.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class SyncCursorPage(Generic[T]):
    """A single page of cursor-paginated results.

    Attributes:
        data: Items on this page.
        has_more: ``True`` when the server has more items beyond this page.

    Internal:
        _fetch_page: Injected by the generated resource method.  Accepts
            ``starting_after`` (the cursor) and returns the next page.
            ``None`` when the page was constructed standalone (e.g. in tests).
    """

    data: list[T]
    has_more: bool
    _fetch_page: Callable[[str], SyncCursorPage[T]] | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __iter__(self) -> Iterator[T]:
        """Iterate over **all** items across pages.

        Automatically fetches subsequent pages by advancing the cursor to the
        ``id`` of the last item.  Stops when ``has_more`` is ``False`` or
        when ``_fetch_page`` is not set (standalone page).

        Yields:
            Every item in order across all pages.
        """
        page: SyncCursorPage[T] = self
        while True:
            yield from page.data
            if not page.has_more or not page.data:
                break
            if page._fetch_page is None:
                break
            cursor: str = getattr(page.data[-1], "id")
            page = page._fetch_page(cursor)

    def iter_pages(self) -> Iterator[SyncCursorPage[T]]:
        """Iterate one **page** at a time.

        Useful when callers need page-level metadata (e.g. ``has_more``) in
        addition to item data.

        Yields:
            Each ``SyncCursorPage``, starting with this one.
        """
        page: SyncCursorPage[T] = self
        while True:
            yield page
            if not page.has_more or not page.data:
                break
            if page._fetch_page is None:
                break
            cursor: str = getattr(page.data[-1], "id")
            page = page._fetch_page(cursor)

    @classmethod
    def from_response(
        cls,
        response_body: dict[str, Any],
        *,
        item_type: Callable[[dict[str, Any]], T],
        fetch_page: Callable[[str], SyncCursorPage[T]] | None = None,
    ) -> SyncCursorPage[T]:
        """Construct a page from a raw API response body.

        Args:
            response_body: Parsed JSON dict with ``"data"`` and ``"has_more"``
                keys.
            item_type: Callable that deserialises a single item dict into ``T``.
            fetch_page: Callable that fetches the next page given a cursor.
                Injected by the generated resource method.

        Returns:
            A ``SyncCursorPage[T]`` instance.
        """
        items: list[T] = [item_type(item) for item in response_body.get("data", [])]
        has_more: bool = bool(response_body.get("has_more", False))
        return cls(data=items, has_more=has_more, _fetch_page=fetch_page)
