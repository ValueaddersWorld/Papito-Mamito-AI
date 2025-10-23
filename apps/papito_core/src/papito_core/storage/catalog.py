"""Release catalog persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from ..config import PapitoPaths
from ..models import AudioAsset, ReleasePlan, ReleaseTrack
from ..utils import slugify


@dataclass
class ReleaseCatalog:
    """Persist release plans as JSON documents."""

    paths: PapitoPaths

    def _catalog_path(self, release_title: str) -> Path:
        slug = slugify(release_title)
        return self.paths.release_catalog / f"{slug}.json"

    def save(self, plan: ReleasePlan) -> Path:
        """Write the release plan to disk."""

        path = self._catalog_path(plan.release_title)
        payload = plan.model_dump(mode="json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def list(self) -> List[Path]:
        """List catalogued releases."""

        if not self.paths.release_catalog.exists():
            return []
        return sorted(self.paths.release_catalog.glob("*.json"))

    def load_all(self) -> List[ReleasePlan]:
        """Load all release plans from disk."""

        plans: List[ReleasePlan] = []
        for path in self.list():
            data = json.loads(path.read_text(encoding="utf-8"))
            plans.append(ReleasePlan.model_validate(data))
        return plans

    def sync(self, plans: Iterable[ReleasePlan]) -> List[Path]:
        """Replace catalog entries with the provided plans."""

        saved_paths: List[Path] = []
        for plan in plans:
            saved_paths.append(self.save(plan))
        return saved_paths

    def update_track_audio(self, track: ReleaseTrack) -> List[Path]:
        """Update existing catalog entries with new audio metadata for the given track."""

        updated_paths: List[Path] = []
        audio_asset = track.audio
        if audio_asset is None:
            return updated_paths

        for path in self.list():
            data = json.loads(path.read_text(encoding="utf-8"))
            plan = ReleasePlan.model_validate(data)
            changed = False
            new_tracks: List[ReleaseTrack] = []
            for existing_track in plan.tracks:
                if existing_track.title == track.title:
                    if existing_track.audio != audio_asset:
                        existing_track = existing_track.model_copy(
                            update={"audio": AudioAsset.model_validate(audio_asset.model_dump())}
                        )
                        changed = True
                new_tracks.append(existing_track)

            if changed:
                plan = plan.model_copy(update={"tracks": new_tracks})
                self.save(plan)
                updated_paths.append(path)
        return updated_paths
