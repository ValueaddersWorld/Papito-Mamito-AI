"""Release orchestration workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Sequence

from ..constants import STREAMING_PLATFORMS
from ..models import ReleasePlan, ReleaseTrack


@dataclass
class ReleaseWorkflow:
    """Create structured release plans for albums / singles / EPs."""

    distribution_defaults: Sequence[str] = tuple(STREAMING_PLATFORMS)

    def build_plan(
        self,
        *,
        release_title: str,
        release_date: date,
        release_type: str,
        tracks: Sequence[ReleaseTrack],
        promotional_beats: Sequence[str] | None = None,
        gratitude_rollcall: Sequence[str] | None = None,
    ) -> ReleasePlan:
        """Compose a release plan from track metadata."""

        if release_type not in {"album", "single", "ep"}:
            raise ValueError("release_type must be one of: album, single, ep")

        track_list: List[ReleaseTrack] = list(tracks)
        if not track_list:
            raise ValueError("At least one track is required for a release plan.")

        promotional = list(promotional_beats or [])
        if not promotional:
            promotional.append("Announce gratitude livestream with fan rollcall.")
            promotional.append("Release behind-the-scenes rehearsal footage.")

        rollcall = list(gratitude_rollcall or [])
        if not rollcall:
            rollcall.append("Value Adders Empire global family")

        return ReleasePlan(
            release_title=release_title,
            release_date=release_date,
            release_type=release_type,
            tracks=track_list,
            promotional_beats=promotional,
            gratitude_rollcall=rollcall,
            distribution_targets=list(self.distribution_defaults),
        )
