"""Content module for Papito Mamito AI."""

from .content_adapter import ContentAdapter
from .ai_responder import AIResponder
from .curated_campaign import (
    get_next_curated_post,
    mark_post_as_used,
    get_campaign_status,
    CURATED_POSTS,
)

__all__ = [
    "ContentAdapter",
    "AIResponder",
    "get_next_curated_post",
    "mark_post_as_used",
    "get_campaign_status",
    "CURATED_POSTS",
]
