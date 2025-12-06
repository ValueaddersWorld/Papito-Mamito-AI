"""Autonomous media generation for Papito Mamito.

Integrates with:
- NanoBanana (image generation)
- Google Veo 3 (video generation)
- Custom prompt engineering for Afrobeat aesthetics
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import random

try:
    import httpx
except ImportError:
    httpx = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


logger = logging.getLogger("papito.media")


class MediaType(str, Enum):
    """Types of media assets."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO_VISUAL = "audio_visual"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


@dataclass
class MediaAsset:
    """A generated media asset."""
    id: str
    media_type: MediaType
    url: str
    local_path: Optional[str] = None
    prompt: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    width: int = 1080
    height: int = 1080
    duration_seconds: Optional[float] = None  # For video
    format: str = "png"
    
    # Context
    content_type: str = ""  # morning_blessing, track_snippet, etc.
    hashtags: List[str] = field(default_factory=list)
    caption: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "media_type": self.media_type.value,
            "url": self.url,
            "local_path": self.local_path,
            "prompt": self.prompt,
            "created_at": self.created_at.isoformat(),
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "content_type": self.content_type,
        }


class PapitoVisualStyle:
    """Papito's signature visual aesthetics.
    
    Maintains consistent brand identity across all generated media.
    """
    
    # Core color palette (Afrobeat + Value Adders)
    COLORS = {
        "gold": "#FFD700",
        "deep_purple": "#4A0080",
        "orange": "#FF6B00",
        "teal": "#00CED1",
        "black": "#0A0A0A",
        "white": "#FAFAFA",
    }
    
    # Visual themes by content type
    THEMES = {
        "morning_blessing": {
            "mood": "sunrise, warm golden light, hopeful, spiritual",
            "elements": "rising sun, African patterns, silhouettes, rays of light",
            "colors": "gold, orange, warm yellows, soft pinks",
        },
        "music_wisdom": {
            "mood": "contemplative, wise, deep, mystical",
            "elements": "musical notes, ancestral patterns, cosmic elements, vinyl records",
            "colors": "deep purple, gold, cosmic blues, starlight",
        },
        "track_snippet": {
            "mood": "energetic, vibrant, rhythmic, celebratory",
            "elements": "sound waves, dancing figures, Afrobeat instruments, stage lights",
            "colors": "electric orange, neon teal, vibrant purple",
        },
        "behind_the_scenes": {
            "mood": "creative, authentic, intimate, innovative",
            "elements": "studio equipment, waveforms, AI circuits, mixing boards",
            "colors": "warm amber, tech blue, studio greens",
        },
        "fan_appreciation": {
            "mood": "celebratory, grateful, inclusive, joyful",
            "elements": "diverse hands raised, hearts, community circles, unity symbols",
            "colors": "rainbow accents, gold, warm community colors",
        },
        "album_promo": {
            "mood": "epic, cinematic, anticipation, grandeur",
            "elements": "album artwork style, January 2026, countdown, musical journey",
            "colors": "rich gold, deep royal purple, premium black",
        },
    }
    
    # Papito's signature elements
    SIGNATURE_ELEMENTS = [
        "Nigerian Adire patterns",
        "Ghanaian Kente cloth motifs",
        "Afrofuturistic elements",
        "Glowing musical notes",
        "Value Adders logo subtly incorporated",
        "AI neural network aesthetics blended with African art",
    ]
    
    @classmethod
    def get_style_prompt(cls, content_type: str) -> str:
        """Generate style description for a content type."""
        theme = cls.THEMES.get(content_type, cls.THEMES["music_wisdom"])
        
        signature = random.choice(cls.SIGNATURE_ELEMENTS)
        
        return (
            f"Style: {theme['mood']}. "
            f"Visual elements: {theme['elements']}. "
            f"Color palette: {theme['colors']}. "
            f"Incorporate {signature}. "
            f"Premium quality, Instagram-worthy, 4K resolution aesthetic. "
            f"Blend Afrofuturism with cutting-edge AI art style."
        )


class ImageGenerator:
    """Generates images using NanoBanana or Google Imagen.
    
    Produces visuals that match Papito's brand and content context.
    """
    
    # Image dimensions for different platforms
    DIMENSIONS = {
        "instagram_square": (1080, 1080),
        "instagram_portrait": (1080, 1350),
        "instagram_story": (1080, 1920),
        "twitter": (1200, 675),
        "tiktok_cover": (1080, 1920),
    }
    
    def __init__(
        self,
        nanobanana_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        output_dir: str = "content/media/images",
    ):
        """Initialize image generator.
        
        Args:
            nanobanana_api_key: NanoBanana API key
            google_api_key: Google AI API key for Imagen
            output_dir: Directory to save generated images
        """
        self.nanobanana_key = nanobanana_api_key or os.getenv("NANOBANANA_API_KEY")
        self.google_key = google_api_key or os.getenv("GOOGLE_AI_API_KEY")
        self.output_dir = output_dir
        
        # Initialize Google Imagen client if available
        self._imagen_client = None
        if self.google_key and genai:
            self._imagen_client = genai.Client(api_key=self.google_key)
        
        os.makedirs(output_dir, exist_ok=True)
    
    def _build_prompt(
        self,
        content_type: str,
        caption: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a detailed image generation prompt.
        
        Args:
            content_type: Type of content (morning_blessing, etc.)
            caption: The post caption for context
            context: Additional context (album info, trending topics, etc.)
            
        Returns:
            Detailed prompt for image generation
        """
        style = PapitoVisualStyle.get_style_prompt(content_type)
        
        # Extract key themes from caption
        caption_essence = caption[:200] if len(caption) > 200 else caption
        
        # Album context for January 2026 release
        album_context = ""
        if context and context.get("include_album"):
            album_context = (
                "Subtly reference the upcoming album releasing January 2026. "
                "Include anticipation and countdown energy. "
            )
        
        # Current date context
        date_context = datetime.now().strftime("%B %Y")
        
        prompt = (
            f"Create a stunning visual for Papito Mamito, the Autonomous Afrobeat AI Artist. "
            f"Content type: {content_type}. "
            f"Essence: {caption_essence}. "
            f"{album_context}"
            f"Current period: {date_context}. "
            f"{style} "
            f"Do NOT include any text or words in the image. "
            f"Photorealistic quality mixed with artistic Afrofuturistic elements."
        )
        
        return prompt
    
    async def generate(
        self,
        content_type: str,
        caption: str,
        platform: str = "instagram_square",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[MediaAsset]:
        """Generate an image for a post.
        
        Args:
            content_type: Type of content
            caption: Post caption for context
            platform: Target platform for dimensions
            context: Additional generation context
            
        Returns:
            MediaAsset or None if generation fails
        """
        prompt = self._build_prompt(content_type, caption, context)
        width, height = self.DIMENSIONS.get(platform, (1080, 1080))
        
        # Try Google Imagen first
        if self._imagen_client:
            return await self._generate_imagen(prompt, width, height, content_type)
        
        # Fall back to NanoBanana
        if self.nanobanana_key:
            return await self._generate_nanobanana(prompt, width, height, content_type)
        
        # No API available - return placeholder
        logger.warning("No image generation API configured")
        return self._create_placeholder(prompt, content_type)
    
    async def _generate_imagen(
        self,
        prompt: str,
        width: int,
        height: int,
        content_type: str,
    ) -> Optional[MediaAsset]:
        """Generate using Google Imagen."""
        try:
            # Use Imagen 3
            response = self._imagen_client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1" if width == height else "16:9",
                    safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                )
            )
            
            if response.generated_images:
                image_data = response.generated_images[0].image.image_bytes
                
                # Save to file
                asset_id = f"papito_{content_type}_{uuid.uuid4().hex[:8]}"
                filename = f"{asset_id}.png"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(image_data)
                
                return MediaAsset(
                    id=asset_id,
                    media_type=MediaType.IMAGE,
                    url=filepath,
                    local_path=filepath,
                    prompt=prompt,
                    width=width,
                    height=height,
                    content_type=content_type,
                    format="png",
                )
                
        except Exception as e:
            logger.error(f"Imagen generation failed: {e}")
        
        return None
    
    async def _generate_nanobanana(
        self,
        prompt: str,
        width: int,
        height: int,
        content_type: str,
    ) -> Optional[MediaAsset]:
        """Generate using NanoBanana API."""
        if not httpx:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.nanobanana.ai/v1/generate",
                    headers={
                        "Authorization": f"Bearer {self.nanobanana_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "num_images": 1,
                        "style": "afrofuturistic",
                    },
                    timeout=120.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    image_url = data.get("images", [{}])[0].get("url", "")
                    
                    if image_url:
                        # Download and save
                        asset_id = f"papito_{content_type}_{uuid.uuid4().hex[:8]}"
                        filename = f"{asset_id}.png"
                        filepath = os.path.join(self.output_dir, filename)
                        
                        img_response = await client.get(image_url)
                        with open(filepath, "wb") as f:
                            f.write(img_response.content)
                        
                        return MediaAsset(
                            id=asset_id,
                            media_type=MediaType.IMAGE,
                            url=image_url,
                            local_path=filepath,
                            prompt=prompt,
                            width=width,
                            height=height,
                            content_type=content_type,
                            format="png",
                        )
                        
        except Exception as e:
            logger.error(f"NanoBanana generation failed: {e}")
        
        return None
    
    def _create_placeholder(self, prompt: str, content_type: str) -> MediaAsset:
        """Create a placeholder asset when no API is available."""
        asset_id = f"placeholder_{content_type}_{uuid.uuid4().hex[:8]}"
        return MediaAsset(
            id=asset_id,
            media_type=MediaType.IMAGE,
            url="https://placehold.co/1080x1080/FFD700/0A0A0A?text=Papito+Mamito",
            prompt=prompt,
            content_type=content_type,
        )


class VideoGenerator:
    """Generates videos using Google Veo 3.
    
    Creates short-form video content for Reels, Stories, TikTok.
    """
    
    # Video durations
    DURATIONS = {
        "story": 15,
        "reel_short": 30,
        "reel_medium": 60,
        "tiktok": 60,
        "promo": 30,
    }
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        output_dir: str = "content/media/videos",
    ):
        """Initialize video generator.
        
        Args:
            google_api_key: Google AI API key for Veo
            output_dir: Directory to save generated videos
        """
        self.google_key = google_api_key or os.getenv("GOOGLE_AI_API_KEY")
        self.output_dir = output_dir
        
        self._veo_client = None
        if self.google_key and genai:
            self._veo_client = genai.Client(api_key=self.google_key)
        
        os.makedirs(output_dir, exist_ok=True)
    
    def _build_video_prompt(
        self,
        content_type: str,
        caption: str,
        duration: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a video generation prompt."""
        style = PapitoVisualStyle.get_style_prompt(content_type)
        
        video_motion = {
            "morning_blessing": "Slow, ethereal sunrise movement. Particles of light floating upward.",
            "music_wisdom": "Smooth camera pan across cosmic musical landscape. Stars pulsing to rhythm.",
            "track_snippet": "Dynamic, energetic movement. Audio waveforms dancing. Quick cuts.",
            "behind_the_scenes": "Intimate studio shots. Close-ups of production. Time-lapse creation.",
            "fan_appreciation": "Montage of diverse faces. Community energy. Celebration movement.",
            "album_promo": "Epic cinematic reveal. Countdown energy. Building anticipation.",
        }
        
        motion = video_motion.get(content_type, "Smooth, cinematic movement")
        
        prompt = (
            f"Create a {duration}-second video for Papito Mamito, Autonomous Afrobeat AI Artist. "
            f"Content: {content_type}. "
            f"Motion: {motion}. "
            f"{style} "
            f"No text overlays. Premium music video aesthetic. "
            f"Afrofuturistic visuals with rhythmic motion that suggests music."
        )
        
        return prompt
    
    async def generate(
        self,
        content_type: str,
        caption: str,
        video_type: str = "reel_short",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[MediaAsset]:
        """Generate a video.
        
        Args:
            content_type: Type of content
            caption: Caption for context
            video_type: Type of video (story, reel_short, etc.)
            context: Additional generation context
            
        Returns:
            MediaAsset or None
        """
        duration = self.DURATIONS.get(video_type, 30)
        prompt = self._build_video_prompt(content_type, caption, duration, context)
        
        if self._veo_client:
            return await self._generate_veo(prompt, duration, content_type)
        
        logger.warning("No video generation API configured")
        return None
    
    async def _generate_veo(
        self,
        prompt: str,
        duration: int,
        content_type: str,
    ) -> Optional[MediaAsset]:
        """Generate using Google Veo 3."""
        try:
            # Generate video with Veo
            operation = self._veo_client.models.generate_videos(
                model="veo-2.0-generate-001",  # or veo-3 when available
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",  # Vertical for Reels/Stories
                    number_of_videos=1,
                    duration_seconds=min(duration, 8),  # Veo limit
                    person_generation="DONT_ALLOW",
                )
            )
            
            # Wait for completion
            while not operation.done:
                import asyncio
                await asyncio.sleep(5)
                operation = self._veo_client.operations.get(operation)
            
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                
                # Save video
                asset_id = f"papito_video_{content_type}_{uuid.uuid4().hex[:8]}"
                filename = f"{asset_id}.mp4"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(video.video.video_bytes)
                
                return MediaAsset(
                    id=asset_id,
                    media_type=MediaType.VIDEO,
                    url=filepath,
                    local_path=filepath,
                    prompt=prompt,
                    width=1080,
                    height=1920,
                    duration_seconds=duration,
                    content_type=content_type,
                    format="mp4",
                )
                
        except Exception as e:
            logger.error(f"Veo generation failed: {e}")
        
        return None


class MediaOrchestrator:
    """Orchestrates media generation for Papito's posts.
    
    Decides what type of media to create based on:
    - Content type
    - Platform requirements
    - Recent content variety
    - Album promotion schedule
    """
    
    # Content type to media mapping
    MEDIA_PREFERENCES = {
        "morning_blessing": [MediaType.IMAGE, MediaType.VIDEO],
        "music_wisdom": [MediaType.IMAGE],
        "track_snippet": [MediaType.VIDEO, MediaType.REEL],
        "behind_the_scenes": [MediaType.VIDEO, MediaType.IMAGE],
        "fan_appreciation": [MediaType.IMAGE, MediaType.CAROUSEL],
        "album_promo": [MediaType.VIDEO, MediaType.IMAGE],
    }
    
    def __init__(
        self,
        image_generator: Optional[ImageGenerator] = None,
        video_generator: Optional[VideoGenerator] = None,
    ):
        """Initialize media orchestrator."""
        self.image_gen = image_generator or ImageGenerator()
        self.video_gen = video_generator or VideoGenerator()
        
        self._recent_media_types: List[MediaType] = []
    
    def _should_include_album_context(self) -> bool:
        """Determine if album context should be included.
        
        January 2026 album release - increase mentions as we get closer.
        """
        now = datetime.now()
        
        # Album releases January 2026
        release_year = 2026
        release_month = 1
        
        # Calculate months until release
        months_until = (release_year - now.year) * 12 + (release_month - now.month)
        
        # Include album context more frequently as release approaches
        if months_until <= 1:
            return True  # Always include in release month
        elif months_until <= 3:
            return random.random() < 0.7  # 70% chance
        elif months_until <= 6:
            return random.random() < 0.4  # 40% chance
        else:
            return random.random() < 0.2  # 20% chance
    
    async def create_media_for_post(
        self,
        content_type: str,
        caption: str,
        platform: str = "instagram",
        prefer_video: bool = False,
    ) -> Optional[MediaAsset]:
        """Create appropriate media for a post.
        
        Args:
            content_type: Type of content
            caption: Post caption
            platform: Target platform
            prefer_video: Whether to prefer video over image
            
        Returns:
            Generated MediaAsset or None
        """
        context = {
            "include_album": self._should_include_album_context(),
            "platform": platform,
        }
        
        # Determine media type
        preferences = self.MEDIA_PREFERENCES.get(
            content_type, 
            [MediaType.IMAGE]
        )
        
        # Add variety - don't repeat same type too often
        if len(self._recent_media_types) >= 3:
            last_three = self._recent_media_types[-3:]
            if all(t == preferences[0] for t in last_three):
                # Switch to alternate type
                if len(preferences) > 1:
                    preferences = preferences[1:]
        
        # Video preference
        if prefer_video and MediaType.VIDEO in preferences:
            preferences = [MediaType.VIDEO] + [p for p in preferences if p != MediaType.VIDEO]
        
        # Generate based on preference
        asset = None
        for media_type in preferences:
            if media_type in (MediaType.VIDEO, MediaType.REEL):
                asset = await self.video_gen.generate(
                    content_type, caption, "reel_short", context
                )
            else:
                platform_format = "instagram_square"
                if platform == "story":
                    platform_format = "instagram_story"
                elif platform == "twitter":
                    platform_format = "twitter"
                
                asset = await self.image_gen.generate(
                    content_type, caption, platform_format, context
                )
            
            if asset:
                self._recent_media_types.append(asset.media_type)
                if len(self._recent_media_types) > 10:
                    self._recent_media_types.pop(0)
                break
        
        return asset
