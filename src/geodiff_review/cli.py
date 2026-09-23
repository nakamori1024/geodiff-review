import argparse
import tempfile
from collections import Counter
from pathlib import Path

from geodiff_review.diff import create_changeset, list_changes
from geodiff_review.inspect import read_schema


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

    with tempfile.TemporaryDirectory() as tmpdir:
        changeset = Path(tmpdir) / "changeset.bin"
        count = create_changeset(args.before, args.after, changeset)
        print(f"changes: {count}")

        if count > 0:
            changes = list_changes(changeset)
            summary: Counter[tuple[str, str]] = Counter()
            for entry in changes:
                summary[(entry["table"], entry["type"])] += 1
            for (table, change_type), n in sorted(summary.items()):
                print(f"  {table}: {n} {change_type}(s)")

    print(f"output: {args.output}")
    return 0
