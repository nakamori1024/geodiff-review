import argparse
import json
import webbrowser
from pathlib import Path

from geodiff_review.inspect import crs_authority
from geodiff_review.normalize import (
    column_names,
    geometry_column_name,
    geometry_kind,
)
from geodiff_review.output import build_output
from geodiff_review.pipeline import (
    TableMismatchError,
    TableNotFoundError,
    prepare_diff,
    summarize,
)
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
    p.add_argument(
        "--table",
        dest="tables",
        action="append",
        metavar="TABLE",
        help="limit comparison to the given table (can be repeated)",
    )
    p.add_argument(
        "--open",
        dest="open_browser",
        action="store_true",
        help="open the generated HTML in a browser",
    )
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        before_schema, normalized = prepare_diff(
            args.before, args.after, tables=args.tables
        )
    except FileNotFoundError as e:
        print(f"error: file not found: {e}")
        return 1
    except TableNotFoundError as e:
        print(f"error: table not found: {', '.join(e.unknown)}")
        print(f"available tables: {', '.join(e.available)}")
        return 1
    except TableMismatchError as e:
        print("error: table sets do not match between the two GeoPackages")
        if e.only_before:
            print(f"  only in --before: {', '.join(e.only_before)}")
        if e.only_after:
            print(f"  only in --after: {', '.join(e.only_after)}")
        if e.common:
            hint = " ".join(f"--table {t}" for t in e.common)
            print(f"hint: use {hint} to compare common tables only")
        return 1

    print(f"before: {args.before} ({len(before_schema)} tables)")
    print(f"after : {args.after} ({len(before_schema)} tables)")

    # Build lookup maps for HTML rendering
    names_map = {s["table"]: column_names(s) for s in before_schema}
    geom_map = {s["table"]: geometry_column_name(s) for s in before_schema}
    kind_map = {s["table"]: geometry_kind(s) for s in before_schema}
    crs_map = {s["table"]: crs_authority(s) for s in before_schema}

    print(f"changes: {len(normalized)}")

    # Print summary grouped by table and change type
    for (table, change_type), n in sorted(summarize(normalized).items()):
        print(f"  {table}: {n} {change_type}(s)")

    # Write normalized diff as JSON if requested
    if args.json_path:
        output = build_output(before_schema, normalized)
        args.json_path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"json: {args.json_path}")

    html_text = render_html(normalized, names_map, geom_map, kind_map, crs_map)
    args.output.write_text(html_text, encoding="utf-8")
    print(f"output: {args.output}")

    if args.open_browser:
        webbrowser.open(args.output.resolve().as_uri())

    return 0
