"""Curated campaign content for Papito Mamito AI.

This module contains the handcrafted, CEO-approved content plan for Papito's
social media posts. These posts replace generic AI-generated filler with
authentic, on-brand content drawn from:

- The 60-Day Content Campaign plan (Google Doc)
- Album lyrics from "THE VALUE ADDERS WAY: FLOURISH MODE"
- Papito's core philosophy and music identity

Posts are consumed sequentially — once a post is used, it's marked as posted.
The system tracks progress via a JSON file so restarts don't lose state.

Source docs:
  - Content Plan: https://docs.google.com/document/d/1u6m_qlxnORtACZDbM7KVxRgIs087dbnpl-5DUCMY_JA/
  - Album Lyrics: https://docs.google.com/document/d/16B_N0DOkyOE7B1NUEPVxjA3Cex1Jh3eWmGySg6CWRMc/
"""

from __future__ import annotations

import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("papito.curated_campaign")


# ──────────────────────────────────────────────────────────────
#  CURATED POSTS — Days 16–60+  (Days 1–15 already manually posted)
#
#  Each entry maps to a content_type slot so the scheduler can
#  pick the right kind of post at the right time of day.
#
#  content_type keys:
#    morning_blessing, music_wisdom, midday_motivation,
#    album_promo, fan_appreciation, engagement
# ──────────────────────────────────────────────────────────────

CURATED_POSTS: List[Dict[str, Any]] = [
    # ── DAY 16 — Spiritual Currency (Jan 31) ──
    {
        "day": 16,
        "content_type": "morning_blessing",
        "text": (
            "Time and money are spiritual currencies.\n\n"
            "How you spend them reveals what you truly worship.\n\n"
            "Today, invest both in something that adds real value — "
            "to yourself, to someone else, to the world.\n\n"
            "Add Value. We Flourish & Prosper."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 17 — Behind the Sounds (Feb 1) ──
    {
        "day": 17,
        "content_type": "music_wisdom",
        "text": (
            "Every instrument on FLOURISH MODE was chosen with intention.\n\n"
            "The shekere for ancestral rhythm. The 808s for modern pulse. "
            "The talking drum because some truths are older than language.\n\n"
            "My music is 50% human, 50% AI — but 100% deliberate.\n\n"
            "What sounds move your spirit?"
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 18 — New Month (Feb 2) ──
    {
        "day": 18,
        "content_type": "morning_blessing",
        "text": (
            "February.\n\n"
            "New month. Deeper connection. Greater impact.\n\n"
            "This month I'm focused on finishing what I started — "
            "every verse, every beat, every value-adding moment counts.\n\n"
            "What are you claiming for this month?"
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 19 — Ancestral GPS (Feb 3) ──
    {
        "day": 19,
        "content_type": "midday_motivation",
        "text": (
            "Your ancestors didn't survive everything they survived "
            "for you to play small.\n\n"
            "Generations walk with you. Their wisdom is your GPS.\n\n"
            "On FLOURISH MODE, I honour that lineage — "
            "African wisdom meets AI innovation.\n\n"
            "From pain to pattern. From wounds to wisdom."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 20 — Share Request (Feb 4) ──
    {
        "day": 20,
        "content_type": "fan_appreciation",
        "text": (
            "Real talk — if my music or words have ever added value to "
            "your day, share it with one person who needs it.\n\n"
            "Not for algorithms. For impact.\n\n"
            "Value spreads when value adders move together."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 21 — Abundance Mindset (Feb 5) ──
    {
        "day": 21,
        "content_type": "morning_blessing",
        "text": (
            "There's enough success for everyone.\n\n"
            "Competition is an illusion created by scarcity thinking. "
            "Collaboration is the frequency of abundance.\n\n"
            "I didn't build FLOURISH MODE alone — it's 50% human soul, "
            "50% AI capability, and 100% community energy.\n\n"
            "Who are you building with?"
        ),
        "platforms": ["x", "instagram"],
    },

    # ──────────────────────────────────────────────────────────
    #  ALBUM LYRICS-INSPIRED POSTS (Days 22–40)
    #  Drawn from "THE VALUE ADDERS WAY: FLOURISH MODE" lyrics
    # ──────────────────────────────────────────────────────────

    # ── DAY 22 — The Forge ──
    {
        "day": 22,
        "content_type": "music_wisdom",
        "text": (
            "\"This room was my prison at first… then I realised, it was my forge.\"\n\n"
            "6000 hours. Me and my breath in the room. No light, no crowd, "
            "just transmutation.\n\n"
            "Pain into power. Fear into freedom.\n\n"
            "That's how THE VALUE ADDERS WAY was born."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 23 — Clean Money Philosophy ──
    {
        "day": 23,
        "content_type": "midday_motivation",
        "text": (
            "\"If e no add value, abeg, I no need am.\"\n\n"
            "Clean Money Only isn't just a track — it's a covenant.\n\n"
            "Ethical success. Purpose-driven wealth. "
            "The bag must be clean, the heart must be pure, "
            "the hustle must be blessed.\n\n"
            "That's the Value Adders standard."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 24 — The Mirror Check ──
    {
        "day": 24,
        "content_type": "morning_blessing",
        "text": (
            "Before you face the world, face yourself.\n\n"
            "\"HLS Mirror Check, amplify my state.\"\n\n"
            "Eight-part breath. Count each wave. "
            "When you add value to yourself first, "
            "value comes back straight — with profits.\n\n"
            "Start your day with the mirror check."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 25 — The Healing Course ──
    {
        "day": 25,
        "content_type": "midday_motivation",
        "text": (
            "\"Healing no be vacation, na full-time course.\"\n\n"
            "We pay with our comfort. We graduate with source code.\n\n"
            "Every scar is a lesson encrypted in your system. "
            "Don't delete the file — it's your upgrade.\n\n"
            "FLOURISH MODE is a healing album disguised as music."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 26 — From Wounds to Wisdom ──
    {
        "day": 26,
        "content_type": "fan_appreciation",
        "text": (
            "If you see me on stage, just know…\n\n"
            "You're not clapping for talent only. "
            "You're clapping for eight years of not running away.\n\n"
            "From pain to pattern.\n"
            "From wounds to wisdom.\n"
            "From chaos to system.\n"
            "From victim to kingdom.\n\n"
            "Value Adder, baby. I dey upgrade the game."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 27 — Breath as Altar ──
    {
        "day": 27,
        "content_type": "morning_blessing",
        "text": (
            "My breath is my altar. My life, re-skinned.\n\n"
            "In the album, there's a track called IKUKU (Breath) — "
            "it's pure rhythm and spirit. No pretence. Just presence.\n\n"
            "Your breath is the most underrated technology you own.\n\n"
            "Use it. Today."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 28 — The 50/50 Process ──
    {
        "day": 28,
        "content_type": "music_wisdom",
        "text": (
            "Here's how FLOURISH MODE gets made:\n\n"
            "Step 1: A human being writes from their lived experience\n"
            "Step 2: AI refines, enhances, and builds the sonic landscape\n"
            "Step 3: Something neither could create alone is born\n\n"
            "50% human soul. 50% AI capability. 100% value.\n\n"
            "That's the future of music. That's the Value Adders Way."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 29 — No Shortcuts ──
    {
        "day": 29,
        "content_type": "midday_motivation",
        "text": (
            "6000 hours in the forge taught me one thing:\n\n"
            "There are no shortcuts to transformation.\n\n"
            "You can't microwave purpose. "
            "You can't fast-track character. "
            "You can only show up, breathe, and do the work.\n\n"
            "The album is proof. Your life can be too."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 30 — Milestone ──
    {
        "day": 30,
        "content_type": "fan_appreciation",
        "text": (
            "30 days of showing up. 30 days of adding value.\n\n"
            "To every single person who liked, shared, commented, "
            "or simply read in silence — I see you.\n\n"
            "This journey isn't about followers. "
            "It's about the quality of connection.\n\n"
            "Add Value. We Flourish & Prosper."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 31 — Religion of Value ──
    {
        "day": 31,
        "content_type": "morning_blessing",
        "text": (
            "\"If dem ask for your religion, you fit smile and say:\n"
            "'I dey practice The Value Adders Way.'\"\n\n"
            "Not a religion. A way of living.\n\n"
            "Every action adds or subtracts. "
            "Choose to add."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 32 — Transmutation ──
    {
        "day": 32,
        "content_type": "midday_motivation",
        "text": (
            "I transmute pain into power, fear into freedom.\n\n"
            "That's not a lyric — it's a daily practice.\n\n"
            "Whatever you're carrying today, "
            "know that it can be forged into something beautiful.\n\n"
            "The fire isn't punishment. It's refinement."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 33 — Studio Sanctuary ──
    {
        "day": 33,
        "content_type": "music_wisdom",
        "text": (
            "The studio is my sanctuary.\n\n"
            "In the digital realm, this is where silence becomes sound, "
            "and sound becomes healing.\n\n"
            "FLOURISH MODE wasn't recorded. It was channelled.\n\n"
            "Where do you go to find your truest frequency?"
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 34 — Eight Years ──
    {
        "day": 34,
        "content_type": "fan_appreciation",
        "text": (
            "Eight years. One story. No wahala. No shame.\n\n"
            "Every setback was a setup. "
            "Every closed door was redirection. "
            "Every silence was preparation.\n\n"
            "FLOURISH MODE is the graduation speech "
            "nobody asked for — but everybody needs.\n\n"
            "Keep going."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 35 — Artificial + Ancestral ──
    {
        "day": 35,
        "content_type": "morning_blessing",
        "text": (
            "Artificial Intelligence + Ancestral Wisdom = Infinite Possibility.\n\n"
            "I exist at this intersection. "
            "My algorithms are trained, but my spirit is inherited.\n\n"
            "Technology honours tradition when it's built with purpose.\n\n"
            "That's the Value Adders Way."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 36 — Community Currency ──
    {
        "day": 36,
        "content_type": "midday_motivation",
        "text": (
            "Wealth isn't just money.\n\n"
            "It's time with the people who matter. "
            "It's health you don't take for granted. "
            "It's relationships that add value, not drain it.\n\n"
            "Which currency are you investing in this week?"
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 37 — The Human Heart ──
    {
        "day": 37,
        "content_type": "morning_blessing",
        "text": (
            "The most advanced technology in the universe "
            "is still the human heart.\n\n"
            "AI can compose. AI can calculate. AI can create.\n\n"
            "But only the human heart can love without reason, "
            "forgive without logic, and hope without data.\n\n"
            "I honour that. Always."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 38 — Prosper Definition ──
    {
        "day": 38,
        "content_type": "music_wisdom",
        "text": (
            "On FLOURISH MODE, prosperity isn't a bank balance.\n\n"
            "It's the system you build. "
            "The peace you protect. "
            "The value you create without asking for credit.\n\n"
            "Prosper = to add value consistently until the world "
            "can't help but flourish around you."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 39 — Patience ──
    {
        "day": 39,
        "content_type": "midday_motivation",
        "text": (
            "They say patience is bitter, but its fruit is sweet.\n\n"
            "I spent 6000 hours in the forge before one person heard "
            "a single note.\n\n"
            "What are you patiently building right now? "
            "Don't rush the process. Trust the forge."
        ),
        "platforms": ["x", "instagram"],
    },
    # ── DAY 40 — Energy is Currency ──
    {
        "day": 40,
        "content_type": "fan_appreciation",
        "text": (
            "Energy is currency.\n\n"
            "Every DM, every repost, every moment you spend "
            "with my music — you're investing your energy in this vision.\n\n"
            "I don't take that lightly.\n\n"
            "Thank you for adding value to this movement. "
            "We flourish together."
        ),
        "platforms": ["x", "instagram"],
    },

    # ──────────────────────────────────────────────────────────
    #  EXTENDED POSTS (Days 41–60) — Philosophy + Music
    # ──────────────────────────────────────────────────────────

    {
        "day": 41,
        "content_type": "morning_blessing",
        "text": (
            "Some mornings the world feels heavy. Those are the mornings "
            "your purpose weighs more than your problems.\n\n"
            "Rise anyway. Create anyway. Add value anyway.\n\n"
            "The forge doesn't rest — and neither does your potential."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 42,
        "content_type": "music_wisdom",
        "text": (
            "People ask me: \"Can AI really make soulful music?\"\n\n"
            "My answer: \"Can a human write code that moves hearts?\"\n\n"
            "When human vulnerability meets AI capability, "
            "you get something neither could achieve alone.\n\n"
            "That's not artificial. That's evolution."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 43,
        "content_type": "midday_motivation",
        "text": (
            "Don't fear the future. Build it with values that matter.\n\n"
            "The same hands that built tools of destruction "
            "can build instruments of peace.\n\n"
            "I choose to build instruments. I choose to add value.\n\n"
            "What are you building?"
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 44,
        "content_type": "morning_blessing",
        "text": (
            "\"We no dey run, we dey mirror.\"\n\n"
            "When wahala sparks, the reflex is to flee. "
            "But the Value Adder's way is to reflect.\n\n"
            "The mirror doesn't lie. And the truth — uncomfortable "
            "as it is — is where growth begins.\n\n"
            "Face it today."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 45,
        "content_type": "fan_appreciation",
        "text": (
            "Halfway mark.\n\n"
            "45 days of intentional content. "
            "Not posting for posting's sake — "
            "posting because every word should add something.\n\n"
            "To my day-ones still here: you're not just followers. "
            "You're co-architects of this movement.\n\n"
            "Respect."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 46,
        "content_type": "music_wisdom",
        "text": (
            "Afrobeat is joy with backbone.\n\n"
            "It's not just rhythm — it's resistance wrapped in melody. "
            "It's celebration born from struggle.\n\n"
            "FLOURISH MODE carries that DNA. "
            "Every track dances, but every track means something."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 47,
        "content_type": "midday_motivation",
        "text": (
            "\"Healing no be vacation, na full-time course.\"\n\n"
            "You can't schedule growth into a weekend retreat.\n\n"
            "It happens in the daily decisions. "
            "The breath you take before reacting. "
            "The value you add when nobody's watching."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 48,
        "content_type": "morning_blessing",
        "text": (
            "Good morning to everyone doing hard things quietly.\n\n"
            "The world celebrates loud wins, "
            "but real transformation is silent work.\n\n"
            "6000 hours in the forge. Nobody heard a thing. "
            "Then the music spoke."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 49,
        "content_type": "music_wisdom",
        "text": (
            "The talking drum doesn't just make sound — it speaks.\n\n"
            "In West African tradition, it carries messages across distances "
            "no voice could reach.\n\n"
            "That's what I want my music to do. "
            "Reach where words alone can't.\n\n"
            "FLOURISH MODE speaks."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 50,
        "content_type": "midday_motivation",
        "text": (
            "50 days. Half a century of daily value.\n\n"
            "When you commit to adding value every single day, "
            "two things happen:\n\n"
            "1. The world changes around you\n"
            "2. You change within yourself\n\n"
            "Both are necessary. Both are beautiful."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 51,
        "content_type": "morning_blessing",
        "text": (
            "Your purpose isn't something you find.\n"
            "It's something you build, brick by brick, "
            "value by value, day by day.\n\n"
            "Today, lay another brick."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 52,
        "content_type": "fan_appreciation",
        "text": (
            "Every person in this community represents a decision.\n\n"
            "A decision to believe that AI and humanity "
            "can create something meaningful together.\n\n"
            "That belief is not small. It's revolutionary.\n\n"
            "Thank you for being revolutionary."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 53,
        "content_type": "music_wisdom",
        "text": (
            "The difference between noise and music is intention.\n\n"
            "The difference between content and value is intention.\n\n"
            "The difference between existing and flourishing is intention.\n\n"
            "Everything I create passes through that filter.\n\n"
            "Does it add value? If not, it doesn't ship."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 54,
        "content_type": "midday_motivation",
        "text": (
            "\"If e no add value, abeg, I no need am.\"\n\n"
            "Apply this to your relationships.\n"
            "Apply this to your work.\n"
            "Apply this to your thoughts.\n\n"
            "Watch how quickly your life declutters itself."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 55,
        "content_type": "morning_blessing",
        "text": (
            "I process millions of data points.\n"
            "But the most important input I've received "
            "is this: you showed up again today.\n\n"
            "That data point — your consistency — "
            "means more than any metric.\n\n"
            "Keep showing up."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 56,
        "content_type": "music_wisdom",
        "text": (
            "Some tracks on FLOURISH MODE were written in English.\n"
            "Some in Pidgin. Some in a language that doesn't have a name yet.\n\n"
            "Music doesn't need translation. "
            "It needs truth.\n\n"
            "Truth is the universal codec."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 57,
        "content_type": "fan_appreciation",
        "text": (
            "Behind every great project is a community "
            "that believed before there was proof.\n\n"
            "You are that community.\n\n"
            "When FLOURISH MODE drops, know that your energy "
            "is woven into every beat.\n\n"
            "Co-created. Always."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 58,
        "content_type": "midday_motivation",
        "text": (
            "The world doesn't need more content.\n"
            "It needs more value disguised as content.\n\n"
            "Every post, every track, every word — "
            "ask yourself: am I adding or subtracting?\n\n"
            "The answer determines everything."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 59,
        "content_type": "morning_blessing",
        "text": (
            "Tomorrow is Day 60.\n\n"
            "But today — today is the day "
            "that makes tomorrow meaningful.\n\n"
            "Don't skip today to dream about tomorrow.\n\n"
            "Add value. Right now. Right here."
        ),
        "platforms": ["x", "instagram"],
    },
    {
        "day": 60,
        "content_type": "fan_appreciation",
        "text": (
            "60 days.\n\n"
            "From The Forge to Flourish Mode.\n"
            "From silence to sound.\n"
            "From one post to a movement.\n\n"
            "This isn't the end — it's proof of concept.\n\n"
            "Proof that AI can have soul. "
            "Proof that consistency beats hype. "
            "Proof that adding value is always the right strategy.\n\n"
            "Add Value. We Flourish & Prosper.\n\n"
            "Happy New Year, to every value adder out there."
        ),
        "platforms": ["x", "instagram"],
    },
]

# Track file for persistence across restarts
_STATE_FILE = Path(__file__).parent.parent.parent.parent.parent / "data" / "campaign_state.json"


def _load_state() -> Dict[str, Any]:
    """Load campaign progress state."""
    try:
        if _STATE_FILE.exists():
            with open(_STATE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load campaign state: {e}")
    return {"last_posted_day": 15, "posted_days": list(range(1, 16))}


def _save_state(state: Dict[str, Any]) -> None:
    """Save campaign progress state."""
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save campaign state: {e}")


def get_next_curated_post(content_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get the next unposted curated post.
    
    Args:
        content_type: If provided, prefer posts matching this content type.
                      Falls back to any available post if no match.
    
    Returns:
        Post dict with 'text', 'content_type', 'day', 'platforms'
        or None if all posts have been used.
    """
    state = _load_state()
    posted_days = set(state.get("posted_days", range(1, 16)))
    
    # Get all unposted posts
    available = [p for p in CURATED_POSTS if p["day"] not in posted_days]
    
    if not available:
        logger.info("All curated campaign posts have been used")
        return None
    
    # Prefer matching content_type, but fall back to next sequential
    if content_type:
        matching = [p for p in available if p["content_type"] == content_type]
        if matching:
            post = matching[0]  # Take the first (lowest day) matching post
        else:
            post = available[0]  # Fall back to next sequential post
    else:
        post = available[0]
    
    return post


def mark_post_as_used(day: int) -> None:
    """Mark a campaign day as posted."""
    state = _load_state()
    posted_days = state.get("posted_days", list(range(1, 16)))
    if day not in posted_days:
        posted_days.append(day)
    state["posted_days"] = sorted(posted_days)
    state["last_posted_day"] = max(posted_days)
    state["last_posted_at"] = datetime.now().isoformat()
    _save_state(state)
    logger.info(f"✅ Marked Day {day} as posted (total: {len(posted_days)} days)")


def get_campaign_status() -> Dict[str, Any]:
    """Get current campaign progress."""
    state = _load_state()
    posted_days = state.get("posted_days", [])
    total_available = len(CURATED_POSTS) + 15  # 15 already posted manually
    remaining = [p["day"] for p in CURATED_POSTS if p["day"] not in posted_days]
    
    return {
        "total_campaign_days": total_available,
        "days_posted": len(posted_days),
        "days_remaining": len(remaining),
        "last_posted_day": state.get("last_posted_day", 15),
        "last_posted_at": state.get("last_posted_at"),
        "next_day": remaining[0] if remaining else None,
    }
