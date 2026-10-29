"""Tests for the text and CSV report formats."""

import csv
import io

from tvmaze.models import Show
from tvmaze.report import format_report_csv, format_report_text

SHOWS = [
    Show("Sherlock", ["Crime", "Drama"], 8.9, premiered="2010-07-25", network="BBC One"),
    Show("=HYPERLINK(\"http://evil\")", [], None),
]


def test_text_report_lists_each_show():
    text = format_report_text(SHOWS[:1], "sherlock", 8.0)
    assert "Search term    : sherlock" in text
    assert "Matching shows : 1" in text
    assert "Name   : Sherlock" in text
    assert "Genres : Crime, Drama" in text


def test_csv_report_has_header_and_rows():
    rows = list(csv.reader(io.StringIO(format_report_csv(SHOWS))))
    assert rows[0] == ["name", "genres", "rating", "premiered", "network", "status", "url"]
    assert rows[1][:5] == ["Sherlock", "Crime; Drama", "8.9", "2010-07-25", "BBC One"]


def test_csv_report_neutralises_formulas():
    rows = list(csv.reader(io.StringIO(format_report_csv(SHOWS))))
    assert rows[2][0].startswith("'=")
    assert rows[2][2] == ""  # unrated
