import argparse
from pathlib import Path


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

    print(f"before: {args.before}")
    print(f"after : {args.after}")
    print(f"output: {args.output}")
    return 0
