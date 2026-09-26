from pathlib import Path

import numpy as np
from pyogrio.raw import read, write
from shapely import from_wkb, to_wkb
from shapely.geometry import Point

DATA = Path(__file__).parent.parent / "tests" / "data"


def geojson_to_gpkg(src, dst, layer="roads"):
    meta, _, geom, fdata = read(src)
    write(
        dst,
        geom,
        fdata,
        fields=meta["fields"],
        layer=layer,
        driver="GPKG",
        geometry_type=meta["geometry_type"],
        crs=meta["crs"],
        layer_options={"FID": "id"},
    )
    print(f"{dst}: {len(geom)} features")


def geojson_to_multi_gpkg(src, dst):
    meta, _, geom, fdata = read(src)

    # roads
    write(
        dst,
        geom,
        fdata,
        fields=meta["fields"],
        layer="roads",
        driver="GPKG",
        geometry_type=meta["geometry_type"],
        crs=meta["crs"],
        layer_options={"FID": "id"},
    )
    print(f"{dst} [roads]: {len(geom)} features")

    lines = [from_wkb(g) for g in geom]

    # road_starts
    starts = np.array(
        [to_wkb(Point(l.geoms[0].coords[0])) for l in lines], dtype=object
    )
    write(
        dst,
        starts,
        fdata,
        fields=meta["fields"],
        layer="road_starts",
        driver="GPKG",
        geometry_type="Point",
        crs=meta["crs"],
        append=True,
        layer_options={"FID": "id"},
    )
    print(f"{dst} [road_starts]: {len(starts)} features")

    # road_buffers
    buffers = np.array([to_wkb(l.buffer(0.00005)) for l in lines], dtype=object)
    write(
        dst,
        buffers,
        fdata,
        fields=meta["fields"],
        layer="road_buffers",
        driver="GPKG",
        geometry_type="Polygon",
        crs=meta["crs"],
        append=True,
        layer_options={"FID": "id"},
    )
    print(f"{dst} [road_buffers]: {len(buffers)} features")


if __name__ == "__main__":
    for year in ("2023", "2025"):
        src = DATA / f"sapporo_chuo_roads_{year}.geojson"
        geojson_to_gpkg(src, DATA / f"sapporo_chuo_roads_{year}.gpkg")
        geojson_to_multi_gpkg(src, DATA / f"sapporo_chuo_roads_{year}_multi.gpkg")
