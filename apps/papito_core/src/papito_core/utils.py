"""Utility helpers."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(value: str) -> str:
    """Create a filesystem-safe slug."""

    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    return value.strip("-")


def timestamped_filename(title: str, suffix: str = ".md") -> str:
    """Return a timestamped filename using a slug derived from the title."""

    slug = slugify(title)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{slug}{suffix}"


def write_text(path: Path, content: str) -> None:
    """Write plain text content to disk, creating the parent directory if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
