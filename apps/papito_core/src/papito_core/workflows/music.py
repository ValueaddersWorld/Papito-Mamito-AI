"""Music workflow for ideation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..engines import SunoAudioEngine, TextGenerator
from ..generation import create_audio_engine, create_text_generator
from ..models import (
    AudioAsset,
    AudioGenerationRequest,
    AudioGenerationResult,
    BrandVoice,
    DEFAULT_VOICE,
    ReleaseTrack,
    SongIdeationRequest,
)
from ..prompts import build_audio_prompt, build_song_prompt


@dataclass
class MusicWorkflow:
    """Create track concepts aligned with Papito's ethos."""

    generator: TextGenerator = field(default_factory=create_text_generator)
    voice: BrandVoice = field(default_factory=lambda: DEFAULT_VOICE.model_copy(deep=True))
    _audio_engine: Optional[SunoAudioEngine] = field(default=None, init=False, repr=False)

    def ideate_track(self, request: SongIdeationRequest) -> ReleaseTrack:
        """Generate a track concept and map it to a ReleaseTrack model."""

        prompt = build_song_prompt(request, voice=self.voice)
        raw_text = self.generator(prompt)
        data = self._parse_response(raw_text)
        return ReleaseTrack(**data)

    def compose(
        self,
        request: SongIdeationRequest,
        *,
        generate_audio: bool = False,
        audio_tags: Optional[Sequence[str]] = None,
        audio_duration_seconds: Optional[int] = None,
        instrumental: bool = False,
    ) -> Tuple[ReleaseTrack, Optional[AudioGenerationResult]]:
        """Produce a track concept and optionally trigger audio generation."""

        track = self.ideate_track(request)
        audio_result: Optional[AudioGenerationResult] = None

        if generate_audio:
            engine = self._ensure_audio_engine()
            if engine is None:
                raise RuntimeError(
                    "Suno audio engine is unavailable. Set SUNO_API_KEY to enable audio generation."
                )

            prompt = build_audio_prompt(track, voice=self.voice)
            tags: List[str] = list(audio_tags or [])
            if track.theme:
                tags.append(track.theme)
            tags.append(track.mood)

            audio_request = AudioGenerationRequest(
                prompt=prompt,
                title=track.title,
                tags=list(dict.fromkeys(tag for tag in tags if tag)),  # Preserve order, remove duplicates
                style=request.theme_focus,
                duration_seconds=audio_duration_seconds,
                instrumental=instrumental,
            )

            audio_result = engine.generate(audio_request)
            track = self.enrich_track_with_audio(track, audio_result)

        return track, audio_result

    @staticmethod
    def _parse_response(response: str) -> Dict[str, Any]:
        """Extract JSON payload from an LLM response."""

        # Attempt to locate JSON in the response; fall back to deterministic scaffold.
        try:
            start = response.index("{")
            json_payload = response[start:]
            data = json.loads(json_payload)
        except (ValueError, json.JSONDecodeError):
            data = {
                "title": "Rise with Abundance",
                "mood": "triumphant",
                "tempo_bpm": 108,
                "key": "A minor",
                "theme": "gratitude meets bold ambition",
                "story_hook": "Papito salutes the people who dared to dream with him.",
                "gratitude_focus": "Thankful for collective resilience.",
                "empowerment_focus": "Remind listeners they carry ancestral power.",
                "instrumentation": ["talking drum", "rhythm guitar", "horns", "synth pads"],
                "hook_lyrics": [
                    "We rise, we rise, we lift the blessing higher",
                    "Value over vanity, spirit on fire",
                ],
            }
        return data

    def _ensure_audio_engine(self) -> Optional[SunoAudioEngine]:
        if self._audio_engine is None:
            self._audio_engine = create_audio_engine()
        return self._audio_engine

    def get_audio_engine(self) -> Optional[SunoAudioEngine]:
        """Return the underlying audio engine, if initialised."""

        return self._ensure_audio_engine()

    def enrich_track_with_audio(
        self, track: ReleaseTrack, audio_result: Optional[AudioGenerationResult]
    ) -> ReleaseTrack:
        """Attach audio metadata to a release track."""

        if audio_result is None:
            return track

        audio_asset = AudioAsset(
            status=audio_result.status,
            task_id=audio_result.task_id,
            audio_url=audio_result.audio_url,
            preview_url=audio_result.preview_url,
            lyric=audio_result.lyric,
            image_url=audio_result.image_url,
            metadata=audio_result.metadata,
        )

        return track.model_copy(update={"audio": audio_asset})
