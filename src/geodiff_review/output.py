from geodiff_review.inspect import crs_authority
from geodiff_review.normalize import (
    geometry_column_name,
    primary_key_name,
)


def _build_tables_meta(schemas):
    tables = {}
    for s in schemas:
        pk = primary_key_name(s)
        geom_col = geometry_column_name(s)

        columns = [{"name": c["name"], "type": c["type"]} for c in s["columns"]]

        geom_info = None
        if geom_col:
            col = next(c for c in s["columns"] if c["name"] == geom_col)
            authority = crs_authority(s)
            crs_info = (
                {"auth_name": authority[0], "auth_code": authority[1]}
                if authority
                else None
            )
            geom_info = {
                "column": geom_col,
                "type": col.get("geometry", {}).get("type"),
                "crs": crs_info,
            }

        tables[s["table"]] = {
            "columns": columns,
            "primary_key": pk,
            "geometry": geom_info,
        }
    return tables


def build_output(schemas, normalized):
    tables = _build_tables_meta(schemas)
    for table_name in tables:
        tables[table_name]["changes"] = []
    for entry in normalized:
        change = {k: v for k, v in entry.items() if k != "table"}
        tables[entry["table"]]["changes"].append(change)
    return {
        "format_version": 2,
        "tables": tables,
    }
