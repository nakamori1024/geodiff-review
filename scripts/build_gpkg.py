from pathlib import Path

from pyogrio.raw import read, write

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


if __name__ == "__main__":
    for year in ("2023", "2025"):
        geojson_to_gpkg(
            DATA / f"sapporo_chuo_roads_{year}.geojson",
            DATA / f"sapporo_chuo_roads_{year}.gpkg",
        )
