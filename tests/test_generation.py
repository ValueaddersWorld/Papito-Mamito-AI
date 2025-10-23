import pytest

from papito_core.engines import StubTextGenerator, SunoTextGenerator
from papito_core.generation import create_text_generator
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
