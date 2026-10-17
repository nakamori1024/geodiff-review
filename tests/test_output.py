from geodiff_review.inspect import read_schema
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    primary_key_name,
)
from geodiff_review.output import build_output
from geodiff_review.pipeline import compute_diff


def test_build_output_no_changes(before_gpkg):
    schema = read_schema(before_gpkg)
    names_map = {s["table"]: column_names(s) for s in schema}
    pk_map = {s["table"]: primary_key_name(s) for s in schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in schema}

    normalized = compute_diff(before_gpkg, before_gpkg, names_map, pk_map, geom_map)
    result = build_output(schema, normalized)

    assert result["format_version"] == 2
    assert "roads" in result["tables"]
    roads = result["tables"]["roads"]
    assert roads["primary_key"] == "id"
    assert roads["geometry"]["column"] == "geom"
    assert roads["geometry"]["type"] == "MULTILINESTRING"
    assert roads["geometry"]["crs"] == {"auth_name": "EPSG", "auth_code": 4326}
    assert {"name": "id", "type": "integer"} in roads["columns"]
    assert roads["changes"] == []


def test_build_output_with_changes(before_gpkg, after_gpkg):
    schema = read_schema(before_gpkg)
    names_map = {s["table"]: column_names(s) for s in schema}
    pk_map = {s["table"]: primary_key_name(s) for s in schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in schema}

    normalized = compute_diff(before_gpkg, after_gpkg, names_map, pk_map, geom_map)
    result = build_output(schema, normalized)

    assert result["format_version"] == 2
    roads = result["tables"]["roads"]
    assert len(roads["changes"]) == 39

    # Each change should not contain "table" key (stripped by build_output)
    for change in roads["changes"]:
        assert "table" not in change
        assert "type" in change
        assert "pk" in change
        assert "row" in change
        assert "changed_columns" in change


def test_build_output_no_crs(no_crs_gpkg):
    schema = read_schema(no_crs_gpkg)
    names_map = {s["table"]: column_names(s) for s in schema}
    pk_map = {s["table"]: primary_key_name(s) for s in schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in schema}

    normalized = compute_diff(no_crs_gpkg, no_crs_gpkg, names_map, pk_map, geom_map)
    result = build_output(schema, normalized)

    roads = result["tables"]["roads"]
    assert roads["geometry"]["crs"] is None
