# geodiff-review

A CLI tool for detecting and reviewing differences in GeoPackage files.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Usage

```bash
uv run geodiff-review
```

## Development

### Preparing test data

Generate GPKG from GeoJSON:

```bash
uv run python scripts/build_gpkg.py
```

### Lint / Format

```bash
uv run ruff check .
uv run ruff format . --check --diff
```
