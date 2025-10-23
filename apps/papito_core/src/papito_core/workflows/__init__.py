"""Workflow entry points."""

from .blog import BlogWorkflow
from .music import MusicWorkflow
from .release import ReleaseWorkflow

__all__ = ["BlogWorkflow", "MusicWorkflow", "ReleaseWorkflow"]
