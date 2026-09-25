import argparse
import json
import webbrowser
from pathlib import Path

from geodiff_review.inspect import read_schema
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    primary_key_name,
)
from geodiff_review.pipeline import compute_diff, summarize
from geodiff_review.render import render_html


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

    html_text = render_html(normalized, names_map, geom_map)
    args.output.write_text(html_text, encoding="utf-8")
    print(f"output: {args.output}")

    if args.open_browser:
        webbrowser.open(args.output.resolve().as_uri())

    return 0
