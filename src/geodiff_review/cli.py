import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path

from geodiff_review.diff import create_changeset, list_changes
from geodiff_review.inspect import read_schema
from geodiff_review.normalize import column_names, normalize_entry


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
    before: Path, after: Path, names_map: dict[str, list[str]]
) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmpdir:
        changeset = Path(tmpdir) / "changeset.bin"
        count = create_changeset(before, after, changeset)
        if count == 0:
            return []
        changes = list_changes(changeset)
        return [normalize_entry(e, names_map[e["table"]]) for e in changes]


def summarize(normalized: list[dict]) -> Counter[tuple[str, str]]:
    return Counter((e["table"], e["type"]) for e in normalized)


def main(argv=None) -> int:
    args = parse_args(argv)

    for label, path in (("--before", args.before), ("--after", args.after)):
        if not path.exists():
            print(f"error: {label} not found: {path}")
            return 1

    before_schema = read_schema(args.before)
    after_schema = read_schema(args.after)

    print(f"before: {args.before} ({len(before_schema)} tables)")
    print(f"after : {args.after} ({len(after_schema)} tables)")

    names_map = {s["table"]: column_names(s) for s in before_schema}
    normalized = compute_diff(args.before, args.after, names_map)
    print(f"changes: {len(normalized)}")

    for (table, change_type), n in sorted(summarize(normalized).items()):
        print(f"  {table}: {n} {change_type}(s)")

    if args.json_path and normalized:
        args.json_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"json: {args.json_path}")

    print(f"output: {args.output}")
    return 0
