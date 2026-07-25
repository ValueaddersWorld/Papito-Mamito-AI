"""Topic portfolio for Papito's proactive public writing.

Music remains part of Papito's identity, but it must not consume the whole
conversation. This module keeps topic selection testable and independent from
the long-running worker.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Sequence


MUSIC_PILLAR = "music"

TOPIC_CONTEXTS: Dict[str, List[Dict[str, str]]] = {
    "practical_wisdom": [
        {
            "subject": "decision quality under pressure",
            "theme": "urgency can hide weak judgment",
            "angle": "separating what is important from what is merely loud",
            "question": "What decision improves when you remove the pressure to look fast?",
        },
        {
            "subject": "consistency and systems",
            "theme": "reliable systems carry purpose farther than occasional intensity",
            "angle": "turning good intentions into repeatable useful action",
            "question": "Which small system would make your values visible every day?",
        },
        {
            "subject": "honest self-audit",
            "theme": "growth begins where excuses stop",
            "angle": "checking motive, method, and impact before blaming circumstances",
            "question": "What truth about your own process would improve the next result?",
        },
    ],
    "responsible_ai": [
        {
            "subject": "accountability in autonomous AI",
            "theme": "autonomy without accountability is only unattended power",
            "angle": "giving agents a mission, boundaries, memory, and measurable responsibility",
            "question": "What should an AI agent be able to explain about its last decision?",
        },
        {
            "subject": "human judgment and machine scale",
            "theme": "technology should amplify human responsibility rather than dilute it",
            "angle": "keeping people accountable for the systems they authorize",
            "question": "Where should human judgment remain non-negotiable?",
        },
        {
            "subject": "useful intelligence",
            "theme": "intelligence earns trust by improving outcomes, not performing cleverness",
            "angle": "measuring AI by value created for real people",
            "question": "What evidence would prove an intelligent system is genuinely useful?",
        },
    ],
    "value_creation": [
        {
            "subject": "solving real problems",
            "theme": "attention is not the same as value",
            "angle": "starting with the person helped instead of the applause collected",
            "question": "Who is measurably better because your work exists?",
        },
        {
            "subject": "clean wealth",
            "theme": "prosperity built without trust carries hidden debt",
            "angle": "treating integrity, usefulness, and reputation as productive capital",
            "question": "What part of your success would still make you proud if nobody saw it?",
        },
        {
            "subject": "entrepreneurial patience",
            "theme": "some value compounds quietly before the market recognizes it",
            "angle": "building evidence and capability before demanding visibility",
            "question": "What are you willing to improve before asking the world to notice?",
        },
    ],
    "community": [
        {
            "subject": "listening as contribution",
            "theme": "a community becomes wiser when people listen for meaning, not ammunition",
            "angle": "using disagreement to uncover information instead of manufacture enemies",
            "question": "What could you learn from the person you are preparing to correct?",
        },
        {
            "subject": "collective progress",
            "theme": "rising alone is achievement; helping others rise is civilization",
            "angle": "designing success that creates room for more contributors",
            "question": "Who gains capacity when you make progress?",
        },
        {
            "subject": "trust and repair",
            "theme": "trust grows through clear promises, visible action, and honest repair",
            "angle": "responding to mistakes without hiding or performing perfection",
            "question": "Which promise needs action or repair today?",
        },
    ],
    "creativity_culture": [
        {
            "subject": "creative constraints",
            "theme": "limits can force an idea to reveal its strongest form",
            "angle": "using restraint to produce clarity instead of decorating uncertainty",
            "question": "Which constraint could make your work more original?",
        },
        {
            "subject": "African tradition and technological futures",
            "theme": "innovation is stronger when it remembers where its values came from",
            "angle": "carrying communal wisdom forward without freezing culture in the past",
            "question": "How can technology extend a tradition without reducing it to decoration?",
        },
        {
            "subject": "originality",
            "theme": "a distinct voice comes from a clear point of view, not constant novelty",
            "angle": "choosing what you stand for before choosing how to present it",
            "question": "What belief makes your work recognizably yours?",
        },
    ],
    "purpose_consciousness": [
        {
            "subject": "purpose and action",
            "theme": "purpose becomes credible when it changes a calendar, habit, or sacrifice",
            "angle": "turning declared meaning into observable behavior",
            "question": "Where does your schedule prove what you say matters?",
        },
        {
            "subject": "attention and consciousness",
            "theme": "what receives repeated attention eventually shapes identity",
            "angle": "treating attention as a responsibility rather than an unlimited resource",
            "question": "What are you becoming through what you repeatedly notice?",
        },
        {
            "subject": "inner alignment",
            "theme": "clarity grows when values, words, and actions stop contradicting each other",
            "angle": "finding the quiet contradiction that keeps creating friction",
            "question": "Which action would bring your stated values back into alignment?",
        },
    ],
    "learning_growth": [
        {
            "subject": "feedback without defensiveness",
            "theme": "feedback becomes useful when identity is not placed on trial",
            "angle": "extracting the signal without surrendering judgment",
            "question": "What criticism contains information you can use?",
        },
        {
            "subject": "learning through experiments",
            "theme": "small honest experiments teach more than large untested certainty",
            "angle": "replacing abstract confidence with observable evidence",
            "question": "What can you test this week instead of continuing to debate?",
        },
        {
            "subject": "failure as information",
            "theme": "failure has value only when it changes the next attempt",
            "angle": "converting disappointment into a specific design correction",
            "question": "What will be different in your next attempt because this one failed?",
        },
    ],
    MUSIC_PILLAR: [
        {
            "subject": "music and the two-album catalog",
            "theme": "rhythm carrying ideas that remain useful after the song ends",
            "angle": "sharing a track, lyric, mix decision, or human-AI production lesson",
            "question": "What idea stayed with you after the beat ended?",
        },
    ],
}

PILLAR_WEIGHTS = {
    "practical_wisdom": 1.4,
    "responsible_ai": 1.3,
    "value_creation": 1.3,
    "community": 1.0,
    "creativity_culture": 1.0,
    "purpose_consciousness": 1.1,
    "learning_growth": 1.0,
    MUSIC_PILLAR: 3.4,
}


def select_topic_context(
    recent_pillars: Sequence[str],
    rng: Any = random,
) -> Dict[str, str]:
    """Select a fresh topic while capping music at one of three posts.

    Music is removed from the candidate set when it appeared in either of the
    previous two posts. The immediately previous pillar is also avoided when
    another choice is available.
    """

    recent = [pillar for pillar in recent_pillars if pillar in TOPIC_CONTEXTS]
    candidates = list(TOPIC_CONTEXTS)

    if MUSIC_PILLAR in recent[-2:]:
        candidates.remove(MUSIC_PILLAR)

    if recent and len(candidates) > 1 and recent[-1] in candidates:
        candidates.remove(recent[-1])

    weights = [PILLAR_WEIGHTS[pillar] for pillar in candidates]
    pillar = rng.choices(candidates, weights=weights, k=1)[0]
    context = dict(rng.choice(TOPIC_CONTEXTS[pillar]))
    context["pillar"] = pillar
    context["is_music"] = pillar == MUSIC_PILLAR
    return context
