"""Hosted music library.

This module enables hosting audio directly on the Papito platform.

Design goals:
- Minimal storage: writes to local filesystem (Railway volume recommended).
- Minimal metadata: JSON file in content/releases/hosted/library.json.
- Fan-facing streaming via FastAPI StaticFiles mount.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..utils import slugify


SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".wav", ".flac", ".ogg"}


@dataclass
class HostedTrack:
    """Metadata for an uploaded/hosted track."""

    id: str
    title: str
    filename: str
    content_type: str
    bytes: int
    uploaded_at: str

    release_title: Optional[str] = None
    track_number: Optional[int] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def library_path(hosted_dir: Path) -> Path:
    return hosted_dir / "library.json"


def load_library(hosted_dir: Path) -> List[HostedTrack]:
    path = library_path(hosted_dir)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    tracks: List[HostedTrack] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                tracks.append(HostedTrack(**item))
    return tracks


def save_library(hosted_dir: Path, tracks: List[HostedTrack]) -> None:
    hosted_dir.mkdir(parents=True, exist_ok=True)
    path = library_path(hosted_dir)
    payload = [t.to_dict() for t in tracks]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def safe_audio_filename(title: str, ext: str) -> str:
    return f"{slugify(title)}{ext.lower()}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
