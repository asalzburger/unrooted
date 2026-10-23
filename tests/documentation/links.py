"""Check local links, assets, and HTML fragments in a generated MkDocs site."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(str(values["id"]))
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.links.append(str(values[attribute]))


def check_links(site: Path) -> list[str]:
    site = site.resolve()
    pages = {path: Page(path) for path in site.rglob("*.html")}
    errors = []
    for path, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            # MkDocs' generated 404 page uses site-root absolute navigation.
            relative = unquote(url.path)
            if relative.startswith("/unrooted/"):
                target = site / relative.removeprefix("/unrooted/")
            elif relative.startswith("/"):
                target = site / relative.lstrip("/")
            else:
                target = path.parent / relative if relative else path
            target = target.resolve()
            if target.is_dir():
                target /= "index.html"
            if not target.is_relative_to(site) or not target.is_file():
                errors.append(f"{path.relative_to(site)}: missing target {link}")
            elif url.fragment and target in pages:
                if unquote(url.fragment) not in pages[target].ids:
                    errors.append(f"{path.relative_to(site)}: missing fragment {link}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    if not (args.site / "index.html").is_file():
        parser.error("Expected a built site with index.html")
    errors = check_links(args.site)
    if errors:
        raise SystemExit("\n".join(errors))
    print("Generated site links, assets, and HTML fragments passed.")


if __name__ == "__main__":
    main()
