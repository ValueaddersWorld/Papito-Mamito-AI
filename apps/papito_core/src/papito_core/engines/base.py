"""Protocols for creative engines."""

from __future__ import annotations

from typing import Protocol


class TextGenerator(Protocol):
    """Protocol describing text generation engines."""

    def __call__(self, prompt: str, *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generate text from a prompt."""

