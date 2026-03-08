"""
APE - Autonomous Production Engineer
WebSocket API

WebSocket endpoint for real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Optional

from server.websocket.manager import manager
from server.models.auth import get_current_user, verify_token
from server.database.models.tenant import UserModel

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for real-time updates.
    
    Connect with: ws://localhost:8000/ws?token=YOUR_ACCESS_TOKEN
    
    After connecting:
    - Join rooms: {"type": "join_room", "room_id": "run_123"}
    - Leave rooms: {"type": "leave_room", "room_id": "run_123"}
    - Heartbeat: {"type": "heartbeat"}
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    # Verify token
    token_data = verify_token(token, "access")
    if not token_data:
        await websocket.close(code=4002, reason="Invalid token")
        return
    
    # Connect
    await manager.connect(
        websocket=websocket,
        user_id=token_data.user_id,
        tenant_id=token_data.tenant_id,
    )
    
    try:
        while True:
            # Receive messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "join_room":
                room_id = message.get("room_id")
                if room_id:
                    await manager.join_room(websocket, room_id)
            
            elif msg_type == "leave_room":
                room_id = message.get("room_id")
                if room_id:
                    await manager.leave_room(websocket, room_id)
            
            elif msg_type == "heartbeat":
                await manager.heartbeat(websocket)
            
            elif msg_type == "get_stats":
                stats = manager.get_stats()
                await manager.send_personal(websocket, {
                    "type": "stats",
                    **stats,
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        raise


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    """
    return manager.get_stats()


@router.get("/ws/room/{room_id}")
async def get_room_stats(room_id: str):
    """
    Get connection count for a specific room.
    """
    return {
        "room_id": room_id,
        "connection_count": manager.get_room_count(room_id),
    }
