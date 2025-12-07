"""Events Module for Papito AI.

This module provides tools for virtual events including:
- Twitter Spaces management
- Digital concerts and listening parties
- Live Q&A sessions
"""

from .spaces_manager import (
    SpacesManager,
    SpaceType,
    SpaceStatus,
    ScheduledSpace,
    get_spaces_manager,
    SPACE_FORMATS,
)

from .digital_concert import (
    DigitalConcertManager,
    DigitalEvent,
    EventType,
    EventStatus,
    get_concert_manager,
    EVENT_TEMPLATES,
)

from .qa_session import (
    QASessionManager,
    QASession,
    Question,
    QuestionStatus,
    SessionStatus,
    get_qa_manager,
)

__all__ = [
    # Spaces
    "SpacesManager",
    "SpaceType",
    "SpaceStatus",
    "ScheduledSpace",
    "get_spaces_manager",
    "SPACE_FORMATS",
    # Digital Concerts
    "DigitalConcertManager",
    "DigitalEvent",
    "EventType",
    "EventStatus", 
    "get_concert_manager",
    "EVENT_TEMPLATES",
    # Q&A Sessions
    "QASessionManager",
    "QASession",
    "Question",
    "QuestionStatus",
    "SessionStatus",
    "get_qa_manager",
]
