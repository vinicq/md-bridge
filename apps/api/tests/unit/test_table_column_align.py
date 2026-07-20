"""Focused regression coverage for table column alignment helpers (#175)."""

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


class _Row:
    def __init__(self, cells):
        self.cells = cells


class _Table:
    def __init__(self, extracted_rows, cell_rows):
        self._extracted_rows = extracted_rows
        self.rows = [_Row(cells) for cells in cell_rows]

    def extract(self):
        return self._extracted_rows


def _page_with_spans(*spans):
    return {"blocks": [{"type": 0, "lines": [{"spans": [{"bbox": span} for span in spans]}]}]}


def test_left_neighbor_text_does_not_vote_for_first_table_column():
    table = _Table(
        [["Name"], ["Alpha"], ["Beta"]],
        [[(0, 0, 100, 20)], [(0, 20, 100, 40)], [(0, 40, 100, 60)]],
    )
    page_text = _page_with_spans(
        (-90, 5, -10, 15),  # ordinary page text beside the table
        (5, 25, 30, 35),
        (5, 45, 28, 55),
    )

    assert mod.detect_column_alignment(table, page_text, 1) == ["l"]


def test_long_left_aligned_text_falls_back_to_plain_separator():
    table = _Table(
        [["Description"], ["A long row"], ["Another long row"]],
        [[(0, 0, 100, 20)], [(0, 20, 100, 40)], [(0, 40, 100, 60)]],
    )
    page_text = _page_with_spans((5, 25, 95, 35), (5, 45, 96, 55))

    assert mod.detect_column_alignment(table, page_text, 1) == [""]


def test_styled_spans_share_one_line_extent_before_voting():
    table = _Table(
        [["Description"], ["A long row"], ["Another long row"]],
        [[(0, 0, 100, 20)], [(0, 20, 100, 40)], [(0, 40, 100, 60)]],
    )
    page_text = _page_with_spans((5, 25, 45, 35), (45, 25, 95, 35), (5, 45, 46, 55), (46, 45, 96, 55))

    assert mod.detect_column_alignment(table, page_text, 1) == [""]


def test_empty_and_duplicate_columns_keep_separator_width_in_sync():
    empty_column = _Table(
        [["Name", "", "Amount"], ["Alpha", "", "1"]],
        [[(0, 0, 100, 20), None, (200, 0, 300, 20)], [(0, 20, 100, 40), None, (200, 20, 300, 40)]],
    )
    duplicate_column = _Table(
        [["Name", "Name", "Amount"], ["Alpha", "Alpha", "1"]],
        [[(0, 0, 100, 20), (100, 0, 200, 20), (200, 0, 300, 20)], [(0, 20, 100, 40), (100, 20, 200, 40), (200, 20, 300, 40)]],
    )

    assert mod.render_table(empty_column).splitlines()[1] == "| --- | --- |"
    assert mod.render_table(duplicate_column).splitlines()[1] == "| --- | --- |"


def test_duplicate_column_with_missing_evidence_falls_back_to_plain_separator():
    assert mod._merge_column_alignment("", "r") == ""
    assert mod._merge_column_alignment("r", "") == ""
    assert mod._merge_column_alignment("r", "r") == "r"


def test_spanning_cell_is_ignored_for_alignment_votes():
    table = _Table(
        [["Merged", ""], ["Left", "Right"], ["Alpha", "10"]],
        [[(0, 0, 200, 20), None], [(0, 20, 100, 40), (100, 20, 200, 40)], [(0, 40, 100, 60), (100, 40, 200, 60)]],
    )
    page_text = _page_with_spans((5, 25, 25, 35), (5, 45, 30, 55), (170, 25, 192, 35), (170, 45, 192, 55))

    assert mod.detect_column_alignment(table, page_text, 2) == ["l", "r"]
