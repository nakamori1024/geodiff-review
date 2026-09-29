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
    entries: list[dict], table: str, geom_col: str
) -> tuple[dict, dict]:
    before_features: list[dict] = []
    after_features: list[dict] = []
    for e in entries:
        if e["table"] != table:
            continue
        pk = e["pk"]["value"]
        for side, bucket in (("before", before_features), ("after", after_features)):
            row = e["row"].get(side)
            if row and row.get(geom_col):
                bucket.append(
                    {
                        "type": "Feature",
                        "geometry": row[geom_col],
                        "properties": {
                            "table": table,
                            "pk": pk,
                            "type": e["type"],
                        },
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
    kind_map: dict[str, str | None] | None = None,
) -> str:
    tables: dict[str, list[dict]] = {}
    for e in entries:
        tables.setdefault(e["table"], []).append(e)
    tables = dict(sorted(tables.items()))

    # Build tabs and table panels
    tab_buttons: list[str] = []
    panel_parts: list[str] = []
    for idx, (table, group) in enumerate(tables.items()):
        selected = "true" if idx == 0 else "false"
        hidden = "" if idx == 0 else " hidden"
        tab_buttons.append(
            f'<button type="button" data-table="{html.escape(table)}"'
            f' aria-selected="{selected}">'
            f"{html.escape(table)}"
            f' <span class="count">{len(group)}</span></button>'
        )

        geom = geom_map.get(table) if geom_map else None
        cols = _reorder_cols(names_map[table], geom)
        panel_parts.append(
            f'<section class="table-panel" data-table="{html.escape(table)}"{hidden}>'
        )
        panel_parts.append("<table>")
        panel_parts.append("<thead><tr><th></th>")
        for c in cols:
            panel_parts.append(f"<th>{html.escape(c)}</th>")
        panel_parts.append("</tr></thead>")
        panel_parts.append("<tbody>")

        for entry in sorted(group, key=lambda e: e["pk"]["value"]):
            changed = set(entry["changes"])
            if entry["type"] in ("insert", "delete"):
                changed.add(entry["pk"]["column"])
            rows = _rows_for(entry)
            for i, (mark, cls, row_data) in enumerate(rows):
                is_last = i == len(rows) - 1
                tr_cls = f"{cls} pair-end" if is_last else cls
                panel_parts.append(f'<tr class="{tr_cls}">')
                panel_parts.append(f"<td>{mark}</td>")
                for c in cols:
                    td_cls = ' class="changed"' if c in changed else ""
                    val = _cell_text(row_data.get(c))
                    panel_parts.append(f"<td{td_cls}>{html.escape(val)}</td>")
                panel_parts.append("</tr>")

        panel_parts.append("</tbody></table></section>")

    table_area = (
        '<div class="table-area">\n'
        '<nav class="tabs">\n'
        + "\n".join(tab_buttons)
        + "\n</nav>\n"
        + "\n".join(panel_parts)
        + "\n</div>"
    )

    # Build map data
    data: dict = {"map": None}
    map_html = ""
    if geom_map:
        layers = []
        for table in tables:
            geom_col = geom_map.get(table)
            kind = kind_map.get(table) if kind_map else None
            if not geom_col or kind is None:
                continue
            before_fc, after_fc = _feature_collections(entries, table, geom_col)
            layers.append(
                {
                    "table": table,
                    "kind": kind,
                    "before": before_fc,
                    "after": after_fc,
                }
            )
        if layers:
            data["map"] = {
                "basemap": BASEMAP_STYLE,
                "layers": layers,
            }
            map_html = '<div id="map"></div>'

    return _fill(
        _read("review.html"),
        {
            "MAPLIBRE_VERSION": MAPLIBRE_VERSION,
            "CSS": _read("review.css"),
            "JS": _read("review.js"),
            "MAP": map_html,
            "TABLES": table_area,
            "DATA": _embed(data),
        },
    )
