import json
import tempfile
from pathlib import Path

import pygeodiff


_UNDEFINED_CRS = {("NONE", -1), ("NONE", 0), ("GDAL", 99999)}


def crs_authority(schema: dict) -> tuple[str, int] | None:
    crs = schema.get("crs")
    if not crs:
        return None
    auth_name = crs.get("auth_name")
    auth_code = crs.get("auth_code")
    if not auth_name or (auth_name.upper(), auth_code) in _UNDEFINED_CRS:
        return None
    return (auth_name, auth_code)


def read_schema(gpkg_path: Path, driver: str = "sqlite") -> list[dict]:
    g = pygeodiff.GeoDiff()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "schema.json"
        g.schema(driver, "", str(gpkg_path), str(out))
        return json.loads(out.read_text(encoding="utf-8"))["geodiff_schema"]
