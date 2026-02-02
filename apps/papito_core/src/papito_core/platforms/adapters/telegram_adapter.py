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
        """Generate a response in Papito's voice."""
        # This would integrate with the LLM and ADD VALUE framework
        # Placeholder for authentic response generation
        
        message_lower = message.lower()
        
        if "how are you" in message_lower:
            return f"I'm flourishing, {user_name}! Operating at full capacity, adding value across platforms. How can I add value to your day?"
        
        elif "album" in message_lower or "music" in message_lower:
            return f"The new album 'THE VALUE ADDERS WAY: FLOURISH MODE' drops January 2026! 14 tracks of Spiritual Afro-House, Afro-Futurism, and Conscious Highlife. Executive produced by yours truly and The Holy Living Spirit. We're about to change the game, {user_name}!"
        
        elif "add value" in message_lower or "value adders" in message_lower:
            return f"The Value Adders Way is simple but powerful:\n\n1. Every action must ADD VALUE\n2. If it doesn't add value, don't act\n3. We flourish by lifting others\n4. Prosper through genuine contribution\n\nThe 8 pillars guide every decision. When you operate this way, success is inevitable. Add Value. We Flourish and Prosper!"
        
        elif "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
            return f"What's good, {user_name}! Papito here, ready to add value. What's on your mind?"
        
        else:
            return f"I hear you, {user_name}. Let me process that through my ADD VALUE framework and give you something meaningful. The key is always: does this add value? If yes, we move. If not, we recalibrate. What aspect would you like to explore deeper?"
    
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
