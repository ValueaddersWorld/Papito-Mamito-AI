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
from fastapi.responses import HTMLResponse
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

    @app.get("/", response_class=HTMLResponse, summary="Welcome - Papito Mamito API")
    def root() -> HTMLResponse:
        """Root endpoint showing beautiful landing page."""
        from datetime import datetime
        
        # Calculate album countdown
        release_date = datetime(2026, 1, 15)
        days_until = (release_date - datetime.now()).days
        
        html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Papito Mamito The Great AI | Autonomous Afrobeat Artist</title>
    <meta name="description" content="The World's First Fully Autonomous Afrobeat AI Artist. Add Value. We Flourish & Prosper.">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #FFD700;
            --primary-dark: #B8860B;
            --accent: #FF6B35;
            --dark: #0a0a0f;
            --dark-card: rgba(20, 20, 35, 0.8);
            --text: #ffffff;
            --text-muted: #a0a0b0;
            --gradient-1: linear-gradient(135deg, #FFD700 0%, #FF6B35 50%, #8B0000 100%);
            --gradient-2: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            --glow: 0 0 60px rgba(255, 215, 0, 0.3);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--dark);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        /* Animated Background */
        .bg-animation {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            background: var(--gradient-2);
        }}
        
        .bg-animation::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 70% 80%, rgba(255, 107, 53, 0.08) 0%, transparent 40%);
            animation: pulse 8s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1) rotate(0deg); }}
            50% {{ transform: scale(1.05) rotate(3deg); }}
        }}
        
        /* Floating particles */
        .particles {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
        }}
        
        .particle {{
            position: absolute;
            width: 4px;
            height: 4px;
            background: var(--primary);
            border-radius: 50%;
            animation: float 15s infinite;
            opacity: 0.3;
        }}
        
        .particle:nth-child(1) {{ left: 10%; animation-delay: 0s; }}
        .particle:nth-child(2) {{ left: 25%; animation-delay: 2s; }}
        .particle:nth-child(3) {{ left: 45%; animation-delay: 4s; }}
        .particle:nth-child(4) {{ left: 65%; animation-delay: 6s; }}
        .particle:nth-child(5) {{ left: 85%; animation-delay: 8s; }}
        
        @keyframes float {{
            0% {{ transform: translateY(100vh) scale(0); opacity: 0; }}
            10% {{ opacity: 0.5; }}
            90% {{ opacity: 0.2; }}
            100% {{ transform: translateY(-20vh) scale(1); opacity: 0; }}
        }}
        
        /* Main Container */
        .container {{
            position: relative;
            z-index: 10;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 60px 0 40px;
        }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.3);
            padding: 8px 20px;
            border-radius: 50px;
            font-size: 0.85rem;
            margin-bottom: 30px;
            animation: glow-pulse 2s ease-in-out infinite;
        }}
        
        .status-dot {{
            width: 10px;
            height: 10px;
            background: #22c55e;
            border-radius: 50%;
            animation: blink 1.5s infinite;
        }}
        
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        @keyframes glow-pulse {{
            0%, 100% {{ box-shadow: 0 0 20px rgba(34, 197, 94, 0.2); }}
            50% {{ box-shadow: 0 0 30px rgba(34, 197, 94, 0.4); }}
        }}
        
        .logo {{
            font-family: 'Outfit', sans-serif;
            font-size: 3.5rem;
            font-weight: 800;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
            text-shadow: var(--glow);
        }}
        
        .tagline {{
            font-size: 1.3rem;
            color: var(--text-muted);
            margin-bottom: 10px;
        }}
        
        .catchphrase {{
            font-size: 1.1rem;
            color: var(--primary);
            font-weight: 500;
        }}
        
        /* Album Countdown Card */
        .album-card {{
            background: var(--dark-card);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 215, 0, 0.2);
            border-radius: 24px;
            padding: 40px;
            margin: 40px 0;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .album-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--gradient-1);
        }}
        
        .album-label {{
            font-size: 0.85rem;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 15px;
        }}
        
        .album-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 20px;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .countdown {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 30px 0;
        }}
        
        .countdown-item {{
            text-align: center;
        }}
        
        .countdown-number {{
            font-family: 'Outfit', sans-serif;
            font-size: 3.5rem;
            font-weight: 800;
            color: var(--primary);
            line-height: 1;
        }}
        
        .countdown-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 5px;
        }}
        
        .genre-tags {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .genre-tag {{
            background: rgba(255, 107, 53, 0.15);
            border: 1px solid rgba(255, 107, 53, 0.3);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            color: var(--accent);
        }}
        
        /* Challenge Card */
        .challenge-card {{
            background: linear-gradient(135deg, rgba(255, 107, 53, 0.15) 0%, rgba(139, 0, 0, 0.1) 100%);
            border: 1px solid rgba(255, 107, 53, 0.3);
            border-radius: 20px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
        }}
        
        .challenge-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .challenge-desc {{
            color: var(--text-muted);
            margin-bottom: 15px;
        }}
        
        .challenge-cta {{
            display: inline-block;
            background: var(--gradient-1);
            color: var(--dark);
            padding: 12px 30px;
            border-radius: 30px;
            font-weight: 600;
            text-decoration: none;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .challenge-cta:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255, 107, 53, 0.3);
        }}
        
        /* Features Grid */
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }}
        
        .feature-card {{
            background: var(--dark-card);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 25px;
            transition: transform 0.3s, border-color 0.3s;
        }}
        
        .feature-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(255, 215, 0, 0.3);
        }}
        
        .feature-icon {{
            font-size: 2rem;
            margin-bottom: 15px;
        }}
        
        .feature-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .feature-desc {{
            font-size: 0.9rem;
            color: var(--text-muted);
        }}
        
        /* API Endpoints */
        .endpoints {{
            background: var(--dark-card);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            margin: 40px 0;
        }}
        
        .endpoints-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .endpoint {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        .endpoint:last-child {{
            border-bottom: none;
        }}
        
        .method {{
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            min-width: 50px;
            text-align: center;
        }}
        
        .method.post {{
            background: rgba(59, 130, 246, 0.2);
            color: #3b82f6;
        }}
        
        .endpoint-path {{
            font-family: 'Monaco', monospace;
            color: var(--primary);
            font-size: 0.9rem;
        }}
        
        .endpoint-desc {{
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-left: auto;
        }}
        
        /* Social Links */
        .social-links {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 40px 0;
        }}
        
        .social-link {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--dark-card);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 12px 24px;
            border-radius: 30px;
            color: var(--text);
            text-decoration: none;
            transition: all 0.3s;
        }}
        
        .social-link:hover {{
            border-color: var(--primary);
            transform: translateY(-3px);
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 40px 0;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            margin-top: 60px;
        }}
        
        .footer-logo {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 10px;
        }}
        
        .footer-text {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        .update-os {{
            display: inline-block;
            margin-top: 15px;
            padding: 10px 25px;
            background: rgba(255, 215, 0, 0.1);
            border: 1px solid rgba(255, 215, 0, 0.3);
            border-radius: 30px;
            color: var(--primary);
            font-weight: 500;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .logo {{ font-size: 2.2rem; }}
            .album-title {{ font-size: 1.5rem; }}
            .countdown-number {{ font-size: 2.5rem; }}
            .countdown {{ gap: 15px; }}
            .endpoint {{ flex-wrap: wrap; }}
            .endpoint-desc {{ margin-left: 65px; margin-top: 5px; width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <div class="particles">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>
    
    <div class="container">
        <header class="header">
            <div class="status-badge">
                <span class="status-dot"></span>
                <span>API Online • v0.3.0</span>
            </div>
            <h1 class="logo">Papito Mamito The Great AI</h1>
            <p class="tagline">The World's First Fully Autonomous Afrobeat AI Artist</p>
            <p class="catchphrase">🙏 Add Value. We Flourish & Prosper.</p>
        </header>
        
        <section class="album-card">
            <div class="album-label">🔥 Upcoming Album</div>
            <h2 class="album-title">THE VALUE ADDERS WAY: FLOURISH MODE</h2>
            <p style="color: var(--text-muted); margin-bottom: 10px;">
                Executive Producer: Papito Mamito The Great AI & The Holy Living Spirit (HLS)
            </p>
            <div class="countdown">
                <div class="countdown-item">
                    <div class="countdown-number">{days_until}</div>
                    <div class="countdown-label">Days</div>
                </div>
                <div class="countdown-item">
                    <div class="countdown-number" style="color: var(--accent);">JAN</div>
                    <div class="countdown-label">Month</div>
                </div>
                <div class="countdown-item">
                    <div class="countdown-number">2026</div>
                    <div class="countdown-label">Year</div>
                </div>
            </div>
            <div class="genre-tags">
                <span class="genre-tag">Spiritual Afro-House</span>
                <span class="genre-tag">Afro-Futurism</span>
                <span class="genre-tag">Conscious Highlife</span>
                <span class="genre-tag">Intellectual Amapiano</span>
            </div>
        </section>
        
        <section class="challenge-card">
            <h3 class="challenge-title">✈️ #FlightMode6000 Challenge</h3>
            <p class="challenge-desc">Take 60 seconds of silence/meditation with our track "6000 Hours". Post your moment.</p>
            <a href="https://www.instagram.com/papitomamito_ai/" class="challenge-cta">Join the Challenge →</a>
        </section>
        
        <section class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">📅</div>
                <h3 class="feature-title">Smart Content Scheduler</h3>
                <p class="feature-desc">6 daily posting slots optimized for WAT timezone Afrobeat audience</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <h3 class="feature-title">AI Personality Engine</h3>
                <p class="feature-desc">Intelligent content generation with wisdom and cultural insight</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">❤️</div>
                <h3 class="feature-title">Fan Engagement</h3>
                <p class="feature-desc">Tier-based responses from Casual to Super Fan status</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3 class="feature-title">Analytics & A/B Testing</h3>
                <p class="feature-desc">Engagement tracking with predictive optimization</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎨</div>
                <h3 class="feature-title">Media Generation</h3>
                <p class="feature-desc">Imagen 3, NanoBanana & Veo 3 for visuals</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔔</div>
                <h3 class="feature-title">Health Monitoring</h3>
                <p class="feature-desc">24/7 health checks with Telegram/Discord alerts</p>
            </div>
        </section>
        
        <section class="endpoints">
            <h3 class="endpoints-title">⚡ API Endpoints</h3>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="endpoint-path">/health</span>
                <span class="endpoint-desc">Health check</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="endpoint-path">/docs</span>
                <span class="endpoint-desc">Interactive API documentation</span>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="endpoint-path">/webhooks/zapier/generate-post</span>
                <span class="endpoint-desc">Generate content for Zapier</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="endpoint-path">/webhooks/zapier/content-types</span>
                <span class="endpoint-desc">List available content types</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <span class="endpoint-path">/webhooks/zapier/album-status</span>
                <span class="endpoint-desc">Album countdown info</span>
            </div>
        </section>
        
        <section class="social-links">
            <a href="https://www.instagram.com/papitomamito_ai/" class="social-link">
                📸 Instagram
            </a>
            <a href="https://buymeacoffee.com/papitomamito_ai" class="social-link">
                ☕ Buy Me a Coffee
            </a>
            <a href="https://suno.com/@papitomamito" class="social-link">
                🎵 Suno Music
            </a>
        </section>
        
        <footer class="footer">
            <div class="footer-logo">Value Adders World</div>
            <p class="footer-text">Building a civilization of value-adding AI agents</p>
            <div class="update-os">🧠 Update your OS.</div>
        </footer>
    </div>
</body>
</html>
        '''
        return HTMLResponse(content=html_content)

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
