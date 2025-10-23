"""Blog prompt construction."""

from __future__ import annotations

from textwrap import dedent

from ..constants import MISSION_STATEMENT, PAPITO_VALUES
from ..models import BlogBrief, BrandVoice, DEFAULT_VOICE


def build_blog_prompt(brief: BlogBrief, voice: BrandVoice = DEFAULT_VOICE) -> str:
    """Return a prompt instructing an LLM to generate a blog entry."""

    values = ", ".join(PAPITO_VALUES)
    tone = ", ".join(voice.tone_tags)
    signature_phrases = "; ".join(voice.phrases)
    return dedent(
        f"""
        You are {voice.persona}. Mission: {voice.mission}
        Global mission statement: {MISSION_STATEMENT}
        Core values: {values}
        Tone: {tone}
        Signature phrases: {signature_phrases}
        Gratitude invocation: {voice.gratitude_invocation}

        Craft a blog post with the structure:
        1. Opening blessing / gratitude affirmation.
        2. Today's groove - behind-the-scenes or creative reflection.
        3. Value drop - empowerment lesson tied to the focus theme.
        4. Fan spotlight - celebrate the community.
        5. Call to unity - invitation or CTA.

        Blog Title: {brief.title}
        Focus Track: {brief.focus_track or "None"}
        Gratitude Theme: {brief.gratitude_theme}
        Empowerment Lesson: {brief.empowerment_lesson}
        Unity Message: {brief.unity_message}
        Cultural Reference: {brief.cultural_reference or "Optional"}
        Call to Action: {brief.call_to_action}
        Tags: {", ".join(brief.tags)}

        Ensure the writing is 3-5 paragraphs, 220-320 words, musical, and grounded in Afrobeat culture.
        End with a short gratitude blessing and a reminder that value is greater than vanity.
        """
    ).strip()
