import pytest

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = PROJECT_ROOT / "apps" / "papito_core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

import json

from papito_core.settings import get_settings


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """Ensure settings cache and env vars are reset between tests."""

    get_settings.cache_clear()
    for var in ("SUNO_API_KEY", "SUNO_BASE_URL", "SUNO_MODEL", "SUNO_TIMEOUT"):
        monkeypatch.delenv(var, raising=False)
    yield
    get_settings.cache_clear()


@pytest.fixture
def cli_paths(tmp_path, monkeypatch):
    """Redirect CLI paths to a temporary directory for filesystem isolation."""

    from papito_core import config
    from papito_core.cli import catalog, paths

    root = tmp_path
    paths.root = root
    paths.docs = root / "docs"
    paths.content = root / "content"
    paths.blogs = paths.content / "blogs"
    paths.releases = paths.content / "releases"
    paths.release_catalog = paths.releases / "catalog"
    paths.release_tracks = paths.releases / "tracks"
    paths.analytics_reports = paths.content / "analytics"
    paths.schedule_reports = paths.content / "schedules"
    paths.ensure()

    catalog.paths = paths
    config.DEFAULT_PATHS = paths
    return paths


@pytest.fixture
def sample_release_plan(tmp_path):
    """Create a sample release plan JSON file."""

    from papito_core.models import ReleasePlan, ReleaseTrack

    plan = ReleasePlan(
        release_title="Test Vibes",
        release_date="2025-12-01",
        release_type="single",
        tracks=[
            ReleaseTrack(
                title="Test Groove",
                mood="uplifting",
                tempo_bpm=110,
                key="C minor",
                theme="joy",
                story_hook="The journey from doubt to glow.",
                instrumentation=["drums", "bass"],
                hook_lyrics=["Glow up together", "Value over vanity"],
            )
        ],
        distribution_targets=["spotify", "apple music"],
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan.model_dump(mode="json")), encoding="utf-8")
    return plan_path
