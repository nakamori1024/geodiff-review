import argparse
import json
import tempfile
from collections import Counter
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


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="geodiff-review",
        description="Detect and review differences between two GeoPackage files.",
    )
    p.add_argument(
        "--before", type=Path, required=True, help="GeoPackage before changes"
    )
    p.add_argument("--after", type=Path, required=True, help="GeoPackage after changes")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("review.html"),
        help="output HTML path (default: review.html)",
    )
    p.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        default=None,
        help="also write the normalized diff as JSON",
    )
    p.add_argument("--table", default=None, help="limit comparison to a single table")
    p.add_argument(
        "--open",
        dest="open_browser",
        action="store_true",
        help="open the generated HTML in a browser",
    )
    return p.parse_args(argv)


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


def main(argv=None) -> int:
    # Parse arguments and validate input paths
    args = parse_args(argv)

    for label, path in (("--before", args.before), ("--after", args.after)):
        if not path.exists():
            print(f"error: {label} not found: {path}")
            return 1

    # Read schemas from both GeoPackages
    before_schema = read_schema(args.before)
    after_schema = read_schema(args.after)

    print(f"before: {args.before} ({len(before_schema)} tables)")
    print(f"after : {args.after} ({len(after_schema)} tables)")

    # Build lookup maps for column names, primary keys, and geometry per table
    names_map = {s["table"]: column_names(s) for s in before_schema}
    pk_map = {s["table"]: primary_key_name(s) for s in before_schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in before_schema}

    # Compute and normalize diff between the two GeoPackages
    normalized = compute_diff(args.before, args.after, names_map, pk_map, geom_map)
    print(f"changes: {len(normalized)}")

    # Print summary grouped by table and change type
    for (table, change_type), n in sorted(summarize(normalized).items()):
        print(f"  {table}: {n} {change_type}(s)")

    # Write normalized diff as JSON if requested
    if args.json_path:
        args.json_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"json: {args.json_path}")

    print(f"output: {args.output}")
    return 0
