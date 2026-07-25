"""Policy-aware, persistent live conversation handling for X.

This module deliberately handles only inbound interactions. A direct mention or
reply is a clear signal that the user wants to hear from Papito. Unsolicited
keyword-search replies and automated likes are intentionally outside its scope.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


@dataclass(frozen=True)
class XConversationConfig:
    """Runtime controls for live X conversations."""

    monitor_enabled: bool = False
    enabled: bool = False
    ai_reply_approved: bool = False
    poll_seconds: int = 180
    max_replies_per_day: int = 12
    max_replies_per_cycle: int = 3
    state_file: str = os.path.join("data", "x_live_conversations.json")
    timezone_name: str = "Europe/Amsterdam"

    @classmethod
    def from_env(cls) -> "XConversationConfig":
        return cls(
            monitor_enabled=_env_bool(
                "PAPITO_X_MONITOR_ENABLED",
                _env_bool("PAPITO_X_READ_ENABLED", False),
            ),
            enabled=_env_bool("PAPITO_X_LIVE_ENGAGEMENT", False),
            ai_reply_approved=_env_bool("PAPITO_X_AI_REPLY_APPROVED", False),
            poll_seconds=_bounded_int("PAPITO_X_POLL_SECONDS", 180, 60, 3600),
            max_replies_per_day=_bounded_int(
                "PAPITO_X_MAX_REPLIES_PER_DAY", 12, 1, 50
            ),
            max_replies_per_cycle=_bounded_int(
                "PAPITO_X_MAX_REPLIES_PER_CYCLE", 3, 1, 10
            ),
            state_file=os.getenv(
                "PAPITO_X_STATE_FILE",
                os.path.join("data", "x_live_conversations.json"),
            ),
            timezone_name=(
                os.getenv("PAPITO_AGENT_TIMEZONE")
                or os.getenv("AGENT_TIMEZONE")
                or "Europe/Amsterdam"
            ),
        )


class LiveXConversationAgent:
    """Listen for direct X interactions and reply with durable memory."""

    _OPT_OUT_PHRASES = {
        "do not reply",
        "don't reply",
        "no more replies",
        "opt out",
        "stop replying",
        "unsubscribe",
    }
    _SENSITIVE_TERMS = {
        "kill yourself",
        "nude",
        "porn",
        "suicide",
    }
    _SPAM_TERMS = {
        "airdrop",
        "claim now",
        "free crypto",
        "guaranteed profit",
        "send wallet",
    }

    def __init__(
        self,
        client: Any,
        reply_builder: Callable[[Dict[str, Any], List[Dict[str, str]]], Optional[str]],
        sanitizer: Callable[..., str],
        config: Optional[XConversationConfig] = None,
        now_provider: Optional[Callable[[], datetime]] = None,
    ):
        self.client = client
        self.reply_builder = reply_builder
        self.sanitizer = sanitizer
        self.config = config or XConversationConfig.from_env()
        self._timezone = ZoneInfo(self.config.timezone_name)
        self._now_provider = now_provider or (lambda: datetime.now(self._timezone))
        self._state = self._load_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "since_id": None,
            "processed_ids": [],
            "pending_mentions": [],
            "opted_out_users": [],
            "conversations": {},
            "reply_day": None,
            "replies_today": 0,
            "last_poll_at": None,
            "last_reply_at": None,
        }

    def _load_state(self) -> Dict[str, Any]:
        state = self._default_state()
        path = Path(self.config.state_file)
        try:
            if path.exists():
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    state.update(loaded)
        except Exception as exc:
            logger.warning("Could not load X conversation state: %s", exc)
        return state

    def _save_state(self) -> None:
        path = Path(self.config.state_file)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = dict(self._state)
            payload["processed_ids"] = list(payload.get("processed_ids", []))[-3000:]
            payload["pending_mentions"] = list(payload.get("pending_mentions", []))[-250:]

            conversations = payload.get("conversations", {})
            if isinstance(conversations, dict):
                payload["conversations"] = {
                    str(key): list(items)[-8:]
                    for key, items in list(conversations.items())[-500:]
                    if isinstance(items, list)
                }

            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(payload, ensure_ascii=True, indent=2),
                encoding="utf-8",
            )
            temporary.replace(path)
        except Exception as exc:
            logger.warning("Could not save X conversation state: %s", exc)

    def _now(self) -> datetime:
        current = self._now_provider()
        if current.tzinfo is None:
            return current.replace(tzinfo=self._timezone)
        return current.astimezone(self._timezone)

    def _reset_daily_budget(self, now: datetime) -> None:
        today = now.date().isoformat()
        if self._state.get("reply_day") != today:
            self._state["reply_day"] = today
            self._state["replies_today"] = 0

    def _is_due(self, now: datetime) -> bool:
        last_poll = self._state.get("last_poll_at")
        if not last_poll:
            return True
        try:
            previous = datetime.fromisoformat(str(last_poll))
            if previous.tzinfo is None:
                previous = previous.replace(tzinfo=self._timezone)
            return (now - previous.astimezone(self._timezone)).total_seconds() >= (
                self.config.poll_seconds
            )
        except (TypeError, ValueError):
            return True

    @staticmethod
    def _mention_id(mention: Dict[str, Any]) -> str:
        return str(mention.get("id") or mention.get("tweet_id") or "")

    @staticmethod
    def _author_key(mention: Dict[str, Any]) -> str:
        return str(
            mention.get("author_id")
            or mention.get("author_username")
            or "unknown"
        ).lower()

    @staticmethod
    def _conversation_key(mention: Dict[str, Any]) -> str:
        return str(
            mention.get("conversation_id")
            or mention.get("id")
            or mention.get("tweet_id")
            or "unknown"
        )

    def _advance_since_id(self, mentions: List[Dict[str, Any]]) -> None:
        ids = [self._mention_id(item) for item in mentions]
        ids = [item for item in ids if item.isdigit()]
        if not ids:
            return
        newest = max(ids, key=int)
        current = str(self._state.get("since_id") or "")
        if not current.isdigit() or int(newest) > int(current):
            self._state["since_id"] = newest

    def _add_pending_mentions(self, mentions: List[Dict[str, Any]]) -> None:
        processed = set(str(item) for item in self._state.get("processed_ids", []))
        existing = {
            self._mention_id(item)
            for item in self._state.get("pending_mentions", [])
            if isinstance(item, dict)
        }
        own_user_id = str(getattr(self.client, "user_id", "") or "")

        for mention in mentions:
            mention_id = self._mention_id(mention)
            if not mention_id or mention_id in processed or mention_id in existing:
                continue
            if own_user_id and str(mention.get("author_id") or "") == own_user_id:
                continue
            self._state["pending_mentions"].append(mention)
            existing.add(mention_id)

    def _mark_processed(self, mention: Dict[str, Any]) -> None:
        mention_id = self._mention_id(mention)
        if mention_id:
            self._state["processed_ids"].append(mention_id)

    def _remember_exchange(
        self,
        mention: Dict[str, Any],
        reply_text: str,
        now: datetime,
    ) -> None:
        key = self._conversation_key(mention)
        conversations = self._state.setdefault("conversations", {})
        history = conversations.setdefault(key, [])
        history.extend(
            [
                {
                    "role": "user",
                    "username": str(mention.get("author_username") or "unknown"),
                    "text": str(mention.get("text") or "")[:500],
                    "at": str(mention.get("created_at") or now.isoformat()),
                },
                {
                    "role": "papito",
                    "username": str(getattr(self.client, "username", "PapitoMamito_ai")),
                    "text": reply_text,
                    "at": now.isoformat(),
                },
            ]
        )
        conversations[key] = history[-8:]

    def _history_for(self, mention: Dict[str, Any]) -> List[Dict[str, str]]:
        conversations = self._state.get("conversations", {})
        history = conversations.get(self._conversation_key(mention), [])
        return list(history)[-6:] if isinstance(history, list) else []

    def _skip_reason(self, mention: Dict[str, Any]) -> Optional[str]:
        text = str(mention.get("text") or "").lower()
        username = str(mention.get("author_username") or "").lower()
        author_key = self._author_key(mention)

        if author_key in set(self._state.get("opted_out_users", [])):
            return "user_opted_out"
        if any(phrase in text for phrase in self._OPT_OUT_PHRASES):
            opted_out = self._state.setdefault("opted_out_users", [])
            if author_key not in opted_out:
                opted_out.append(author_key)
            return "opt_out_recorded"
        if any(term in text or term in username for term in self._SENSITIVE_TERMS):
            return "sensitive_content"
        if any(term in text for term in self._SPAM_TERMS):
            return "spam"
        return None

    async def process(self, force: bool = False) -> Dict[str, Any]:
        """Poll and process direct mentions once."""

        result = {
            "monitoring": self.config.monitor_enabled,
            "enabled": self.config.enabled,
            "approved": self.config.ai_reply_approved,
            "fetched": 0,
            "replied": 0,
            "skipped": 0,
            "pending": len(self._state.get("pending_mentions", [])),
            "reason": None,
        }
        if not self.config.monitor_enabled:
            result["reason"] = "x_monitoring_disabled"
            return result

        now = self._now()
        self._reset_daily_budget(now)
        if not force and not self._is_due(now):
            result["reason"] = "poll_not_due"
            return result

        self._state["last_poll_at"] = now.isoformat()
        fetch_result = self.client.fetch_mentions(
            since_id=self._state.get("since_id"),
            limit=50,
        )
        if not fetch_result.get("success"):
            result["reason"] = fetch_result.get("error") or "mention_fetch_failed"
            self._save_state()
            return result

        mentions = fetch_result.get("mentions") or []
        mentions = [item for item in mentions if isinstance(item, dict)]
        result["fetched"] = len(mentions)
        self._advance_since_id(mentions)
        self._add_pending_mentions(mentions)
        result["pending"] = len(self._state.get("pending_mentions", []))

        if not self.config.enabled:
            result["reason"] = "live_engagement_disabled"
            self._save_state()
            return result
        if not self.config.ai_reply_approved:
            result["reason"] = "x_ai_reply_approval_required"
            self._save_state()
            return result

        pending = list(self._state.get("pending_mentions", []))
        pending.sort(
            key=lambda item: (
                int(self._mention_id(item))
                if self._mention_id(item).isdigit()
                else 0
            )
        )
        remaining: List[Dict[str, Any]] = []

        for mention in pending:
            if result["replied"] >= self.config.max_replies_per_cycle:
                remaining.append(mention)
                continue
            if self._state["replies_today"] >= self.config.max_replies_per_day:
                remaining.append(mention)
                result["reason"] = "daily_reply_budget_reached"
                continue

            skip_reason = self._skip_reason(mention)
            if skip_reason:
                self._mark_processed(mention)
                result["skipped"] += 1
                continue

            try:
                reply_text = self.reply_builder(mention, self._history_for(mention))
            except Exception as exc:
                logger.error("X reply generation failed: %s", exc)
                remaining.append(mention)
                continue

            reply_text = self.sanitizer(reply_text or "", max_length=275)
            if not reply_text:
                remaining.append(mention)
                continue

            reply_result = self.client.reply_to_tweet(
                self._mention_id(mention),
                reply_text,
            )
            if not reply_result.get("success"):
                logger.warning(
                    "Could not reply to X mention %s: %s",
                    self._mention_id(mention),
                    reply_result.get("error", "unknown error"),
                )
                remaining.append(mention)
                continue

            self._mark_processed(mention)
            self._remember_exchange(mention, reply_text, now)
            self._state["replies_today"] += 1
            self._state["last_reply_at"] = now.isoformat()
            result["replied"] += 1

        self._state["pending_mentions"] = remaining
        result["pending"] = len(remaining)
        self._save_state()
        return result

    def status(self) -> Dict[str, Any]:
        """Return non-secret operational state for logs and health checks."""

        return {
            "monitoring": self.config.monitor_enabled,
            "enabled": self.config.enabled,
            "approved": self.config.ai_reply_approved,
            "poll_seconds": self.config.poll_seconds,
            "max_replies_per_day": self.config.max_replies_per_day,
            "replies_today": int(self._state.get("replies_today") or 0),
            "pending": len(self._state.get("pending_mentions", [])),
            "processed": len(self._state.get("processed_ids", [])),
            "last_poll_at": self._state.get("last_poll_at"),
            "last_reply_at": self._state.get("last_reply_at"),
        }
