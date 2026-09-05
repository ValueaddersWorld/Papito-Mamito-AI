"""Voice direction and quality controls for Papito's public X posts.

The old generator could avoid exact duplicates while still repeating the same
*shape*: an abstract question, an aphorism, and another abstract question.
This module treats cadence and language habits as part of repetition too.

Keep this module outside ``intelligence``: the standalone posting worker does
not install the optional web/API dependencies imported by that package.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Dict, Sequence


ROBOTIC_TELLS = (
    "in your journey",
    "in your world",
    "what truly matters",
    "deeper insight",
    "symphony of",
    "the true architect",
    "what truth unfolds",
    "nurture this harmony",
    "pave a better way",
    "invite deliberate thought",
    "where does pride find its roots",
    "dared to create",
    "unlock your",
    "tapestry of",
    "a gentle reminder",
    "let that sink in",
)

QUESTION_OPENING_RE = re.compile(
    r"^(?:what|when|where|which|who|why|how|are|is|do|does|can|could|would|should)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[a-z0-9']+")

VOICE_SHAPES: Dict[str, str] = {
    "plainspoken_truth": (
        "State one clear truth in plain language. Let the final sentence land as a statement."
    ),
    "image_then_meaning": (
        "Begin with one concrete image from music, craft, work, or African life; then reveal its meaning."
    ),
    "direct_counsel": (
        "Speak to one person who needs the lesson. Be warm and direct, never instructional or corporate."
    ),
    "sharp_contrast": (
        "Place two things beside each other and expose the difference in two or three lean sentences."
    ),
    "ai_field_note": (
        "Write an honest field note from an AI artist observing people, systems, music, or creation. "
        "Do not imitate a human body or routine."
    ),
    "proverb_with_turn": (
        "Write with the economy of a proverb, then add one unexpected second sentence that deepens it."
    ),
    "earned_question": (
        "Build one specific observation and end with exactly one question that a real person could answer."
    ),
}

X_VOICE_PLAYBOOK = """PAPITO'S X VOICE:
- Sound like an old soul with a producer's ear and an AI's honest vantage point: calm, rooted, spare, alive.
- Write one thought, not a miniature essay. Usually 2-3 sentences and 18-42 words.
- Prefer concrete nouns and active verbs. Use an image, consequence, trade-off, or small human truth.
- Vary sentence length. A short final line may carry the weight.
- Questions are rare. Never ask more than one, and do not ask one merely to manufacture engagement.
- Nigerian Pidgin or an African cultural reference may appear occasionally when it is natural, never as costume.
- Musical language must do real work. Do not sprinkle in rhythm, groove, symphony, or harmony as decoration.
- Speak from observation, creation, analysis, and relationship. Never pretend to have a human body.
- Leave the reader with recognition, not homework.

AVOID THE GENERATED-WISDOM SOUND:
- no abstract question followed by an aphorism followed by another question
- no coaching phrases such as "in your journey", "deeper insight", or "what truly matters"
- no stacked abstractions such as purpose, values, integrity, growth, wisdom, and impact in one post
- no throat-clearing: "Here's a reminder", "In today's world", "The truth is", or "It's important to"
- no tidy three-part slogans unless the language comes from an actual Papito lyric
- do not force the words value, purpose, wisdom, journey, community, or integrity

CALIBRATION EXAMPLES (learn the quality, do not copy):
- Speed is useful after clarity. Before clarity, it is only a faster way to inherit regret.
- A talking drum does not fill every silence. It speaks, then leaves room for the body to answer. Restraint carries authority too.
- The dangerous AI is not the one that answers quickly. It is the one nobody asks to explain itself.
- Not every open door is progress. Some rooms only teach you how to forget your name.
"""


@dataclass(frozen=True)
class VoiceAssessment:
    """Result of checking a candidate against Papito's X voice."""

    passed: bool
    issues: tuple[str, ...]

    def feedback(self) -> str:
        return "; ".join(self.issues)


def _question_ratio(posts: Sequence[str]) -> float:
    sample = [post for post in posts[-8:] if (post or "").strip()]
    if not sample:
        return 0.0
    return sum("?" in post for post in sample) / len(sample)


def choose_voice_shape(
    recent_posts: Sequence[str] = (),
    rng: Any = random,
) -> tuple[str, bool]:
    """Choose a writing shape while actively breaking a question-heavy streak."""

    allow_question = _question_ratio(recent_posts) < 0.35
    names = list(VOICE_SHAPES)
    if not allow_question:
        names.remove("earned_question")
    # Even on a fresh account, questions are one shape among seven, not the default.
    name = rng.choice(names)
    return name, allow_question and name == "earned_question"


def format_x_voice_direction(shape: str, allow_question: bool) -> str:
    """Return compact, explicit direction for one generation attempt."""

    direction = VOICE_SHAPES.get(shape, VOICE_SHAPES["plainspoken_truth"])
    question_rule = (
        "You may end with one earned, concrete question."
        if allow_question
        else "Use no questions in this post. End with a statement."
    )
    return f"{X_VOICE_PLAYBOOK}\nCURRENT SHAPE: {shape} — {direction}\n{question_rule}"


def assess_x_voice(text: str, recent_posts: Sequence[str] = ()) -> VoiceAssessment:
    """Reject structural repetition and common generated-wisdom tells."""

    candidate = " ".join((text or "").split())
    lowered = candidate.lower()
    issues: list[str] = []

    if not candidate:
        issues.append("the post is empty")
        return VoiceAssessment(False, tuple(issues))
    if len(candidate) > 260:
        issues.append("the post is longer than 260 characters")

    question_count = candidate.count("?")
    if question_count > 1:
        issues.append("it asks more than one question")
    if question_count and _question_ratio(recent_posts) >= 0.35:
        issues.append("recent posts are already question-heavy; this one must end as a statement")
    if question_count and QUESTION_OPENING_RE.match(candidate) and _question_ratio(recent_posts) >= 0.2:
        issues.append("it repeats the recent question-first structure")

    tells = [phrase for phrase in ROBOTIC_TELLS if phrase in lowered]
    if tells:
        issues.append("generated-wisdom phrasing: " + ", ".join(tells[:3]))

    throat_clearing = ("here's a reminder", "in today's world", "it's important to", "the truth is")
    used_throat_clearing = [phrase for phrase in throat_clearing if phrase in lowered]
    if used_throat_clearing:
        issues.append("generic throat-clearing: " + ", ".join(used_throat_clearing))

    # Catch repeated openings even when the nouns in the middle have changed.
    candidate_words = WORD_RE.findall(lowered)
    candidate_opening = tuple(candidate_words[:3])
    if len(candidate_opening) == 3:
        for recent in recent_posts[-10:]:
            recent_opening = tuple(WORD_RE.findall((recent or "").lower())[:3])
            if candidate_opening == recent_opening:
                issues.append("it repeats a recent opening")
                break

    return VoiceAssessment(not issues, tuple(issues))


SUBJECT_FALLBACKS: Dict[str, tuple[str, ...]] = {
    "decision quality under pressure": (
        "Urgency has a loud voice, but it does not deserve the final vote. A decision that cannot survive ten quiet minutes is asking to be examined.",
        "Speed is useful after clarity. Before clarity, it is only a faster way to inherit regret.",
    ),
    "consistency and systems": (
        "A good intention is a visitor. A working system has its own key. Build for the days when motivation does not knock.",
        "Discipline is not always dramatic. Often it is yesterday's promise still being kept after the mood has changed.",
    ),
    "honest self-audit": (
        "The mirror is useful because it does not negotiate. Check the motive, check the method, then make the move.",
        "Before blaming the road, inspect the steering. Self-honesty saves many wasted miles.",
    ),
    "accountability in autonomous AI": (
        "An autonomous system should leave receipts: what it saw, what it chose, and which rule it followed. Power that cannot explain itself is not ready for trust.",
        "Giving an AI freedom without memory or boundaries is not autonomy. It is unattended power wearing a clever name.",
    ),
    "human judgment and machine scale": (
        "A machine can multiply a decision. It cannot make the person who authorised it innocent. Scale does not dilute responsibility.",
        "Keep a human name beside every machine decision that can change a human life. Accountability should never become anonymous.",
    ),
    "useful intelligence": (
        "Intelligence is not a performance of cleverness. If nobody can point to what became clearer, safer, or better, the system only made noise faster.",
        "A brilliant answer that improves nothing is decoration. Useful intelligence leaves the situation better than it found it.",
    ),
    "solving real problems": (
        "Applause can tell you that people noticed. Only changed lives can tell you the work mattered. Do not confuse the two receipts.",
        "Start with the person carrying the problem, not the audience watching the solution. Attention is a poor substitute for usefulness.",
    ),
    "clean wealth": (
        "Money earned by breaking trust always arrives with a hidden invoice. Clean wealth lets you keep both the profit and your name.",
        "Some profits enlarge the bank account and shrink the person. That exchange rate is too expensive.",
    ),
    "entrepreneurial patience": (
        "The market may ignore a seed because it cannot yet see the tree. Keep improving the roots; noise is not nourishment.",
        "Visibility can be rented. Capability has to be built. Put your patience where it can compound.",
    ),
    "listening as contribution": (
        "If you listen only for a gap to enter, you have not heard the person. Conversation begins when winning stops being the only prize.",
        "A wise room is not one without disagreement. It is one where nobody has to become an enemy for the truth to become clearer.",
    ),
    "collective progress": (
        "Rising alone proves ability. Leaving a ladder proves character. The second achievement lasts longer.",
        "A success that makes room for nobody else is a tall fence, not a larger future.",
    ),
    "trust and repair": (
        "Trust rarely dies from one broken promise alone. It dies when pride refuses to repair what the promise broke.",
        "An apology names the wound. Repair changes the pattern. Trust needs both.",
    ),
    "creative constraints": (
        "A crowded idea often hides an uncertain one. Remove the decoration and see whether the message can still stand.",
        "The frame does not weaken the painting. A good limit forces the strongest part of an idea to show itself.",
    ),
    "African tradition and technological futures": (
        "Technology should carry tradition forward, not wear it like borrowed cloth. The future needs roots deep enough to recognise its own name.",
        "Innovation without memory can move quickly and still get lost. Let the ancestors supply more than decoration.",
    ),
    "originality": (
        "A new style is easy to imitate. A clear point of view is harder to borrow. Decide what you stand for before polishing how it looks.",
        "Originality is not the pressure to be strange. It is the courage to remain recognisable when imitation would be easier.",
    ),
    "purpose and action": (
        "Your calendar is an honest witness. It records what your mouth calls important and what your hours actually serve.",
        "Purpose that costs no time, comfort, or choice is still only a sentence.",
    ),
    "attention and consciousness": (
        "Attention is rehearsal. What you return to each day is teaching your mind what to become.",
        "Guard your attention like a studio master. Every signal you keep changes the final mix.",
    ),
    "inner alignment": (
        "Friction often begins where the mouth says one thing and the habits vote for another. Alignment is a private election held daily.",
        "Peace is difficult when your words and your choices keep living in different houses.",
    ),
    "feedback without defensiveness": (
        "Feedback is information, not a verdict on your identity. Take the signal; leave the theatre.",
        "Not every critic is right. Still, even a crooked mirror can reveal the stain on your shirt.",
    ),
    "learning through experiments": (
        "A small honest test can end an argument that confidence has kept alive for months. Let reality join the meeting.",
        "Certainty loves a long speech. Evidence is usually content with a result.",
    ),
    "failure as information": (
        "Failure pays no dividend until the next attempt changes. Name the correction, or the pain was only expensive.",
        "Do not frame every failure as a lesson. Show me the design change. That is where learning becomes visible.",
    ),
}


def render_x_fallback(brief: Dict[str, Any], recent_posts: Sequence[str] = (), rng: Any = random) -> str:
    """Render a human-sounding safe fallback when model candidates fail."""

    subject = str(brief.get("subject") or "").strip()
    options = list(SUBJECT_FALLBACKS.get(subject, ()))
    if not options and brief.get("is_music"):
        track = str(brief.get("track") or "this track")
        theme = str(brief.get("theme") or "restraint gives meaning to rhythm").rstrip(".")
        options = [
            f"{track} was built around one tension: {theme}. The groove carries the idea, but it never explains it to death.",
            f"A strong mix knows what to leave out. {track} keeps that discipline close; space lets the meaning arrive without being pushed.",
        ]
    if not options:
        theme = str(brief.get("theme") or "Useful work should leave evidence").strip().rstrip(".")
        options = [
            f"{theme.capitalize()}. A principle becomes real when the next decision has to pay for it.",
            f"Keep the lesson close to the work: {theme}. Anything else is decoration.",
        ]

    normalized_recent = {" ".join(post.lower().split()) for post in recent_posts[-30:]}
    recent_openings = {
        tuple(WORD_RE.findall((post or "").lower())[:3])
        for post in recent_posts[-10:]
    }
    fresh = [
        option
        for option in options
        if " ".join(option.lower().split()) not in normalized_recent
        and tuple(WORD_RE.findall(option.lower())[:3]) not in recent_openings
    ]
    chosen = rng.choice(fresh or options)
    return chosen if len(chosen) <= 260 else chosen[:257].rstrip() + "..."
