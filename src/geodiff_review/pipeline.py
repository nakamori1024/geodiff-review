import tempfile
from collections import Counter
from pathlib import Path

from geodiff_review.diff import create_changeset, list_changes
from geodiff_review.normalize import normalize_entry
from geodiff_review.rows import read_rows


def compute_diff(
    before: Path,
    after: Path,
    names_map: dict[str, list[str]],
    pk_map: dict[str, str | None],
    geom_map: dict[str, str | None],
) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmpdir:
        changeset = Path(tmpdir) / "changeset.bin"
        count = create_changeset(before, after, changeset)
        if count == 0:
            return []
        changes = list_changes(changeset)
        normalized = [
            normalize_entry(
                e, names_map[e["table"]], pk_map[e["table"]], geom_map[e["table"]]
            )
            for e in changes
        ]

    # Collect primary keys needed from before/after GeoPackages
    before_pks: dict[str, list] = {}
    after_pks: dict[str, list] = {}
    for e in normalized:
        table = e["table"]
        value = e["pk"]["value"]
        if e["type"] in ("update", "delete"):
            before_pks.setdefault(table, []).append(value)
        if e["type"] in ("update", "insert"):
            after_pks.setdefault(table, []).append(value)

    # Read rows from both GeoPackages
    def _exclude(table: str) -> list[str]:
        g = geom_map[table]
        return [g] if g else []

    before_rows: dict[str, dict] = {}
    for t, pks in before_pks.items():
        pk_col = pk_map[t]
        if pk_col is not None:
            before_rows[t] = read_rows(before, t, pk_col, pks, exclude=_exclude(t))

    after_rows: dict[str, dict] = {}
    for t, pks in after_pks.items():
        pk_col = pk_map[t]
        if pk_col is not None:
            after_rows[t] = read_rows(after, t, pk_col, pks, exclude=_exclude(t))

    # Attach row data to each normalized entry
    for e in normalized:
        t, v = e["table"], e["pk"]["value"]
        e["row"] = {
            "before": before_rows.get(t, {}).get(v),
            "after": after_rows.get(t, {}).get(v),
        }

    return normalized


def summarize(normalized: list[dict]) -> Counter[tuple[str, str]]:
    return Counter((e["table"], e["type"]) for e in normalized)
