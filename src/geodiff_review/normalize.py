def column_names(schema: dict) -> list[str]:
    return [c["name"] for c in schema["columns"]]


def normalize_entry(entry: dict, names: list[str]) -> dict:
    out = {"table": entry["table"], "type": entry["type"], "changes": []}
    for ch in entry["changes"]:
        out["changes"].append(
            {
                "column": names[ch["column"]],
                "before": ch.get("old"),
                "after": ch.get("new"),
            }
        )
    return out
