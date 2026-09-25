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
