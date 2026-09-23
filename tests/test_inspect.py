from geodiff_review.inspect import read_schema


def test_read_schema(before_gpkg):
    schemas = read_schema(before_gpkg)
    assert len(schemas) == 1
    assert schemas[0]["table"] == "roads"

    names = [c["name"] for c in schemas[0]["columns"]]
    assert names == [
        "id",
        "geom",
        "road_class",
        "ward_code",
        "route_no",
        "route_name",
        "width_min",
        "width_max",
        "service_status",
    ]
    assert schemas[0]["columns"][0]["primary_key"] is True
