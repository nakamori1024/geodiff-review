from collections import Counter

from geodiff_review.inspect import read_schema
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    primary_key_name,
)
from geodiff_review.pipeline import compute_diff


def test_compute_diff_includes_rows(before_gpkg, after_gpkg):
    schema = read_schema(before_gpkg)
    names_map = {s["table"]: column_names(s) for s in schema}
    pk_map = {s["table"]: primary_key_name(s) for s in schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in schema}

    normalized = compute_diff(before_gpkg, after_gpkg, names_map, pk_map, geom_map)
    by_pk = {e["pk"]["value"]: e for e in normalized}

    # update: both before and after
    assert by_pk[27]["row"]["before"]["route_no"] == "00027"
    assert by_pk[27]["row"]["after"]["route_no"] == "00027"

    # insert: before is None
    assert by_pk[835]["row"]["before"] is None
    assert by_pk[835]["row"]["after"]["route_name"] == "宮の森２条１２・１３丁目１号線"

    # delete: after is None
    assert by_pk[9203]["row"]["before"]["route_name"] == "中島橋歩道線"
    assert by_pk[9203]["row"]["after"] is None


def test_compute_diff_multi_table(before_multi_gpkg, after_multi_gpkg):
    schema = read_schema(before_multi_gpkg)
    names_map = {s["table"]: column_names(s) for s in schema}
    pk_map = {s["table"]: primary_key_name(s) for s in schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in schema}

    assert set(names_map) == {"roads", "road_starts", "road_buffers"}

    normalized = compute_diff(
        before_multi_gpkg, after_multi_gpkg, names_map, pk_map, geom_map
    )
    by_table = Counter(e["table"] for e in normalized)

    assert by_table["roads"] == 39
    assert by_table["road_buffers"] == 39
    assert by_table["road_starts"] == 32
