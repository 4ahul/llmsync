from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from llmsync.database import get_db
from llmsync.models import Thread, User
from llmsync.schemas import ThreadCreate, ThreadUpdate, ThreadResponse
from llmsync.dependencies import get_current_user

router = APIRouter(prefix="/api/threads", tags=["threads"])

@router.post("", response_model=ThreadResponse)
async def create_thread(
    thread_data: ThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new thread."""
    thread = Thread(
        user_id=current_user.id,
        title=thread_data.title
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    return thread

@router.get("", response_model=dict)
async def list_threads(
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's threads (paginated)."""
    query = select(Thread).where(
        Thread.user_id == current_user.id,
        Thread.deleted_at.is_(None)
    ).order_by(Thread.updated_at.desc())

    if cursor:
        # Get cursor thread's updated_at
        cursor_thread = await db.get(Thread, cursor)
        if cursor_thread:
            query = query.where(Thread.updated_at < cursor_thread.updated_at)

    query = query.limit(limit + 1)  # Fetch one extra to check has_more
    result = await db.execute(query)
    threads = result.scalars().all()

    has_more = len(threads) > limit
    threads = threads[:limit]

    next_cursor = threads[-1].id if has_more and threads else None

    return {
        "threads": [ThreadResponse.model_validate(t) for t in threads],
        "next_cursor": str(next_cursor) if next_cursor else None,
        "has_more": has_more
    }

@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get thread by ID."""
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

    return thread

@router.put("/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: UUID,
    thread_data: ThreadUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update thread."""
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

    if thread_data.title is not None:
        thread.title = thread_data.title
        thread.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(thread)

    return thread

@router.delete("/{thread_id}")
async def delete_thread(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft-delete thread."""
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

    thread.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Thread deleted successfully"}
