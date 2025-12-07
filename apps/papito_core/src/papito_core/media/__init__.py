"""Media module for Papito Mamito.

Handles:
- Images (via NanoBanana / Imagen)
- Videos (via Veo 3)
- Interview management
- Press releases
- Collaboration management
"""

from .generator import (
    MediaType,
    MediaAsset,
    ImageGenerator,
    VideoGenerator,
    MediaOrchestrator,
)

from .interview_system import (
    InterviewSystem,
    InterviewRequest,
    InterviewStatus,
    InterviewType,
    get_interview_system,
    STANDARD_QUESTIONS,
)

from .press_release import (
    PressReleaseGenerator,
    PressReleaseType,
    get_press_generator,
)

from .collab_manager import (
    CollaborationManager,
    CollabRequest,
    CollabStatus,
    CollabType,
    Collaborator,
    get_collab_manager,
)

__all__ = [
    # Media generation
    "MediaType",
    "MediaAsset",
    "ImageGenerator",
    "VideoGenerator",
    "MediaOrchestrator",
    # Interview system
    "InterviewSystem",
    "InterviewRequest",
    "InterviewStatus",
    "InterviewType",
    "get_interview_system",
    "STANDARD_QUESTIONS",
    # Press releases
    "PressReleaseGenerator",
    "PressReleaseType",
    "get_press_generator",
    # Collaboration
    "CollaborationManager",
    "CollabRequest",
    "CollabStatus",
    "CollabType",
    "Collaborator",
    "get_collab_manager",
]

