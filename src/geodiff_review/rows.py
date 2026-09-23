import sqlite3
from collections.abc import Sequence
from pathlib import Path


def read_rows(
    gpkg: Path,
    table: str,
    pk_column: str,
    pk_values: Sequence,
    exclude: Sequence[str] = (),
) -> dict:
    if not pk_values:
        return {}

    con = sqlite3.connect(gpkg)
    con.row_factory = sqlite3.Row
    try:
        placeholders = ",".join("?" * len(pk_values))
        sql = f'SELECT * FROM "{table}" WHERE "{pk_column}" IN ({placeholders})'
        return {
            row[pk_column]: {k: v for k, v in row.items() if k not in exclude}
            for row in (dict(r) for r in con.execute(sql, list(pk_values)))
        }
    finally:
        con.close()
