import warnings
from pathlib import Path

import numpy as np
import pytest
from pyogrio.raw import read, write
from pyproj import Transformer
from shapely import from_wkb, to_wkb
from shapely.ops import transform

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
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="'crs' was not provided")
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


def _reproject_gpkg(src_geojson, dst, target_crs="EPSG:6669"):
    """Read a GeoJSON and write a GeoPackage reprojected to target_crs."""
    meta, _, geom, fdata = read(src_geojson)
    transformer = Transformer.from_crs(meta["crs"], target_crs, always_xy=True)
    projected = np.array(
        [to_wkb(transform(transformer.transform, from_wkb(g))) for g in geom],
        dtype=object,
    )
    write(
        dst,
        projected,
        fdata,
        fields=meta["fields"],
        layer="roads",
        driver="GPKG",
        geometry_type=meta["geometry_type"],
        crs=target_crs,
        layer_options={"FID": "id"},
    )


@pytest.fixture(scope="session")
def projected_before_gpkg(tmp_path_factory):
    """GeoPackage in EPSG:6669 (Japan Plane Rectangular CS I)."""
    dst = tmp_path_factory.mktemp("gpkg") / "projected_before.gpkg"
    _reproject_gpkg(DATA / "sapporo_chuo_roads_2023.geojson", dst)
    return dst


@pytest.fixture(scope="session")
def projected_after_gpkg(tmp_path_factory):
    """GeoPackage in EPSG:6669 (Japan Plane Rectangular CS I)."""
    dst = tmp_path_factory.mktemp("gpkg") / "projected_after.gpkg"
    _reproject_gpkg(DATA / "sapporo_chuo_roads_2025.geojson", dst)
    return dst
