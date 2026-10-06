from geodiff_review.cli import main


def test_unknown_table(before_multi_gpkg, after_multi_gpkg, tmp_path):
    rc = main(
        [
            "--before",
            str(before_multi_gpkg),
            "--after",
            str(after_multi_gpkg),
            "--table",
            "nope",
            "-o",
            str(tmp_path / "r.html"),
        ]
    )
    assert rc == 1
