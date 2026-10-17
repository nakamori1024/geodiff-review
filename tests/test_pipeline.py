from collections import Counter

import pytest

from geodiff_review.inspect import read_schema
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    primary_key_name,
)
from geodiff_review.pipeline import (
    TableMismatchError,
    TableNotFoundError,
    compute_diff,
    diff_gpkg,
)


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


def test_diff_gpkg(before_gpkg, after_gpkg):
    result = diff_gpkg(before_gpkg, after_gpkg)
    assert result["format_version"] == 2
    assert "roads" in result["tables"]
    roads = result["tables"]["roads"]
    assert roads["primary_key"] == "id"
    assert len(roads["changes"]) == 39
    for change in roads["changes"]:
        assert "table" not in change


def test_diff_gpkg_no_changes(before_gpkg):
    result = diff_gpkg(before_gpkg, before_gpkg)
    assert result["tables"]["roads"]["changes"] == []


def test_diff_gpkg_with_table_filter(before_multi_gpkg, after_multi_gpkg):
    result = diff_gpkg(before_multi_gpkg, after_multi_gpkg, tables=["roads"])
    assert list(result["tables"].keys()) == ["roads"]
    assert len(result["tables"]["roads"]["changes"]) == 39


def test_diff_gpkg_str_paths(before_gpkg, after_gpkg):
    result = diff_gpkg(str(before_gpkg), str(after_gpkg))
    assert result["format_version"] == 2
    assert len(result["tables"]["roads"]["changes"]) == 39


def test_diff_gpkg_file_not_found(tmp_path):
    missing = tmp_path / "missing.gpkg"
    with pytest.raises(FileNotFoundError):
        diff_gpkg(missing, missing)


def test_diff_gpkg_file_not_found_str(tmp_path):
    missing = str(tmp_path / "missing.gpkg")
    with pytest.raises(FileNotFoundError):
        diff_gpkg(missing, missing)


def test_diff_gpkg_table_not_found(before_multi_gpkg, after_multi_gpkg):
    with pytest.raises(TableNotFoundError) as exc_info:
        diff_gpkg(before_multi_gpkg, after_multi_gpkg, tables=["nope"])
    assert "nope" in exc_info.value.unknown
    assert "roads" in exc_info.value.available


def test_diff_gpkg_table_mismatch(before_gpkg, after_multi_gpkg):
    with pytest.raises(TableMismatchError) as exc_info:
        diff_gpkg(before_gpkg, after_multi_gpkg)
    assert exc_info.value.only_after
    assert "roads" in exc_info.value.common
