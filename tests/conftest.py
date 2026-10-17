from pathlib import Path

import pytest
from pyogrio.raw import read, write

from scripts.build_gpkg import geojson_to_gpkg, geojson_to_multi_gpkg

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def before_gpkg(tmp_path_factory):
    dst = tmp_path_factory.mktemp("gpkg") / "before.gpkg"
    geojson_to_gpkg(DATA / "sapporo_chuo_roads_2023.geojson", dst)
    return dst


@pytest.fixture(scope="session")
def after_gpkg(tmp_path_factory):
    dst = tmp_path_factory.mktemp("gpkg") / "after.gpkg"
    geojson_to_gpkg(DATA / "sapporo_chuo_roads_2025.geojson", dst)
    return dst


@pytest.fixture(scope="session")
def before_multi_gpkg(tmp_path_factory):
    dst = tmp_path_factory.mktemp("gpkg") / "before_multi.gpkg"
    geojson_to_multi_gpkg(DATA / "sapporo_chuo_roads_2023.geojson", dst)
    return dst


@pytest.fixture(scope="session")
def after_multi_gpkg(tmp_path_factory):
    dst = tmp_path_factory.mktemp("gpkg") / "after_multi.gpkg"
    geojson_to_multi_gpkg(DATA / "sapporo_chuo_roads_2025.geojson", dst)
    return dst


@pytest.fixture(scope="session")
def no_crs_gpkg(tmp_path_factory):
    """GeoPackage with no CRS (GDAL writes GDAL:99999)."""
    src = DATA / "sapporo_chuo_roads_2023.geojson"
    meta, _, geom, fdata = read(src)
    dst = tmp_path_factory.mktemp("gpkg") / "no_crs.gpkg"
    write(
        dst,
        geom,
        fdata,
        fields=meta["fields"],
        layer="roads",
        driver="GPKG",
        geometry_type=meta["geometry_type"],
        crs=None,
        layer_options={"FID": "id"},
    )
    return dst
