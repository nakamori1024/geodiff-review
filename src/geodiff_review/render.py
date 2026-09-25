import html
import json

MAX_LEN = 20
MAPLIBRE_VERSION = "5.4.0"
BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron"

_CSS = """\
body { font-family: sans-serif; font-size: 13px; }
table { border-collapse: collapse; }
th, td { padding: 2px 8px; border: 1px solid #8c959f; white-space: nowrap; }
th { background: #f6f8fa; text-align: left; }
tr.add td { background: #e6ffec; }
tr.del td { background: #ffebe9; }
tr.add td.changed { background: #abf2bc; }
tr.del td.changed { background: #ffc0c0; }
tr.del:not(.pair-end) td { border-bottom-color: #d0d7de; }
#map { width: 100%; height: 50vh; }
"""


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

    parts: list[str] = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html><head><meta charset='utf-8'>")
    parts.append(
        f'<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/maplibre-gl@{MAPLIBRE_VERSION}/dist/maplibre-gl.css">'
    )
    parts.append(
        f'<script src="https://cdn.jsdelivr.net/npm/maplibre-gl@{MAPLIBRE_VERSION}/dist/maplibre-gl.js"></script>'
    )
    parts.append(f"<style>{_CSS}</style>")
    parts.append("</head><body>")

    if geom_map:
        before_fc, after_fc = _feature_collections(entries, geom_map)
        before_json = _embed(before_fc)
        after_json = _embed(after_fc)
        parts.append('<div id="map"></div>')
        parts.append("<script>")
        parts.append(f"const before = {before_json};")
        parts.append(f"const after = {after_json};")
        parts.append(f"""
const map = new maplibregl.Map({{
  container: 'map',
  style: '{BASEMAP_STYLE}',
  center: [0, 0],
  zoom: 1
}});

map.on('load', () => {{
  map.addSource('before', {{ type: 'geojson', data: before }});
  map.addSource('after',  {{ type: 'geojson', data: after  }});

  map.addLayer({{
    id: 'before-line', type: 'line', source: 'before',
    paint: {{ 'line-color': '#cf222e', 'line-width': 8, 'line-opacity': 0.5 }}
  }});
  map.addLayer({{
    id: 'after-line', type: 'line', source: 'after',
    paint: {{ 'line-color': '#20dd5b', 'line-width': 4 }}
  }});

  const bounds = new maplibregl.LngLatBounds();
  for (const fc of [before, after])
    for (const f of fc.features)
      for (const part of f.geometry.coordinates)
        for (const c of part) bounds.extend(c);
  if (!bounds.isEmpty()) map.fitBounds(bounds, {{ padding: 40 }});
}});""")
        parts.append("</script>")

    for table, group in tables.items():
        geom = geom_map.get(table) if geom_map else None
        cols = _reorder_cols(names_map[table], geom)
        parts.append(f"<h2>{html.escape(table)}</h2>")
        parts.append("<table>")
        parts.append("<thead><tr><th></th>")
        for c in cols:
            parts.append(f"<th>{html.escape(c)}</th>")
        parts.append("</tr></thead>")
        parts.append("<tbody>")

        for entry in sorted(group, key=lambda e: e["pk"]["value"]):
            changed = set(entry["changes"])
            if entry["type"] in ("insert", "delete"):
                changed.add(entry["pk"]["column"])
            rows = _rows_for(entry)
            for i, (mark, cls, row_data) in enumerate(rows):
                is_last = i == len(rows) - 1
                tr_cls = f"{cls} pair-end" if is_last else cls
                parts.append(f'<tr class="{tr_cls}">')
                parts.append(f"<td>{mark}</td>")
                for c in cols:
                    td_cls = ' class="changed"' if c in changed else ""
                    val = _cell_text(row_data.get(c))
                    parts.append(f"<td{td_cls}>{html.escape(val)}</td>")
                parts.append("</tr>")

        parts.append("</tbody></table>")

    parts.append("</body></html>")
    return "\n".join(parts)
