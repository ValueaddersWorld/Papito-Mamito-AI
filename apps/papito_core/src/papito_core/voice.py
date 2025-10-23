"""Papito Mamito voice helpers."""

from __future__ import annotations

from .models import BrandVoice, DEFAULT_VOICE


def describe_voice(voice: BrandVoice = DEFAULT_VOICE) -> str:
    """Return a human-readable summary of the Papito voice."""

    tone = ", ".join(voice.tone_tags)
    phrases = "\n".join(f"- {phrase}" for phrase in voice.phrases)
    return (
        f"Persona: {voice.persona}\n"
        f"Mission: {voice.mission}\n"
        f"Tone: {tone}\n"
        f"Signature phrases:\n{phrases}"
    )
