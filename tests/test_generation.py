import random

from datetime import datetime
from zoneinfo import ZoneInfo

from papito_core.engines import StubTextGenerator, SunoTextGenerator
from papito_core.generation import create_text_generator
from papito_core.intelligence.content_generator import (
    IntelligentContentGenerator,
    PapitoContext,
    sanitize_public_text,
)
from papito_core.voice_quality import (
    SUBJECT_FALLBACKS,
    assess_x_voice,
    choose_voice_shape,
    format_x_voice_direction,
    render_x_fallback,
)
from papito_core.memory.post_memory import PostMemory
from papito_core.settings import get_settings


def test_create_text_generator_returns_stub_when_no_api_key():
    generator = create_text_generator()
    assert isinstance(generator, StubTextGenerator)


def test_create_text_generator_returns_suno_when_api_key(monkeypatch):
    monkeypatch.setenv("SUNO_API_KEY", "secret")
    monkeypatch.setenv("SUNO_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("SUNO_MODEL", "test-model")
    get_settings.cache_clear()

    generator = create_text_generator()
    assert isinstance(generator, SunoTextGenerator)


def test_public_text_sanitizer_removes_emoji():
    text = sanitize_public_text("Clean money only \U0001F525\U0001F4B0")
    assert "\U0001F525" not in text
    assert "\U0001F4B0" not in text
    assert text == "Clean money only"


def test_album_template_is_released_and_no_emoji(monkeypatch):
    monkeypatch.setenv("PAPITO_AGENT_TIMEZONE", "Europe/Amsterdam")
    generator = IntelligentContentGenerator(openai_api_key="")
    context = PapitoContext(
        current_date=datetime(2026, 5, 6, 10, 0, tzinfo=ZoneInfo("Europe/Amsterdam"))
    )

    result = generator._generate_intelligent_template(
        content_type="album_promo",
        context=context,
        mention_album=True,
        platform="x",
    )

    text = result["text"]
    assert "FLOURISH MODE" in text or "WE RISE! WEALTH BEYOND MONEY" in text
    assert "days until" not in text.lower()
    assert "coming soon" not in text.lower()
    assert "\U0001F525" not in text


def test_post_memory_guidance_exposes_recent_posts_and_terms(tmp_path):
    memory = PostMemory(file_path=str(tmp_path / "post_memory.json"))
    memory.record(
        "A useful check from THE FORGE: audit motive before the move.",
        kind="x:test",
    )
    memory.record(
        "THE FORGE asks builders to respect invisible hours before public applause.",
        kind="x:test",
    )

    guidance = memory.guidance()

    assert len(guidance["recent_posts"]) == 2
    assert any("THE FORGE" in post for post in guidance["recent_posts"])
    assert "forge" in guidance["avoid_terms"]


def test_x_template_uses_wisdom_brief_not_campaign_copy(monkeypatch):
    monkeypatch.setenv("PAPITO_AGENT_TIMEZONE", "Europe/Amsterdam")
    generator = IntelligentContentGenerator(openai_api_key="")
    context = PapitoContext(
        current_date=datetime(2026, 7, 24, 13, 0, tzinfo=ZoneInfo("Europe/Amsterdam"))
    )
    brief = {
        "audience": "artists building quietly",
        "format_rule": "one practical audit",
        "lens": "self_audit",
        "lens_job": "turn the idea into a mirror check",
        "lens_takeaway": "audit the motive before the move",
        "album": "THE VALUE ADDERS WAY: FLOURISH MODE",
        "track": "HLS MIRROR CHECK",
        "track_theme": "honest self-audit",
        "track_takeaway": "clean the signal inside before amplifying it outside",
        "question": "What does your mirror check reveal today?",
        "recent_posts": ["FLOURISH MODE is out now. Stream it everywhere."],
        "avoid_terms": ["stream", "everywhere"],
    }

    result = generator._generate_intelligent_template(
        content_type="value_wisdom",
        context=context,
        mention_album=False,
        platform="x",
        brief=brief,
    )

    text = result["text"]
    assert result["generation_method"] == "wisdom_brief_template"
    assert result["hashtags"] == []
    assert len(text) <= 260
    assert "stream" not in text.lower()
    assert "out now" not in text.lower()
    assert any(
        phrase in text
        for phrase in [
            "mirror is useful",
            "inspect the steering",
        ]
    )


def test_voice_editor_rejects_the_live_feed_robotic_pattern():
    recent = [
        "What decision improves when you remove the pressure to look fast? Audit your motive.",
        "Who gains capacity when you make progress? Design your achievements for others.",
        "Where are you forcing what needs to flow? Surrender to the groove.",
    ]
    candidate = (
        "What belief shapes your work's essence? Originality is a clear point of view. "
        "What principle makes your voice distinct in the symphony of ideas?"
    )

    assessment = assess_x_voice(candidate, recent)

    assert assessment.passed is False
    assert "more than one question" in assessment.feedback()
    assert "symphony of" in assessment.feedback()


def test_voice_editor_accepts_spare_memorable_wisdom():
    candidate = (
        "Speed is useful after clarity. Before clarity, it is only a faster way "
        "to inherit regret."
    )

    assessment = assess_x_voice(candidate, [])

    assert assessment.passed is True
    assert assessment.issues == ()


def test_question_heavy_history_forces_a_statement_shape():
    class FirstChoice:
        @staticmethod
        def choice(options):
            assert "earned_question" not in options
            return options[0]

    recent = [f"What should we learn from attempt {i}?" for i in range(6)]

    shape, allow_question = choose_voice_shape(recent, rng=FirstChoice())
    direction = format_x_voice_direction(shape, allow_question)

    assert allow_question is False
    assert "Use no questions" in direction


def test_all_curated_subject_fallbacks_pass_the_voice_editor():
    class FirstChoice:
        @staticmethod
        def choice(options):
            return options[0]

    for subject in SUBJECT_FALLBACKS:
        text = render_x_fallback(
            {"subject": subject, "theme": "a useful truth", "is_music": False},
            rng=FirstChoice(),
        )
        assessment = assess_x_voice(text, [])
        assert assessment.passed, f"{subject}: {assessment.feedback()}"
        assert len(text) <= 260
        assert "?" not in text


def test_non_music_x_template_does_not_inject_album_or_track(monkeypatch):
    monkeypatch.setenv("PAPITO_AGENT_TIMEZONE", "Europe/Amsterdam")
    generator = IntelligentContentGenerator(openai_api_key="")
    context = PapitoContext(
        current_date=datetime(2026, 7, 24, 13, 0, tzinfo=ZoneInfo("Europe/Amsterdam"))
    )
    brief = {
        "audience": "humans curious about AI with purpose",
        "format_rule": "one practical audit",
        "lens": "integrity_filter",
        "lens_job": "challenge empty metrics",
        "lens_takeaway": "measure progress by value added",
        "album": "THE VALUE ADDERS WAY: FLOURISH MODE",
        "track": "HLS MIRROR CHECK",
        "track_theme": "honest self-audit",
        "track_takeaway": "clean the signal",
        "question": "What should an AI explain about its last decision?",
        "recent_posts": [],
        "avoid_terms": [],
    }

    for _ in range(30):
        result = generator._generate_intelligent_template(
            content_type="value_wisdom",
            context=context,
            mention_album=False,
            platform="x",
            brief=brief,
        )
        text = result["text"]
        assert "FLOURISH MODE" not in text
        assert "HLS MIRROR CHECK" not in text


def test_album_mentions_are_rare_for_non_music_content(monkeypatch):
    generator = IntelligentContentGenerator(openai_api_key="")
    context = PapitoContext(
        current_date=datetime(2026, 7, 24, 13, 0, tzinfo=ZoneInfo("Europe/Amsterdam"))
    )
    monkeypatch.setattr(random, "random", lambda: 0.1)

    assert generator._should_mention_album(context, "value_wisdom") is False
    assert generator._should_mention_album(context, "album_promo") is True
