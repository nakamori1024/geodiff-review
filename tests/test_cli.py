import json
import re

from geodiff_review.cli import main


def test_table_filter(before_multi_gpkg, after_multi_gpkg, tmp_path):
    out = tmp_path / "r.html"
    rc = main(
        [
            "--before",
            str(before_multi_gpkg),
            "--after",
            str(after_multi_gpkg),
            "--table",
            "roads",
            "-o",
            str(out),
        ]
    )
    assert rc == 0
    tabs = re.findall(
        r'<button type="button" data-table="([^"]+)"',
        out.read_text(encoding="utf-8"),
    )
    assert tabs == ["roads"]


def test_no_changes(before_gpkg, tmp_path):
    html_path = tmp_path / "r.html"
    json_path = tmp_path / "d.json"
    rc = main(
        [
            "--before",
            str(before_gpkg),
            "--after",
            str(before_gpkg),
            "-o",
            str(html_path),
            "--json",
            str(json_path),
        ]
    )
    assert rc == 0
    assert "No changes." in html_path.read_text(encoding="utf-8")
    assert json.loads(json_path.read_text(encoding="utf-8")) == []


def test_unknown_table(before_multi_gpkg, after_multi_gpkg, tmp_path):
    rc = main(
        [
            "--before",
            str(before_multi_gpkg),
            "--after",
            str(after_multi_gpkg),
            "--table",
            "nope",
            "-o",
            str(tmp_path / "r.html"),
        ]
    )
    assert rc == 1
