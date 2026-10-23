"""Generated navigation must resolve to pages, assets, and existing fragments."""

from pathlib import Path
from runpy import run_path

CHECK = run_path(str(Path(__file__).resolve().parents[1] / "documentation/links.py"))[
    "check_links"
]


def test_local_links_and_external_urls(tmp_path):
    (tmp_path / "index.html").write_text(
        '<a href="guide/#example">Guide</a><img src="plot.png">'
        '<a href="https://example.com/">External</a><a href="mailto:a@b.c">Mail</a>'
    )
    (tmp_path / "plot.png").write_bytes(b"asset")
    (tmp_path / "guide").mkdir()
    (tmp_path / "guide/index.html").write_text(
        '<h1 id="example">Example</h1><a href="/unrooted/">Home</a>'
    )
    assert CHECK(tmp_path) == []


def test_missing_page_asset_and_fragment(tmp_path):
    (tmp_path / "index.html").write_text(
        '<a href="missing/">Missing</a><img src="absent.png">'
        '<a href="#absent">Missing fragment</a>'
    )
    errors = CHECK(tmp_path)
    assert len(errors) == 3
    assert any("missing fragment" in error for error in errors)
