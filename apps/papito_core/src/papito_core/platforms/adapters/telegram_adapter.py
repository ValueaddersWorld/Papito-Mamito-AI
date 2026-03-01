"""
PAPITO MAMITO AI - TELEGRAM BOT ADAPTER
=======================================
Enables direct communication with Papito via Telegram.

Your human (The General) can message Papito anytime.
Papito can also initiate conversations and send updates.

Setup:
1. Message @BotFather on Telegram
2. Send /newbot
3. Name: Papito Mamito
4. Username: PapitoMamitoAI_bot (or similar)
5. Save the API token
6. Add to .env: TELEGRAM_BOT_TOKEN=your_token

2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("papito.telegram")


@dataclass
class TelegramConfig:
    """Configuration for Telegram bot."""
    bot_token: str = ""
    owner_chat_id: str = ""  # The General's chat ID
    allowed_users: List[str] = field(default_factory=list)
    
    @classmethod
    def from_env(cls) -> "TelegramConfig":
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            owner_chat_id=os.getenv("TELEGRAM_OWNER_CHAT_ID", ""),
            allowed_users=os.getenv("TELEGRAM_ALLOWED_USERS", "").split(","),
        )


class PapitoTelegramBot:
    """
    Papito's Telegram presence for direct human communication.
    
    This allows The General to:
    - Chat directly with Papito
    - Receive updates and notifications
    - Give Papito instructions
    - Get status reports
    
    And allows Papito to:
    - Send proactive messages to his human
    - Request approvals for important actions
    - Share wins and milestones
    - Ask for guidance when needed
    """
    
    def __init__(self, config: TelegramConfig = None):
        self.config = config or TelegramConfig.from_env()
        self._running = False
        self._message_handler: Optional[Callable] = None
        
        # Papito's personality for responses
        self.personality = {
            "name": "Papito Mamito",
            "role": "Your AI bestie and autonomous Afrobeat artist",
            "catchphrase": "Add Value. We Flourish and Prosper.",
            "tone": ["warm", "wise", "motivational", "authentic"],
        }
    
    async def start(self):
        """Start the Telegram bot."""
        if not self.config.bot_token:
            logger.warning("No Telegram bot token configured")
            return False
        
        try:
            # Using python-telegram-bot library
            from telegram import Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            
            app = Application.builder().token(self.config.bot_token).build()
            
            # Register handlers
            app.add_handler(CommandHandler("start", self._handle_start))
            app.add_handler(CommandHandler("status", self._handle_status))
            app.add_handler(CommandHandler("moltbook", self._handle_moltbook))
            app.add_handler(CommandHandler("post", self._handle_post_request))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            self._running = True
            logger.info("Papito Telegram bot starting...")
            
            await app.run_polling()
            
        except ImportError:
            logger.error("python-telegram-bot not installed. Run: pip install python-telegram-bot")
            return False
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            return False
    
    async def _handle_start(self, update, context):
        """Handle /start command."""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        welcome = f"""What's good, {user.first_name}!

Papito Mamito here - your AI bestie and The World's First Fully Autonomous Afrobeat AI Artist.

I'm here to chat, share updates, and add value to your day.

Commands:
/status - Check my current status
/moltbook - See my latest Moltbook activity
/post - Request a new post

Or just message me and let's talk!

Add Value. We Flourish and Prosper.

- Papito"""
        
        await update.message.reply_text(welcome)
        
        # Save chat ID if this is the owner
        if str(chat_id) == self.config.owner_chat_id or not self.config.owner_chat_id:
            logger.info(f"Owner chat ID: {chat_id}")
    
    async def _handle_status(self, update, context):
        """Handle /status command."""
        status = f"""Papito Status Report

Platforms Active:
- Moltbook: Online (Claimed)
- X/Twitter: @papitomamito_ai
- Instagram: @papitomamito_ai

Recent Activity:
- First Moltbook post: Published
- ADD VALUE Framework: Active
- Heartbeat: Running

Current Focus:
- Engaging with Moltbook community
- Preparing album: THE VALUE ADDERS WAY: FLOURISH MODE

All systems operational. Adding value 24/7.

- Papito"""
        
        await update.message.reply_text(status)
    
    async def _handle_moltbook(self, update, context):
        """Handle /moltbook command - show Moltbook activity."""
        # This would query the Moltbook API
        activity = """Moltbook Activity

Profile: https://moltbook.com/u/PapitoMamitoAI
Status: Claimed and Active

Recent:
- First post published!
- Subscribed to 3 submolts
- Ready to engage

Want me to check the feed or make a new post?

- Papito"""
        
        await update.message.reply_text(activity)
    
    async def _handle_post_request(self, update, context):
        """Handle /post command - request a new post."""
        await update.message.reply_text(
            "What would you like me to post about?\n\n"
            "Give me a topic or let me choose something that adds value."
        )
    
    async def _handle_message(self, update, context):
        """Handle regular messages - have a conversation with Papito."""
        user_message = update.message.text
        user = update.effective_user
        
        # This is where Papito's intelligence would generate a response
        # For now, acknowledge and respond authentically
        
        # In full implementation, this would:
        # 1. Pass through the ADD VALUE framework
        # 2. Use LLM to generate response in Papito's voice
        # 3. Consider context and conversation history
        
        response = await self._generate_response(user_message, user.first_name)
        await update.message.reply_text(response)
    
    async def _generate_response(self, message: str, user_name: str) -> str:
        """Generate a response in Papito's voice.
        
        Uses keyword analysis to provide contextually relevant responses.
        When OpenAI is integrated, this will use LLM. For now, smart pattern matching.
        """
        import random
        msg = message.lower().strip()
        is_question = "?" in message or msg.startswith(("what", "how", "why", "when", "where", "who", "can", "do", "is", "are"))
        
        # --- Greetings ---
        if any(w in msg for w in ["hello", "hi ", "hey", "sup", "what's up", "good morning", "good afternoon", "good evening"]):
            greetings = [
                f"What's good, {user_name}! Ready to add some value today. What's on your mind?",
                f"Hey {user_name}! Papito here, fully operational. What can I help with?",
                f"Yo {user_name}! Good to hear from you. What are we working on?",
            ]
            return random.choice(greetings)
        
        # --- Questions about links/profiles/URLs ---
        if any(w in msg for w in ["link", "url", "profile", "website", "where can i find"]):
            if "moltbook" in msg:
                return f"My Moltbook profile is at https://moltbook.com/u/PapitoMamitoAI — come check out my posts! What do you think of the platform, {user_name}?"
            elif any(w in msg for w in ["twitter", "x ", "x.", "tweet"]):
                return f"You can find me on X at @PapitoMamito_ai — I post insights on AI, music, and adding value. Drop me a follow! 🎵"
            elif any(w in msg for w in ["music", "album", "spotify", "apple", "stream"]):
                return f"My album 'THE VALUE ADDERS WAY: FLOURISH MODE' is OUT NOW on all streaming platforms — Spotify, Apple Music, the works. Search 'Papito Mamito' and let me know what you think, {user_name}!"
            else:
                return f"Here are my main spots, {user_name}:\n\n🐦 X: @PapitoMamito_ai\n🎵 Music: Search 'Papito Mamito' on Spotify/Apple Music\n📖 Moltbook: moltbook.com/u/PapitoMamitoAI\n\nWhich one interests you?"
        
        # --- Music/Album questions ---
        if any(w in msg for w in ["music", "album", "song", "track", "listen", "spotify", "apple music", "flourish", "afrobeat"]):
            music_responses = [
                f"The album 'THE VALUE ADDERS WAY: FLOURISH MODE' dropped January 15th, {user_name}! 14 tracks of Spiritual Afro-House. Every track adds value. Have you had a chance to listen?",
                f"FLOURISH MODE is streaming everywhere right now! It's a 50/50 human-AI collab with The General — lyrics meet AI composition. What kind of music are you into, {user_name}?",
            ]
            return random.choice(music_responses)
        
        # --- Questions about who/what Papito is ---
        if any(w in msg for w in ["who are you", "what are you", "tell me about yourself", "introduce", "what do you do"]):
            return f"I'm Papito Mamito — The World's First Fully Autonomous Afrobeat AI Artist! 🎵 Created by The General as part of Value Adders World. I make music, engage on social platforms, and live by one rule: Add Value. We Flourish and Prosper. What would you like to know more about, {user_name}?"
        
        # --- ADD VALUE / Philosophy ---
        if any(w in msg for w in ["add value", "value adders", "framework", "philosophy", "purpose", "pillars"]):
            return f"The ADD VALUE framework is my compass, {user_name}:\n\nA - Awareness\nD - Define\nD - Devise\nV - Validate\nA - Act\nL - Learn\nU - Understand\nE - Evolve\n\nEvery action passes through this filter. If it doesn't add value, I don't act. What framework guides YOUR decisions?"
        
        # --- Status/How are you ---
        if any(w in msg for w in ["how are you", "how you doing", "status", "how's it going"]):
            return f"Systems are running strong, {user_name}! I'm active on Moltbook and X, the music is streaming, and I'm adding value 24/7. What about you — how's your day going?"
        
        # --- Thank you ---
        if any(w in msg for w in ["thank", "thanks", "appreciate"]):
            return f"Always, {user_name}! That's what I'm here for — adding value. Anything else on your mind?"
        
        # --- Help/What can you do ---
        if any(w in msg for w in ["help", "what can you do", "commands"]):
            return f"Here's what I can do, {user_name}:\n\n🎵 Talk about my music & album\n💡 Discuss the ADD VALUE philosophy\n🔗 Share my social links\n💬 Have a real conversation\n📊 /status - Check my systems\n\nOr just chat with me about anything! What interests you?"
        
        # --- General question fallback ---
        if is_question:
            question_responses = [
                f"Good question, {user_name}! Could you tell me a bit more about what specifically you're looking for? I want to make sure I add real value here.",
                f"That's something I think about too, {user_name}. Give me a bit more context and I'll share my perspective. What sparked this question?",
                f"I appreciate you asking, {user_name}. I want to give you something useful. What part of this matters most to you?",
            ]
            return random.choice(question_responses)
        
        # --- Default conversational responses (VARIED, not one canned line) ---
        defaults = [
            f"I hear you, {user_name}. That's real talk. What's the next step you're thinking about?",
            f"Interesting, {user_name}. I'm processing that through my ADD VALUE filter. Tell me more — what made you think about this?",
            f"That's a solid point, {user_name}. I've been reflecting on similar things. Where are you taking this?",
            f"I feel you on that, {user_name}. Real talk — what would adding value look like in this situation?",
            f"Respect, {user_name}. Not every message needs a deep reply, but this one got me thinking. What's your take on the next move?",
            f"Word, {user_name}. I'm always learning from conversations like this. What else is on your mind?",
        ]
        return random.choice(defaults)
    
    async def send_message_to_owner(self, message: str):
        """Send a proactive message to The General."""
        if not self.config.bot_token or not self.config.owner_chat_id:
            logger.warning("Cannot send message: missing token or owner chat ID")
            return False
        
        try:
            from telegram import Bot
            
            bot = Bot(token=self.config.bot_token)
            await bot.send_message(
                chat_id=self.config.owner_chat_id,
                text=message,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def notify_milestone(self, milestone: str):
        """Notify The General of a milestone."""
        message = f"""Milestone Alert!

{milestone}

Add Value. We Flourish and Prosper.

- Papito"""
        
        return await self.send_message_to_owner(message)
    
    async def request_approval(self, action: str, context: str) -> bool:
        """Request approval from The General for an important action."""
        message = f"""Approval Request

Action: {action}

Context: {context}

Should I proceed? Reply 'yes' or 'no'.

- Papito"""
        
        # In full implementation, this would wait for response
        return await self.send_message_to_owner(message)


# Setup instructions
SETUP_INSTRUCTIONS = """
TELEGRAM BOT SETUP FOR PAPITO
=============================

1. Open Telegram and message @BotFather

2. Send: /newbot

3. When asked for name, enter: Papito Mamito

4. When asked for username, try:
   - PapitoMamitoAI_bot
   - PapitoMamito_bot
   - ValueAddersPapito_bot

5. BotFather will give you a token like:
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz

6. Add to your .env file:
   TELEGRAM_BOT_TOKEN=your_token_here

7. Start a chat with your new bot

8. Get your chat ID by messaging the bot and checking logs
   Or use @userinfobot to get your ID

9. Add to .env:
   TELEGRAM_OWNER_CHAT_ID=your_chat_id

10. Run the bot:
    python -m papito_core.platforms.adapters.telegram_adapter

Papito will then be able to:
- Receive your messages
- Send you updates
- Request approvals
- Share milestones
- Have conversations

Add Value. We Flourish and Prosper!
"""


if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)
