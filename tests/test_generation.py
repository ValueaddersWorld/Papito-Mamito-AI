import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from papito_core.engines import StubTextGenerator, SunoTextGenerator
from papito_core.generation import create_text_generator
from papito_core.intelligence.content_generator import (
    IntelligentContentGenerator,
    PapitoContext,
    sanitize_public_text,
)
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
    assert "FLOURISH MODE" in text
    assert "days until" not in text.lower()
    assert "coming" not in text.lower()
    assert "\U0001F525" not in text
