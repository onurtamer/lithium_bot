"""
Lithium Bot API - Event Bus
Redis Pub/Sub based event manager for real-time data streaming
"""
import asyncio
import json
from typing import Callable, Dict, Set
import redis.asyncio as redis_async
import structlog
import os

logger = structlog.get_logger()

class EventBus:
    """Redis-based event bus for real-time event streaming"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._pubsub = None
        self._redis = None
        self._listener_task = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self._redis = redis_async.from_url(self.redis_url)
        self._pubsub = self._redis.pubsub()
        logger.info("EventBus: Redis connected")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.aclose()
        logger.info("EventBus: Redis disconnected")
    
    async def publish(self, channel: str, event_type: str, data: dict):
        """Publish event to Redis channel"""
        if not self._redis:
            await self.connect()
        
        payload = json.dumps({
            "type": event_type,
            "data": data
        })
        await self._redis.publish(channel, payload)
        logger.debug(f"EventBus: Published {event_type} to {channel}")
    
    async def subscribe(self, channel: str, callback: Callable):
        """Subscribe to Redis channel"""
        if not self._pubsub:
            await self.connect()
        
        if channel not in self._subscribers:
            self._subscribers[channel] = set()
            await self._pubsub.subscribe(channel)
        
        self._subscribers[channel].add(callback)
        logger.info(f"EventBus: Subscribed to {channel}")
    
    async def unsubscribe(self, channel: str, callback: Callable):
        """Unsubscribe from Redis channel"""
        if channel in self._subscribers:
            self._subscribers[channel].discard(callback)
            if not self._subscribers[channel]:
                await self._pubsub.unsubscribe(channel)
                del self._subscribers[channel]
    
    async def start_listening(self):
        """Start listening for messages"""
        if not self._pubsub:
            await self.connect()
        
        async def listener():
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    
                    if channel in self._subscribers:
                        try:
                            data = json.loads(message["data"])
                            for callback in self._subscribers[channel]:
                                await callback(data)
                        except Exception as e:
                            logger.error(f"EventBus: Error processing message: {e}")
        
        self._listener_task = asyncio.create_task(listener())
        logger.info("EventBus: Listener started")


# Global event bus instance
event_bus = EventBus()


# Event channel helpers
def guild_channel(guild_id: str, event_type: str) -> str:
    """Generate guild-specific channel name"""
    return f"guild:{guild_id}:{event_type}"


# Standard event types
class EventTypes:
    MESSAGE = "message"
    MESSAGE_DELETE = "message_delete"
    MEMBER_JOIN = "member_join"
    MEMBER_LEAVE = "member_leave"
    MEMBER_BAN = "member_ban"
    TICKET_CREATE = "ticket_create"
    TICKET_UPDATE = "ticket_update"
    TICKET_CLOSE = "ticket_close"
    SETTINGS_UPDATE = "settings_update"
    MODULE_UPDATE = "module_update"
    MODERATION_ACTION = "moderation_action"
    AUDIT_LOG = "audit_log"
