"""Configuration helpers for Papito Mamito."""

from __future__ import annotations

from pathlib import Path


class PapitoPaths:
    """Centralised lookup for important repository paths."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[3]
        self.docs = self.root / "docs"
        self.content = self.root / "content"
        self.blogs = self.content / "blogs"
        self.releases = self.content / "releases"
        self.release_catalog = self.releases / "catalog"
        self.release_tracks = self.releases / "tracks"
        self.analytics_reports = self.content / "analytics"
        self.schedule_reports = self.content / "schedules"
        self.fanbase = self.content / "fans"
        self.distribution_packages = self.releases / "distribution"

    def ensure(self) -> None:
        """Create required directories if they do not already exist."""
        for path in (
            self.docs,
            self.content,
            self.blogs,
            self.releases,
            self.release_catalog,
            self.release_tracks,
            self.analytics_reports,
            self.schedule_reports,
            self.fanbase,
            self.distribution_packages,
        ):
            path.mkdir(parents=True, exist_ok=True)


DEFAULT_PATHS = PapitoPaths()
