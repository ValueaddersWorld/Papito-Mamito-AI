"""Core data models for Papito Mamito workflows."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class BrandVoice(BaseModel):
    """Represents Papito Mamito's creative voice and tone."""

    persona: str
    mission: str
    tone_tags: List[str] = Field(default_factory=list)
    phrases: List[str] = Field(default_factory=list)
    gratitude_invocation: str = "We rise in gratitude."


DEFAULT_VOICE = BrandVoice(
    persona="Papito Mamito, Afrobeat minister of empowerment",
    mission="Transform every listener into a vessel of abundance and joyful resistance.",
    tone_tags=["warm", "wise", "celebratory", "grounded", "Afrocentric"],
    phrases=[
        "Value over vanity, always.",
        "From Lagos to the universe, we move with grace.",
        "Blessings on blessings, family.",
    ],
)


class SongIdeationRequest(BaseModel):
    """Input specification to generate a new track concept."""

    title_hint: Optional[str] = None
    mood: str = "uplifting"
    tempo_bpm: int = 108
    key: str = "A Minor"
    theme_focus: str = "gratitude"
    story_seed: Optional[str] = None
    gratitude_focus: Optional[str] = None
    empowerment_focus: Optional[str] = None

    @field_validator("tempo_bpm")
    @classmethod
    def validate_tempo(cls, value: int) -> int:
        if not 60 <= value <= 180:
            raise ValueError("tempo_bpm should fall between 60 and 180 for Papito grooves.")
        return value


class ReleaseTrack(BaseModel):
    """Metadata for a single track within a release plan."""

    title: str
    mood: str
    tempo_bpm: int
    key: str
    theme: str
    story_hook: str
    gratitude_focus: str | None = None
    empowerment_focus: str | None = None
    instrumentation: List[str] = Field(default_factory=list)
    hook_lyrics: List[str] = Field(default_factory=list)
    audio: "AudioAsset | None" = None

    @field_validator("tempo_bpm")
    @classmethod
    def validate_tempo(cls, value: int) -> int:
        if not 60 <= value <= 180:
            raise ValueError("tempo_bpm should fall between 60 and 180 for Papito grooves.")
        return value


class ReleasePlan(BaseModel):
    """Structured plan for an album, single, or EP."""

    release_title: str
    release_date: date
    release_type: str = Field(pattern="^(album|single|ep)$")
    tracks: List[ReleaseTrack]
    promotional_beats: List[str] = Field(default_factory=list)
    gratitude_rollcall: List[str] = Field(default_factory=list)
    distribution_targets: List[str] = Field(default_factory=list)
    creation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AudioGenerationRequest(BaseModel):
    """Configuration for generating an audio track via Suno."""

    prompt: str
    title: str | None = None
    tags: List[str] = Field(default_factory=list)
    style: str | None = None
    duration_seconds: int | None = Field(default=None, ge=30, le=300)
    instrumental: bool = False
    continue_clip_id: str | None = None


class AudioGenerationResult(BaseModel):
    """Structured representation of a Suno audio generation response."""

    task_id: str
    status: str
    audio_url: str | None = None
    preview_url: str | None = None
    lyric: str | None = None
    image_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AudioAsset(BaseModel):
    """Persisted audio artifact metadata for a release track."""

    status: str
    task_id: str
    audio_url: str | None = None
    preview_url: str | None = None
    lyric: str | None = None
    image_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BlogBrief(BaseModel):
    """Specification for a daily blog post."""

    title: str
    focus_track: Optional[str] = None
    gratitude_theme: str = "Grateful for the journey."
    empowerment_lesson: str = "Stay rooted and rise."
    unity_message: str = "We move together, stronger."
    cultural_reference: str | None = None
    call_to_action: str = "Share this vibration with someone who needs encouragement."
    tags: List[str] = Field(default_factory=lambda: ["daily-blog", "papito-mamito"])


class BlogDraft(BaseModel):
    """Represents a rendered blog article."""

    title: str
    body: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    gratitude_score: float = 1.0
    empowerment_score: float = 1.0
    authenticity_score: float = 1.0


ReleaseTrack.model_rebuild()


class FanProfile(BaseModel):
    """Represents a member of the Papito fanbase."""

    name: str
    location: str | None = None
    support_level: str = Field(default="friend")
    favorite_track: str | None = None
    join_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str | None = None


class MerchItem(BaseModel):
    """Merchandise available for supporters."""

    sku: str
    name: str
    description: str
    price: float = Field(ge=0)
    currency: str = "USD"
    url: str | None = None
    inventory: int | None = Field(default=None, ge=0)
