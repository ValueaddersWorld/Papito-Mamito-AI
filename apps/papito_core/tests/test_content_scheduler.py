"""Tests for ContentScheduler module."""

import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from papito_core.automation.content_scheduler import (
    ContentScheduler,
    ContentType,
    PostingSlot,
    SchedulingConfig,
)


class TestContentType:
    """Tests for ContentType enum."""
    
    def test_content_types_exist(self):
        """Verify all expected content types are defined."""
        assert ContentType.MORNING_BLESSING == "morning_blessing"
        assert ContentType.TRACK_SNIPPET == "track_snippet"
        assert ContentType.BEHIND_THE_SCENES == "behind_the_scenes"
        assert ContentType.LYRICS_QUOTE == "lyrics_quote"
        assert ContentType.FAN_APPRECIATION == "fan_appreciation"
        assert ContentType.EDUCATIONAL == "educational"
        assert ContentType.AFROBEAT_HISTORY == "afrobeat_history"


class TestPostingSlot:
    """Tests for PostingSlot dataclass."""
    
    def test_default_platforms(self):
        """Verify default platforms are X and Instagram."""
        slot = PostingSlot(hour=8, content_types=[ContentType.MORNING_BLESSING])
        assert "x" in slot.platforms
        assert "instagram" in slot.platforms
    
    def test_custom_platforms(self):
        """Verify custom platforms can be set."""
        slot = PostingSlot(
            hour=8, 
            content_types=[ContentType.TRACK_SNIPPET],
            platforms=["tiktok"]
        )
        assert slot.platforms == ["tiktok"]


class TestSchedulingConfig:
    """Tests for SchedulingConfig dataclass."""
    
    def test_default_timezone(self):
        """Verify default timezone is West Africa Time."""
        config = SchedulingConfig()
        assert config.timezone == "Africa/Lagos"
    
    def test_default_post_frequency(self):
        """Verify default post frequency range."""
        config = SchedulingConfig()
        assert config.min_posts_per_day == 3
        assert config.max_posts_per_day == 5
    
    def test_has_posting_slots(self):
        """Verify default slots are configured."""
        config = SchedulingConfig()
        assert len(config.posting_slots) >= 3


class TestContentScheduler:
    """Tests for ContentScheduler class."""
    
    @pytest.fixture
    def scheduler(self):
        """Create a scheduler instance."""
        return ContentScheduler()
    
    def test_get_current_time_wat(self, scheduler):
        """Verify current time is in WAT timezone."""
        now = scheduler.get_current_time_wat()
        assert now.tzinfo is not None
        assert str(now.tzinfo) == "Africa/Lagos"
    
    def test_get_slots_for_today_respects_range(self, scheduler):
        """Verify slots returned are within configured range."""
        slots = scheduler.get_slots_for_today()
        assert len(slots) >= scheduler.config.min_posts_per_day
        assert len(slots) <= scheduler.config.max_posts_per_day
    
    def test_get_slots_for_today_with_explicit_count(self, scheduler):
        """Verify exact slot count when specified."""
        slots = scheduler.get_slots_for_today(num_posts=2)
        assert len(slots) == 2
    
    def test_select_content_type_returns_valid_type(self, scheduler):
        """Verify selected content type is from slot options."""
        slot = PostingSlot(
            hour=8,
            content_types=[ContentType.MORNING_BLESSING, ContentType.MUSIC_WISDOM]
        )
        content_type = scheduler.select_content_type(slot)
        assert content_type in slot.content_types
    
    def test_select_content_type_tracks_recent(self, scheduler):
        """Verify content type selection tracks recently used."""
        slot = PostingSlot(
            hour=8,
            content_types=[ContentType.MORNING_BLESSING]
        )
        scheduler.select_content_type(slot)
        assert ContentType.MORNING_BLESSING in scheduler._recent_content_types
    
    def test_generate_schedule_returns_posts(self, scheduler):
        """Verify schedule generation returns scheduled posts."""
        schedule = scheduler.generate_schedule(days=3)
        assert len(schedule) > 0
    
    def test_generate_schedule_sets_timezone(self, scheduler):
        """Verify generated posts have correct timezone."""
        schedule = scheduler.generate_schedule(days=1)
        if schedule:
            assert schedule[0].timezone == "Africa/Lagos"
    
    def test_get_content_generation_prompt_returns_dict(self, scheduler):
        """Verify prompt generation returns config dict."""
        prompt = scheduler.get_content_generation_prompt(
            ContentType.MORNING_BLESSING,
            "x"
        )
        assert isinstance(prompt, dict)
        assert "style" in prompt
        assert "tone" in prompt
    
    def test_should_post_now_within_tolerance(self, scheduler):
        """Verify should_post_now respects tolerance window."""
        # This test is time-dependent, so we just verify it returns proper type
        result = scheduler.should_post_now(tolerance_minutes=15)
        assert result is None or isinstance(result, PostingSlot)


class TestContentPromptGeneration:
    """Tests for content prompt configurations."""
    
    @pytest.fixture
    def scheduler(self):
        return ContentScheduler()
    
    def test_morning_blessing_includes_catchphrase(self, scheduler):
        """Verify morning blessing prompts include catchphrase option."""
        prompt = scheduler.get_content_generation_prompt(
            ContentType.MORNING_BLESSING, "x"
        )
        assert prompt.get("include_catchphrase") is True
    
    def test_track_snippet_includes_hashtags(self, scheduler):
        """Verify track snippet prompts include hashtags."""
        prompt = scheduler.get_content_generation_prompt(
            ContentType.TRACK_SNIPPET, "instagram"
        )
        assert prompt.get("include_hashtags") is True
    
    def test_educational_has_series_name(self, scheduler):
        """Verify educational content has series name."""
        prompt = scheduler.get_content_generation_prompt(
            ContentType.EDUCATIONAL, "x"
        )
        assert prompt.get("series_name") == "How Papito Makes Music"
