"""Generator factory utilities."""

from __future__ import annotations

import warnings

from typing import Optional

from .engines import (
    SunoAudioEngine,
    SunoClient,
    SunoError,
    SunoTextGenerator,
    TextGenerator,
    StubTextGenerator,
)
from .settings import get_settings


def create_text_generator() -> TextGenerator:
    """Return the preferred text generator based on environment configuration."""

    settings = get_settings()
    if settings.suno_api_key:
        try:
            client = SunoClient()
            return SunoTextGenerator(client=client)
        except SunoError as exc:  # pragma: no cover - defensive fallback
            warnings.warn(
                f"Falling back to stub generator because Suno configuration failed: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            warnings.warn(
                f"Falling back to stub generator because Suno configuration failed: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )
    return StubTextGenerator()


def create_audio_engine() -> Optional[SunoAudioEngine]:
    """Return an audio engine when credentials are configured."""

    settings = get_settings()
    if not settings.suno_api_key:
        return None
    try:
        client = SunoClient()
        return SunoAudioEngine(client=client)
    except SunoError as exc:  # pragma: no cover - defensive fallback
        warnings.warn(
            f"Unable to initialise Suno audio engine: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return None
    except Exception as exc:  # pragma: no cover - defensive fallback
        warnings.warn(
            f"Unable to initialise Suno audio engine: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return None
