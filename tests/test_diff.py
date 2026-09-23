from collections import Counter

from geodiff_review.diff import create_changeset, list_changes


def test_create_changeset(before_gpkg, after_gpkg, tmp_path):
    out = tmp_path / "changeset.bin"
    assert create_changeset(before_gpkg, after_gpkg, out) == 39
    assert out.exists()


def test_list_changes(before_gpkg, after_gpkg, tmp_path):
    out = tmp_path / "changeset.bin"
    create_changeset(before_gpkg, after_gpkg, out)
    changes = list_changes(out)

    assert len(changes) == 39
    assert Counter(c["type"] for c in changes) == {
        "update": 34,
        "insert": 4,
        "delete": 1,
    }
    assert {c["table"] for c in changes} == {"roads"}
