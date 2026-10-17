import tempfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from geodiff_review.diff import create_changeset, list_changes
from geodiff_review.inspect import read_schema
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    normalize_entry,
    primary_key_name,
)
from geodiff_review.rows import read_rows


class GeodiffReviewError(Exception):
    pass


class TableNotFoundError(GeodiffReviewError):
    def __init__(self, unknown: list[str], available: list[str]):
        self.unknown = unknown
        self.available = available
        super().__init__(f"table not found: {', '.join(unknown)}")


class TableMismatchError(GeodiffReviewError):
    def __init__(
        self,
        only_before: list[str],
        only_after: list[str],
        common: list[str],
    ):
        self.only_before = only_before
        self.only_after = only_after
        self.common = common
        super().__init__("table sets do not match between the two GeoPackages")


def prepare_diff(
    before: str | Path,
    after: str | Path,
    tables: Sequence[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Read schemas, validate tables, and compute the normalized diff.

    Returns:
        (schemas, normalized) where *schemas* is the before-side schema list.

    Raises:
        FileNotFoundError: if *before* or *after* does not exist.
        TableNotFoundError: if a requested table is not in both files.
        TableMismatchError: if the table sets differ between the two files.
    """
    before = Path(before)
    after = Path(after)
    for path in (before, after):
        if not path.exists():
            raise FileNotFoundError(path)

    before_schema = read_schema(before)
    after_schema = read_schema(after)

    if tables:
        available = {s["table"] for s in before_schema} & {
            s["table"] for s in after_schema
        }
        unknown = [t for t in tables if t not in available]
        if unknown:
            raise TableNotFoundError(unknown, sorted(available))
        before_schema = [s for s in before_schema if s["table"] in tables]
        after_schema = [s for s in after_schema if s["table"] in tables]

    before_tables = {s["table"] for s in before_schema}
    after_tables = {s["table"] for s in after_schema}
    if before_tables != after_tables:
        raise TableMismatchError(
            only_before=sorted(before_tables - after_tables),
            only_after=sorted(after_tables - before_tables),
            common=sorted(before_tables & after_tables),
        )

    names_map = {s["table"]: column_names(s) for s in before_schema}
    pk_map = {s["table"]: primary_key_name(s) for s in before_schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in before_schema}

    normalized = compute_diff(before, after, names_map, pk_map, geom_map, tables=tables)
    return before_schema, normalized


def diff_gpkg(
    before: str | Path,
    after: str | Path,
    tables: Sequence[str] | None = None,
) -> dict:
    """Compare two GeoPackage files and return the JSON output as a dict.

    This is a convenience wrapper around :func:`prepare_diff` and
    :func:`~geodiff_review.output.build_output`.

    Raises:
        FileNotFoundError: if *before* or *after* does not exist.
        TableNotFoundError: if a requested table is not in both files.
        TableMismatchError: if the table sets differ between the two files.
    """
    from geodiff_review.output import build_output

    schemas, normalized = prepare_diff(before, after, tables=tables)
    return build_output(schemas, normalized)


def compute_diff(
    before: Path,
    after: Path,
    names_map: dict[str, list[str]],
    pk_map: dict[str, str | None],
    geom_map: dict[str, str | None],
    tables: Sequence[str] | None = None,
) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmpdir:
        changeset = Path(tmpdir) / "changeset.bin"
        count = create_changeset(before, after, changeset, tables=tables)
        if count == 0:
            return []
        changes = list_changes(changeset)
        normalized = [
            normalize_entry(e, names_map[e["table"]], pk_map[e["table"]])
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
    before_rows: dict[str, dict] = {}
    for t, pks in before_pks.items():
        pk_col = pk_map[t]
        if pk_col is not None:
            before_rows[t] = read_rows(before, t, pk_col, pks, geom_column=geom_map[t])

    after_rows: dict[str, dict] = {}
    for t, pks in after_pks.items():
        pk_col = pk_map[t]
        if pk_col is not None:
            after_rows[t] = read_rows(after, t, pk_col, pks, geom_column=geom_map[t])

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
