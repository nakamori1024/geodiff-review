import html
import json
import re
from importlib.resources import files

MAX_LEN = 20
MAPLIBRE_VERSION = "5.4.0"
BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron"

_TEMPLATES = files("geodiff_review") / "templates"


def _read(name: str) -> str:
    return (_TEMPLATES / name).read_text(encoding="utf-8")


def _fill(template: str, values: dict[str, str]) -> str:
    return re.sub(r"__([A-Z][A-Z_]*?)__", lambda m: values[m.group(1)], template)


def _cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        s = json.dumps(value, ensure_ascii=False)
    else:
        s = str(value)
    return s if len(s) <= MAX_LEN else s[:MAX_LEN] + "…"


def _rows_for(entry: dict) -> list[tuple[str, str, dict]]:
    t = entry["type"]
    if t == "insert":
        return [("+", "add", entry["row"]["after"])]
    if t == "delete":
        return [("-", "del", entry["row"]["before"])]
    return [
        ("-", "del", entry["row"]["before"]),
        ("+", "add", entry["row"]["after"]),
    ]


def _feature_collections(
    entries: list[dict], geom_map: dict[str, str | None]
) -> tuple[dict, dict]:
    before_features: list[dict] = []
    after_features: list[dict] = []
    for e in entries:
        geom_col = geom_map.get(e["table"])
        if not geom_col:
            continue
        pk = e["pk"]["value"]
        for side, bucket in (("before", before_features), ("after", after_features)):
            row = e["row"].get(side)
            if row and row.get(geom_col):
                bucket.append(
                    {
                        "type": "Feature",
                        "geometry": row[geom_col],
                        "properties": {"pk": pk, "type": e["type"]},
                    }
                )
    return (
        {"type": "FeatureCollection", "features": before_features},
        {"type": "FeatureCollection", "features": after_features},
    )


def _embed(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")


def _reorder_cols(cols: list[str], geom: str | None) -> list[str]:
    if geom is None or geom not in cols:
        return cols
    return [c for c in cols if c != geom] + [geom]


def render_html(
    entries: list[dict],
    names_map: dict[str, list[str]],
    geom_map: dict[str, str | None] | None = None,
) -> str:
    tables: dict[str, list[dict]] = {}
    for e in entries:
        tables.setdefault(e["table"], []).append(e)

    # Build tables HTML
    table_parts: list[str] = []
    for table, group in tables.items():
        geom = geom_map.get(table) if geom_map else None
        cols = _reorder_cols(names_map[table], geom)
        table_parts.append(f"<h2>{html.escape(table)}</h2>")
        table_parts.append("<table>")
        table_parts.append("<thead><tr><th></th>")
        for c in cols:
            table_parts.append(f"<th>{html.escape(c)}</th>")
        table_parts.append("</tr></thead>")
        table_parts.append("<tbody>")

        for entry in sorted(group, key=lambda e: e["pk"]["value"]):
            changed = set(entry["changes"])
            if entry["type"] in ("insert", "delete"):
                changed.add(entry["pk"]["column"])
            rows = _rows_for(entry)
            for i, (mark, cls, row_data) in enumerate(rows):
                is_last = i == len(rows) - 1
                tr_cls = f"{cls} pair-end" if is_last else cls
                table_parts.append(f'<tr class="{tr_cls}">')
                table_parts.append(f"<td>{mark}</td>")
                for c in cols:
                    td_cls = ' class="changed"' if c in changed else ""
                    val = _cell_text(row_data.get(c))
                    table_parts.append(f"<td{td_cls}>{html.escape(val)}</td>")
                table_parts.append("</tr>")

        table_parts.append("</tbody></table>")

    # Build map data
    data: dict = {"map": None}
    map_html = ""
    if geom_map:
        before_fc, after_fc = _feature_collections(entries, geom_map)
        data["map"] = {
            "basemap": BASEMAP_STYLE,
            "before": before_fc,
            "after": after_fc,
        }
        map_html = '<div id="map"></div>'

    return _fill(
        _read("review.html"),
        {
            "MAPLIBRE_VERSION": MAPLIBRE_VERSION,
            "CSS": _read("review.css"),
            "JS": _read("review.js"),
            "MAP": map_html,
            "TABLES": "\n".join(table_parts),
            "DATA": _embed(data),
        },
    )
