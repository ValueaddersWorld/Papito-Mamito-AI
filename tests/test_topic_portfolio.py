import random

from papito_core.topic_portfolio import (
    MUSIC_PILLAR,
    TOPIC_CONTEXTS,
    select_topic_context,
)
from papito_core.memory.post_memory import PostMemory


def test_music_is_capped_at_one_in_any_three_post_window():
    rng = random.Random(42)
    pillars = []

    for _ in range(500):
        context = select_topic_context(pillars, rng=rng)
        pillars.append(context["pillar"])

    for index in range(2, len(pillars)):
        assert pillars[index - 2 : index + 1].count(MUSIC_PILLAR) <= 1


def test_portfolio_reaches_every_non_music_pillar():
    rng = random.Random(7)
    pillars = []

    for _ in range(1000):
        context = select_topic_context(pillars, rng=rng)
        pillars.append(context["pillar"])

    assert set(TOPIC_CONTEXTS) - {MUSIC_PILLAR} <= set(pillars)


def test_immediately_previous_pillar_is_not_repeated():
    rng = random.Random(21)
    pillars = []

    for _ in range(100):
        context = select_topic_context(pillars, rng=rng)
        if pillars:
            assert context["pillar"] != pillars[-1]
        pillars.append(context["pillar"])


def test_post_memory_persists_content_pillars(tmp_path):
    path = tmp_path / "post_memory.json"
    memory = PostMemory(file_path=str(path))
    memory.record("A useful AI reflection.", kind="x:forever_agent:responsible_ai")
    memory.record("A track production lesson.", kind="x:forever_agent:music")

    restored = PostMemory(file_path=str(path))

    assert restored.recent_kinds(
        kind_prefix="x:forever_agent:",
    ) == [
        "x:forever_agent:responsible_ai",
        "x:forever_agent:music",
    ]
