"""Streaming analytics ingestion helpers."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence

from pydantic import BaseModel, Field, ValidationError


class PlatformSnapshot(BaseModel):
    """Represents a single streaming analytics snapshot for a platform."""

    platform: str
    streams: int = 0
    listeners: int = 0
    saves: int = 0
    followers: int | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalyticsSummary(BaseModel):
    """Aggregated streaming analytics report."""

    timeframe_start: datetime
    timeframe_end: datetime
    total_streams: int
    total_listeners: int
    total_saves: int
    platform_breakdown: dict[str, dict[str, int]]
    top_platforms: List[str]


@dataclass
class StreamingAnalyticsService:
    """Aggregate analytics across multiple platform snapshots."""

    def aggregate(self, snapshots: Sequence[PlatformSnapshot]) -> AnalyticsSummary:
        if not snapshots:
            raise ValueError("At least one snapshot is required.")

        streams_total = 0
        listeners_total = 0
        saves_total = 0
        platform_rollup: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for snapshot in snapshots:
            platform = snapshot.platform.lower()
            platform_rollup[platform]["streams"] += snapshot.streams
            platform_rollup[platform]["listeners"] += snapshot.listeners
            platform_rollup[platform]["saves"] += snapshot.saves
            if snapshot.followers is not None:
                platform_rollup[platform]["followers"] += snapshot.followers

            streams_total += snapshot.streams
            listeners_total += snapshot.listeners
            saves_total += snapshot.saves

        sorted_platforms = sorted(
            platform_rollup.items(),
            key=lambda item: item[1]["streams"],
            reverse=True,
        )
        top_platforms = [name for name, _ in sorted_platforms[:3]]

        timeframe_start = min(snapshot.timestamp for snapshot in snapshots)
        timeframe_end = max(snapshot.timestamp for snapshot in snapshots)

        return AnalyticsSummary(
            timeframe_start=timeframe_start,
            timeframe_end=timeframe_end,
            total_streams=streams_total,
            total_listeners=listeners_total,
            total_saves=saves_total,
            platform_breakdown={k: dict(v) for k, v in platform_rollup.items()},
            top_platforms=top_platforms,
        )

    def load(self, payload: Iterable[dict[str, object]]) -> AnalyticsSummary:
        """Load snapshots from an iterable of dicts."""

        snapshots: List[PlatformSnapshot] = []
        for row in payload:
            try:
                snapshots.append(PlatformSnapshot.model_validate(row))
            except ValidationError as exc:
                raise ValueError(f"Invalid snapshot payload: {row}") from exc
        return self.aggregate(snapshots)

    def from_path(self, path: Path) -> AnalyticsSummary:
        """Load analytics from a JSON file."""

        suffix = path.suffix.lower()
        if suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._from_json_payload(data)
        if suffix == ".csv":
            return self._from_csv(path)
        raise ValueError(f"Unsupported analytics file type: {path}")

    def _from_json_payload(self, data: object) -> AnalyticsSummary:
        if isinstance(data, dict):
            values = data.get("snapshots")
            if isinstance(values, list):
                data = values
            else:
                raise ValueError("Expected 'snapshots' array in analytics JSON.")
        if not isinstance(data, list):
            raise ValueError("Analytics JSON must contain a list of snapshots.")
        return self.load(data)

    def _from_csv(self, path: Path) -> AnalyticsSummary:
        """Load analytics from a CSV export."""

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = [self._normalise_csv_row(row) for row in reader]
        return self.load(rows)

    @staticmethod
    def _normalise_csv_row(row: dict[str, str]) -> dict[str, object]:
        """Normalise CSV fields into the expected schema."""

        def parse_int(value: str | None) -> int:
            if value is None:
                return 0
            value = value.strip()
            if not value:
                return 0
            value = value.replace(",", "")
            try:
                return int(float(value))
            except ValueError:
                return 0

        return {
            "platform": row.get("platform") or row.get("Platform") or "unknown",
            "streams": parse_int(row.get("streams") or row.get("Streams")),
            "listeners": parse_int(row.get("listeners") or row.get("Listeners")),
            "saves": parse_int(row.get("saves") or row.get("Saves")),
            "followers": parse_int(row.get("followers") or row.get("Followers")),
            "timestamp": row.get("timestamp") or row.get("date") or row.get("Date"),
        }
