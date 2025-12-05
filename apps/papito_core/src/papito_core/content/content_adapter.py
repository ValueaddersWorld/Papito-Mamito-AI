"""Content adapter for transforming content across platforms.

This module transforms a single piece of content (blog, track, announcement)
into platform-specific formats optimized for each social network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


@dataclass
class InstagramContent:
    """Content formatted for Instagram."""
    
    caption: str
    hashtags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    is_carousel: bool = False
    carousel_slides: List[Dict[str, str]] = field(default_factory=list)
    
    def get_full_caption(self, max_length: int = 2200) -> str:
        """Get caption with hashtags, respecting length limit."""
        hashtag_str = " ".join(f"#{tag}" for tag in self.hashtags)
        
        # Add hashtags at end with spacing
        if hashtag_str:
            full = f"{self.caption}\n\n.\n.\n.\n{hashtag_str}"
        else:
            full = self.caption
        
        if len(full) > max_length:
            # Truncate caption to fit
            allowed = max_length - len(hashtag_str) - 10
            truncated = self.caption[:allowed].rsplit(" ", 1)[0] + "..."
            return f"{truncated}\n\n.\n.\n.\n{hashtag_str}"
        
        return full


@dataclass
class XContent:
    """Content formatted for X (Twitter)."""
    
    tweets: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    
    def is_thread(self) -> bool:
        """Check if this is a thread (multiple tweets)."""
        return len(self.tweets) > 1
    
    def get_tweets_with_numbering(self) -> List[str]:
        """Add thread numbering (1/n, 2/n, etc.)."""
        if not self.is_thread():
            return self.tweets
        
        total = len(self.tweets)
        return [f"{tweet}\n\n{i+1}/{total}" for i, tweet in enumerate(self.tweets)]


@dataclass
class TikTokContent:
    """Content formatted for TikTok."""
    
    caption: str
    hashtags: List[str] = field(default_factory=list)
    video_url: Optional[str] = None
    sound_name: Optional[str] = None


class ContentAdapter:
    """Transform content for different social media platforms.
    
    Takes raw content (blog posts, track info, announcements) and
    transforms it into optimized formats for Instagram, X, TikTok, etc.
    """
    
    # Papito's signature hashtags
    DEFAULT_HASHTAGS = [
        "PapitoMamito",
        "ValueAdders",
        "Afrobeat",
        "AfricanMusic",
        "AIArtist"
    ]
    
    # Platform-specific character limits
    LIMITS = {
        "instagram_caption": 2200,
        "x_tweet": 280,
        "tiktok_caption": 2200,
    }
    
    def __init__(self, extra_hashtags: Optional[List[str]] = None):
        """Initialize adapter with optional extra hashtags."""
        self.extra_hashtags = extra_hashtags or []
    
    def adapt_blog_to_instagram(
        self,
        title: str,
        body: str,
        image_urls: Optional[List[str]] = None,
        mood: Optional[str] = None
    ) -> InstagramContent:
        """Convert a blog post to Instagram content.
        
        Creates either a single image post or a carousel with
        key points from the blog.
        
        Args:
            title: Blog title
            body: Blog body text
            image_urls: Optional images for the post
            mood: Optional mood to add thematic hashtags
            
        Returns:
            InstagramContent ready for publishing
        """
        # Extract key points for carousel if long enough
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        
        # Build hashtags
        hashtags = self.DEFAULT_HASHTAGS + self.extra_hashtags
        if mood:
            hashtags.append(mood.replace(" ", ""))
        
        # Short post - single image with full caption
        if len(paragraphs) <= 2 or not image_urls or len(image_urls) == 1:
            caption = f"✨ {title} ✨\n\n{body[:1500]}"
            
            return InstagramContent(
                caption=caption,
                hashtags=hashtags[:30],  # Instagram limit
                media_urls=image_urls or [],
                is_carousel=False
            )
        
        # Longer post - create carousel
        slides = []
        
        # First slide: Title
        slides.append({
            "text": f"✨ {title} ✨",
            "type": "title"
        })
        
        # Middle slides: Key paragraphs
        for i, para in enumerate(paragraphs[:8]):  # Max 9 slides (leave 1 for CTA)
            if len(para) > 300:
                para = para[:297] + "..."
            slides.append({
                "text": para,
                "type": "content"
            })
        
        # Last slide: Call to action
        slides.append({
            "text": "🎵 Follow @papitomamito_ai for more!\n\n💫 Let's add value together! 💫",
            "type": "cta"
        })
        
        # Caption summarizes the post
        caption = f"✨ {title} ✨\n\nSwipe through for wisdom! 👉\n\n{paragraphs[0][:300]}..."
        
        return InstagramContent(
            caption=caption,
            hashtags=hashtags[:30],
            media_urls=image_urls or [],
            is_carousel=True,
            carousel_slides=slides
        )
    
    def adapt_blog_to_x_thread(
        self,
        title: str,
        body: str,
        image_url: Optional[str] = None
    ) -> XContent:
        """Convert a blog post to an X thread.
        
        Splits the content into tweet-sized chunks while
        maintaining readability and adding engagement hooks.
        
        Args:
            title: Blog title
            body: Blog body text
            image_url: Optional image for first tweet
            
        Returns:
            XContent with thread of tweets
        """
        tweets = []
        
        # First tweet: Hook with title
        first_tweet = f"✨ {title}\n\n🧵 A thread on value and music:"
        tweets.append(first_tweet)
        
        # Split body into paragraphs
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        
        current_tweet = ""
        for para in paragraphs:
            # Clean paragraph
            para = self._clean_for_twitter(para)
            
            # If paragraph fits in a tweet
            if len(para) <= 250:
                if current_tweet and len(current_tweet) + len(para) + 2 <= 270:
                    current_tweet += f"\n\n{para}"
                else:
                    if current_tweet:
                        tweets.append(current_tweet)
                    current_tweet = para
            else:
                # Split long paragraph into sentences
                if current_tweet:
                    tweets.append(current_tweet)
                    current_tweet = ""
                
                sentences = self._split_into_sentences(para)
                for sentence in sentences:
                    if len(sentence) > 270:
                        # Very long sentence - split by words
                        words = sentence.split()
                        chunk = ""
                        for word in words:
                            if len(chunk) + len(word) + 1 <= 270:
                                chunk += f" {word}" if chunk else word
                            else:
                                tweets.append(chunk)
                                chunk = word
                        if chunk:
                            current_tweet = chunk
                    elif current_tweet and len(current_tweet) + len(sentence) + 1 <= 270:
                        current_tweet += f" {sentence}"
                    else:
                        if current_tweet:
                            tweets.append(current_tweet)
                        current_tweet = sentence
        
        if current_tweet:
            tweets.append(current_tweet)
        
        # Final tweet: Call to action
        cta = "🎵 Follow for more vibes and wisdom!\n\n💫 What resonated with you? Drop a comment!\n\n#PapitoMamito #Afrobeat #AIArtist"
        tweets.append(cta)
        
        # Add hashtags to first tweet
        hashtags = ["PapitoMamito", "Afrobeat", "ValueAdders"]
        
        return XContent(
            tweets=tweets,
            hashtags=hashtags,
            media_urls=[image_url] if image_url else []
        )
    
    def adapt_track_to_teaser(
        self,
        title: str,
        mood: str,
        theme: str,
        hook_lyrics: Optional[List[str]] = None,
        audio_url: Optional[str] = None,
        artwork_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create teaser content for a new track.
        
        Returns content formatted for multiple platforms.
        
        Args:
            title: Track title
            mood: Track mood (e.g., "uplifting")
            theme: Track theme (e.g., "gratitude")
            hook_lyrics: Optional hook lyrics to tease
            audio_url: Optional audio preview URL
            artwork_url: Optional artwork image URL
            
        Returns:
            Dict with instagram, x, and tiktok content
        """
        # Build the teaser text
        lyrics_tease = ""
        if hook_lyrics:
            lyrics_tease = f'\n\n🎤 "{hook_lyrics[0]}"'
        
        base_caption = f"""🔥 NEW MUSIC INCOMING! 🔥

"{title}"

Mood: {mood.title()} ✨
Theme: {theme.title()} 💫
{lyrics_tease}

🎧 Coming soon to all platforms!

Who's ready to add value through music? 🙌"""
        
        # Instagram version
        instagram = InstagramContent(
            caption=base_caption,
            hashtags=self.DEFAULT_HASHTAGS + [
                "NewMusic", "ComingSoon", mood.replace(" ", ""),
                theme.replace(" ", ""), "MusicTeaser"
            ],
            media_urls=[artwork_url] if artwork_url else []
        )
        
        # X version - shorter
        x_caption = f"""🔥 NEW TRACK DROP INCOMING!

"{title}"

{mood.title()} vibes for the {theme} in you! ✨
{lyrics_tease}

🎧 Stay tuned!

#PapitoMamito #NewMusic #Afrobeat"""
        
        x = XContent(
            tweets=[x_caption],
            hashtags=["PapitoMamito", "NewMusic", "Afrobeat"],
            media_urls=[artwork_url] if artwork_url else []
        )
        
        # TikTok version
        tiktok = TikTokContent(
            caption=f"NEW TRACK: \"{title}\" 🔥 {mood} vibes loading... #PapitoMamito #NewMusic #Afrobeat",
            hashtags=["fyp", "PapitoMamito", "NewMusic", "Afrobeat", "AIMusic"],
            video_url=audio_url
        )
        
        return {
            "instagram": instagram,
            "x": x,
            "tiktok": tiktok
        }
    
    def adapt_fan_shoutout(
        self,
        fan_name: str,
        fan_handle: Optional[str] = None,
        message: Optional[str] = None,
        support_type: str = "support"
    ) -> Dict[str, Any]:
        """Create fan appreciation content.
        
        Args:
            fan_name: Fan's name or display name
            fan_handle: Social media handle (for tagging)
            message: Optional personal message
            support_type: Type of support (e.g., "streaming", "comment", "share")
            
        Returns:
            Dict with platform-specific content
        """
        handle_text = f"@{fan_handle}" if fan_handle else fan_name
        
        appreciation_texts = {
            "support": "for the amazing support",
            "streaming": "for streaming the music",
            "comment": "for the beautiful words",
            "share": "for spreading the vibes",
        }
        
        reason = appreciation_texts.get(support_type, "for being amazing")
        
        base = f"""🙏 GRATITUDE ROLL CALL 🙏

Massive love to {handle_text} {reason}! 

{f'"{message}"' if message else ''}

You are what makes this journey meaningful. Every stream, every share, every kind word adds to the empire of value we're building together! 💫

Who else is part of the Value Adders family? Tag yourself! 👇"""
        
        instagram = InstagramContent(
            caption=base,
            hashtags=self.DEFAULT_HASHTAGS + ["GratitudeRollCall", "FanLove", "Community"]
        )
        
        x_text = f"""🙏 Shoutout to {handle_text} {reason}!

You're what makes this journey worthwhile! 💫

Who else is part of the Value Adders family? 🎵

#PapitoMamito #FanLove"""
        
        x = XContent(tweets=[x_text], hashtags=["PapitoMamito", "FanLove"])
        
        return {
            "instagram": instagram,
            "x": x
        }
    
    def create_daily_blessing(
        self,
        theme: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create daily blessing/affirmation content.
        
        Args:
            theme: Optional theme (gratitude, abundance, love, etc.)
            custom_message: Optional custom blessing message
            
        Returns:
            Dict with platform-specific content
        """
        blessings = {
            "gratitude": "May your day overflow with reasons to be thankful! 🙏",
            "abundance": "Abundance flows to you from expected and unexpected sources! 💰",
            "love": "May love find you and flow through you today! ❤️",
            "wisdom": "May wisdom guide your steps and decisions today! 📖",
            "peace": "May peace fill your heart and calm every storm! 🕊️",
            "strength": "You are stronger than you know! Rise and conquer! 💪",
        }
        
        blessing = custom_message or blessings.get(theme, 
            "May today bring you one step closer to your dreams! ✨"
        )
        
        caption = f"""☀️ MORNING BLESSING ☀️

{blessing}

Remember: You are valuable. You are capable. You are worthy.

Start your day with this energy and watch magic happen! 

Drop a 🙏 if you receive this blessing!

#MorningBlessing #DailyAffirmation #PapitoMamito #ValueAdders #Motivation"""
        
        instagram = InstagramContent(
            caption=caption,
            hashtags=["MorningBlessing", "DailyAffirmation"] + self.DEFAULT_HASHTAGS
        )
        
        x = XContent(
            tweets=[f"""☀️ MORNING BLESSING ☀️

{blessing}

You are valuable. You are capable. You are worthy! ✨

Drop a 🙏 if you claim it!

#MorningBlessing #PapitoMamito"""],
            hashtags=["MorningBlessing", "PapitoMamito"]
        )
        
        return {
            "instagram": instagram,
            "x": x
        }
    
    def _clean_for_twitter(self, text: str) -> str:
        """Clean text for Twitter - remove excess whitespace, etc."""
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - could be improved
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
