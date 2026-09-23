# tests/conftest.py
from pathlib import Path

import pytest

from scripts.build_gpkg import geojson_to_gpkg

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def before_gpkg(tmp_path_factory):
    dst = tmp_path_factory.mktemp("gpkg") / "before.gpkg"
    geojson_to_gpkg(DATA / "sapporo_chuo_roads_2023.geojson", dst)
    return dst
