"""Prompt templates for Papito Mamito."""

from .blog import build_blog_prompt
from .music import build_audio_prompt, build_song_prompt

__all__ = ["build_blog_prompt", "build_song_prompt", "build_audio_prompt"]
