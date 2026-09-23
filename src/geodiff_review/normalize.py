def column_names(schema: dict) -> list[str]:
    return [c["name"] for c in schema["columns"]]


def primary_key_name(schema: dict) -> str | None:
    for c in schema["columns"]:
        if c.get("primary_key"):
            return c["name"]
    return None


def normalize_entry(entry: dict, names: list[str], pk: str | None = None) -> dict:
    out = {"table": entry["table"], "type": entry["type"], "pk": None, "changes": []}
    for ch in entry["changes"]:
        name = names[ch["column"]]
        before, after = ch.get("old"), ch.get("new")
        if name == pk:
            out["pk"] = {"column": name, "value": before if before is not None else after}
            continue
        out["changes"].append({"column": name, "before": before, "after": after})
    return out
