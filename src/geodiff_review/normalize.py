def column_names(schema: dict) -> list[str]:
    return [c["name"] for c in schema["columns"]]


def primary_key_name(schema: dict) -> str | None:
    for c in schema["columns"]:
        if c.get("primary_key"):
            return c["name"]
    return None


def geometry_column_name(schema: dict) -> str | None:
    for c in schema["columns"]:
        if c.get("type") == "geometry":
            return c["name"]
    return None


def normalize_entry(entry: dict, names: list[str], pk: str | None = None) -> dict:
    changed = []
    pk_value = None
    for ch in entry["changes"]:
        name = names[ch["column"]]
        if name == pk:
            before, after = ch.get("old"), ch.get("new")
            pk_value = before if before is not None else after
        else:
            changed.append(name)

    return {
        "table": entry["table"],
        "type": entry["type"],
        "pk": {"column": pk, "value": pk_value} if pk else None,
        "row": None,
        "changes": changed,
    }
