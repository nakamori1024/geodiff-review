# geodiff-review

A CLI tool for detecting and reviewing differences in GeoPackage files.
Generates a single-file HTML report with diff tables and an interactive map
(the map requires internet access for MapLibre GL JS and OpenFreeMap basemap tiles).

This tool uses [geodiff](https://github.com/MerginMaps/geodiff) by Mergin Maps
to compute differences. It is not affiliated with the geodiff project.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Usage

```bash
uv run geodiff-review --before before.gpkg --after after.gpkg
```

This generates `review.html` with:

- Diff tables for each table in the GeoPackage (insert/delete/update with changed cells highlighted)
- Tabbed panels when the GeoPackage contains multiple tables
- An interactive map (MapLibre GL JS) showing before (red) and after (green) geometries
- Layer toggle controls for showing/hiding individual tables on the map
- Bidirectional selection between table rows and map features

### Options

| Option | Description |
|---|---|
| `--before` | GeoPackage before changes (required) |
| `--after` | GeoPackage after changes (required) |
| `-o`, `--output` | Output HTML path (default: `review.html`) |
| `--table TABLE` | Limit comparison to the given table (can be repeated) |
| `--json` | Also write the normalized diff as JSON |
| `--open` | Open the generated HTML in a browser |

### Examples

```bash
# Generate HTML and open in browser
uv run geodiff-review --before before.gpkg --after after.gpkg --open

# Also export JSON
uv run geodiff-review --before before.gpkg --after after.gpkg --json diff.json

# Compare specific tables only
uv run geodiff-review --before before.gpkg --after after.gpkg --table roads --table road_starts
```

## Supported geometry types

| Geometry type | Map rendering |
|---|---|
| Point / MultiPoint | Circle |
| LineString / MultiLineString | Line |
| Polygon / MultiPolygon | Fill + stroke |

Tables with unsupported or mixed geometry types are shown in the diff table only (no map layer).

## Development

### Preparing test data

Generate GPKG from GeoJSON:

```bash
uv run python scripts/build_gpkg.py
```

This creates single-table and multi-table (roads, road_starts, road_buffers) GPKGs from the test GeoJSON data.

### Running tests

```bash
uv run pytest
```

### Lint / Format

```bash
uv run ruff check .
uv run ruff format . --check --diff
```
