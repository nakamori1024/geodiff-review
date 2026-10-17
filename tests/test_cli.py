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
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["format_version"] == 2
    assert "roads" in data["tables"]
    roads = data["tables"]["roads"]
    assert roads["primary_key"] == "id"
    assert roads["geometry"]["column"] == "geom"
    assert roads["geometry"]["type"] == "MULTILINESTRING"
    assert roads["geometry"]["crs"] == {"auth_name": "EPSG", "auth_code": 4326}
    assert {"name": "id", "type": "integer"} in roads["columns"]
    assert roads["changes"] == []


def test_table_mismatch(before_gpkg, after_multi_gpkg, tmp_path):
    rc = main(
        [
            "--before",
            str(before_gpkg),
            "--after",
            str(after_multi_gpkg),
            "-o",
            str(tmp_path / "r.html"),
        ]
    )
    assert rc == 1


def test_table_mismatch_with_filter(before_gpkg, after_multi_gpkg, tmp_path):
    out = tmp_path / "r.html"
    rc = main(
        [
            "--before",
            str(before_gpkg),
            "--after",
            str(after_multi_gpkg),
            "--table",
            "roads",
            "-o",
            str(out),
        ]
    )
    assert rc == 0
    assert out.exists()


def test_no_crs_outputs_null(no_crs_gpkg, tmp_path):
    json_path = tmp_path / "d.json"
    rc = main(
        [
            "--before",
            str(no_crs_gpkg),
            "--after",
            str(no_crs_gpkg),
            "-o",
            str(tmp_path / "r.html"),
            "--json",
            str(json_path),
        ]
    )
    assert rc == 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    roads = data["tables"]["roads"]
    assert roads["geometry"]["crs"] is None


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


def test_projected_json_preserves_source_coords(
    projected_before_gpkg, projected_after_gpkg, tmp_path
):
    json_path = tmp_path / "d.json"
    rc = main(
        [
            "--before",
            str(projected_before_gpkg),
            "--after",
            str(projected_after_gpkg),
            "-o",
            str(tmp_path / "r.html"),
            "--json",
            str(json_path),
        ]
    )
    assert rc == 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    roads = data["tables"]["roads"]
    assert roads["geometry"]["crs"] == {"auth_name": "EPSG", "auth_code": 6669}

    # Coordinates in JSON should remain in projected CRS (not lon/lat)
    for change in roads["changes"]:
        for side in ("before", "after"):
            row = change.get("row", {}).get(side)
            if row and row.get("geom"):
                _assert_projected(row["geom"]["coordinates"])


def _assert_projected(coords):
    """Assert coords are in projected CRS (large values, not lon/lat)."""
    if isinstance(coords[0], (int, float)):
        assert abs(coords[0]) > 1000 or abs(coords[1]) > 1000
    else:
        for c in coords:
            _assert_projected(c)
