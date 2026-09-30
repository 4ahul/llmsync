from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
import json
import asyncio
from llmsync.database import get_db
from llmsync.models import SyncEvent, User
from llmsync.auth import decode_access_token
from llmsync.services.redis_client import redis_client
from llmsync.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])

class ConnectionManager:
    """Manage WebSocket connections with Redis pub/sub."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.pubsub_tasks: dict[str, asyncio.Task] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Register new WebSocket connection for user."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

        # Start pub/sub listener for this user if not already running
        if user_id not in self.pubsub_tasks:
            task = asyncio.create_task(self._listen_to_pubsub(user_id))
            self.pubsub_tasks[user_id] = task

    def disconnect(self, user_id: str, websocket: WebSocket):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
            except ValueError:
                pass  # Already removed

            # If no more connections, cancel pub/sub task
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.pubsub_tasks:
                    self.pubsub_tasks[user_id].cancel()
                    del self.pubsub_tasks[user_id]

        logger.info(f"User {user_id} disconnected")

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a user."""
        if user_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to connection: {e}")
                    dead_connections.append(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(user_id, conn)

    async def _listen_to_pubsub(self, user_id: str):
        """Listen to Redis pub/sub channel for user's sync events."""
        channel = f"sync:{user_id}"
        try:
            pubsub = await redis_client.subscribe(channel)
            logger.info(f"Started pub/sub listener for user {user_id}")

            while user_id in self.active_connections:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message['type'] == 'message':
                        # Parse and broadcast to all user's connections
                        data = json.loads(message['data'])
                        await self.send_to_user(user_id, {
                            "type": "sync_event",
                            "event": data
                        })
                except Exception as e:
                    logger.error(f"Error in pub/sub listener: {e}")
                    await asyncio.sleep(1)

            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"Stopped pub/sub listener for user {user_id}")

        except asyncio.CancelledError:
            logger.info(f"Pub/sub listener cancelled for user {user_id}")
        except Exception as e:
            logger.error(f"Pub/sub listener error for user {user_id}: {e}")

manager = ConnectionManager()

async def broadcast_event_to_user(user_id: str, event_data: dict):
    """Publish sync event to user's Redis channel."""
    channel = f"sync:{user_id}"
    try:
        await redis_client.publish(channel, json.dumps(event_data))
    except Exception as e:
        logger.error(f"Failed to broadcast event: {e}")

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time sync."""
    user_id = None
    try:
        # Authenticate
        payload = decode_access_token(token)
        user_id = payload["user_id"]

        # Verify user exists
        result = await db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()

        if not user:
            await websocket.close(code=1008, reason="User not found")
            return

        # Connect
        await manager.connect(user_id, websocket)

        try:
            while True:
                # Receive messages (ping/cursor updates)
                data = await websocket.receive_json()

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "cursor":
                    # Store cursor in Redis
                    cursor = data.get("cursor", 0)
                    await redis_client.set_with_expiry(
                        f"sync_cursor:{user_id}",
                        str(cursor),
                        expire_seconds=30 * 24 * 60 * 60  # 30 days
                    )
        except WebSocketDisconnect:
            if user_id:
                manager.disconnect(user_id, websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if user_id:
                manager.disconnect(user_id, websocket)

    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        try:
            await websocket.close(code=1008, reason="Authentication failed")
        except:
            pass

@router.get("/events")
async def get_sync_events(
    cursor: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sync events since cursor (polling fallback)."""
    query = select(SyncEvent).where(
        SyncEvent.user_id == current_user.id,
        SyncEvent.id > cursor
    ).order_by(SyncEvent.id.asc()).limit(limit)

    result = await db.execute(query)
    events = result.scalars().all()

    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "entity_id": str(e.entity_id),
                "entity_type": e.entity_type,
                "payload": e.payload,
                "timestamp": e.timestamp.isoformat()
            }
            for e in events
        ],
        "cursor": events[-1].id if events else cursor
    }
