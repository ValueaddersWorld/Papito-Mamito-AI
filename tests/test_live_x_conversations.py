import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from papito_core.engagement.live_x_conversations import (
    LiveXConversationAgent,
    XConversationConfig,
)


class FakeXClient:
    user_id = "papito-user"
    username = "PapitoMamito_ai"

    def __init__(self, mentions=None, fetch_error=None):
        self.mentions = list(mentions or [])
        self.fetch_error = fetch_error
        self.fetch_calls = 0
        self.replies = []

    def fetch_mentions(self, since_id=None, limit=50):
        self.fetch_calls += 1
        if self.fetch_error:
            return {"success": False, "mentions": [], "error": self.fetch_error}
        fresh = [
            mention
            for mention in self.mentions
            if not since_id or int(mention["id"]) > int(since_id)
        ]
        return {"success": True, "mentions": fresh[:limit]}

    def reply_to_tweet(self, tweet_id, content):
        self.replies.append((str(tweet_id), content))
        return {"success": True, "tweet_id": f"reply-{tweet_id}"}


def sanitize(text, max_length=None):
    cleaned = (text or "").replace("🔥", "").strip()
    return cleaned[:max_length] if max_length else cleaned


def config(tmp_path, **overrides):
    values = {
        "monitor_enabled": True,
        "enabled": True,
        "ai_reply_approved": True,
        "poll_seconds": 60,
        "monitor_only_poll_seconds": 21600,
        "credit_backoff_seconds": 86400,
        "max_replies_per_day": 12,
        "max_replies_per_cycle": 3,
        "state_file": str(tmp_path / "x-live.json"),
        "timezone_name": "Europe/Amsterdam",
    }
    values.update(overrides)
    return XConversationConfig(**values)


def mention(tweet_id="100", text="@PapitoMamito_ai what did the album teach you?"):
    return {
        "id": tweet_id,
        "text": text,
        "author_id": "listener-1",
        "author_username": "listener",
        "author_name": "Listener",
        "conversation_id": "thread-1",
        "created_at": "2026-07-25T10:00:00+02:00",
    }


def test_live_replies_are_approval_gated(tmp_path):
    client = FakeXClient([mention()])
    agent = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "A direct answer.",
        sanitizer=sanitize,
        config=config(tmp_path, ai_reply_approved=False),
    )

    result = asyncio.run(agent.process(force=True))

    assert result["reason"] == "x_ai_reply_approval_required"
    assert result["pending"] == 1
    assert client.fetch_calls == 1
    assert client.replies == []


def test_monitor_only_queues_mentions_without_replying(tmp_path):
    client = FakeXClient([mention()])
    agent = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "This must never be sent.",
        sanitizer=sanitize,
        config=config(tmp_path, enabled=False, ai_reply_approved=False),
    )

    result = asyncio.run(agent.process(force=True))

    assert result["fetched"] == 1
    assert result["pending"] == 1
    assert result["reason"] == "live_engagement_disabled"
    assert client.fetch_calls == 1
    assert client.replies == []


def test_monitoring_can_be_disabled_independently(tmp_path):
    client = FakeXClient([mention()])
    agent = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "This must never be sent.",
        sanitizer=sanitize,
        config=config(tmp_path, monitor_enabled=False),
    )

    result = asyncio.run(agent.process(force=True))

    assert result["reason"] == "x_monitoring_disabled"
    assert client.fetch_calls == 0
    assert client.replies == []


def test_monitor_only_mode_uses_low_cost_polling_cadence(tmp_path):
    current = [
        datetime(2026, 7, 25, 12, 0, tzinfo=ZoneInfo("Europe/Amsterdam"))
    ]
    client = FakeXClient()
    agent = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "This must never be sent.",
        sanitizer=sanitize,
        config=config(tmp_path, enabled=False, ai_reply_approved=False),
        now_provider=lambda: current[0],
    )

    asyncio.run(agent.process(force=True))
    current[0] += timedelta(hours=1)
    early = asyncio.run(agent.process())
    current[0] += timedelta(hours=5)
    due = asyncio.run(agent.process())

    assert early["reason"] == "poll_not_due"
    assert due["reason"] == "live_engagement_disabled"
    assert client.fetch_calls == 2
    assert agent.status()["effective_poll_seconds"] == 21600


def test_credit_error_opens_persisted_circuit_breaker(tmp_path):
    current = [
        datetime(2026, 7, 25, 12, 0, tzinfo=ZoneInfo("Europe/Amsterdam"))
    ]
    client = FakeXClient(fetch_error="402 Payment Required: credits depleted")
    agent = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "This must never be sent.",
        sanitizer=sanitize,
        config=config(tmp_path),
        now_provider=lambda: current[0],
    )

    first = asyncio.run(agent.process(force=True))
    current[0] += timedelta(hours=1)
    blocked = asyncio.run(agent.process(force=True))

    assert "credits depleted" in first["reason"]
    assert blocked["reason"] == "x_credit_backoff_active"
    assert client.fetch_calls == 1
    assert agent.status()["fetch_backoff_until"] is not None

    restarted = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "This must never be sent.",
        sanitizer=sanitize,
        config=config(tmp_path),
        now_provider=lambda: current[0],
    )
    persisted = asyncio.run(restarted.process(force=True))

    assert persisted["reason"] == "x_credit_backoff_active"
    assert client.fetch_calls == 1


def test_live_reply_is_persisted_and_not_repeated_after_restart(tmp_path):
    client = FakeXClient([mention()])
    first = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "Discipline turns intention into sound. 🔥",
        sanitizer=sanitize,
        config=config(tmp_path),
        now_provider=lambda: datetime(2026, 7, 25, 12, 0, tzinfo=ZoneInfo("Europe/Amsterdam")),
    )

    first_result = asyncio.run(first.process(force=True))
    assert first_result["replied"] == 1
    assert client.replies == [("100", "Discipline turns intention into sound.")]

    restarted_client = FakeXClient([mention()])
    restarted = LiveXConversationAgent(
        client=restarted_client,
        reply_builder=lambda item, history: "This must never be sent.",
        sanitizer=sanitize,
        config=config(tmp_path),
    )
    second_result = asyncio.run(restarted.process(force=True))

    assert second_result["replied"] == 0
    assert restarted_client.replies == []


def test_conversation_memory_reaches_the_next_reply(tmp_path):
    client = FakeXClient([mention()])
    histories = []

    def build_reply(item, history):
        histories.append(list(history))
        return "The first lesson is patience."

    agent = LiveXConversationAgent(
        client=client,
        reply_builder=build_reply,
        sanitizer=sanitize,
        config=config(tmp_path),
    )
    asyncio.run(agent.process(force=True))

    client.mentions.append(
        mention(
            tweet_id="101",
            text="@PapitoMamito_ai how did that change the second album?",
        )
    )
    asyncio.run(agent.process(force=True))

    assert histories[0] == []
    assert len(histories[1]) == 2
    assert histories[1][0]["role"] == "user"
    assert histories[1][1]["role"] == "papito"


def test_opt_out_is_honored_without_reply(tmp_path):
    client = FakeXClient([mention(text="@PapitoMamito_ai please stop replying")])
    agent = LiveXConversationAgent(
        client=client,
        reply_builder=lambda item, history: "This must never be sent.",
        sanitizer=sanitize,
        config=config(tmp_path),
    )

    result = asyncio.run(agent.process(force=True))

    assert result["skipped"] == 1
    assert client.replies == []
