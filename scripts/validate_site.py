#!/usr/bin/env python3
"""Validate DinoRPG Maintenance's static pages before GitHub Pages deployment.

Standard library only: no Node.js, packages or external network connections.
Run from the repository root: python3 scripts/validate_site.py .
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


PAGES = {
    "index.html": "fr",
    "credits.html": "fr",
    "en/index.html": "en",
    "en/credits.html": "en",
    "es/index.html": "es",
    "es/credits.html": "es",
    "de/index.html": "de",
    "de/credits.html": "de",
}
ASSETS = [
    "style.css",
    "LICENSE",
    "scripts/language.js",
    "assets/background_beta.webp",
    "assets/sky_footer.webp",
    "assets/4dinoz.webp",
    "assets/drpg.png",
]


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []
        self.document_lang = ""
        self.languages: set[str] = set()

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "html":
            self.document_lang = data.get("lang", "")
        if tag == "a" and data.get("hreflang"):
            self.languages.add(data["hreflang"])

        for attr in ("href", "src"):
            value = data.get(attr)
            if value:
                self.refs.append((tag, value))


def local_target(root: Path, source: Path, ref: str) -> Path | None:
    parsed = urlsplit(ref)
    if parsed.scheme or parsed.netloc or ref.startswith("#"):
        return None
    # All site links are relative; root-relative URLs are intentionally unsupported,
    # since GitHub Pages may be visited before the custom domain is configured.
    if parsed.path.startswith("/"):
        raise ValueError(f"Absolute path {ref!r} is not portable to the GitHub Pages project URL")
    path = unquote(parsed.path)
    if not path:
        return source
    target = (source.parent / path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes the site root: {ref!r}") from exc
    if target.is_dir() or path.endswith("/"):
        target = target / "index.html"
    return target


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()

    for rel in [*PAGES, *ASSETS]:
        file = root / rel
        if not file.is_file() or file.stat().st_size == 0:
            errors.append(f"Missing or empty: {rel}")

    for rel, lang in PAGES.items():
        page = root / rel
        if not page.is_file():
            continue
        parser = ResourceParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parser.close()
        if parser.document_lang != lang:
            errors.append(f"{rel}: expected html lang={lang!r}, got {parser.document_lang!r}")
        if parser.languages != {"fr", "en", "es", "de"}:
            errors.append(f"{rel}: missing language links ({sorted(parser.languages)})")

        for tag, href in parser.refs:
            try:
                target = local_target(root, page, href)
            except ValueError as exc:
                errors.append(f"{rel}: {exc}")
                continue
            if target is not None and not target.is_file():
                errors.append(f"{rel}: broken local {tag} reference {href!r}")

    css = root / "style.css"
    if css.is_file():
        source = css.read_text(encoding="utf-8")
        for ref in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)['\"]?\s*\)", source):
            try:
                target = local_target(root, css, ref)
            except ValueError as exc:
                errors.append(f"style.css: {exc}")
                continue
            if target is not None and not target.is_file():
                errors.append(f"style.css: broken url({ref})")

    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors = validate(root)
    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print("  -", error)
        return 1
    print(f"✅ Validated {len(PAGES)} pages, {len(ASSETS)} essential resources, and internal links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
