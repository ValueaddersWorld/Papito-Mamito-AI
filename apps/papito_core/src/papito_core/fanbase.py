"""Utilities for managing Papito Mamito's fanbase and merch."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from .config import PapitoPaths
from .models import FanProfile, MerchItem
from .utils import write_text


@dataclass
class FanbaseRegistry:
    """Read/write fan profiles and merch catalog data."""

    paths: PapitoPaths
    fan_filename: str = "fanbase.json"
    merch_filename: str = "merch_catalog.json"

    @property
    def fan_path(self) -> Path:
        return self.paths.fanbase / self.fan_filename

    @property
    def merch_path(self) -> Path:
        return self.paths.fanbase / self.merch_filename

    def list_fans(self) -> List[FanProfile]:
        if not self.fan_path.exists():
            return []
        data = json.loads(self.fan_path.read_text(encoding="utf-8"))
        return [FanProfile.model_validate(item) for item in data]

    def add_fan(self, fan: FanProfile) -> None:
        fans = self.list_fans()
        fans.append(fan)
        self._write_json(self.fan_path, [f.model_dump(mode="json") for f in fans])

    def list_merch(self) -> List[MerchItem]:
        if not self.merch_path.exists():
            return []
        data = json.loads(self.merch_path.read_text(encoding="utf-8"))
        return [MerchItem.model_validate(item) for item in data]

    def sync_merch(self, items: Sequence[MerchItem]) -> None:
        self._write_json(self.merch_path, [item.model_dump(mode="json") for item in items])

    @staticmethod
    def _write_json(path: Path, payload: object) -> None:
        write_text(path, json.dumps(payload, indent=2))
