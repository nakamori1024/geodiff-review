from geodiff_review.diff import create_changeset, list_changes
from geodiff_review.inspect import read_schema
from geodiff_review.normalize import column_names, normalize_entry


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


def test_normalize_entry_update(before_gpkg, after_gpkg, tmp_path):
    names = column_names(read_schema(before_gpkg)[0])
    out = tmp_path / "changeset.bin"
    create_changeset(before_gpkg, after_gpkg, out)
    normalized = [normalize_entry(e, names) for e in list_changes(out)]

    target = [
        e
        for e in normalized
        if e["type"] == "update"
        and any(c["column"] == "width_max" for c in e["changes"])
    ]
    assert len(target) == 1
    changed = {c["column"]: (c["before"], c["after"]) for c in target[0]["changes"]}
    assert changed["id"] == (511, None)
    assert changed["width_max"] == (18.45, 18.02)
