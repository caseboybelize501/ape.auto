"""
APE - Autonomous Production Engineer
WebSocket Manager

Manages WebSocket connections and broadcasting.
"""

from typing import Dict, List, Optional
from fastapi import WebSocket
import asyncio
import json
from datetime import datetime


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Features:
    - Connection tracking per user/tenant
    - Room-based broadcasting (by run_id, tenant_id)
    - Automatic reconnection support
    - Connection heartbeat
    """
    
    def __init__(self):
        # Active connections: websocket -> connection_info
        self.active_connections: Dict[WebSocket, dict] = {}
        
        # Room subscriptions: room_id -> set of websockets
        self.rooms: Dict[str, set[WebSocket]] = {}
        
        # User connections: user_id -> set of websockets
        self.user_connections: Dict[str, set[WebSocket]] = {}
        
        # Tenant connections: tenant_id -> set of websockets
        self.tenant_connections: Dict[str, set[WebSocket]] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        tenant_id: str
    ) -> None:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            user_id: Authenticated user ID
            tenant_id: Tenant ID
        """
        await websocket.accept()
        
        connection_info = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "connected_at": datetime.utcnow(),
            "last_heartbeat": datetime.utcnow(),
            "rooms": set(),
        }
        
        self.active_connections[websocket] = connection_info
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Add to tenant connections
        if tenant_id not in self.tenant_connections:
            self.tenant_connections[tenant_id] = set()
        self.tenant_connections[tenant_id].add(websocket)
        
        # Send welcome message
        await self.send_personal(
            websocket,
            {
                "type": "connected",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove and close a WebSocket connection.
        
        Args:
            websocket: WebSocket to disconnect
        """
        if websocket not in self.active_connections:
            return
        
        connection_info = self.active_connections[websocket]
        
        # Remove from rooms
        for room_id in connection_info.get("rooms", []):
            if room_id in self.rooms:
                self.rooms[room_id].discard(websocket)
        
        # Remove from user connections
        user_id = connection_info.get("user_id")
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from tenant connections
        tenant_id = connection_info.get("tenant_id")
        if tenant_id and tenant_id in self.tenant_connections:
            self.tenant_connections[tenant_id].discard(websocket)
            if not self.tenant_connections[tenant_id]:
                del self.tenant_connections[tenant_id]
        
        # Remove from active connections
        del self.active_connections[websocket]
    
    async def send_personal(
        self,
        websocket: WebSocket,
        message: dict
    ) -> bool:
        """
        Send a message to a specific connection.
        
        Args:
            websocket: Target WebSocket
            message: Message dict
        
        Returns:
            True if sent successfully
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            return False
    
    async def send_to_user(
        self,
        user_id: str,
        message: dict
    ) -> int:
        """
        Send message to all connections of a user.
        
        Args:
            user_id: Target user ID
            message: Message dict
        
        Returns:
            Number of connections messaged
        """
        count = 0
        websockets = self.user_connections.get(user_id, set())
        
        for websocket in websockets:
            if await self.send_personal(websocket, message):
                count += 1
        
        return count
    
    async def send_to_tenant(
        self,
        tenant_id: str,
        message: dict
    ) -> int:
        """
        Send message to all connections in a tenant.
        
        Args:
            tenant_id: Target tenant ID
            message: Message dict
        
        Returns:
            Number of connections messaged
        """
        count = 0
        websockets = self.tenant_connections.get(tenant_id, set())
        
        for websocket in websockets:
            if await self.send_personal(websocket, message):
                count += 1
        
        return count
    
    async def join_room(
        self,
        websocket: WebSocket,
        room_id: str
    ) -> bool:
        """
        Join a room for targeted broadcasting.
        
        Args:
            websocket: WebSocket connection
            room_id: Room ID (e.g., run_id, generation_id)
        
        Returns:
            True if joined successfully
        """
        if websocket not in self.active_connections:
            return False
        
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(websocket)
        self.active_connections[websocket]["rooms"].add(room_id)
        
        # Send confirmation
        await self.send_personal(
            websocket,
            {
                "type": "room_joined",
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        
        return True
    
    async def leave_room(
        self,
        websocket: WebSocket,
        room_id: str
    ) -> bool:
        """
        Leave a room.
        
        Args:
            websocket: WebSocket connection
            room_id: Room ID
        
        Returns:
            True if left successfully
        """
        if websocket not in self.active_connections:
            return False
        
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
        
        self.active_connections[websocket]["rooms"].discard(room_id)
        
        return True
    
    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict
    ) -> int:
        """
        Broadcast message to all connections in a room.
        
        Args:
            room_id: Room ID
            message: Message dict
        
        Returns:
            Number of connections messaged
        """
        count = 0
        websockets = self.rooms.get(room_id, set())
        
        # Create a copy to avoid modification during iteration
        for websocket in websockets.copy():
            if await self.send_personal(websocket, message):
                count += 1
            else:
                # Connection dead, remove from room
                self.rooms[room_id].discard(websocket)
        
        return count
    
    async def broadcast(
        self,
        message: dict,
        tenant_id: Optional[str] = None
    ) -> int:
        """
        Broadcast message to all connections (optionally filtered by tenant).
        
        Args:
            message: Message dict
            tenant_id: Optional tenant filter
        
        Returns:
            Number of connections messaged
        """
        count = 0
        
        if tenant_id:
            websockets = self.tenant_connections.get(tenant_id, set())
        else:
            websockets = set(self.active_connections.keys())
        
        for websocket in websockets:
            if await self.send_personal(websocket, message):
                count += 1
        
        return count
    
    async def heartbeat(
        self,
        websocket: WebSocket
    ) -> bool:
        """
        Update heartbeat timestamp for a connection.
        
        Args:
            websocket: WebSocket connection
        
        Returns:
            True if connection exists
        """
        if websocket not in self.active_connections:
            return False
        
        self.active_connections[websocket]["last_heartbeat"] = datetime.utcnow()
        
        await self.send_personal(
            websocket,
            {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        
        return True
    
    def get_connection_count(self) -> int:
        """Get total active connection count."""
        return len(self.active_connections)
    
    def get_room_count(self, room_id: str) -> int:
        """Get connection count for a room."""
        return len(self.rooms.get(room_id, set()))
    
    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "total_rooms": len(self.rooms),
            "users_connected": len(self.user_connections),
            "tenants_connected": len(self.tenant_connections),
        }


# Global manager instance
manager = ConnectionManager()
