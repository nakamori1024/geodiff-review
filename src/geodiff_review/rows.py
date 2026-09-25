import sqlite3
from collections.abc import Sequence
from pathlib import Path

from geodiff_review.geometry import decode_gpkg_bytes


def read_rows(
    gpkg: Path,
    table: str,
    pk_column: str,
    pk_values: Sequence,
    geom_column: str | None = None,
) -> dict:
    if not pk_values:
        return {}

    con = sqlite3.connect(gpkg)
    con.row_factory = sqlite3.Row
    try:
        placeholders = ",".join("?" * len(pk_values))
        sql = f'SELECT * FROM "{table}" WHERE "{pk_column}" IN ({placeholders})'
        result = {}
        for r in con.execute(sql, list(pk_values)):
            d = dict(r)
            if geom_column and d.get(geom_column) is not None:
                d[geom_column] = decode_gpkg_bytes(d[geom_column])
            result[r[pk_column]] = d
        return result
    finally:
        con.close()
