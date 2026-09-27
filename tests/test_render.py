import json
import re

from geodiff_review.inspect import read_schema
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    geometry_kind,
    primary_key_name,
)
from geodiff_review.pipeline import compute_diff
from geodiff_review.render import render_html


def _build_maps(schema):
    names_map = {s["table"]: column_names(s) for s in schema}
    pk_map = {s["table"]: primary_key_name(s) for s in schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in schema}
    kind_map = {s["table"]: geometry_kind(s) for s in schema}
    return names_map, pk_map, geom_map, kind_map


def test_render_html_contains_rows(before_gpkg, after_gpkg):
    schema = read_schema(before_gpkg)
    names_map, pk_map, geom_map, kind_map = _build_maps(schema)

    normalized = compute_diff(before_gpkg, after_gpkg, names_map, pk_map, geom_map)
    out = render_html(normalized, names_map, geom_map, kind_map)

    assert "<table" in out
    assert "北１条東１８丁目線" in out
    assert out.count('class="add') == 38  # insert 4 + update 34
    assert out.count('class="del') == 35  # delete 1 + update 34
    assert not re.search(r"__[A-Z][A-Z_]*__", out)


def test_render_multi_layers(before_multi_gpkg, after_multi_gpkg):
    schema = read_schema(before_multi_gpkg)
    names_map, pk_map, geom_map, kind_map = _build_maps(schema)

    normalized = compute_diff(
        before_multi_gpkg, after_multi_gpkg, names_map, pk_map, geom_map
    )
    out = render_html(normalized, names_map, geom_map, kind_map)

    m = re.search(
        r'<script id="geodiff-data" type="application/json">(.*?)</script>',
        out,
        re.DOTALL,
    )
    assert m is not None
    data = json.loads(m.group(1))
    kinds = {l["table"]: l["kind"] for l in data["map"]["layers"]}
    assert kinds == {"roads": "line", "road_starts": "point", "road_buffers": "polygon"}
    assert not re.search(r"__[A-Z][A-Z_]*__", out)
