"""Recent post memory (anti-repeat) for Papito.

Goal:
- Reduce generic/repeated posts by tracking recent content fingerprints.
- Keep it lightweight (JSON file), safe for Railway runtime.

This is NOT a full analytics system; it's a simple guardrail.
"""

from __future__ import annotations

import json
import os
import re
import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


_WORD_RE = re.compile(r"[a-z0-9']+")


def _normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(_normalize(text)))


def _fingerprint(text: str) -> str:
    canonical = _normalize(text)
    return hashlib.sha256(canonical.encode("utf-8", errors="ignore")).hexdigest()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass
class MemoryItem:
    fingerprint: str
    created_at: str
    kind: str
    preview: str
    token_sample: List[str]


class PostMemory:
    """Stores a rolling window of recent posts to prevent repeats."""

    def __init__(self, file_path: Optional[str] = None, max_items: int = 200):
        self.file_path = file_path or os.getenv("PAPITO_POST_MEMORY_FILE") or os.path.join(
            "data", "post_memory.json"
        )
        self.max_items = max_items
        self._items: List[MemoryItem] = []
        self._load()

    def _load(self) -> None:
        try:
            if not os.path.exists(self.file_path):
                return
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_items = data.get("items", []) if isinstance(data, dict) else []
            for it in raw_items:
                if not isinstance(it, dict):
                    continue
                fp = it.get("fingerprint")
                if not fp:
                    continue
                self._items.append(
                    MemoryItem(
                        fingerprint=fp,
                        created_at=str(it.get("created_at") or ""),
                        kind=str(it.get("kind") or "unknown"),
                        preview=str(it.get("preview") or ""),
                        token_sample=list(it.get("token_sample") or []),
                    )
                )
            self._items = self._items[-self.max_items :]
        except Exception:
            # If the memory file is corrupted, ignore it rather than crashing the agent.
            self._items = []

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            payload = {
                "updated_at": datetime.utcnow().isoformat(),
                "items": [
                    {
                        "fingerprint": i.fingerprint,
                        "created_at": i.created_at,
                        "kind": i.kind,
                        "preview": i.preview,
                        "token_sample": i.token_sample,
                    }
                    for i in self._items
                ],
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            # Best-effort persistence.
            pass

    def is_repeated(self, text: str) -> bool:
        fp = _fingerprint(text)
        return any(i.fingerprint == fp for i in self._items)

    def is_too_similar(self, text: str, threshold: float = 0.85) -> bool:
        """Heuristic similarity check to catch near-duplicates."""
        candidate_tokens = _tokens(text)
        if not candidate_tokens:
            return False

        # Compare to a recent window only for speed.
        for item in reversed(self._items[-30:]):
            item_tokens = set(item.token_sample)
            if not item_tokens:
                continue
            if _jaccard(candidate_tokens, item_tokens) >= threshold:
                return True
        return False

    def record(self, text: str, kind: str) -> None:
        fp = _fingerprint(text)
        token_sample = sorted(list(_tokens(text)))[:80]
        self._items.append(
            MemoryItem(
                fingerprint=fp,
                created_at=datetime.utcnow().isoformat(),
                kind=kind,
                preview=(text or "")[:160],
                token_sample=token_sample,
            )
        )
        self._items = self._items[-self.max_items :]
        self._save()
