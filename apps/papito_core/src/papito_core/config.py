"""Configuration helpers for Papito Mamito."""

from __future__ import annotations

from pathlib import Path


class PapitoPaths:
    """Centralised lookup for important repository paths."""

    def __init__(self, root: Path | None = None) -> None:
        # Resolve repository root robustly (works for local dev and Docker images).
        # File: <repo>/apps/papito_core/src/papito_core/config.py
        # Repo root is typically parents[4], but we also scan upwards for a folder
        # that looks like the project root.
        if root is None:
            candidate = None
            here = Path(__file__).resolve()
            for parent in here.parents:
                if (parent / "content").exists() and (parent / "apps").exists():
                    candidate = parent
                    break
                if (parent / "README.md").exists() and (parent / "apps").exists():
                    candidate = parent
                    break
            root = candidate or here.parents[4]

        self.root = root
        self.docs = self.root / "docs"
        self.content = self.root / "content"
        self.blogs = self.content / "blogs"
        self.releases = self.content / "releases"
        self.release_catalog = self.releases / "catalog"
        self.release_tracks = self.releases / "tracks"
        self.release_hosted = self.releases / "hosted"
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
            self.release_hosted,
            self.analytics_reports,
            self.schedule_reports,
            self.fanbase,
            self.distribution_packages,
        ):
            path.mkdir(parents=True, exist_ok=True)


DEFAULT_PATHS = PapitoPaths()
