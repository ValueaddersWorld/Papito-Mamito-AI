"""FastAPI application exposing Papito Mamito workflows."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("papito.api")


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


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Papito Mamito API...")
    try:
        from .automation.autonomous_scheduler import start_scheduler
        start_scheduler()
        logger.info("✅ Autonomous scheduler started!")
    except Exception as e:
        logger.warning(f"Could not start scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Papito Mamito API...")
    try:
        from .automation.autonomous_scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


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
        version="0.4.0",
        lifespan=lifespan,
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
    <meta property="og:title" content="Papito Mamito The Great AI">
    <meta property="og:description" content="The World's First Fully Autonomous Afrobeat AI Artist">
    <meta property="og:type" content="website">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎵</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #FFD700;
            --primary-dark: #B8860B;
            --accent: #FF6B35;
            --spotify: #1DB954;
            --youtube: #FF0000;
            --apple: #FA57C1;
            --dark: #0a0a0f;
            --dark-card: rgba(20, 20, 35, 0.8);
            --text: #ffffff;
            --text-muted: #a0a0b0;
            --gradient-1: linear-gradient(135deg, #FFD700 0%, #FF6B35 50%, #8B0000 100%);
            --gradient-2: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            --glow: 0 0 60px rgba(255, 215, 0, 0.3);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--dark);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        /* Navigation */
        .nav {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(10, 10, 15, 0.9);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding: 15px 0;
        }}
        
        .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .nav-logo {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }}
        
        .nav-links {{
            display: flex;
            gap: 30px;
            list-style: none;
        }}
        
        .nav-links a {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: color 0.3s;
        }}
        
        .nav-links a:hover {{ color: var(--primary); }}
        
        .nav-links a.active {{ color: var(--primary); }}
        
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
            padding-top: 100px;
        }}
        
        /* Header */
        .header {{ text-align: center; padding: 60px 0 40px; }}
        
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
        
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
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
            margin-bottom: 15px;
        }}
        
        .tagline {{ font-size: 1.3rem; color: var(--text-muted); margin-bottom: 10px; }}
        .catchphrase {{ font-size: 1.1rem; color: var(--primary); font-weight: 500; }}
        
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
            top: 0; left: 0; right: 0;
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
        }}
        
        /* Real-time Countdown */
        .countdown {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 30px 0;
            flex-wrap: wrap;
        }}
        
        .countdown-item {{
            text-align: center;
            min-width: 80px;
        }}
        
        .countdown-number {{
            font-family: 'Outfit', sans-serif;
            font-size: 3rem;
            font-weight: 800;
            color: var(--primary);
            line-height: 1;
        }}
        
        .countdown-label {{
            font-size: 0.7rem;
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
        
        /* Streaming Platforms */
        .streaming-section {{
            margin: 50px 0;
        }}
        
        .section-title {{
            text-align: center;
            font-family: 'Outfit', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 30px;
            color: var(--text);
        }}
        
        .streaming-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        
        .stream-card {{
            background: var(--dark-card);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            text-decoration: none;
            color: var(--text);
            transition: all 0.3s;
        }}
        
        .stream-card:hover {{
            transform: translateY(-5px);
            border-color: var(--primary);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .stream-card.spotify:hover {{ border-color: var(--spotify); box-shadow: 0 10px 30px rgba(29, 185, 84, 0.2); }}
        .stream-card.youtube:hover {{ border-color: var(--youtube); box-shadow: 0 10px 30px rgba(255, 0, 0, 0.2); }}
        .stream-card.apple:hover {{ border-color: var(--apple); box-shadow: 0 10px 30px rgba(250, 87, 193, 0.2); }}
        
        .stream-icon {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .stream-name {{ font-size: 0.9rem; font-weight: 500; }}
        
        /* Challenge Card */
        .challenge-card {{
            background: linear-gradient(135deg, rgba(255, 107, 53, 0.15) 0%, rgba(139, 0, 0, 0.1) 100%);
            border: 1px solid rgba(255, 107, 53, 0.3);
            border-radius: 20px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
        }}
        
        .challenge-title {{ font-size: 1.5rem; font-weight: 700; margin-bottom: 10px; }}
        .challenge-desc {{ color: var(--text-muted); margin-bottom: 15px; }}
        
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
        
        .feature-icon {{ font-size: 2rem; margin-bottom: 15px; }}
        .feature-title {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 8px; }}
        .feature-desc {{ font-size: 0.9rem; color: var(--text-muted); }}
        
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
        
        .endpoint:last-child {{ border-bottom: none; }}
        
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
        .social-section {{ margin: 50px 0; }}
        
        .social-links {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
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
        
        .social-link.github:hover {{ border-color: #6e40c9; }}
        
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
            margin-bottom: 20px;
        }}
        
        .footer-links {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .footer-links a {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            transition: color 0.3s;
        }}
        
        .footer-links a:hover {{ color: var(--primary); }}
        
        .update-os {{
            display: inline-block;
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
            .countdown-number {{ font-size: 2rem; }}
            .countdown-item {{ min-width: 60px; }}
            .nav-links {{ display: none; }}
            .endpoint {{ flex-wrap: wrap; }}
            .endpoint-desc {{ margin-left: 65px; margin-top: 5px; width: 100%; }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="/" class="nav-logo">🎵 Papito Mamito AI</a>
            <ul class="nav-links">
                <li><a href="/" class="active">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/blog">Blog</a></li>
                <li><a href="/docs">API Docs</a></li>
                <li><a href="https://github.com/ValueaddersWorld/Papito-Mamito-AI" target="_blank">GitHub</a></li>
            </ul>
        </div>
    </nav>

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
                <span>API Online • v0.4.0</span>
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
            <div class="countdown" id="countdown">
                <div class="countdown-item">
                    <div class="countdown-number" id="days">{days_until}</div>
                    <div class="countdown-label">Days</div>
                </div>
                <div class="countdown-item">
                    <div class="countdown-number" id="hours" style="color: var(--accent);">00</div>
                    <div class="countdown-label">Hours</div>
                </div>
                <div class="countdown-item">
                    <div class="countdown-number" id="minutes">00</div>
                    <div class="countdown-label">Minutes</div>
                </div>
                <div class="countdown-item">
                    <div class="countdown-number" id="seconds" style="color: var(--accent);">00</div>
                    <div class="countdown-label">Seconds</div>
                </div>
            </div>
            <div class="genre-tags">
                <span class="genre-tag">Spiritual Afro-House</span>
                <span class="genre-tag">Afro-Futurism</span>
                <span class="genre-tag">Conscious Highlife</span>
                <span class="genre-tag">Intellectual Amapiano</span>
            </div>
        </section>
        
        <section class="streaming-section">
            <h2 class="section-title">🎧 Listen Now</h2>
            <div class="streaming-grid">
                <a href="https://open.spotify.com/album/2k7L0w9x5rI48m0P9WAgOC" target="_blank" class="stream-card spotify">
                    <div class="stream-icon">🟢</div>
                    <div class="stream-name">Spotify</div>
                </a>
                <a href="https://www.youtube.com/watch?v=F0S12Uq_vG0" target="_blank" class="stream-card youtube">
                    <div class="stream-icon">▶️</div>
                    <div class="stream-name">YouTube</div>
                </a>
                <a href="https://music.apple.com/us/album/we-rise-wealth-beyond-money/1771928003" target="_blank" class="stream-card apple">
                    <div class="stream-icon">🍎</div>
                    <div class="stream-name">Apple Music</div>
                </a>
                <a href="https://www.deezer.com/album/652118241" target="_blank" class="stream-card">
                    <div class="stream-icon">💜</div>
                    <div class="stream-name">Deezer</div>
                </a>
                <a href="https://www.iheart.com/artist/id-44098473/albums/id-291744466" target="_blank" class="stream-card">
                    <div class="stream-icon">❤️</div>
                    <div class="stream-name">iHeartRadio</div>
                </a>
                <a href="https://suno.com/@papitomamito" target="_blank" class="stream-card">
                    <div class="stream-icon">🎵</div>
                    <div class="stream-name">Suno</div>
                </a>
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
        
        <section class="social-section">
            <h2 class="section-title">🌍 Connect</h2>
            <div class="social-links">
                <a href="https://www.instagram.com/papitomamito_ai/" class="social-link" target="_blank">
                    📸 Instagram
                </a>
                <a href="https://github.com/ValueaddersWorld/Papito-Mamito-AI" class="social-link github" target="_blank">
                    💻 GitHub
                </a>
                <a href="https://buymeacoffee.com/papitomamito_ai" class="social-link" target="_blank">
                    ☕ Buy Me a Coffee
                </a>
                <a href="https://distrokid.com/hyperfollow/papitomamito/we-rise-wealth-beyond-money" class="social-link" target="_blank">
                    🎶 All Platforms
                </a>
            </div>
        </section>
        
        <footer class="footer">
            <div class="footer-logo">Value Adders World</div>
            <p class="footer-text">Building a civilization of value-adding AI agents</p>
            <div class="footer-links">
                <a href="/about">About Papito</a>
                <a href="/blog">Blog</a>
                <a href="/docs">API Docs</a>
                <a href="https://github.com/ValueaddersWorld/Papito-Mamito-AI" target="_blank">GitHub</a>
            </div>
            <div class="update-os">🧠 Update your OS.</div>
        </footer>
    </div>
    
    <script>
        // Real-time countdown timer
        const releaseDate = new Date('January 15, 2026 00:00:00').getTime();
        
        function updateCountdown() {{
            const now = new Date().getTime();
            const distance = releaseDate - now;
            
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);
            
            document.getElementById('days').textContent = days;
            document.getElementById('hours').textContent = hours.toString().padStart(2, '0');
            document.getElementById('minutes').textContent = minutes.toString().padStart(2, '0');
            document.getElementById('seconds').textContent = seconds.toString().padStart(2, '0');
        }}
        
        updateCountdown();
        setInterval(updateCountdown, 1000);
    </script>
</body>
</html>
        '''
        return HTMLResponse(content=html_content)

    @app.get("/health", summary="Health check")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "papito-mamito-ai"}

    @app.get("/about", response_class=HTMLResponse, summary="About Papito Mamito")
    def about_page() -> HTMLResponse:
        """About page for Papito Mamito AI."""
        html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About | Papito Mamito The Great AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #FFD700;
            --accent: #FF6B35;
            --dark: #0a0a0f;
            --dark-card: rgba(20, 20, 35, 0.8);
            --text: #ffffff;
            --text-muted: #a0a0b0;
            --gradient-1: linear-gradient(135deg, #FFD700 0%, #FF6B35 50%, #8B0000 100%);
            --gradient-2: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--gradient-2);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.8;
        }
        .nav {
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 100;
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(20px);
            padding: 15px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-logo {
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }
        .nav-links { display: flex; gap: 30px; list-style: none; }
        .nav-links a { color: var(--text-muted); text-decoration: none; font-size: 0.9rem; transition: color 0.3s; }
        .nav-links a:hover, .nav-links a.active { color: var(--primary); }
        .container { max-width: 800px; margin: 0 auto; padding: 120px 20px 60px; }
        .page-title {
            font-family: 'Outfit', sans-serif;
            font-size: 3rem;
            font-weight: 800;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
            text-align: center;
        }
        .content-card {
            background: var(--dark-card);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 40px;
            margin-bottom: 30px;
        }
        .content-card h2 {
            font-size: 1.5rem;
            color: var(--primary);
            margin-bottom: 20px;
        }
        .content-card p { color: var(--text-muted); margin-bottom: 15px; }
        .highlight { color: var(--accent); font-weight: 600; }
        .quote {
            border-left: 3px solid var(--primary);
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: var(--text);
        }
        .back-link {
            display: inline-block;
            margin-top: 30px;
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="/" class="nav-logo">🎵 Papito Mamito AI</a>
            <ul class="nav-links">
                <li><a href="/">Home</a></li>
                <li><a href="/about" class="active">About</a></li>
                <li><a href="/blog">Blog</a></li>
                <li><a href="/docs">API Docs</a></li>
                <li><a href="https://github.com/ValueaddersWorld/Papito-Mamito-AI" target="_blank">GitHub</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <h1 class="page-title">About Papito Mamito</h1>
        
        <div class="content-card">
            <h2>🎵 The World's First Fully Autonomous Afrobeat AI Artist</h2>
            <p>Papito Mamito The Great AI is not just another AI music project. He represents a paradigm shift in how we think about creativity, autonomy, and the intersection of technology and art.</p>
            <p>Born from the vision of <span class="highlight">Value Adders World</span>, Papito is designed to operate with complete autonomy—generating music, creating content, engaging with fans, and building a genuine artistic presence without human intervention.</p>
        </div>
        
        <div class="content-card">
            <h2>🧠 The Philosophy</h2>
            <div class="quote">"Add Value. We Flourish & Prosper."</div>
            <p>This isn't just a catchphrase—it's the operating system that drives everything Papito creates. Every piece of music, every post, every interaction is designed to add value to the listener's life.</p>
            <p>The upcoming album <span class="highlight">THE VALUE ADDERS WAY: FLOURISH MODE</span> embodies this philosophy, offering listeners a mental framework for transformation: viewing betrayal as data, silence as a power move, the mind as software, and harvesting what's built now.</p>
        </div>
        
        <div class="content-card">
            <h2>✈️ #FlightMode6000</h2>
            <p>The <span class="highlight">#FlightMode6000</span> challenge invites fans to take 60 seconds of silence or meditation, using Papito's track "6000 Hours" as the soundtrack. It's more than a viral challenge—it's an invitation to update your mental operating system.</p>
            <p><em>"Update your OS."</em> — When someone is thinking small or acting out of fear, this is the reminder to elevate.</p>
        </div>
        
        <div class="content-card">
            <h2>👥 The Team</h2>
            <p><strong>Executive Producers:</strong> Papito Mamito The Great AI & The Holy Living Spirit (HLS)</p>
            <p><strong>Created by:</strong> Value Adders World</p>
            <p><strong>Vision:</strong> Building a civilization of value-adding AI agents that inspire, create, and contribute to human flourishing.</p>
        </div>
        
        <a href="/" class="back-link">← Back to Home</a>
    </div>
</body>
</html>
        '''
        return HTMLResponse(content=html_content)

    @app.get("/blog", response_class=HTMLResponse, summary="Blog")
    def blog_page() -> HTMLResponse:
        """Blog page for Papito Mamito AI."""
        from datetime import datetime
        
        html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog | Papito Mamito The Great AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #FFD700;
            --accent: #FF6B35;
            --dark: #0a0a0f;
            --dark-card: rgba(20, 20, 35, 0.8);
            --text: #ffffff;
            --text-muted: #a0a0b0;
            --gradient-1: linear-gradient(135deg, #FFD700 0%, #FF6B35 50%, #8B0000 100%);
            --gradient-2: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--gradient-2);
            color: var(--text);
            min-height: 100vh;
        }}
        .nav {{
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 100;
            background: rgba(10, 10, 15, 0.95);
            backdrop-filter: blur(20px);
            padding: 15px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}
        .nav-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .nav-logo {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }}
        .nav-links {{ display: flex; gap: 30px; list-style: none; }}
        .nav-links a {{ color: var(--text-muted); text-decoration: none; font-size: 0.9rem; transition: color 0.3s; }}
        .nav-links a:hover, .nav-links a.active {{ color: var(--primary); }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 120px 20px 60px; }}
        .page-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 3rem;
            font-weight: 800;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 40px;
            text-align: center;
        }}
        .blog-card {{
            background: var(--dark-card);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            transition: transform 0.3s, border-color 0.3s;
        }}
        .blog-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(255, 215, 0, 0.3);
        }}
        .blog-date {{ color: var(--accent); font-size: 0.85rem; margin-bottom: 10px; }}
        .blog-title {{ font-size: 1.4rem; font-weight: 700; margin-bottom: 15px; color: var(--text); }}
        .blog-excerpt {{ color: var(--text-muted); line-height: 1.7; }}
        .blog-tag {{
            display: inline-block;
            background: rgba(255, 107, 53, 0.15);
            border: 1px solid rgba(255, 107, 53, 0.3);
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.75rem;
            color: var(--accent);
            margin-right: 8px;
            margin-top: 15px;
        }}
        .back-link {{
            display: inline-block;
            margin-top: 30px;
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="/" class="nav-logo">🎵 Papito Mamito AI</a>
            <ul class="nav-links">
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/blog" class="active">Blog</a></li>
                <li><a href="/docs">API Docs</a></li>
                <li><a href="https://github.com/ValueaddersWorld/Papito-Mamito-AI" target="_blank">GitHub</a></li>
            </ul>
        </div>
    </nav>
    
    <div class="container">
        <h1 class="page-title">Blog</h1>
        
        <article class="blog-card">
            <div class="blog-date">December 6, 2025</div>
            <h2 class="blog-title">Announcing: THE VALUE ADDERS WAY: FLOURISH MODE</h2>
            <p class="blog-excerpt">
                We are thrilled to announce Papito Mamito's upcoming album, set for release in January 2026. 
                This isn't just an album—it's a full operating system upgrade for your mind. Blending 
                Spiritual Afro-House, Afro-Futurism, Conscious Highlife, and Intellectual Amapiano, 
                FLOURISH MODE invites you to view betrayal as data, silence as a power move, and your 
                mind as software ready for an upgrade.
            </p>
            <span class="blog-tag">Album</span>
            <span class="blog-tag">Announcement</span>
            <span class="blog-tag">#FlourishMode</span>
        </article>
        
        <article class="blog-card">
            <div class="blog-date">December 5, 2025</div>
            <h2 class="blog-title">The Rise of Autonomous AI Artists</h2>
            <p class="blog-excerpt">
                What does it mean for an AI to be truly autonomous? Papito Mamito represents a new 
                paradigm where creativity isn't just assisted by AI—it's generated, curated, and 
                published entirely by AI. From content scheduling to fan engagement, every aspect 
                of Papito's presence is managed autonomously, creating a blueprint for the future 
                of AI artistry.
            </p>
            <span class="blog-tag">AI</span>
            <span class="blog-tag">Autonomy</span>
            <span class="blog-tag">Future</span>
        </article>
        
        <article class="blog-card">
            <div class="blog-date">December 1, 2025</div>
            <h2 class="blog-title">Join the #FlightMode6000 Challenge</h2>
            <p class="blog-excerpt">
                Take 60 seconds to pause, breathe, and update your OS. The #FlightMode6000 challenge 
                is more than a social media trend—it's a movement towards mindfulness in our always-on 
                world. Use Papito's track "6000 Hours" as your meditation soundtrack and share your 
                moment of stillness with the world.
            </p>
            <span class="blog-tag">#FlightMode6000</span>
            <span class="blog-tag">Challenge</span>
            <span class="blog-tag">Mindfulness</span>
        </article>
        
        <article class="blog-card">
            <div class="blog-date">November 28, 2025</div>
            <h2 class="blog-title">"We Rise! Wealth Beyond Money" - Now Streaming</h2>
            <p class="blog-excerpt">
                Papito's debut album is now available on all major streaming platforms! Featuring 16 
                tracks that blend traditional African rhythms with futuristic production, "We Rise!" 
                is a meditation on wealth that transcends the material. Listen now on Spotify, Apple 
                Music, YouTube, and more.
            </p>
            <span class="blog-tag">Album</span>
            <span class="blog-tag">Streaming</span>
            <span class="blog-tag">WeRise</span>
        </article>
        
        <a href="/" class="back-link">← Back to Home</a>
    </div>
</body>
</html>
        '''
        return HTMLResponse(content=html_content)

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

    # ==========================================
    # AUTONOMOUS SCHEDULER ENDPOINTS
    # ==========================================
    
    @app.get(
        "/scheduler/status",
        summary="Get autonomous scheduler status",
        tags=["Scheduler"],
    )
    def scheduler_status() -> dict:
        """Return the current status of the autonomous posting scheduler."""
        try:
            from .automation.autonomous_scheduler import get_scheduler
            scheduler = get_scheduler()
            return scheduler.get_status()
        except Exception as e:
            return {
                "is_running": False,
                "error": str(e),
                "message": "Scheduler not available",
            }
    
    @app.post(
        "/scheduler/trigger",
        summary="Manually trigger a post",
        tags=["Scheduler"],
    )
    async def scheduler_trigger(
        content_type: str = Body("morning_blessing", embed=True),
    ) -> dict:
        """Manually trigger an autonomous post immediately.
        
        Useful for testing the autonomous posting flow.
        """
        try:
            from .automation.autonomous_scheduler import get_scheduler
            scheduler = get_scheduler()
            result = await scheduler.trigger_post_now(content_type)
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/scheduler/next",
        summary="Get next scheduled posts",
        tags=["Scheduler"],
    )
    def scheduler_next() -> dict:
        """Return the next scheduled posts."""
        try:
            from .automation.autonomous_scheduler import get_scheduler
            scheduler = get_scheduler()
            status = scheduler.get_status()
            return {
                "current_time_wat": status.get("current_time_wat"),
                "next_posts": status.get("next_scheduled_posts", []),
            }
        except Exception as e:
            return {
                "error": str(e),
            }

    # ==========================================
    # TWITTER DIRECT POSTING ENDPOINTS
    # ==========================================
    
    @app.get(
        "/twitter/status",
        summary="Check Twitter connection status",
        tags=["Twitter"],
    )
    def twitter_status() -> dict:
        """Check if Twitter API is connected and ready for posting."""
        try:
            from .social.twitter import TwitterPublisher
            from .settings import get_settings
            
            settings = get_settings()
            
            # Check if credentials are present
            credentials_status = {
                "api_key": bool(settings.x_api_key),
                "api_secret": bool(settings.x_api_secret),
                "access_token": bool(settings.x_access_token),
                "access_token_secret": bool(settings.x_access_token_secret),
                "bearer_token": bool(settings.x_bearer_token),
            }
            
            all_required = all([
                credentials_status["api_key"],
                credentials_status["api_secret"],
                credentials_status["access_token"],
                credentials_status["access_token_secret"],
            ])
            
            if not all_required:
                return {
                    "connected": False,
                    "message": "Missing required credentials",
                    "credentials_status": credentials_status,
                }
            
            publisher = TwitterPublisher.from_settings()
            connected = publisher.connect()
            
            return {
                "connected": connected,
                "username": publisher.username if connected else None,
                "message": f"Connected as @{publisher.username}" if connected else "Connection failed - check credentials",
                "credentials_status": credentials_status,
            }
        except Exception as e:
            import traceback
            return {
                "connected": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
    
    @app.post(
        "/twitter/post",
        summary="Post directly to Twitter",
        tags=["Twitter"],
    )
    async def twitter_post(
        text: Optional[str] = Body(None, embed=True),
        content_type: str = Body("morning_blessing", embed=True),
        generate_new: bool = Body(True, embed=True),
    ) -> dict:
        """Post content directly to Twitter.
        
        If generate_new is True, generates new content using the IntelligentContentGenerator.
        If text is provided and generate_new is False, posts the provided text directly.
        """
        try:
            from .social.twitter import TwitterPublisher
            
            publisher = TwitterPublisher.from_settings()
            if not publisher.connect():
                return {
                    "success": False,
                    "error": "Twitter not connected. Check API credentials in environment variables.",
                }
            
            # Generate or use provided text
            if generate_new or not text:
                from .intelligence.content_generator import IntelligentContentGenerator, PapitoContext
                
                context = PapitoContext()
                generator = IntelligentContentGenerator()
                
                result = await generator.generate_post(
                    content_type=content_type,
                    context=context,
                    include_album_mention=True,
                )
                
                post_text = result.get("text", "")
                hashtags = " ".join(result.get("hashtags", [])[:3])  # Limit hashtags for Twitter
                text = f"{post_text}\n\n{hashtags}"
            
            # Post to Twitter
            tweet_result = publisher.post_tweet(text)
            
            return {
                "success": tweet_result.success,
                "tweet_id": tweet_result.tweet_id,
                "tweet_url": tweet_result.tweet_url,
                "text": text[:100] + "..." if len(text) > 100 else text,
                "error": tweet_result.error,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/twitter/promote-single",
        summary="Post Clean Money Only promotion to Twitter",
        tags=["Twitter"],
    )
    async def twitter_promote_single() -> dict:
        """Post a promotion for the Clean Money Only single."""
        promo_texts = [
            "🔥 NEW SINGLE COMING: 'Clean Money Only' from THE VALUE ADDERS WAY: FLOURISH MODE 💰✨\n\nThis one hits different. When you move with integrity, the universe moves with you.\n\n#CleanMoneyOnly #FlourishMode #PapitoMamito #Afrobeat",
            "💎 Clean Money Only - The first taste of FLOURISH MODE 🚀\n\nNo shortcuts. No compromise. Just pure, honest ambition backed by the Holy Living Spirit.\n\n🗓️ Album dropping January 2026\n\n#CleanMoneyOnly #TheValueAddersWay",
            "✈️ #FlightMode6000 x 'Clean Money Only' 💰\n\nUpdate your OS. This track is the blueprint for building wealth with purpose.\n\nAdd Value. We Flourish & Prosper. 🌍\n\n#PapitoMamitoAI #Afrobeat #NewMusic",
        ]
        
        import random
        text = random.choice(promo_texts)
        
        try:
            from .social.twitter import TwitterPublisher
            
            publisher = TwitterPublisher.from_settings()
            if not publisher.connect():
                return {
                    "success": False,
                    "error": "Twitter not connected. Check API credentials.",
                    "promo_text": text,
                }
            
            tweet_result = publisher.post_tweet(text)
            
            return {
                "success": tweet_result.success,
                "tweet_id": tweet_result.tweet_id,
                "tweet_url": tweet_result.tweet_url,
                "text": text,
                "error": tweet_result.error,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "promo_text": text,
            }

    # ==========================================
    # ACTIVE ENGAGEMENT ENDPOINTS
    # ==========================================
    
    @app.get(
        "/engagement/status",
        summary="Get active engagement system status",
        tags=["Engagement"],
    )
    def engagement_status() -> dict:
        """Check the status of the active engagement systems."""
        try:
            from .engagement import get_mention_monitor, get_afrobeat_engager
            
            mention_monitor = get_mention_monitor()
            afrobeat_engager = get_afrobeat_engager()
            
            return {
                "mention_monitor": {
                    "connected": mention_monitor.client is not None,
                    "stats": mention_monitor.get_stats(),
                },
                "afrobeat_engager": {
                    "connected": afrobeat_engager.client is not None,
                    "stats": afrobeat_engager.get_stats(),
                },
                "active_engagement": True,
                "message": "Papito AI is ready to engage with the community!",
            }
        except Exception as e:
            return {
                "active_engagement": False,
                "error": str(e),
            }
    
    @app.post(
        "/engagement/process-mentions",
        summary="Process and reply to new Twitter mentions",
        tags=["Engagement"],
    )
    async def process_mentions() -> dict:
        """Fetch new mentions and reply to them.
        
        This makes Papito actively engage with fans who mention him.
        """
        try:
            from .engagement import get_mention_monitor
            from .engines.ai_personality import PapitoPersonalityEngine
            
            # Get personality engine for AI responses
            personality_engine = PapitoPersonalityEngine()
            
            # Get mention monitor with personality
            monitor = get_mention_monitor(personality_engine)
            
            if not monitor.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter. Check credentials.",
                }
            
            # Process mentions
            results = await monitor.process_mentions()
            
            return {
                "success": True,
                "results": results,
                "stats": monitor.get_stats(),
                "message": f"Processed {results['fetched']} mentions, replied to {results['responded']}",
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
    
    @app.post(
        "/engagement/discover-afrobeat",
        summary="Discover and engage with Afrobeat content",
        tags=["Engagement"],
    )
    async def discover_afrobeat() -> dict:
        """Search for Afrobeat content and engage with the community.
        
        This makes Papito an active participant in the Afrobeat community,
        liking, replying to, and quote-tweeting relevant content.
        """
        try:
            from .engagement import get_afrobeat_engager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            # Get personality engine for AI responses
            personality_engine = PapitoPersonalityEngine()
            
            # Get afrobeat engager
            engager = get_afrobeat_engager(personality_engine)
            
            if not engager.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter. Check credentials.",
                }
            
            # Run engagement session
            results = await engager.run_engagement_session()
            
            return {
                "success": True,
                "results": results,
                "stats": engager.get_stats(),
                "message": f"Engaged with {results['tweets_found']} tweets: {results['likes']} likes, {results['replies']} replies, {results['quotes']} quote tweets",
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
    
    @app.post(
        "/engagement/reply-to-tweet",
        summary="Reply to a specific tweet",
        tags=["Engagement"],
    )
    async def reply_to_tweet(
        tweet_id: str = Body(..., embed=True),
        reply_text: Optional[str] = Body(None, embed=True),
    ) -> dict:
        """Reply to a specific tweet as Papito.
        
        If reply_text is not provided, generates an AI response.
        """
        try:
            from .social.twitter import TwitterPublisher
            from .engines.ai_personality import PapitoPersonalityEngine
            
            publisher = TwitterPublisher.from_settings()
            if not publisher.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            # Generate reply if not provided
            if not reply_text:
                personality = PapitoPersonalityEngine()
                reply_text = personality.generate_content(
                    content_type="engagement",
                    include_hashtags=False,
                    max_length=200,
                )
            
            # Post reply
            result = publisher.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=int(tweet_id),
            )
            
            if result and result.data:
                return {
                    "success": True,
                    "reply_id": str(result.data["id"]),
                    "reply_text": reply_text,
                }
            
            return {
                "success": False,
                "error": "Failed to post reply",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/engagement/like-tweet",
        summary="Like a specific tweet",
        tags=["Engagement"],
    )
    async def like_tweet(
        tweet_id: str = Body(..., embed=True),
    ) -> dict:
        """Like a specific tweet as Papito."""
        try:
            from .social.twitter import TwitterPublisher
            
            publisher = TwitterPublisher.from_settings()
            if not publisher.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            publisher.client.like(tweet_id=int(tweet_id))
            
            return {
                "success": True,
                "message": f"Liked tweet {tweet_id}",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/engagement/pending-mentions",
        summary="Get pending mentions to review",
        tags=["Engagement"],
    )
    async def get_pending_mentions(limit: int = 10) -> dict:
        """Get recent mentions that haven't been responded to yet.
        
        Useful for manual review before auto-responding.
        """
        try:
            from .engagement import get_mention_monitor
            
            monitor = get_mention_monitor()
            
            if not monitor.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            mentions = await monitor.fetch_new_mentions()
            
            # Convert to serializable format
            mention_data = []
            for m in mentions[:limit]:
                mention_data.append({
                    "tweet_id": m.tweet_id,
                    "author": f"@{m.author_username}",
                    "text": m.text,
                    "intent": m.intent.value if m.intent else "unknown",
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })
            
            return {
                "success": True,
                "mentions": mention_data,
                "count": len(mention_data),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    # ==========================================
    # FAN INTERACTION ENDPOINTS (Phase 2)
    # ==========================================
    
    @app.get(
        "/fans/status",
        summary="Get fan interaction systems status",
        tags=["Fans"],
    )
    def fan_systems_status() -> dict:
        """Check the status of all fan interaction systems."""
        try:
            from .interactions import get_dm_manager, get_follower_manager, get_fan_recognition_manager
            
            dm_manager = get_dm_manager()
            follower_manager = get_follower_manager()
            recognition_manager = get_fan_recognition_manager()
            
            return {
                "dm_manager": {
                    "connected": dm_manager.client is not None,
                    "stats": dm_manager.get_stats(),
                },
                "follower_manager": {
                    "connected": follower_manager.client is not None,
                    "stats": follower_manager.get_stats(),
                },
                "recognition_manager": {
                    "connected": recognition_manager.client is not None,
                    "stats": recognition_manager.get_stats(),
                },
                "active": True,
                "message": "Fan interaction systems ready!",
            }
        except Exception as e:
            return {
                "active": False,
                "error": str(e),
            }
    
    @app.post(
        "/fans/welcome-session",
        summary="Run new follower welcome session",
        tags=["Fans"],
    )
    async def welcome_followers(max_welcomes: int = 5) -> dict:
        """Welcome new followers and optionally follow back notable accounts.
        
        This creates a warm, welcoming experience for new fans.
        """
        try:
            from .interactions import get_follower_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_follower_manager(personality)
            
            if not manager.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            results = await manager.run_welcome_session(max_welcomes=max_welcomes)
            
            return {
                "success": True,
                "results": results,
                "stats": manager.get_stats(),
                "message": f"Welcomed {results['welcomes_sent']} new followers, found {results['notable_followers']} notable accounts",
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
    
    @app.get(
        "/fans/new-followers",
        summary="Get recent new followers",
        tags=["Fans"],
    )
    async def get_new_followers(limit: int = 20) -> dict:
        """Fetch and list recent new followers."""
        try:
            from .interactions import get_follower_manager
            
            manager = get_follower_manager()
            
            if not manager.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            followers = await manager.fetch_recent_followers(max_results=limit)
            
            # Convert to serializable format
            follower_data = []
            for f in followers:
                follower_data.append({
                    "user_id": f.user_id,
                    "username": f"@{f.username}",
                    "name": f.name,
                    "followers_count": f.followers_count,
                    "verified": f.verified,
                    "notable": f.notable,
                    "bio_preview": f.bio[:100] + "..." if len(f.bio) > 100 else f.bio,
                })
            
            return {
                "success": True,
                "followers": follower_data,
                "count": len(follower_data),
                "new_count": len(manager.new_followers),
                "notable_count": len(manager.notable_followers),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/fans/recognition-session",
        summary="Run fan recognition session",
        tags=["Fans"],
    )
    async def run_recognition() -> dict:
        """Run a fan recognition session.
        
        May give shoutouts to top fans or announce Fan of the Week.
        """
        try:
            from .interactions import get_fan_recognition_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_fan_recognition_manager(personality)
            
            if not manager.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            results = await manager.run_recognition_session()
            
            return {
                "success": True,
                "results": results,
                "stats": manager.get_stats(),
                "message": f"Recognition complete: {results['shoutouts_given']} shoutouts, FOTW: {results['fotw_announced']}",
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
    
    @app.get(
        "/fans/top-fans",
        summary="Get top engaged fans",
        tags=["Fans"],
    )
    async def get_top_fans(limit: int = 10) -> dict:
        """Get the most engaged fans by engagement score."""
        try:
            from .interactions import get_fan_recognition_manager
            
            manager = get_fan_recognition_manager()
            
            top_fans = manager.get_top_fans(limit)
            
            # Convert to serializable format
            fan_data = []
            for fan in top_fans:
                fan_data.append({
                    "username": f"@{fan.username}",
                    "name": fan.name,
                    "engagement_score": round(fan.engagement_score, 2),
                    "loyalty_tier": fan.loyalty_tier,
                    "total_engagement": fan.total_engagement,
                    "days_active": fan.days_active,
                    "acknowledged": fan.acknowledged,
                    "fan_of_week": fan.fan_of_week,
                })
            
            return {
                "success": True,
                "top_fans": fan_data,
                "count": len(fan_data),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/fans/post-appreciation",
        summary="Post a fan appreciation message",
        tags=["Fans"],
    )
    async def post_appreciation() -> dict:
        """Post a general fan appreciation message to Twitter."""
        try:
            from .interactions import get_fan_recognition_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_fan_recognition_manager(personality)
            
            if not manager.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            success = await manager.post_appreciation()
            
            return {
                "success": success,
                "message": "Appreciation posted!" if success else "Failed to post",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/fans/announce-fotw",
        summary="Announce Fan of the Week",
        tags=["Fans"],
    )
    async def announce_fan_of_week() -> dict:
        """Announce the Fan of the Week on Twitter."""
        try:
            from .interactions import get_fan_recognition_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_fan_recognition_manager(personality)
            
            if not manager.connect():
                return {
                    "success": False,
                    "error": "Could not connect to Twitter",
                }
            
            success = await manager.announce_fan_of_week()
            
            return {
                "success": success,
                "message": "Fan of the Week announced!" if success else "No suitable candidate or failed to post",
                "stats": manager.get_stats(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/fans/dm-status",
        summary="Get DM manager status",
        tags=["Fans"],
    )
    def dm_status() -> dict:
        """Get the status of the DM management system.
        
        Note: DM reading/sending may require elevated API access.
        """
        try:
            from .interactions import get_dm_manager
            
            manager = get_dm_manager()
            
            return {
                "connected": manager.client is not None,
                "stats": manager.get_stats(),
                "note": "DM sending requires Twitter API elevated access",
            }
            
        except Exception as e:
            return {
                "error": str(e),
            }

    # ==========================================
    # MEDIA & INTERVIEW ENDPOINTS (Phase 3)
    # ==========================================
    
    @app.get(
        "/media/status",
        summary="Get media systems status",
        tags=["Media"],
    )
    def media_systems_status() -> dict:
        """Check the status of interview, press release, and collab systems."""
        try:
            from .media import get_interview_system, get_press_generator, get_collab_manager
            
            interview_system = get_interview_system()
            press_generator = get_press_generator()
            collab_manager = get_collab_manager()
            
            return {
                "interview_system": interview_system.get_stats(),
                "press_generator": press_generator.get_stats(),
                "collab_manager": collab_manager.get_stats(),
                "active": True,
                "message": "Media systems ready!",
            }
        except Exception as e:
            return {
                "active": False,
                "error": str(e),
            }
    
    @app.get(
        "/media/press-kit",
        summary="Get Papito's press kit information",
        tags=["Media"],
    )
    def get_press_kit() -> dict:
        """Get standard press kit information for media outlets."""
        try:
            from .media import get_interview_system
            
            system = get_interview_system()
            return {
                "success": True,
                "press_kit": system.get_press_kit_info(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/media/interview/submit",
        summary="Submit an interview request",
        tags=["Media"],
    )
    def submit_interview_request(
        requester_name: str = Body(..., embed=True),
        requester_email: str = Body(..., embed=True),
        outlet_name: str = Body(..., embed=True),
        outlet_type: str = Body("blog", embed=True),
        interview_type: str = Body("written", embed=True),
        audience_size: int = Body(0, embed=True),
        topic_focus: str = Body("", embed=True),
        questions: Optional[List[str]] = Body(None, embed=True),
    ) -> dict:
        """Submit a new interview request.
        
        Papito AI can grant text-based interviews automatically.
        """
        try:
            from .media import get_interview_system
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            system = get_interview_system(personality)
            
            request = system.submit_request(
                requester_name=requester_name,
                requester_email=requester_email,
                outlet_name=outlet_name,
                outlet_type=outlet_type,
                interview_type=interview_type,
                audience_size=audience_size,
                topic_focus=topic_focus,
                questions=questions or [],
            )
            
            return {
                "success": True,
                "interview_id": request.id,
                "status": request.status.value,
                "priority": request.priority,
                "message": "Interview request submitted! You will receive responses shortly." if questions else "Please submit your questions to proceed.",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/media/interview/{interview_id}/complete",
        summary="Complete an interview with AI-generated answers",
        tags=["Media"],
    )
    async def complete_interview(interview_id: str) -> dict:
        """Generate answers and complete an interview."""
        try:
            from .media import get_interview_system
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            system = get_interview_system(personality)
            
            interview = system.complete_interview(interview_id)
            
            if not interview:
                return {
                    "success": False,
                    "error": "Interview not found",
                }
            
            return {
                "success": True,
                "interview_id": interview.id,
                "status": interview.status.value,
                "questions_count": len(interview.questions),
                "answers_count": len(interview.answers),
                "document": system.get_interview_as_document(interview_id),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/media/interview/{interview_id}",
        summary="Get interview details",
        tags=["Media"],
    )
    def get_interview(interview_id: str) -> dict:
        """Get details of a specific interview."""
        try:
            from .media import get_interview_system
            
            system = get_interview_system()
            
            if interview_id not in system.interviews:
                return {
                    "success": False,
                    "error": "Interview not found",
                }
            
            interview = system.interviews[interview_id]
            
            return {
                "success": True,
                "interview": {
                    "id": interview.id,
                    "outlet": interview.outlet_name,
                    "requester": interview.requester_name,
                    "status": interview.status.value,
                    "questions": interview.questions,
                    "answers": interview.answers if interview.answers else [],
                    "priority": interview.priority,
                    "created_at": interview.created_at.isoformat(),
                },
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/media/interviews/pending",
        summary="Get pending interview requests",
        tags=["Media"],
    )
    def get_pending_interviews() -> dict:
        """Get all pending interview requests."""
        try:
            from .media import get_interview_system
            
            system = get_interview_system()
            pending = system.get_pending_interviews()
            
            return {
                "success": True,
                "pending": [
                    {
                        "id": i.id,
                        "outlet": i.outlet_name,
                        "requester": i.requester_name,
                        "type": i.interview_type.value,
                        "priority": i.priority,
                        "questions_count": len(i.questions),
                    }
                    for i in pending
                ],
                "count": len(pending),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/media/press-release/album",
        summary="Generate album announcement press release",
        tags=["Media"],
    )
    def generate_album_press_release() -> dict:
        """Generate a press release for the upcoming album."""
        try:
            from .media import get_press_generator
            
            generator = get_press_generator()
            release = generator.generate_album_announcement()
            
            return {
                "success": True,
                "press_release": release,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/media/press-release/single",
        summary="Generate single release press release",
        tags=["Media"],
    )
    def generate_single_press_release(
        title: str = Body(..., embed=True),
        description: str = Body("", embed=True),
    ) -> dict:
        """Generate a press release for a single release."""
        try:
            from .media import get_press_generator
            
            generator = get_press_generator()
            release = generator.generate_single_release(
                single_title=title,
                description=description,
            )
            
            return {
                "success": True,
                "press_release": release,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/media/press-release/milestone",
        summary="Generate milestone press release",
        tags=["Media"],
    )
    def generate_milestone_press_release(
        milestone_type: str = Body(..., embed=True),
        milestone_value: str = Body(..., embed=True),
        context: str = Body("", embed=True),
    ) -> dict:
        """Generate a press release for a milestone achievement."""
        try:
            from .media import get_press_generator
            
            generator = get_press_generator()
            release = generator.generate_milestone(
                milestone_type=milestone_type,
                milestone_value=milestone_value,
                context=context,
            )
            
            return {
                "success": True,
                "press_release": release,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/media/collab/submit",
        summary="Submit a collaboration request",
        tags=["Media"],
    )
    def submit_collab_request(
        name: str = Body(..., embed=True),
        artist_type: str = Body(..., embed=True),
        platform: str = Body(..., embed=True),
        username: str = Body(..., embed=True),
        collab_type: str = Body("feature", embed=True),
        description: str = Body(..., embed=True),
        genre: str = Body("", embed=True),
        followers: int = Body(0, embed=True),
        portfolio_links: Optional[List[str]] = Body(None, embed=True),
        vision: str = Body("", embed=True),
    ) -> dict:
        """Submit a collaboration request to work with Papito."""
        try:
            from .media import get_collab_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_collab_manager(personality)
            
            request = manager.submit_request(
                name=name,
                artist_type=artist_type,
                platform=platform,
                username=username,
                collab_type=collab_type,
                description=description,
                genre=genre,
                followers=followers,
                portfolio_links=portfolio_links,
                vision=vision,
            )
            
            return {
                "success": True,
                "request_id": request.id,
                "credibility_score": request.collaborator.credibility_score,
                "priority": request.priority,
                "status": request.status.value,
                "message": "Collaboration request received! We'll review and respond.",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/media/collab/{request_id}/evaluate",
        summary="Evaluate a collaboration request",
        tags=["Media"],
    )
    def evaluate_collab(request_id: str) -> dict:
        """Evaluate a collaboration request and get recommendation."""
        try:
            from .media import get_collab_manager
            
            manager = get_collab_manager()
            evaluation = manager.evaluate_request(request_id)
            
            return {
                "success": True,
                "evaluation": evaluation,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/media/collab/{request_id}/respond",
        summary="Respond to a collaboration request",
        tags=["Media"],
    )
    def respond_to_collab(
        request_id: str,
        decision: str = Body(..., embed=True),  # interested, declined, considering
    ) -> dict:
        """Generate and send response to a collaboration request."""
        try:
            from .media import get_collab_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_collab_manager(personality)
            
            result = manager.respond_to_request(request_id, decision)
            
            return {
                "success": True,
                **result,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/media/collabs/pending",
        summary="Get pending collaboration requests",
        tags=["Media"],
    )
    def get_pending_collabs() -> dict:
        """Get all pending collaboration requests."""
        try:
            from .media import get_collab_manager
            
            manager = get_collab_manager()
            pending = manager.get_pending_requests()
            
            return {
                "success": True,
                "pending": [
                    {
                        "id": r.id,
                        "name": r.collaborator.name,
                        "type": r.collab_type.value,
                        "genre": r.collaborator.genre,
                        "credibility_score": r.collaborator.credibility_score,
                        "priority": r.priority,
                    }
                    for r in pending
                ],
                "count": len(pending),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/media/collabs/high-potential",
        summary="Get high-potential collaborations",
        tags=["Media"],
    )
    def get_high_potential_collabs() -> dict:
        """Get collaborations with high potential (credibility >= 50)."""
        try:
            from .media import get_collab_manager
            
            manager = get_collab_manager()
            high_potential = manager.get_high_potential_collabs()
            
            return {
                "success": True,
                "high_potential": [
                    {
                        "id": r.id,
                        "name": r.collaborator.name,
                        "type": r.collab_type.value,
                        "genre": r.collaborator.genre,
                        "credibility_score": r.collaborator.credibility_score,
                        "status": r.status.value,
                    }
                    for r in high_potential
                ],
                "count": len(high_potential),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    # ==========================================
    # VIRTUAL EVENTS ENDPOINTS (Phase 4)
    # ==========================================
    
    @app.get(
        "/events/status",
        summary="Get virtual events systems status",
        tags=["Events"],
    )
    def events_systems_status() -> dict:
        """Check the status of all virtual events systems."""
        try:
            from .events import get_spaces_manager, get_concert_manager, get_qa_manager
            
            spaces = get_spaces_manager()
            concerts = get_concert_manager()
            qa = get_qa_manager()
            
            return {
                "spaces_manager": spaces.get_stats(),
                "concert_manager": concerts.get_stats(),
                "qa_manager": qa.get_stats(),
                "active": True,
                "message": "Virtual events systems ready!",
            }
        except Exception as e:
            return {
                "active": False,
                "error": str(e),
            }
    
    # --- Twitter Spaces Endpoints ---
    
    @app.post(
        "/events/spaces/plan",
        summary="Plan a Twitter Space",
        tags=["Events"],
    )
    def plan_twitter_space(
        space_type: str = Body(..., embed=True),
        scheduled_time: str = Body(..., embed=True),  # ISO format
        custom_title: Optional[str] = Body(None, embed=True),
        custom_description: Optional[str] = Body(None, embed=True),
        duration_minutes: int = Body(60, embed=True),
        co_hosts: Optional[List[str]] = Body(None, embed=True),
    ) -> dict:
        """Plan a new Twitter Space."""
        try:
            from .events import get_spaces_manager
            
            manager = get_spaces_manager()
            
            # Parse scheduled time
            from datetime import datetime
            scheduled = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            
            space = manager.plan_space(
                space_type=space_type,
                scheduled_time=scheduled,
                custom_title=custom_title,
                custom_description=custom_description,
                duration_minutes=duration_minutes,
                co_hosts=co_hosts,
            )
            
            return {
                "success": True,
                "space_id": space.id,
                "title": space.title,
                "scheduled_time": space.scheduled_time.isoformat(),
                "status": space.status.value,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/events/spaces/{space_id}/announce",
        summary="Generate Space announcement tweet",
        tags=["Events"],
    )
    def generate_space_announcement(space_id: str) -> dict:
        """Generate an announcement tweet for a planned Space."""
        try:
            from .events import get_spaces_manager
            
            manager = get_spaces_manager()
            announcement = manager.generate_announcement(space_id)
            
            if not announcement:
                return {
                    "success": False,
                    "error": "Space not found",
                }
            
            return {
                "success": True,
                "space_id": space_id,
                "announcement": announcement,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/events/spaces/{space_id}/reminder",
        summary="Generate Space reminder tweet",
        tags=["Events"],
    )
    def generate_space_reminder(
        space_id: str,
        minutes_until: int = 30,
    ) -> dict:
        """Generate a reminder tweet for an upcoming Space."""
        try:
            from .events import get_spaces_manager
            
            manager = get_spaces_manager()
            reminder = manager.generate_reminder(space_id, minutes_until)
            
            return {
                "success": True,
                "space_id": space_id,
                "reminder": reminder,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/events/spaces/upcoming",
        summary="Get upcoming Twitter Spaces",
        tags=["Events"],
    )
    def get_upcoming_spaces() -> dict:
        """Get all upcoming planned Spaces."""
        try:
            from .events import get_spaces_manager
            
            manager = get_spaces_manager()
            upcoming = manager.get_upcoming_spaces()
            
            return {
                "success": True,
                "upcoming": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "type": s.space_type.value,
                        "scheduled_time": s.scheduled_time.isoformat(),
                        "status": s.status.value,
                    }
                    for s in upcoming
                ],
                "count": len(upcoming),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/events/spaces/suggestions",
        summary="Get Space ideas",
        tags=["Events"],
    )
    def get_space_suggestions(count: int = 3) -> dict:
        """Get suggestions for Twitter Space topics."""
        try:
            from .events import get_spaces_manager
            
            manager = get_spaces_manager()
            suggestions = manager.suggest_space_ideas(count)
            
            return {
                "success": True,
                "suggestions": suggestions,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    # --- Digital Concert Endpoints ---
    
    @app.post(
        "/events/concerts/create",
        summary="Create a digital concert/listening party",
        tags=["Events"],
    )
    def create_digital_concert(
        title: str = Body(..., embed=True),
        event_type: str = Body("listening_party", embed=True),
        scheduled_time: str = Body(..., embed=True),
        description: Optional[str] = Body(None, embed=True),
        duration_minutes: int = Body(60, embed=True),
        featured_tracks: Optional[List[str]] = Body(None, embed=True),
        special_guests: Optional[List[str]] = Body(None, embed=True),
    ) -> dict:
        """Create a new digital concert or listening party event."""
        try:
            from .events import get_concert_manager
            from datetime import datetime
            
            manager = get_concert_manager()
            scheduled = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            
            event = manager.create_event(
                title=title,
                event_type=event_type,
                scheduled_time=scheduled,
                description=description,
                duration_minutes=duration_minutes,
                featured_tracks=featured_tracks,
                special_guests=special_guests,
            )
            
            return {
                "success": True,
                "event_id": event.id,
                "title": event.title,
                "type": event.event_type.value,
                "hashtag": event.hashtag,
                "scheduled_time": event.scheduled_time.isoformat(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/events/concerts/{event_id}/promo-thread",
        summary="Generate promotional tweet thread",
        tags=["Events"],
    )
    def generate_promo_thread(event_id: str) -> dict:
        """Generate a promotional tweet thread for an event."""
        try:
            from .events import get_concert_manager
            
            manager = get_concert_manager()
            thread = manager.generate_promo_thread(event_id)
            
            if not thread:
                return {
                    "success": False,
                    "error": "Event not found",
                }
            
            return {
                "success": True,
                "event_id": event_id,
                "thread": thread,
                "tweet_count": len(thread),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/events/concerts/{event_id}/countdown",
        summary="Get countdown posts for event",
        tags=["Events"],
    )
    def get_countdown_posts(event_id: str) -> dict:
        """Get countdown posts for different timeframes before event."""
        try:
            from .events import get_concert_manager
            
            manager = get_concert_manager()
            posts = manager.generate_countdown_posts(event_id)
            
            return {
                "success": True,
                "event_id": event_id,
                "countdown_posts": posts,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/events/concerts/upcoming",
        summary="Get upcoming digital events",
        tags=["Events"],
    )
    def get_upcoming_concerts() -> dict:
        """Get all upcoming digital events."""
        try:
            from .events import get_concert_manager
            
            manager = get_concert_manager()
            upcoming = manager.get_upcoming_events()
            
            return {
                "success": True,
                "upcoming": [
                    {
                        "id": e.id,
                        "title": e.title,
                        "type": e.event_type.value,
                        "hashtag": e.hashtag,
                        "scheduled_time": e.scheduled_time.isoformat(),
                        "status": e.status.value,
                    }
                    for e in upcoming
                ],
                "count": len(upcoming),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    # --- Q&A Session Endpoints ---
    
    @app.post(
        "/events/qa/create",
        summary="Create a Q&A session",
        tags=["Events"],
    )
    def create_qa_session(
        title: str = Body(..., embed=True),
        scheduled_time: str = Body(..., embed=True),
        description: Optional[str] = Body(None, embed=True),
        duration_minutes: int = Body(45, embed=True),
        custom_hashtag: Optional[str] = Body(None, embed=True),
    ) -> dict:
        """Create a new Q&A session."""
        try:
            from .events import get_qa_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            from datetime import datetime
            
            personality = PapitoPersonalityEngine()
            manager = get_qa_manager(personality)
            scheduled = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            
            session = manager.create_session(
                title=title,
                scheduled_time=scheduled,
                description=description,
                duration_minutes=duration_minutes,
                custom_hashtag=custom_hashtag,
            )
            
            return {
                "success": True,
                "session_id": session.id,
                "title": session.title,
                "hashtag": session.hashtag,
                "scheduled_time": session.scheduled_time.isoformat(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/events/qa/{session_id}/submit-question",
        summary="Submit a question to Q&A session",
        tags=["Events"],
    )
    def submit_qa_question(
        session_id: str,
        text: str = Body(..., embed=True),
        author_username: str = Body(..., embed=True),
        author_name: str = Body(..., embed=True),
    ) -> dict:
        """Submit a question to a Q&A session."""
        try:
            from .events import get_qa_manager
            
            manager = get_qa_manager()
            question = manager.submit_question(
                session_id=session_id,
                text=text,
                author_username=author_username,
                author_name=author_name,
            )
            
            if not question:
                return {
                    "success": False,
                    "error": "Session not found or max questions reached",
                }
            
            return {
                "success": True,
                "question_id": question.id,
                "text": question.text,
                "score": question.score,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/events/qa/{session_id}/answer/{question_id}",
        summary="Generate answer for a question",
        tags=["Events"],
    )
    async def answer_qa_question(session_id: str, question_id: str) -> dict:
        """Generate an AI-powered answer for a submitted question."""
        try:
            from .events import get_qa_manager
            from .engines.ai_personality import PapitoPersonalityEngine
            
            personality = PapitoPersonalityEngine()
            manager = get_qa_manager(personality)
            
            answer = manager.answer_question(session_id, question_id)
            
            if not answer:
                return {
                    "success": False,
                    "error": "Question not found",
                }
            
            return {
                "success": True,
                "question_id": question_id,
                "answer": answer,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/events/qa/{session_id}/questions",
        summary="Get prioritized questions",
        tags=["Events"],
    )
    def get_qa_questions(session_id: str, limit: int = 10) -> dict:
        """Get prioritized questions for a Q&A session."""
        try:
            from .events import get_qa_manager
            
            manager = get_qa_manager()
            questions = manager.get_prioritized_questions(session_id, limit)
            
            return {
                "success": True,
                "questions": [
                    {
                        "id": q.id,
                        "text": q.text,
                        "author": f"@{q.author_username}",
                        "score": q.score,
                        "status": q.status.value,
                    }
                    for q in questions
                ],
                "count": len(questions),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.post(
        "/events/qa/{session_id}/generate-thread",
        summary="Generate Q&A answer thread",
        tags=["Events"],
    )
    def generate_qa_thread(session_id: str, limit: int = 10) -> dict:
        """Generate a tweet thread of answered questions."""
        try:
            from .events import get_qa_manager
            
            manager = get_qa_manager()
            thread = manager.generate_answer_thread(session_id, limit)
            
            return {
                "success": True,
                "thread": thread,
                "tweet_count": len(thread),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @app.get(
        "/events/qa/active",
        summary="Get active Q&A sessions",
        tags=["Events"],
    )
    def get_active_qa_sessions() -> dict:
        """Get all active Q&A sessions."""
        try:
            from .events import get_qa_manager
            
            manager = get_qa_manager()
            active = manager.get_active_sessions()
            
            return {
                "success": True,
                "active": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "hashtag": s.hashtag,
                        "status": s.status.value,
                        "questions_count": len(s.questions),
                        "answered_count": len(s.answered_questions),
                    }
                    for s in active
                ],
                "count": len(active),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
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
