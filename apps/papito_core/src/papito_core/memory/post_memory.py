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
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


_WORD_RE = re.compile(r"[a-z0-9']+")
_COMMON_TOKENS = {
    "about", "after", "again", "album", "also", "always", "because", "being",
    "could", "every", "first", "flourish", "flourishing", "from", "genuine",
    "have", "into", "just", "make", "music", "only", "papito", "post",
    "purpose", "really", "should", "that", "their", "there", "these", "this",
    "through", "today", "value", "what", "when", "where", "which", "while",
    "with", "world", "would", "your",
}


def _normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(_normalize(text)))


def _useful_tokens(text: str) -> set[str]:
    return {
        token
        for token in _tokens(text)
        if len(token) > 3 and token not in _COMMON_TOKENS
    }


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
        if self.is_repeated(text):
            return
        fp = _fingerprint(text)
        token_sample = sorted(list(_useful_tokens(text)))[:80]
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

    def recent_previews(self, limit: int = 8, kind_prefix: Optional[str] = None) -> List[str]:
        """Return recent post previews for prompt avoidance."""
        items = self._items
        if kind_prefix:
            items = [item for item in items if item.kind.startswith(kind_prefix)]
        return [item.preview for item in items[-limit:] if item.preview]

    def recent_kinds(self, limit: int = 8, kind_prefix: Optional[str] = None) -> List[str]:
        """Return recent content kinds for persistent portfolio decisions."""
        items = self._items
        if kind_prefix:
            items = [item for item in items if item.kind.startswith(kind_prefix)]
        return [item.kind for item in items[-limit:] if item.kind]

    def overused_terms(self, limit: int = 10, recent: int = 80) -> List[str]:
        """Return recurring terms from recent memory to steer generation away."""
        counter: Counter[str] = Counter()
        for item in self._items[-recent:]:
            counter.update(item.token_sample)
        return [term for term, _ in counter.most_common(limit)]

    def guidance(self, limit: int = 8) -> Dict[str, Any]:
        """Build compact anti-stagnation context for content generation."""
        return {
            "recent_posts": self.recent_previews(limit=limit),
            "avoid_terms": self.overused_terms(limit=10),
            "memory_size": len(self._items),
        }
