"""Unit tests for the AI responder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest


class TestSentiment:
    """Tests for Sentiment enum."""
    
    def test_sentiment_values(self):
        """Test Sentiment enum has expected values."""
        from papito_core.content.ai_responder import Sentiment
        
        assert Sentiment.POSITIVE.value == "positive"
        assert Sentiment.NEGATIVE.value == "negative"
        assert Sentiment.NEUTRAL.value == "neutral"
        assert Sentiment.QUESTION.value == "question"
        assert Sentiment.REQUEST.value == "request"


class TestResponseContext:
    """Tests for ResponseContext dataclass."""
    
    def test_create_response_context(self):
        """Test creating a ResponseContext."""
        from papito_core.content.ai_responder import ResponseContext
        
        context = ResponseContext(
            original_message="Love your music!",
            sender_name="TestFan",
            platform="instagram",
            interaction_type="comment",
        )
        
        assert context.original_message == "Love your music!"
        assert context.platform == "instagram"
        assert context.sentiment is None  # Optional


class TestGeneratedResponse:
    """Tests for GeneratedResponse dataclass."""
    
    def test_create_generated_response(self):
        """Test creating a GeneratedResponse."""
        from papito_core.content.ai_responder import GeneratedResponse, Sentiment
        
        response = GeneratedResponse(
            text="Thank you for the love!",
            confidence=0.85,
            sentiment_detected=Sentiment.POSITIVE,
        )
        
        assert response.text == "Thank you for the love!"
        assert response.confidence == 0.85
        assert response.requires_human_review is False
        assert response.alternatives == []


class TestAIResponder:
    """Tests for AIResponder class."""
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_responder_initialization(self, mock_settings):
        """Test AIResponder initialization."""
        mock_settings.return_value = MagicMock(
            openai_api_key="test-key",
            anthropic_api_key=None,
            openai_model="gpt-4o-mini",
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import AIResponder
        
        responder = AIResponder()
        
        assert responder.openai_key == "test-key"
        assert "Papito Mamito" in responder.PERSONA
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_detect_sentiment_positive(self, mock_settings):
        """Test sentiment detection for positive message."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import AIResponder, Sentiment
        
        responder = AIResponder()
        
        result = responder._detect_sentiment("Love your music! Amazing track! 🔥")
        
        assert result == Sentiment.POSITIVE
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_detect_sentiment_negative(self, mock_settings):
        """Test sentiment detection for negative message."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import AIResponder, Sentiment
        
        responder = AIResponder()
        
        result = responder._detect_sentiment("This is trash, hate it")
        
        assert result == Sentiment.NEGATIVE
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_detect_sentiment_question(self, mock_settings):
        """Test sentiment detection for question."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import AIResponder, Sentiment
        
        responder = AIResponder()
        
        result = responder._detect_sentiment("When is the next track dropping?")
        
        assert result == Sentiment.QUESTION
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_check_sensitive_money(self, mock_settings):
        """Test that generic financial terms don't trigger review (autonomous operation)."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import AIResponder
        
        responder = AIResponder()
        
        # Generic invest/money terms don't trigger review for autonomous operation
        requires_review, reason = responder._check_sensitive("Can I invest in your project?")
        
        assert requires_review is False
        assert reason is None
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_check_sensitive_collab(self, mock_settings):
        """Test that generic collab terms don't trigger review (autonomous operation)."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import AIResponder
        
        responder = AIResponder()
        
        # Generic collab terms don't trigger review for autonomous operation
        requires_review, reason = responder._check_sensitive("Let's do a collab!")
        
        assert requires_review is False
        assert reason is None
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_generate_template_response(self, mock_settings):
        """Test template response generation."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import (
            AIResponder, 
            ResponseContext, 
            Sentiment
        )
        
        responder = AIResponder()
        
        context = ResponseContext(
            original_message="Love your work!",
            sender_name="TestFan",
            platform="instagram",
            interaction_type="comment",
            sentiment=Sentiment.POSITIVE,
        )
        
        response = responder._generate_template(context)
        
        assert "TestFan" in response
        assert "🙏" in response or "✨" in response or "💫" in response
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_post_process_length(self, mock_settings):
        """Test response post-processing respects length limits."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import AIResponder
        
        responder = AIResponder()
        
        # Very long response
        long_text = "A" * 500
        result = responder._post_process(long_text, "x")  # X has 280 char limit
        
        assert len(result) <= 280
    
    @patch("papito_core.content.ai_responder.get_settings")
    def test_generate_response_full(self, mock_settings):
        """Test full response generation flow."""
        mock_settings.return_value = MagicMock(
            openai_api_key=None,  # No API key = use templates
            anthropic_api_key=None,
            openai_model=None,
            anthropic_model=None,
        )
        
        from papito_core.content.ai_responder import (
            AIResponder,
            ResponseContext,
            Sentiment,
        )
        
        responder = AIResponder()
        
        context = ResponseContext(
            original_message="Your music is amazing!",
            sender_name="Fan123",
            platform="instagram",
            interaction_type="comment",
        )
        
        result = responder.generate_response(context)
        
        assert result.text  # Has text
        assert result.confidence == 0.6  # Template confidence
        assert result.sentiment_detected == Sentiment.POSITIVE
        assert result.requires_human_review is False
