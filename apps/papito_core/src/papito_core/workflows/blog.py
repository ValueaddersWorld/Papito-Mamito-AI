"""Blog workflow implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent

from ..engines import StubTextGenerator, TextGenerator
from ..generation import create_text_generator
from ..models import BlogBrief, BlogDraft, BrandVoice, DEFAULT_VOICE
from ..prompts import build_blog_prompt


@dataclass
class BlogWorkflow:
    """Generate Papito-styled blog entries."""

    generator: TextGenerator = field(default_factory=create_text_generator)
    voice: BrandVoice = field(default_factory=lambda: DEFAULT_VOICE.model_copy(deep=True))

    def generate(self, brief: BlogBrief) -> BlogDraft:
        """Generate a draft blog post from a brief."""

        prompt = build_blog_prompt(brief, voice=self.voice)
        raw_text = self.generator(prompt)
        if isinstance(self.generator, StubTextGenerator):
            raw_text = self._render_stub(brief)
        return BlogDraft(title=brief.title, body=raw_text)

    def _render_stub(self, brief: BlogBrief) -> str:
        """Deterministic blog body used when the stub generator is active."""

        focus_line = (
            f"for {brief.focus_track}"
            if brief.focus_track
            else "for the next wave of abundance"
        )
        paragraphs = [
            f"Blessings family - today we breathe in gratitude as we move with {brief.gratitude_theme.lower()}.",
            (
                "In the studio we layered percussion over warm horns, shaping the groove "
                f"{focus_line}. Every rhythm is a prayer, every melody a roadmap to joy."
            ),
            (
                f"Lesson of the day: {brief.empowerment_lesson}. "
                "Value beats vanity every time, and when we honour our roots we unlock futures."
            ),
            (
                f"Fan spotlight: {brief.unity_message}. "
                "Your messages, your dances, your stories keep Papito pulsing with purpose."
            ),
            dedent(
                f"""
                Call to unity: {brief.call_to_action}

                We close with gratitude: value over vanity, always. \
                Rise with me and pass the blessing forward.
                """
            ).strip(),
        ]
        return "\n\n".join(paragraphs)
