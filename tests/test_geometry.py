import base64
import copy

import pytest
from pyproj import Transformer

from geodiff_review.geometry import decode_gpkg_bytes, make_transformer, transform_geom


def test_decode_multilinestring():
    b64 = "R1AAA+YQAAAnEeFfhKthQOTMwBKZq2FAN5+E40OHRUA7vDFOjYhFQAEFAAAAAQAAAAECAAAAAwAAAOTMwBKZq2FAN5+E40OHRUBN1HcjmKthQFJnSdtTh0VAJxHhX4SrYUA7vDFOjYhFQA=="
    g = decode_gpkg_bytes(base64.b64decode(b64))
    assert g is not None
    assert g["type"] == "MultiLineString"
    assert len(g["coordinates"]) == 1  # 1 part
    assert len(g["coordinates"][0]) == 3  # 3 vertices
    lon, lat = g["coordinates"][0][0]
    assert 141 < lon < 142
    assert 43 < lat < 44


def test_decode_invalid_blob():
    with pytest.raises(ValueError):
        decode_gpkg_bytes(b"hello")


def test_make_transformer_4326_returns_none():
    assert make_transformer("EPSG", 4326) is None


def test_make_transformer_projected_returns_transformer():
    t = make_transformer("EPSG", 6669)
    assert isinstance(t, Transformer)


def test_transform_geom_noop_when_none():
    geom = {"type": "Point", "coordinates": [141.35, 43.06]}
    result = transform_geom(geom, None)
    assert result is geom


def test_transform_geom_converts_to_lonlat():
    t = make_transformer("EPSG", 6669)
    # Round-trip: 4326 -> 6669 -> 4326
    fwd = Transformer.from_crs("EPSG:4326", "EPSG:6669", always_xy=True)
    x, y = fwd.transform(141.35, 43.06)

    geom = {"type": "Point", "coordinates": [x, y]}
    result = transform_geom(geom, t)
    lon, lat = result["coordinates"]
    assert abs(lon - 141.35) < 0.01
    assert abs(lat - 43.06) < 0.01


def test_transform_geom_does_not_mutate_input():
    t = make_transformer("EPSG", 6669)
    fwd = Transformer.from_crs("EPSG:4326", "EPSG:6669", always_xy=True)
    x, y = fwd.transform(141.35, 43.06)

    geom = {"type": "Point", "coordinates": [x, y]}
    original = copy.deepcopy(geom)
    transform_geom(geom, t)
    assert geom == original
