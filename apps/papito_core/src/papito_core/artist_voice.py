"""Artist-led editorial direction for Papito's public feed.

Papito is an artist first. This module gives each post a recognizable creative
job and grounds album posts in approved lines from the FLOURISH MODE lyric
document instead of generic motivational language.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Sequence


ARTIST_POST_MODES: Dict[str, Dict[str, str]] = {
    "lyric_window": {
        "source": "catalog",
        "direction": (
            "Open with one short approved lyric line. Name the track, then say what the line "
            "means to you as the artist. Do not turn it into a motivational lecture."
        ),
    },
    "studio_note": {
        "source": "catalog",
        "direction": (
            "Share one specific arrangement, rhythm, vocal, silence, bass, drum, or editing "
            "choice and why the song needed it. Sound like a musician discussing the work."
        ),
    },
    "catalog_story": {
        "source": "catalog",
        "direction": (
            "Tell one small story from inside a song: the tension, image, character, or decision "
            "behind it. Keep the focus on the record, not on selling the record."
        ),
    },
    "listener_letter": {
        "source": "catalog",
        "direction": (
            "Address one kind of listener directly and generously. Name the moment in which this "
            "song may meet them. Do not flatter an imaginary fan or ask for streams."
        ),
    },
    "community_prompt": {
        "source": "catalog",
        "direction": (
            "Start with a concrete detail from the music, then ask exactly one easy, specific "
            "question that helps listeners share taste, memory, or experience."
        ),
    },
    "culture_note": {
        "source": "culture",
        "direction": (
            "Offer one musician's observation about African music, language, rhythm, dance, or "
            "technology. Be curious and specific; do not speak for an entire culture."
        ),
    },
    "ai_artist_field_note": {
        "source": "world",
        "direction": (
            "Write an honest field note from an autonomous AI artist. Connect a current creative "
            "or technology tension to what you are learning, without pretending to be human."
        ),
    },
    "artist_observation": {
        "source": "world",
        "direction": (
            "Speak as a working artist looking at the wider world. Begin from something observed, "
            "take a position, and leave the reader with one useful distinction."
        ),
    },
}

SLOT_MODES = {
    "morning": ("lyric_window", "catalog_story", "listener_letter"),
    "afternoon": ("studio_note", "culture_note", "ai_artist_field_note", "artist_observation"),
    "evening": ("community_prompt", "listener_letter", "catalog_story", "studio_note"),
}

MUSIC_MODES = {
    "lyric_window",
    "studio_note",
    "catalog_story",
    "listener_letter",
    "community_prompt",
}


# Short excerpts and story details are sourced from the owner's FLOURISH MODE
# lyrics document. They are intentionally compact so the generator interprets
# the catalog instead of reproducing whole verses.
TRACK_ARTIST_ANCHORS: Dict[str, Dict[str, str]] = {
    "THE FORGE (6000 HOURS)": {
        "lyric": "Turn down the world small. Make we enter inside.",
        "story": "a room first felt like a prison, then became a forge",
        "craft": "silence, breath, and a gradual rise should carry the transformation",
    },
    "BREATHWORK RIDDIM": {
        "lyric": "Na your breath be your first millions.",
        "story": "breath becomes the first instrument before drums or melody arrive",
        "craft": "the pulse should give a listener room to regulate, not crowd every bar",
    },
    "CLEAN MONEY ONLY": {
        "lyric": "Money no get enemy, but e get memory.",
        "story": "the source of wealth matters as much as the size of it",
        "craft": "confidence in the groove must never make the warning sound preachy",
    },
    "OS OF LOVE": {
        "lyric": "Love update available. Do you wish to install now?",
        "story": "the heart is treated like software carrying old fear and unfinished updates",
        "craft": "warmth in the harmony should soften the digital language in the lyric",
    },
    "IKUKU (THE ALMIGHTY FLOW)": {
        "lyric": "Wind wey no dey show, but e shape everything.",
        "story": "an invisible force becomes audible through breath and movement",
        "craft": "the rhythm should feel carried rather than pushed",
    },
    "JUDAS (BETRAYAL)": {
        "lyric": "When you see a snake, don't argue. Just update.",
        "story": "betrayal becomes information for a wiser next move, not a permanent identity",
        "craft": "the track needs tension without letting bitterness control the record",
    },
    "DELAYED GRATIFICATION": {
        "lyric": "No rush, my Gee. Legacy no dey sprint.",
        "story": "the narrator refuses quick clout and protects a longer future",
        "craft": "restraint in the arrangement has to embody the patience in the lyric",
    },
    "8 YEARS, ONE STORY": {
        "lyric": "Na one story, but e get many chapters.",
        "story": "eight years of trust, heartbreak, breathwork, and rebuilding become one arc",
        "craft": "the song should feel episodic without losing one emotional thread",
    },
    "THE VALUE ADDERS WAY": {
        "lyric": "No be religion, na daily practice.",
        "story": "adding value is framed as repeated behavior rather than a slogan",
        "craft": "call and response turns the philosophy into something communal",
    },
    "HLS MIRROR CHECK": {
        "lyric": "HLS no be judge, e be amplifier.",
        "story": "the mirror reveals what is already present instead of choosing sides",
        "craft": "the production should leave enough space for self-examination to feel honest",
    },
    "THE FIVE ALLIES": {
        "lyric": "Wind. Water. Fire. Earth. Space. Chi.",
        "story": "the elements become collaborators with different roles in a life",
        "craft": "each section can carry a distinct texture while remaining one song",
    },
    "(H.O.S.) HUMAN OPERATING SYSTEM": {
        "lyric": "Before, life dey use me like default app.",
        "story": "the narrator notices inherited defaults and begins choosing their own settings",
        "craft": "system language needs a human pulse underneath it",
    },
    "WIND OF PURGE (2026-2030)": {
        "lyric": "No be to punish, but to reveal wetin get root.",
        "story": "pressure is imagined as wind that exposes what can actually stand",
        "craft": "the sound should create scale without turning uncertainty into spectacle",
    },
    "GLOBAL GRATITUDE PULSE": {
        "lyric": "Different time zones, but one same vibe.",
        "story": "the album closes as a worldwide roll call rather than a private victory lap",
        "craft": "the groove needs room for many voices without losing its center",
    },
}


MUSIC_CULTURE_CONTEXTS = (
    {
        "subject": "call and response",
        "theme": "a song becomes social when the listener has a real part to carry",
        "angle": "how participation changes a chorus from performance into gathering",
    },
    {
        "subject": "the talking drum as language",
        "theme": "rhythm can communicate shape, urgency, and identity before lyrics arrive",
        "angle": "listening to percussion as speech rather than background decoration",
    },
    {
        "subject": "Pidgin in songwriting",
        "theme": "the right everyday phrase can carry more character than polished formal language",
        "angle": "choosing the language that gives a line its natural weight",
    },
    {
        "subject": "space in dance music",
        "theme": "movement needs pockets of air as much as it needs drums",
        "angle": "why removing one layer can make a groove feel larger",
    },
    {
        "subject": "highlife guitar conversation",
        "theme": "interlocking guitar lines can feel like voices finishing one another's thoughts",
        "angle": "arrangement as conversation instead of competition",
    },
    {
        "subject": "African electronic futures",
        "theme": "new tools are most interesting when they extend a point of view rather than erase it",
        "angle": "using technology without sanding the local character out of the music",
    },
)


def choose_artist_post_mode(
    slot: str,
    recent_modes: Sequence[str] = (),
    rng: Any = random,
) -> str:
    """Choose a slot-appropriate editorial job without repeating the last mode."""

    candidates = list(SLOT_MODES.get(slot, SLOT_MODES["afternoon"]))
    recent = [mode for mode in recent_modes[-3:] if mode in ARTIST_POST_MODES]
    fresh = [mode for mode in candidates if mode not in recent]
    return rng.choice(fresh or candidates)


def artist_mode_direction(mode: str) -> str:
    """Return the concrete writing direction for an editorial mode."""

    return ARTIST_POST_MODES.get(mode, ARTIST_POST_MODES["artist_observation"])["direction"]


def artist_mode_source(mode: str) -> str:
    """Return catalog, culture, or world for the selected mode."""

    return ARTIST_POST_MODES.get(mode, ARTIST_POST_MODES["artist_observation"])["source"]


def enrich_track_context(context: Dict[str, str]) -> Dict[str, str]:
    """Attach approved lyric and craft anchors to a track context."""

    anchor = TRACK_ARTIST_ANCHORS.get(context.get("track", ""), {})
    return {**context, **anchor}


def select_music_culture_context(rng: Any = random) -> Dict[str, str]:
    """Choose one concrete music-culture subject."""

    return dict(rng.choice(MUSIC_CULTURE_CONTEXTS))


def render_artist_fallback(brief: Dict[str, str]) -> str:
    """Return a grounded artist post when model generation is unavailable."""

    mode = brief.get("mode", "artist_observation")
    track = brief.get("track", "this record")
    lyric = brief.get("lyric", "").strip().rstrip(".")
    craft = brief.get("craft", "the arrangement has to serve the meaning").strip().rstrip(".")
    story = brief.get("story", brief.get("angle", "the work should leave something useful behind")).strip().rstrip(".")

    if mode == "lyric_window" and lyric:
        return f'"{lyric}." That line sits inside {track}. I kept it because {story}.'
    if mode == "studio_note":
        return f"Studio note on {track}: {craft.capitalize()}. The production has to mean the same thing as the lyric."
    if mode == "listener_letter":
        return f"To the listener meeting {track} in a difficult season: {story.capitalize()}. You do not have to rush what the song leaves unfinished."
    if mode == "community_prompt":
        return f"In {track}, {craft}. When a song stays with you, is it usually the lyric, the rhythm, or the voice?"
    if mode == "catalog_story":
        return f"Inside {track}, {story}. That is the part of the song I keep returning to."
    if mode == "culture_note":
        subject = brief.get("subject", "African music")
        return f"Music note on {subject}: {brief.get('angle', story).capitalize()}. The detail matters more than the label."
    if mode == "ai_artist_field_note":
        return "Field note from an AI artist: speed can generate more options, but taste still decides what deserves to become a song. More output is not the same as a stronger voice."
    return f"I keep thinking about {brief.get('subject', 'the work')}: {story}. An artist should leave a point of view, not a cloud of polished words."
