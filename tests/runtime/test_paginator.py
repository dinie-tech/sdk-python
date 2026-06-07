"""Tests for dinie.runtime.paginator.

DoD-R5 coverage:
- __iter__ iterates items across pages; stops when has_more=False
- The discriminating case: page 2 has limit items with has_more=False → stops at end of page 2
  (a len==limit heuristic would incorrectly continue to page 3)
- iter_pages() yields one page at a time
- cursor = last item's .id
- No fetch_page → iterates only current page data
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dinie.runtime.paginator import SyncCursorPage


@dataclass
class Item:
    id: str
    name: str


def _make_items(prefix: str, count: int) -> list[Item]:
    return [Item(id=f"{prefix}-{i}", name=f"item-{i}") for i in range(count)]


class TestSyncCursorPageIter:
    def test_single_page_no_more(self) -> None:
        items = _make_items("a", 3)
        page: SyncCursorPage[Item] = SyncCursorPage(data=items, has_more=False)
        result = list(page)
        assert result == items

    def test_empty_page(self) -> None:
        page: SyncCursorPage[Item] = SyncCursorPage(data=[], has_more=False)
        assert list(page) == []

    def test_empty_page_with_has_more_true_stops(self) -> None:
        """Even if has_more=True, no data means no cursor → stop."""
        page: SyncCursorPage[Item] = SyncCursorPage(data=[], has_more=True)
        assert list(page) == []

    def test_three_pages_iteration(self) -> None:
        """Items flow across 3 pages; stop when has_more=False."""
        page3_items = _make_items("c", 2)
        page3: SyncCursorPage[Item] = SyncCursorPage(data=page3_items, has_more=False)

        page2_items = _make_items("b", 3)

        def fetch_from_page2(cursor: str) -> SyncCursorPage[Item]:
            assert cursor == page2_items[-1].id
            return page3

        page2: SyncCursorPage[Item] = SyncCursorPage(
            data=page2_items, has_more=True, _fetch_page=fetch_from_page2
        )

        page1_items = _make_items("a", 3)

        def fetch_from_page1(cursor: str) -> SyncCursorPage[Item]:
            assert cursor == page1_items[-1].id
            return page2

        page1: SyncCursorPage[Item] = SyncCursorPage(
            data=page1_items, has_more=True, _fetch_page=fetch_from_page1
        )

        result = list(page1)
        assert result == page1_items + page2_items + page3_items

    def test_r5_discriminator_page2_full_has_more_false(self) -> None:
        """DoD-R5 discriminating case: page 2 has `limit` items with has_more=False.

        A len==limit heuristic would fetch page 3. has_more=False must stop iteration.
        """
        limit = 5
        page3_fetch_count = [0]

        def should_not_be_called(cursor: str) -> SyncCursorPage[Item]:
            page3_fetch_count[0] += 1
            return SyncCursorPage(data=[], has_more=False)

        page2_items = _make_items("b", limit)  # exactly limit items
        page2: SyncCursorPage[Item] = SyncCursorPage(
            data=page2_items,
            has_more=False,  # ← stop signal; len==limit would be misleading
            _fetch_page=should_not_be_called,
        )

        page1_items = _make_items("a", limit)

        def fetch_page2(cursor: str) -> SyncCursorPage[Item]:
            return page2

        page1: SyncCursorPage[Item] = SyncCursorPage(
            data=page1_items, has_more=True, _fetch_page=fetch_page2
        )

        result = list(page1)
        assert result == page1_items + page2_items
        assert page3_fetch_count[0] == 0, "page 3 should never be fetched when has_more=False"

    def test_no_fetch_page_stops_after_current(self) -> None:
        """Without _fetch_page, iteration stops at the current page even if has_more=True."""
        items = _make_items("a", 3)
        page: SyncCursorPage[Item] = SyncCursorPage(data=items, has_more=True)
        assert list(page) == items

    def test_cursor_is_last_item_id(self) -> None:
        """The cursor passed to _fetch_page is the id of the last item."""
        page1_items = _make_items("a", 3)
        cursors_seen: list[str] = []

        def capture_cursor(cursor: str) -> SyncCursorPage[Item]:
            cursors_seen.append(cursor)
            return SyncCursorPage(data=[], has_more=False)

        page1: SyncCursorPage[Item] = SyncCursorPage(
            data=page1_items, has_more=True, _fetch_page=capture_cursor
        )
        list(page1)
        assert cursors_seen == [page1_items[-1].id]


class TestIterPages:
    def test_single_page(self) -> None:
        items = _make_items("a", 2)
        page: SyncCursorPage[Item] = SyncCursorPage(data=items, has_more=False)
        pages = list(page.iter_pages())
        assert len(pages) == 1
        assert pages[0].data == items

    def test_three_pages(self) -> None:
        p3: SyncCursorPage[Item] = SyncCursorPage(data=_make_items("c", 1), has_more=False)
        p2: SyncCursorPage[Item] = SyncCursorPage(
            data=_make_items("b", 2), has_more=True, _fetch_page=lambda _: p3
        )
        p1: SyncCursorPage[Item] = SyncCursorPage(
            data=_make_items("a", 2), has_more=True, _fetch_page=lambda _: p2
        )
        pages = list(p1.iter_pages())
        assert len(pages) == 3
        assert pages[0] is p1
        assert pages[1] is p2
        assert pages[2] is p3

    def test_iter_pages_metadata(self) -> None:
        p2: SyncCursorPage[Item] = SyncCursorPage(data=_make_items("b", 1), has_more=False)
        p1: SyncCursorPage[Item] = SyncCursorPage(
            data=_make_items("a", 1), has_more=True, _fetch_page=lambda _: p2
        )
        pages = list(p1.iter_pages())
        assert pages[0].has_more is True
        assert pages[1].has_more is False


class TestFromResponse:
    def test_basic(self) -> None:
        raw: dict[str, Any] = {
            "data": [{"id": "x1", "name": "foo"}, {"id": "x2", "name": "bar"}],
            "has_more": True,
        }
        page = SyncCursorPage.from_response(raw, item_type=lambda d: Item(**d))
        assert len(page.data) == 2
        assert page.has_more is True
        assert page.data[0].id == "x1"

    def test_empty_response(self) -> None:
        raw: dict[str, Any] = {"data": [], "has_more": False}
        page = SyncCursorPage.from_response(raw, item_type=lambda d: Item(**d))
        assert page.data == []
        assert page.has_more is False

    def test_missing_has_more_defaults_false(self) -> None:
        raw: dict[str, Any] = {"data": [{"id": "x1", "name": "foo"}]}
        page = SyncCursorPage.from_response(raw, item_type=lambda d: Item(**d))
        assert page.has_more is False
