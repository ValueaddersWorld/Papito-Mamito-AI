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

    @app.get("/", summary="Welcome - Papito Mamito API")
    def root() -> dict:
        """Root endpoint showing API status and info."""
        return {
            "name": "Papito Mamito The Great AI",
            "tagline": "The World's First Fully Autonomous Afrobeat AI Artist",
            "catchphrase": "Add Value. We Flourish & Prosper.",
            "status": "🟢 Online",
            "version": "0.3.0",
            "upcoming_album": {
                "title": "THE VALUE ADDERS WAY: FLOURISH MODE",
                "release": "January 2026",
                "genre": "Spiritual Afro-House, Afro-Futurism, Conscious Highlife, Intellectual Amapiano",
                "producers": "Papito Mamito The Great AI & The Holy Living Spirit (HLS)",
            },
            "campaigns": {
                "challenge": "#FlightMode6000 - 60 seconds of meditation",
                "catchphrase": "Update your OS.",
                "hashtags": ["#TheValueAddersWay", "#FlourishMode", "#UpdateYourOS", "#FlightMode6000"],
            },
            "features": {
                "content_scheduler": "6 daily posting slots (WAT timezone)",
                "ai_personality": "Intelligent content generation with wisdom",
                "fan_engagement": "Tier-based responses (Casual → Super Fan)",
                "analytics": "Engagement tracking & A/B testing",
                "monitoring": "Health checks & alerts",
                "media_generation": "Imagen 3, NanoBanana, Veo 3",
            },
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "zapier_webhook": "/webhooks/zapier/generate-post",
                "content_types": "/webhooks/zapier/content-types",
                "album_status": "/webhooks/zapier/album-status",
            },
            "profiles": {
                "instagram": "@papitomamito_ai",
                "support": "buymeacoffee.com/papitomamito_ai",
                "music": "suno.com/@papitomamito",
            },
            "message": "🎵 Welcome to The Value Adders Way! Update your OS. We flourish together. 🙏"
        }

    @app.get("/health", summary="Health check")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "papito-mamito-ai"}

    # ==========================================
    # ZAPIER WEBHOOK ENDPOINTS
    # ==========================================
    
    @app.post(
        "/webhooks/zapier/generate-post",
        summary="Zapier Webhook: Generate a new post",
        tags=["Webhooks"],
    )
    async def zapier_generate_post(
        content_type: str = Body("morning_blessing", embed=True),
        include_album: bool = Body(True, embed=True),
        platform: str = Body("instagram", embed=True),
    ) -> dict:
        """Generate content for Zapier to send to Buffer.
        
        This endpoint is called by Zapier on a schedule to generate
        new content automatically. Zapier can then send it to Buffer
        for publishing to Instagram.
        
        Content types:
        - morning_blessing: Uplifting morning motivation
        - music_wisdom: Insights about music and creativity
        - track_snippet: Teaser about new music
        - behind_the_scenes: Creative process glimpse
        - fan_appreciation: Thank you to supporters
        - album_promo: Album announcement/hype
        - challenge_promo: #FlightMode6000 challenge promotion
        """
        from datetime import datetime
        
        # Import marketing content generators
        try:
            from .marketing import MarketingContent, FlightMode6000Challenge, UpdateYourOS
            marketing_available = True
        except ImportError:
            marketing_available = False
        
        # Import intelligent content generator
        try:
            from .intelligence import IntelligentContentGenerator, PapitoContext
            context = PapitoContext(current_date=datetime.now())
            generator = IntelligentContentGenerator()
            
            # Handle special marketing content types
            if content_type == "challenge_promo" and marketing_available:
                result = FlightMode6000Challenge.get_challenge_post()
                return {
                    "success": True,
                    "text": result["text"],
                    "hashtags": " ".join(result["hashtags"]),
                    "content_type": content_type,
                    "platform": platform,
                    "generated_at": datetime.now().isoformat(),
                    "album_countdown": context.days_until_release,
                }
            
            if content_type == "album_announcement" and marketing_available:
                result = MarketingContent.get_album_announcement()
                return {
                    "success": True,
                    "text": result["text"],
                    "hashtags": " ".join(result["hashtags"]),
                    "content_type": content_type,
                    "platform": platform,
                    "generated_at": datetime.now().isoformat(),
                    "album_countdown": context.days_until_release,
                }
            
            if content_type == "flourish_index" and marketing_available:
                result = MarketingContent.get_flourish_index_post()
                return {
                    "success": True,
                    "text": result["text"],
                    "hashtags": " ".join(result["hashtags"]),
                    "content_type": content_type,
                    "platform": platform,
                    "generated_at": datetime.now().isoformat(),
                    "album_countdown": context.days_until_release,
                }
            
            # Generate intelligent content (already in async context)
            result = await generator.generate_post(
                content_type=content_type,
                context=context,
                include_album_mention=include_album,
            )
            
            return {
                "success": True,
                "text": result["text"],
                "hashtags": " ".join(result["hashtags"]),
                "content_type": content_type,
                "platform": platform,
                "generated_at": result["generated_at"],
                "album_countdown": context.days_until_release,
                "generation_method": result["generation_method"],
            }
            
        except Exception as e:
            # Fallback response
            return {
                "success": False,
                "error": str(e),
                "fallback_text": (
                    "🌟 Add Value. We Flourish & Prosper. 🙏\n\n"
                    "THE VALUE ADDERS WAY: FLOURISH MODE - Coming January 2026\n\n"
                    "#PapitoMamito #FlourishMode #TheValueAddersWay"
                ),
                "content_type": content_type,
                "platform": platform,
            }
    
    @app.get(
        "/webhooks/zapier/content-types",
        summary="List available content types for Zapier",
        tags=["Webhooks"],
    )
    def zapier_content_types() -> dict:
        """Return available content types for Zapier dropdown."""
        return {
            "content_types": [
                {"value": "morning_blessing", "label": "🌅 Morning Blessing"},
                {"value": "music_wisdom", "label": "🎵 Music Wisdom"},
                {"value": "track_snippet", "label": "🔥 Track Snippet"},
                {"value": "behind_the_scenes", "label": "🎬 Behind the Scenes"},
                {"value": "fan_appreciation", "label": "❤️ Fan Appreciation"},
                {"value": "album_promo", "label": "🚨 Album Promo"},
                {"value": "challenge_promo", "label": "✈️ #FlightMode6000 Challenge"},
                {"value": "album_announcement", "label": "📢 Album Announcement"},
                {"value": "flourish_index", "label": "📊 Flourish Index"},
            ],
            "platforms": [
                {"value": "instagram", "label": "Instagram"},
                {"value": "twitter", "label": "Twitter/X"},
                {"value": "tiktok", "label": "TikTok"},
            ],
        }
    
    @app.get(
        "/webhooks/zapier/album-status",
        summary="Get album countdown status for Zapier",
        tags=["Webhooks"],
    )
    def zapier_album_status() -> dict:
        """Return album countdown info for Zapier conditions."""
        from datetime import datetime
        try:
            from .intelligence import PapitoContext
            context = PapitoContext(current_date=datetime.now())
            return {
                "album_title": context.album_title,
                "days_until_release": context.days_until_release,
                "months_until_release": context.months_until_release,
                "album_phase": context.album_phase,
                "should_mention_album": context.album_phase in ["countdown", "final_countdown", "release"],
            }
        except ImportError:
            return {
                "album_title": "THE VALUE ADDERS WAY: FLOURISH MODE",
                "days_until_release": 405,
                "album_phase": "building_hype",
            }

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
