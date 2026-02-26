# tools/make_pypi_readme.py
from __future__ import annotations

import re
from pathlib import Path

README_IN = Path("README.md")
CHANGELOG = Path("CHANGELOG.md")
README_OUT = Path("README_PYPI.md")


def latest_section(text: str) -> str:
    """Cuts latest version from Keep a Changelog."""
    matches = list(re.finditer(r"(?m)^## \[", text))
    if not matches:
        return ""
    # Skip [Unreleased]
    release_matches = [
        m
        for m in matches
        if not text[m.start() : m.start() + 20].startswith("## [Unreleased]")
    ]
    if not release_matches:
        return ""
    start = release_matches[0].start()
    end = release_matches[1].start() if len(release_matches) > 1 else len(text)
    return text[start:end].strip()


readme = README_IN.read_text(encoding="utf-8")

changelog_block = ""
if CHANGELOG.exists():
    changelog_text = CHANGELOG.read_text(encoding="utf-8")
    latest = latest_section(changelog_text)
    if latest:
        changelog_block = f"## What's new\n\n{latest}\n\n---\n\n"

README_OUT.write_text(changelog_block + readme, encoding="utf-8")
print(f"README_PYPI.md written ({len(changelog_block) + len(readme)} chars)")
