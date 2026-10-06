import json
import tempfile
from collections.abc import Sequence
from pathlib import Path

import pygeodiff


def create_changeset(
    before: Path, after: Path, out: Path, tables: Sequence[str] | None = None
) -> int:
    g = pygeodiff.GeoDiff()
    if tables:
        g.set_tables_to_include(list(tables))
    g.create_changeset(str(before), str(after), str(out))
    return g.changes_count(str(out))


def list_changes(changeset: Path) -> list[dict]:
    g = pygeodiff.GeoDiff()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir) / "changes.json"
        g.list_changes(str(changeset), str(tmp))
        return json.loads(tmp.read_text(encoding="utf-8"))["geodiff"]
