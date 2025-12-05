"""FastAPI application exposing Papito Mamito workflows."""

from __future__ import annotations

import time
from collections import deque
from typing import Optional

from fastapi import (
    BackgroundTasks,
    Body,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
)
from fastapi.security import APIKeyHeader

from .automation import AnalyticsSummary, StreamingAnalyticsService
from .config import PapitoPaths
from .fanbase import FanbaseRegistry
from .models import BlogBrief, BlogDraft, FanProfile, MerchItem, ReleaseTrack, SongIdeationRequest
from .settings import get_settings
from .storage import ReleaseCatalog
from .workflows import BlogWorkflow, MusicWorkflow


class RateLimitExceeded(Exception):
    """Raised when a client exceeds the rate limit."""


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key: str) -> None:
        now = time.monotonic()
        history = self._hits.setdefault(key, deque())
        while history and now - history[0] > self.window:
            history.popleft()
        if len(history) >= self.limit:
            raise RateLimitExceeded
        history.append(now)


def create_app() -> FastAPI:
    """Instantiate the Papito Mamito API application."""

    settings = get_settings()
    
    # Initialize paths (gracefully handle errors)
    try:
        paths = PapitoPaths()
        paths.ensure()
    except Exception as e:
        print(f"Warning: Failed to initialize paths: {e}")
        paths = None

    app = FastAPI(
        title="Papito Mamito API",
        description="Autonomous creative workflows for Papito Mamito AI.",
        version="0.2.0",
    )

    api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
    rate_limiter = RateLimiter(limit=max(settings.api_rate_limit_per_min, 1))

    # Initialize services with graceful error handling
    blog_workflow = None
    music_workflow = None
    analytics_service = None
    fanbase_registry = None
    catalog = None
    
    try:
        blog_workflow = BlogWorkflow()
    except Exception as e:
        print(f"Warning: Failed to initialize BlogWorkflow: {e}")
    
    try:
        music_workflow = MusicWorkflow()
    except Exception as e:
        print(f"Warning: Failed to initialize MusicWorkflow: {e}")
    
    try:
        analytics_service = StreamingAnalyticsService()
    except Exception as e:
        print(f"Warning: Failed to initialize StreamingAnalyticsService: {e}")
    
    try:
        if paths:
            fanbase_registry = FanbaseRegistry(paths=paths)
    except Exception as e:
        print(f"Warning: Failed to initialize FanbaseRegistry: {e}")
    
    try:
        if paths:
            catalog = ReleaseCatalog(paths=paths)
    except Exception as e:
        print(f"Warning: Failed to initialize ReleaseCatalog: {e}")

    def authorize(request: Request, api_key: str | None = Depends(api_key_header)) -> str:
        keys = settings.api_keys_set
        identity = api_key or (request.client.host if request.client else "anonymous")
        if keys and (api_key not in keys):
            raise HTTPException(status_code=401, detail="Invalid API key.")
        try:
            rate_limiter.hit(identity)
        except RateLimitExceeded:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")
        return identity

    @app.get("/health", summary="Health check")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "papito-mamito-ai"}

    @app.post(
        "/blogs",
        response_model=BlogDraft,
        summary="Generate a blog entry",
        dependencies=[Depends(authorize)],
    )
    def create_blog(brief: BlogBrief) -> BlogDraft:
        return blog_workflow.generate(brief)

    @app.post(
        "/songs/ideate",
        summary="Generate a song concept (optionally with audio metadata)",
        dependencies=[Depends(authorize)],
    )
    def create_song(
        request: SongIdeationRequest,
        background_tasks: BackgroundTasks,
        generate_audio: bool = Query(
            False,
            description="Trigger Suno audio generation if credentials are configured.",
        ),
        audio_duration_seconds: Optional[int] = Query(
            None,
            ge=30,
            le=300,
            description="Requested audio duration when generating audio.",
        ),
        instrumental: bool = Query(
            False,
            description="Request an instrumental version when generating audio.",
        ),
        poll: bool = Query(
            False,
            description="If audio generation is triggered, poll for completion in the background.",
        ),
    ) -> dict[str, object]:
        try:
            track, audio_result = music_workflow.compose(
                request,
                generate_audio=generate_audio,
                audio_duration_seconds=audio_duration_seconds,
                instrumental=instrumental,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        background = None
        if audio_result and poll and audio_result.task_id:
            background = "Audio polling scheduled."
            background_tasks.add_task(
                _poll_audio_and_update,
                music_workflow,
                catalog,
                track,
                audio_result.task_id,
            )

        return {
            "track": track,
            "audio_result": audio_result,
            "background_task": background,
        }

    @app.post(
        "/analytics/summarise",
        response_model=AnalyticsSummary,
        summary="Aggregate analytics snapshots",
        dependencies=[Depends(authorize)],
    )
    def summarise_analytics(
        payload: dict = Body(..., description="Payload containing a `snapshots` array."),
    ) -> AnalyticsSummary:
        snapshots = payload.get("snapshots")
        if not isinstance(snapshots, list):
            raise HTTPException(status_code=400, detail="Payload requires a 'snapshots' array.")
        try:
            return analytics_service.load(snapshots)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(
        "/fans",
        response_model=list[FanProfile],
        summary="List registered fans",
        dependencies=[Depends(authorize)],
    )
    def list_fans() -> list[FanProfile]:
        return fanbase_registry.list_fans()

    @app.post(
        "/fans",
        response_model=FanProfile,
        summary="Register a new fan",
        dependencies=[Depends(authorize)],
    )
    def add_fan(profile: FanProfile) -> FanProfile:
        fanbase_registry.add_fan(profile)
        return profile

    @app.get(
        "/merch",
        response_model=list[MerchItem],
        summary="Retrieve merch catalog",
        dependencies=[Depends(authorize)],
    )
    def list_merch() -> list[MerchItem]:
        return fanbase_registry.list_merch()

    return app


def _poll_audio_and_update(
    workflow: MusicWorkflow,
    catalog: ReleaseCatalog,
    track: ReleaseTrack,
    task_id: str,
    max_attempts: int = 30,
    interval_seconds: float = 5.0,
) -> None:
    """Poll Suno for completion and update release catalog audio metadata."""

    engine = workflow.get_audio_engine()
    if engine is None:
        return

    current_attempt = 0
    result = None
    while current_attempt < max_attempts:
        current_attempt += 1
        try:
            result = engine.poll(task_id)
        except Exception:
            time.sleep(interval_seconds)
            continue

        status = result.status.lower()
        if status in {"complete", "completed", "ready", "succeeded"}:
            break
        time.sleep(interval_seconds)

    if result:
        enriched_track = workflow.enrich_track_with_audio(track, result)
        catalog.update_track_audio(enriched_track)


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("papito_core.api:app", host="0.0.0.0", port=8000, reload=True)
