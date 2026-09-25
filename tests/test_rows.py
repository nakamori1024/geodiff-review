from geodiff_review.rows import read_rows


def test_read_rows(before_gpkg):
    rows = read_rows(before_gpkg, "roads", "id", [27, 511], geom_column="geom")
    assert set(rows) == {27, 511}
    assert rows[27]["geom"]["type"] == "MultiLineString"
    assert rows[511]["width_max"] == 18.45
    assert rows[27]["route_no"] == "00027"


def test_read_rows_empty(before_gpkg):
    assert read_rows(before_gpkg, "roads", "id", []) == {}


def test_read_rows_missing_id(after_gpkg):
    # 9203 does not exist in after (deleted row)
    rows = read_rows(after_gpkg, "roads", "id", [9203], geom_column="geom")
    assert rows == {}
