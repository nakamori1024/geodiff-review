import json
import tempfile
from pathlib import Path

import pygeodiff


def create_changeset(before: Path, after: Path, out: Path) -> int:
    g = pygeodiff.GeoDiff()
    g.create_changeset(str(before), str(after), str(out))
    return g.changes_count(str(out))


def list_changes(changeset: Path) -> list[dict]:
    g = pygeodiff.GeoDiff()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir) / "changes.json"
        g.list_changes(str(changeset), str(tmp))
        return json.loads(tmp.read_text(encoding="utf-8"))["geodiff"]
