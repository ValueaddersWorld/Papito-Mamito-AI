import random

from papito_core.artist_voice import (
    ARTIST_POST_MODES,
    MUSIC_MODES,
    SLOT_MODES,
    TRACK_ARTIST_ANCHORS,
    choose_artist_post_mode,
    render_artist_fallback,
)
from papito_core.voice_quality import assess_artist_voice, assess_x_voice


def test_recent_robotic_feed_posts_are_rejected():
    posts = [
        (
            "Originality springs from knowing what you stand for. Before you chase trends, "
            "anchor in your beliefs. Let that foundation guide your voice, making what you "
            "create unmistakably yours. Authenticity speaks louder than novelty."
        ),
        (
            'The drums in "GLOBAL GRATITUDE PULSE" pulse with intention, guiding movement '
            "and breath. They create space for reflection, reminding us that thankfulness can "
            "be a collective experience. Every beat is a step toward renewal."
        ),
        (
            "Excuses can act like chains, binding you to the same spot. When you pause for an "
            "honest self-audit, you expose the roots of your stagnation. Growth waits for no "
            "one, not even your circumstances."
        ),
    ]

    for post in posts:
        assessment = assess_x_voice(post)
        assert not assessment.passed
        assert "generated-wisdom phrasing" in assessment.feedback()


def test_each_slot_uses_artist_editorial_modes_without_immediate_repeat():
    rng = random.Random(9)
    recent = []

    for slot in ("morning", "afternoon", "evening") * 20:
        mode = choose_artist_post_mode(slot, recent, rng=rng)
        assert mode in SLOT_MODES[slot]
        if any(candidate not in recent[-3:] for candidate in SLOT_MODES[slot]):
            assert mode not in recent[-3:]
        recent.append(mode)

    assert set(recent) == set(ARTIST_POST_MODES)


def test_catalog_modes_have_real_lyric_and_craft_anchors():
    assert len(TRACK_ARTIST_ANCHORS) == 14
    for anchor in TRACK_ARTIST_ANCHORS.values():
        assert anchor["lyric"]
        assert anchor["story"]
        assert anchor["craft"]


def test_artist_fallbacks_pass_artist_voice_gate():
    base = {
        "track": "DELAYED GRATIFICATION",
        "subject": "space in dance music",
        "angle": "removing one layer can make a groove feel larger",
        "lyric": "No rush, my Gee. Legacy no dey sprint.",
        "story": "the narrator protects a longer future",
        "craft": "restraint in the arrangement embodies patience",
    }

    for mode in ARTIST_POST_MODES:
        brief = {**base, "mode": mode}
        text = render_artist_fallback(brief)
        assessment = assess_artist_voice(
            text,
            music_post=mode in MUSIC_MODES or mode == "culture_note",
            track=brief["track"],
        )
        assert assessment.passed, f"{mode}: {assessment.feedback()}"
        assert len(text) <= 280
        assert "?" not in text or mode == "community_prompt"
