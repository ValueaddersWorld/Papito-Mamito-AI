"""
PAPITO MAMITO AI - DISCORD ADAPTER
==================================
Adapter for Discord platform.

This adapter provides:
- Real-time message listening via bot
- Channel messaging
- DM support
- Reactions
- Server management

API Requirements:
- Discord Bot Token
- Bot must be invited to server with proper permissions

© 2026 Value Adders World - Entertainment Division
"Add value or don't act."
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from ..base import (
    Platform,
    PlatformAdapter,
    PlatformConfig,
    PlatformEvent,
    PlatformAction,
    ActionResult,
    PlatformCapability,
    EventCategory,
)

logger = logging.getLogger("papito.platforms.discord")


class DiscordAdapter(PlatformAdapter):
    """
    Adapter for Discord platform.
    
    Capabilities:
    - Text messages in channels
    - Direct messages
    - Replies (threads)
    - Reactions
    - Rich embeds
    - Real-time WebSocket connection
    
    Usage:
        config = PlatformConfig(
            platform=Platform.DISCORD,
            bearer_token="your_bot_token",  # Discord bot token
            custom_settings={
                "guild_ids": [123456789],  # Server IDs to operate in
                "allowed_channels": [987654321],  # Channel IDs to respond in
            }
        )
        
        adapter = DiscordAdapter(config)
        await adapter.connect()
        
        # Listen for messages
        await adapter.listen(handle_event)
        
        # Send a message
        result = await adapter.execute(PlatformAction(
            action_type="post",
            content="Hello from Papito!",
            options={"channel_id": "123456789"},
        ))
    """
    
    platform = Platform.DISCORD
    
    capabilities = {
        PlatformCapability.TEXT_POST,
        PlatformCapability.IMAGE_POST,
        PlatformCapability.REPLY,
        PlatformCapability.DIRECT_MESSAGE,
        PlatformCapability.GROUP_MESSAGE,
        PlatformCapability.STREAMING,  # Discord uses WebSocket
        PlatformCapability.WEBHOOKS,
    }
    
    def __init__(self, config: PlatformConfig):
        """Initialize Discord adapter.
        
        Args:
            config: Platform configuration with Discord credentials
        """
        super().__init__(config)
        
        self._client = None
        self._bot_user = None
        self._guild_ids: List[int] = config.custom_settings.get("guild_ids", [])
        self._allowed_channels: List[int] = config.custom_settings.get("allowed_channels", [])
        self._running = False
        self._bot_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """Connect to Discord."""
        try:
            import discord
            from discord.ext import commands
            
            # Set up intents
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            intents.guilds = True
            
            # Create bot
            self._client = commands.Bot(
                command_prefix="!papito ",
                intents=intents,
            )
            
            # Store reference to adapter
            adapter = self
            
            @self._client.event
            async def on_ready():
                adapter._bot_user = self._client.user
                adapter._connected = True
                logger.info(f"Discord bot connected as {self._client.user}")
            
            @self._client.event
            async def on_message(message: discord.Message):
                # Ignore own messages
                if message.author == self._client.user:
                    return
                
                # Check if in allowed channel
                if adapter._allowed_channels and message.channel.id not in adapter._allowed_channels:
                    return
                
                # Convert to PlatformEvent
                event = adapter._convert_message_to_event(message)
                if event:
                    await adapter._emit_event(event)
                
                # Process commands
                await self._client.process_commands(message)
            
            # Start bot in background
            self._bot_task = asyncio.create_task(
                self._client.start(self.config.bearer_token)
            )
            
            # Wait for connection
            for _ in range(30):  # 30 second timeout
                if self._connected:
                    return True
                await asyncio.sleep(1)
            
            logger.error("Discord connection timeout")
            return False
            
        except ImportError:
            logger.error("discord.py not installed - run: pip install discord.py")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Discord: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Discord."""
        if self._client:
            await self._client.close()
        
        if self._bot_task:
            self._bot_task.cancel()
            self._bot_task = None
        
        self._client = None
        self._connected = False
        logger.info("Disconnected from Discord")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Discord connection health."""
        if not self._client or not self._connected:
            return {"status": "disconnected", "platform": "discord"}
        
        return {
            "status": "healthy",
            "platform": "discord",
            "bot_user": str(self._bot_user) if self._bot_user else None,
            "guilds": len(self._client.guilds) if self._client else 0,
            "latency_ms": round(self._client.latency * 1000, 2) if self._client else None,
        }
    
    async def listen(self, callback: Callable[[PlatformEvent], None]) -> None:
        """Start listening for Discord events."""
        self.register_callback(callback)
        logger.info("Listening for Discord messages")
    
    async def stop_listening(self) -> None:
        """Stop listening for events."""
        self._event_callbacks.clear()
        logger.info("Stopped listening on Discord")
    
    def _convert_message_to_event(self, message) -> Optional[PlatformEvent]:
        """Convert a Discord message to a PlatformEvent."""
        try:
            # Determine category
            if self._bot_user and self._bot_user.mentioned_in(message):
                category = EventCategory.MENTION
            elif message.reference:
                category = EventCategory.REPLY
            elif isinstance(message.channel, type(None)) or hasattr(message.channel, "recipient"):
                category = EventCategory.MESSAGE  # DM
            else:
                category = EventCategory.COMMENT  # Regular message
            
            return PlatformEvent(
                event_id=f"discord_{message.id}",
                platform=Platform.DISCORD,
                category=category,
                user_id=str(message.author.id),
                user_name=message.author.name,
                user_display_name=message.author.display_name,
                content=message.content,
                source_id=str(message.id),
                conversation_id=str(message.channel.id),
                metadata={
                    "channel_id": str(message.channel.id),
                    "channel_name": getattr(message.channel, "name", "DM"),
                    "guild_id": str(message.guild.id) if message.guild else None,
                    "guild_name": message.guild.name if message.guild else None,
                    "has_attachments": len(message.attachments) > 0,
                },
                raw_event=message,
                created_at=message.created_at.replace(tzinfo=timezone.utc),
            )
        except Exception as e:
            logger.error(f"Error converting Discord message: {e}")
            return None
    
    async def execute(self, action: PlatformAction) -> ActionResult:
        """Execute an action on Discord."""
        if not self._client or not self._connected:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message="Not connected to Discord",
            )
        
        try:
            if action.action_type == "post":
                return await self._send_message(action)
            elif action.action_type == "reply":
                return await self._reply_to_message(action)
            elif action.action_type == "dm":
                return await self._send_dm(action)
            elif action.action_type == "react":
                return await self._add_reaction(action)
            else:
                return ActionResult(
                    success=False,
                    action_id=action.action_id,
                    platform=Platform.DISCORD,
                    error_message=f"Unknown action type: {action.action_type}",
                )
        except Exception as e:
            logger.error(f"Error executing Discord action: {e}")
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message=str(e),
            )
    
    async def _send_message(self, action: PlatformAction) -> ActionResult:
        """Send a message to a channel."""
        channel_id = action.options.get("channel_id")
        
        if not channel_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message="No channel_id specified",
            )
        
        channel = self._client.get_channel(int(channel_id))
        if not channel:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message=f"Channel {channel_id} not found",
            )
        
        message = await channel.send(action.content)
        
        return ActionResult(
            success=True,
            action_id=action.action_id,
            platform=Platform.DISCORD,
            result_id=str(message.id),
            result_url=message.jump_url,
        )
    
    async def _reply_to_message(self, action: PlatformAction) -> ActionResult:
        """Reply to a message."""
        channel_id = action.options.get("channel_id")
        message_id = action.reply_to_id
        
        if not channel_id or not message_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message="Missing channel_id or message_id",
            )
        
        channel = self._client.get_channel(int(channel_id))
        if not channel:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message=f"Channel {channel_id} not found",
            )
        
        try:
            original = await channel.fetch_message(int(message_id))
            message = await original.reply(action.content)
            
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                result_id=str(message.id),
                result_url=message.jump_url,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message=str(e),
            )
    
    async def _send_dm(self, action: PlatformAction) -> ActionResult:
        """Send a direct message."""
        user_id = action.target_user_id
        
        if not user_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message="No user_id specified",
            )
        
        try:
            user = await self._client.fetch_user(int(user_id))
            message = await user.send(action.content)
            
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                result_id=str(message.id),
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message=str(e),
            )
    
    async def _add_reaction(self, action: PlatformAction) -> ActionResult:
        """Add a reaction to a message."""
        channel_id = action.options.get("channel_id")
        message_id = action.target_content_id
        emoji = action.options.get("emoji", "👍")
        
        if not channel_id or not message_id:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message="Missing channel_id or message_id",
            )
        
        try:
            channel = self._client.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.add_reaction(emoji)
            
            return ActionResult(
                success=True,
                action_id=action.action_id,
                platform=Platform.DISCORD,
            )
        except Exception as e:
            return ActionResult(
                success=False,
                action_id=action.action_id,
                platform=Platform.DISCORD,
                error_message=str(e),
            )
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information."""
        if not self._client:
            return {}
        
        try:
            user = await self._client.fetch_user(int(user_id))
            return {
                "id": str(user.id),
                "username": user.name,
                "display_name": user.display_name,
                "discriminator": user.discriminator,
                "avatar_url": str(user.avatar.url) if user.avatar else None,
                "bot": user.bot,
            }
        except Exception as e:
            logger.error(f"Error getting Discord user: {e}")
            return {}
    
    async def get_content(self, content_id: str) -> Dict[str, Any]:
        """Get message by ID (requires channel_id in metadata)."""
        # Discord requires channel ID to fetch messages
        logger.warning("Discord get_content requires channel context")
        return {}
