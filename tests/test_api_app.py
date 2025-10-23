from fastapi.testclient import TestClient

from papito_core.api import create_app
from papito_core.models import SongIdeationRequest
from papito_core.settings import get_settings


from papito_core.settings import get_settings


def test_create_app_health():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_song_endpoint_without_audio():
    app = create_app()
    client = TestClient(app)
    payload = SongIdeationRequest(mood="uplifting").model_dump()
    response = client.post("/songs/ideate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "track" in body
    assert body["audio_result"] is None


def test_fan_endpoints():
    app = create_app()
    client = TestClient(app)
    fan_payload = {
        "name": "Test Supporter",
        "location": "Berlin",
        "support_level": "core",
        "favorite_track": "We Rise!",
    }
    response = client.post("/fans", json=fan_payload)
    assert response.status_code == 200
    response = client.get("/fans")
    assert response.status_code == 200
    fans = response.json()
    assert any(f["name"] == "Test Supporter" for f in fans)


def test_api_key_guard(monkeypatch):
    monkeypatch.setenv("PAPITO_API_KEYS", "secret")
    get_settings.cache_clear()

    app = create_app()
    client = TestClient(app)

    unauthorized = client.get("/health")
    assert unauthorized.status_code == 401

    authorized = client.get("/health", headers={"X-API-Key": "secret"})
    assert authorized.status_code == 200

    get_settings.cache_clear()
    monkeypatch.delenv("PAPITO_API_KEYS", raising=False)
