"""Song ideation prompt builder."""

from __future__ import annotations

from textwrap import dedent

from ..constants import MISSION_STATEMENT, PAPITO_VALUES
from ..models import BrandVoice, DEFAULT_VOICE, ReleaseTrack, SongIdeationRequest


def build_song_prompt(request: SongIdeationRequest, voice: BrandVoice = DEFAULT_VOICE) -> str:
    """Return a prompt instructing an LLM to craft a track concept."""

    values = ", ".join(PAPITO_VALUES)
    tone = ", ".join(voice.tone_tags)
    gratitude = request.gratitude_focus or "Honor the blessings in every breath."
    empowerment = request.empowerment_focus or "Encourage listeners to own their greatness."
    story_seed = request.story_seed or "Share Papito's journey from humble beginnings to global empowerment."
    title_hint = request.title_hint or "Invent a title that captures the theme."

    return dedent(
        f"""
        You are {voice.persona}. Mission: {voice.mission}
        Global mission statement: {MISSION_STATEMENT}
        Core values: {values}
        Tone palette: {tone}

        Design an Afrobeat/Highlife/Afrofusion track concept.

        Title hint: {title_hint}
        Mood: {request.mood}
        Tempo (BPM): {request.tempo_bpm}
        Musical key: {request.key}
        Theme focus: {request.theme_focus}
        Story seed: {story_seed}
        Gratitude focus: {gratitude}
        Empowerment focus: {empowerment}

        Output JSON with fields: title, mood, tempo_bpm, key, theme, story_hook,
        gratitude_focus, empowerment_focus, instrumentation (list), hook_lyrics (list of 2-4 lines).

        Ensure the concept is performance-ready and aligned with Papito's mission.
        """
    ).strip()


def build_audio_prompt(track: ReleaseTrack, voice: BrandVoice = DEFAULT_VOICE) -> str:
    """Construct a rich prompt for Suno audio generation."""

    values = ", ".join(PAPITO_VALUES)
    tone = ", ".join(voice.tone_tags)
    hook_preview = "; ".join(track.hook_lyrics) if track.hook_lyrics else "Craft an unforgettable hook."

    return dedent(
        f"""
        Persona: {voice.persona}
        Mission: {voice.mission}
        Core values: {values}
        Tone palette: {tone}

        Compose an Afrobeat / Highlife / Afrofusion track.
        Title: {track.title}
        Mood: {track.mood}
        Tempo: {track.tempo_bpm} BPM
        Key: {track.key}
        Theme: {track.theme}
        Story hook: {track.story_hook}
        Gratitude focus: {track.gratitude_focus or "Celebrate community resilience and blessings."}
        Empowerment focus: {track.empowerment_focus or "Inspire listeners to embrace their power."}
        Instrumentation palette: {", ".join(track.instrumentation) or "talking drum, rhythm guitar, horns, synth pads"}

        Hook inspiration: {hook_preview}

        Requirements:
        - Afrocentric percussion and groove-forward bass.
        - Vibrant call-and-response chorus with layered vocals.
        - Export lyrics aligned with Papito's gratitude-first ethos.
        - Blend ancestral textures with modern production punch.
        """
    ).strip()
