import json
import tempfile
from pathlib import Path

import pygeodiff


def read_schema(gpkg_path: Path, driver: str = "sqlite") -> list[dict]:
    g = pygeodiff.GeoDiff()
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "schema.json"
        g.schema(driver, "", str(gpkg_path), str(out))
        return json.loads(out.read_text(encoding="utf-8"))["geodiff_schema"]
