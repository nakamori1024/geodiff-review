from pyproj import Transformer
from shapely import from_wkb
from shapely.geometry import mapping

_ENVELOPE_SIZE = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def decode_gpkg_bytes(raw: bytes) -> dict | None:
    if raw[:2] != b"GP":
        raise ValueError("not a GeoPackage binary blob")

    flags = raw[3]
    envelope = (flags >> 1) & 0x07
    if envelope not in _ENVELOPE_SIZE:
        raise ValueError(f"invalid envelope indicator: {envelope}")
    if (flags >> 4) & 0x01:  # empty geometry
        return None

    return mapping(from_wkb(raw[8 + _ENVELOPE_SIZE[envelope] :]))


def make_transformer(auth_name: str, auth_code: int) -> Transformer | None:
    if auth_name.upper() == "EPSG" and auth_code == 4326:
        return None
    return Transformer.from_crs(f"{auth_name}:{auth_code}", "EPSG:4326", always_xy=True)


def transform_geom(geom: dict, transformer: Transformer | None) -> dict:
    if transformer is None:
        return geom
    return {
        "type": geom["type"],
        "coordinates": _transform_coords(geom["coordinates"], transformer),
    }


def _transform_coords(coords, transformer: Transformer):
    if isinstance(coords[0], (int, float)):
        x, y = transformer.transform(coords[0], coords[1])
        if len(coords) > 2:
            return [x, y, coords[2]]
        return [x, y]
    return [_transform_coords(c, transformer) for c in coords]
