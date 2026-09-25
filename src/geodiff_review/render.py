import html
import json

MAX_LEN = 20

_CSS = """\
body { font-family: sans-serif; font-size: 13px; }
table { border-collapse: collapse; }
th, td { padding: 2px 8px; border: 1px solid #d0d7de; white-space: nowrap; }
th { background: #f6f8fa; text-align: left; }
tr.add td { background: #e6ffec; }
tr.del td { background: #ffebe9; }
tr.add td.changed { background: #abf2bc; }
tr.del td.changed { background: #ffc0c0; }
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
    parts.append(f"<style>{_CSS}</style>")
    parts.append("</head><body>")

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
            for mark, cls, row_data in _rows_for(entry):
                parts.append(f'<tr class="{cls}">')
                parts.append(f"<td>{mark}</td>")
                for c in cols:
                    td_cls = ' class="changed"' if c in changed else ""
                    val = _cell_text(row_data.get(c))
                    parts.append(f"<td{td_cls}>{html.escape(val)}</td>")
                parts.append("</tr>")

        parts.append("</tbody></table>")

    parts.append("</body></html>")
    return "\n".join(parts)
