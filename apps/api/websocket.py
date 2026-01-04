"""
Lithium Bot API - WebSocket Gateway
Real-time WebSocket endpoint for live data streaming to frontend
"""
import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from apps.api.event_bus import event_bus, guild_channel, EventTypes
import structlog

logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per guild"""
    
    def __init__(self):
        # guild_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._subscriptions: Dict[str, bool] = {}
    
    async def connect(self, websocket: WebSocket, guild_id: str):
        """Accept connection and add to guild group"""
        await websocket.accept()
        
        if guild_id not in self.active_connections:
            self.active_connections[guild_id] = set()
        
        self.active_connections[guild_id].add(websocket)
        
        # Subscribe to guild events if first connection
        if guild_id not in self._subscriptions:
            await self._subscribe_to_guild(guild_id)
            self._subscriptions[guild_id] = True
        
        logger.info(f"WebSocket: Client connected to guild {guild_id}")
    
    def disconnect(self, websocket: WebSocket, guild_id: str):
        """Remove connection from guild group"""
        if guild_id in self.active_connections:
            self.active_connections[guild_id].discard(websocket)
            if not self.active_connections[guild_id]:
                del self.active_connections[guild_id]
        
        logger.info(f"WebSocket: Client disconnected from guild {guild_id}")
    
    async def broadcast(self, guild_id: str, message: dict):
        """Broadcast message to all connections in guild"""
        if guild_id not in self.active_connections:
            return
        
        dead_connections = set()
        for connection in self.active_connections[guild_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.active_connections[guild_id].discard(conn)
    
    async def _subscribe_to_guild(self, guild_id: str):
        """Subscribe to all event channels for a guild"""
        
        async def handler(data: dict):
            await self.broadcast(guild_id, data)
        
        # Subscribe to all event types
        for event_type in [
            EventTypes.MESSAGE,
            EventTypes.MESSAGE_DELETE,
            EventTypes.MEMBER_JOIN,
            EventTypes.MEMBER_LEAVE,
            EventTypes.TICKET_CREATE,
            EventTypes.TICKET_UPDATE,
            EventTypes.SETTINGS_UPDATE,
            EventTypes.MODULE_UPDATE,
            EventTypes.MODERATION_ACTION,
            EventTypes.AUDIT_LOG,
        ]:
            channel = guild_channel(guild_id, event_type)
            await event_bus.subscribe(channel, handler)
        
        # Also subscribe to general guild channel
        await event_bus.subscribe(f"guild:{guild_id}:events", handler)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/{guild_id}")
async def websocket_endpoint(websocket: WebSocket, guild_id: str):
    """
    WebSocket endpoint for real-time guild events.
    
    Events pushed to clients:
    - message: New message in guild
    - message_delete: Message deleted
    - member_join: Member joined
    - member_leave: Member left
    - ticket_create: Ticket opened
    - ticket_update: Ticket status changed
    - settings_update: Guild settings changed
    - module_update: Module config changed
    - moderation_action: Moderation action taken
    - audit_log: Audit log entry
    """
    # TODO: Add authentication check
    # user = await get_ws_user(websocket)
    # if not user:
    #     await websocket.close(code=4001)
    #     return
    
    await manager.connect(websocket, guild_id)
    
    try:
        # Send initial connection success
        await websocket.send_json({
            "type": "connected",
            "data": {"guild_id": guild_id, "status": "live"}
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong, requests)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )
                
                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket, guild_id)
