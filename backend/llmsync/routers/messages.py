from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from llmsync.database import get_db
from llmsync.models import Message, Thread, User, SyncEvent
from llmsync.schemas import MessageCreate, MessageResponse
from llmsync.dependencies import get_current_user
from llmsync.routers.sync import broadcast_event_to_user

router = APIRouter(prefix="/api", tags=["messages"])

@router.post("/threads/{thread_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    thread_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a message in a thread."""
    # Verify thread exists and belongs to user
    result = await db.execute(
        select(Thread).where(
            Thread.id == thread_id,
            Thread.user_id == current_user.id,
            Thread.deleted_at.is_(None)
        )
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found or deleted"
        )

    # Create message
    message = Message(
        id=message_data.id,
        thread_id=thread_id,
        user_id=current_user.id,
        thread_seq=message_data.thread_seq,
        encrypted_content=message_data.encrypted_content,
        encrypted_key=message_data.encrypted_key,
        nonce=message_data.nonce,
        role=message_data.role,
        model=message_data.model,
        tokens_input=message_data.tokens_input,
        tokens_output=message_data.tokens_output,
        timestamp=message_data.timestamp
    )

    try:
        db.add(message)
        await db.commit()
        await db.refresh(message)
    except IntegrityError as e:
        await db.rollback()
        # Check if it's duplicate UUID - idempotent return
        if "messages_pkey" in str(e) or "duplicate key" in str(e).lower():
            result = await db.execute(
                select(Message).where(Message.id == message_data.id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Message conflict"
        )

    # Update thread last_message_at
    thread.last_message_at = message.timestamp
    thread.updated_at = datetime.now(timezone.utc)

    # Create sync event
    sync_event = SyncEvent(
        user_id=current_user.id,
        event_type="message_created",
        entity_id=message.id,
        entity_type="message",
        payload={"thread_id": str(thread_id)}
    )
    db.add(sync_event)

    await db.commit()
    await db.refresh(message)
    await db.refresh(sync_event)

    # Broadcast to connected clients
    await broadcast_event_to_user(str(current_user.id), {
        "id": sync_event.id,
        "event_type": sync_event.event_type,
        "entity_id": str(sync_event.entity_id),
        "entity_type": sync_event.entity_type,
        "payload": sync_event.payload,
        "timestamp": sync_event.timestamp.isoformat()
    })

    return message

@router.get("/threads/{thread_id}/messages", response_model=dict)
async def list_messages(
    thread_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    seq_from: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List messages in a thread."""
    # Verify thread access
    result = await db.execute(
        select(Thread).where(
            Thread.id == thread_id,
            Thread.user_id == current_user.id,
            Thread.deleted_at.is_(None)
        )
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Fetch messages
    query = select(Message).where(
        Message.thread_id == thread_id,
        Message.thread_seq >= seq_from,
        Message.deleted_at.is_(None)
    ).order_by(Message.thread_seq.asc()).limit(limit + 1)

    result = await db.execute(query)
    messages = result.scalars().all()

    has_more = len(messages) > limit
    messages = messages[:limit]

    return {
        "messages": [MessageResponse.model_validate(m) for m in messages],
        "has_more": has_more
    }

@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message by ID."""
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.user_id == current_user.id,
            Message.deleted_at.is_(None)
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    return message

@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft-delete message."""
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.user_id == current_user.id,
            Message.deleted_at.is_(None)
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    message.deleted_at = datetime.now(timezone.utc)

    # Create sync event
    sync_event = SyncEvent(
        user_id=current_user.id,
        event_type="message_deleted",
        entity_id=message.id,
        entity_type="message",
        payload={"thread_id": str(message.thread_id)}
    )
    db.add(sync_event)

    await db.commit()
    await db.refresh(sync_event)

    # Broadcast to connected clients
    await broadcast_event_to_user(str(current_user.id), {
        "id": sync_event.id,
        "event_type": sync_event.event_type,
        "entity_id": str(sync_event.entity_id),
        "entity_type": sync_event.entity_type,
        "payload": sync_event.payload,
        "timestamp": sync_event.timestamp.isoformat()
    })

    return {"message": "Message deleted successfully"}
