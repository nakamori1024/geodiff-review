from geodiff_review.diff import create_changeset, list_changes
from geodiff_review.inspect import read_schema
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    normalize_entry,
    primary_key_name,
)


def test_column_names(before_gpkg):
    names = column_names(read_schema(before_gpkg)[0])
    assert names == [
        "id",
        "geom",
        "road_class",
        "ward_code",
        "route_no",
        "route_name",
        "width_min",
        "width_max",
        "service_status",
    ]


def test_primary_key_name(before_gpkg):
    assert primary_key_name(read_schema(before_gpkg)[0]) == "id"


def test_geometry_column_name(before_gpkg):
    assert geometry_column_name(read_schema(before_gpkg)[0]) == "geom"


def test_normalize_entry_update(before_gpkg, after_gpkg, tmp_path):
    schema = read_schema(before_gpkg)[0]
    names = column_names(schema)
    pk = primary_key_name(schema)
    geom = geometry_column_name(schema)
    out = tmp_path / "changeset.bin"
    create_changeset(before_gpkg, after_gpkg, out)
    normalized = [normalize_entry(e, names, pk, geom) for e in list_changes(out)]

    target = [
        e
        for e in normalized
        if e["type"] == "update"
        and any(c["column"] == "width_max" for c in e["changes"]["fields"])
    ]
    assert len(target) == 1
    assert target[0]["pk"] == {"column": "id", "value": 511}
    assert target[0]["changes"]["geometry"] is None
    changed = {
        c["column"]: (c["before"], c["after"]) for c in target[0]["changes"]["fields"]
    }
    assert "id" not in changed
    assert "geom" not in changed
    assert changed["width_max"] == (18.45, 18.02)
