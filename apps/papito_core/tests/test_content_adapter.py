"""Unit tests for the content adapter."""

from __future__ import annotations

import pytest


class TestInstagramContent:
    """Tests for InstagramContent dataclass."""
    
    def test_instagram_content_creation(self):
        """Test creating InstagramContent."""
        from papito_core.content.content_adapter import InstagramContent
        
        content = InstagramContent(
            caption="Test caption",
            hashtags=["test", "papito"],
            media_urls=["https://example.com/image.jpg"],
        )
        
        assert content.caption == "Test caption"
        assert len(content.hashtags) == 2
        assert content.is_carousel is False
    
    def test_get_full_caption_with_hashtags(self):
        """Test caption generation with hashtags."""
        from papito_core.content.content_adapter import InstagramContent
        
        content = InstagramContent(
            caption="Hello world!",
            hashtags=["PapitoMamito", "Afrobeat"],
        )
        
        full = content.get_full_caption()
        
        assert "Hello world!" in full
        assert "#PapitoMamito" in full
        assert "#Afrobeat" in full
    
    def test_get_full_caption_truncation(self):
        """Test caption truncation for long content."""
        from papito_core.content.content_adapter import InstagramContent
        
        # Create a very long caption
        long_caption = "A" * 2500
        content = InstagramContent(
            caption=long_caption,
            hashtags=["test"],
        )
        
        full = content.get_full_caption(max_length=100)
        
        assert len(full) <= 100
        assert "..." in full


class TestXContent:
    """Tests for XContent dataclass."""
    
    def test_x_content_single_tweet(self):
        """Test single tweet detection."""
        from papito_core.content.content_adapter import XContent
        
        content = XContent(
            tweets=["Just one tweet!"],
            hashtags=["test"],
        )
        
        assert content.is_thread() is False
    
    def test_x_content_thread(self):
        """Test thread detection."""
        from papito_core.content.content_adapter import XContent
        
        content = XContent(
            tweets=["First tweet", "Second tweet", "Third tweet"],
            hashtags=["thread"],
        )
        
        assert content.is_thread() is True
    
    def test_get_tweets_with_numbering(self):
        """Test thread numbering."""
        from papito_core.content.content_adapter import XContent
        
        content = XContent(
            tweets=["First", "Second", "Third"],
        )
        
        numbered = content.get_tweets_with_numbering()
        
        assert "1/3" in numbered[0]
        assert "2/3" in numbered[1]
        assert "3/3" in numbered[2]


class TestContentAdapter:
    """Tests for ContentAdapter class."""
    
    def test_adapter_initialization(self):
        """Test ContentAdapter initialization."""
        from papito_core.content.content_adapter import ContentAdapter
        
        adapter = ContentAdapter()
        
        assert "PapitoMamito" in adapter.DEFAULT_HASHTAGS
        assert "ValueAdders" in adapter.DEFAULT_HASHTAGS
    
    def test_adapt_blog_to_instagram_short(self):
        """Test blog to Instagram with short content."""
        from papito_core.content.content_adapter import ContentAdapter
        
        adapter = ContentAdapter()
        result = adapter.adapt_blog_to_instagram(
            title="Test Blog",
            body="Short paragraph here.",
            mood="uplifting",
        )
        
        assert "Test Blog" in result.caption
        assert result.is_carousel is False
        assert "uplifting" in result.hashtags
    
    def test_adapt_blog_to_instagram_long(self):
        """Test blog to Instagram with long content creates carousel."""
        from papito_core.content.content_adapter import ContentAdapter
        
        adapter = ContentAdapter()
        
        # Create long content with multiple paragraphs
        body = "\n\n".join([f"Paragraph {i} with some content here." for i in range(5)])
        
        result = adapter.adapt_blog_to_instagram(
            title="Long Blog",
            body=body,
            image_urls=["img1.jpg", "img2.jpg", "img3.jpg"],
        )
        
        assert result.is_carousel is True
        assert len(result.carousel_slides) > 0
    
    def test_adapt_blog_to_x_thread(self):
        """Test blog to X thread."""
        from papito_core.content.content_adapter import ContentAdapter
        
        adapter = ContentAdapter()
        result = adapter.adapt_blog_to_x_thread(
            title="Thread Topic",
            body="Long content that should be split.\n\nAnother paragraph.\n\nAnd another.",
        )
        
        assert len(result.tweets) >= 2
        assert "PapitoMamito" in result.hashtags
    
    def test_adapt_track_to_teaser(self):
        """Test track teaser creation."""
        from papito_core.content.content_adapter import ContentAdapter
        
        adapter = ContentAdapter()
        result = adapter.adapt_track_to_teaser(
            title="New Track",
            mood="uplifting",
            theme="gratitude",
            hook_lyrics=["We rise together!"],
        )
        
        assert "instagram" in result
        assert "x" in result
        assert "tiktok" in result
        
        # Check Instagram content
        ig = result["instagram"]
        assert "New Track" in ig.caption
        assert "uplifting" in ig.caption.lower() or "Uplifting" in ig.caption
    
    def test_create_daily_blessing(self):
        """Test daily blessing creation."""
        from papito_core.content.content_adapter import ContentAdapter
        
        adapter = ContentAdapter()
        result = adapter.create_daily_blessing(theme="gratitude")
        
        assert "instagram" in result
        assert "x" in result
        
        assert "MORNING BLESSING" in result["instagram"].caption
        assert "MorningBlessing" in result["instagram"].hashtags
    
    def test_adapt_fan_shoutout(self):
        """Test fan shoutout creation."""
        from papito_core.content.content_adapter import ContentAdapter
        
        adapter = ContentAdapter()
        result = adapter.adapt_fan_shoutout(
            fan_name="TestFan",
            fan_handle="testfan",
            message="You are amazing!",
            support_type="streaming",
        )
        
        assert "instagram" in result
        assert "@testfan" in result["instagram"].caption
        assert "streaming" in result["instagram"].caption
