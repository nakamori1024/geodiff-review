import base64

import pytest

from geodiff_review.geometry import decode_gpkg_bytes


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
