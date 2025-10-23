from papito_core.engines import StubTextGenerator
from papito_core.models import AudioGenerationResult, BlogBrief, SongIdeationRequest
from papito_core.workflows import BlogWorkflow, MusicWorkflow


def test_blog_workflow_stub_output_contains_sections():
    workflow = BlogWorkflow(generator=StubTextGenerator())
    brief = BlogBrief(title="Rise Notes", gratitude_theme="Abundant gratitude")
    draft = workflow.generate(brief)

    assert "Blessings family" in draft.body
    assert "Call to unity" in draft.body


def test_music_workflow_stub_fallback_returns_default_track():
    workflow = MusicWorkflow(generator=StubTextGenerator())
    request = SongIdeationRequest(title_hint="Glow")
    track = workflow.ideate_track(request)

    assert track.title == "Rise with Abundance"
    assert track.tempo_bpm == 108


def test_music_workflow_compose_without_audio(monkeypatch):
    workflow = MusicWorkflow(generator=StubTextGenerator())
    request = SongIdeationRequest()
    track, audio_result = workflow.compose(request, generate_audio=False)
    assert track.title == "Rise with Abundance"
    assert track.audio is None
    assert audio_result is None


def test_music_workflow_compose_with_audio_missing_credentials(monkeypatch):
    workflow = MusicWorkflow(generator=StubTextGenerator())
    request = SongIdeationRequest()
    try:
        workflow.compose(request, generate_audio=True)
    except RuntimeError as exc:
        assert "SUNO_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when audio generation requested without credentials.")


def test_music_workflow_compose_with_audio_metadata(monkeypatch):
    workflow = MusicWorkflow(generator=StubTextGenerator())

    class FakeAudioEngine:
        def generate(self, request):
            return AudioGenerationResult(
                task_id="task-123",
                status="complete",
                audio_url="https://example.com/audio.mp3",
                preview_url="https://example.com/preview.mp3",
                lyric="Sample lyric",
                image_url="https://example.com/art.png",
                metadata={"bpm": 108},
            )

        def poll(self, task_id):
            return self.generate(None)

    workflow._audio_engine = FakeAudioEngine()  # type: ignore[attr-defined]
    request = SongIdeationRequest()
    track, audio_result = workflow.compose(request, generate_audio=True)

    assert audio_result is not None
    assert track.audio is not None
    assert track.audio.audio_url == "https://example.com/audio.mp3"
