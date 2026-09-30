"""
LLMSync Cleanup Worker

Background worker that enforces retention policies:
- Deletes files past grace period
- Cleans up old sync events
- Removes soft-deleted data after retention period
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from llmsync.config import settings
from llmsync.database import async_session_maker
from llmsync.models import File, Message, Thread, SyncEvent
from llmsync.services.minio_client import minio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_deleted_files():
    """Delete files past retention grace period from MinIO and database."""
    if not settings.retention_enabled:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_grace_period_days)

    async with async_session_maker() as db:
        # Get files to delete
        result = await db.execute(
            select(File).where(
                File.deleted_at < cutoff,
                File.deleted_at.isnot(None)
            )
        )
        files = result.scalars().all()

        deleted_count = 0
        for file in files:
            try:
                # Delete from MinIO
                minio_client.delete_file(file.storage_path)

                # Delete from database
                await db.delete(file)
                deleted_count += 1

            except Exception as e:
                logger.error(f"Failed to delete file {file.id}: {e}")

        await db.commit()

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} deleted files")

        return deleted_count

async def cleanup_old_sync_events():
    """Delete sync events older than retention period."""
    if not settings.retention_enabled:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days_messages)

    async with async_session_maker() as db:
        result = await db.execute(
            delete(SyncEvent).where(SyncEvent.timestamp < cutoff)
        )
        await db.commit()

        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old sync events")

        return deleted_count

async def cleanup_old_messages():
    """Soft-delete messages older than retention period."""
    if not settings.retention_enabled:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days_messages)

    async with async_session_maker() as db:
        # Find messages to soft-delete
        result = await db.execute(
            select(Message).where(
                Message.timestamp < cutoff,
                Message.deleted_at.is_(None)
            )
        )
        messages = result.scalars().all()

        for message in messages:
            message.deleted_at = datetime.now(timezone.utc)

        await db.commit()

        if len(messages) > 0:
            logger.info(f"Soft-deleted {len(messages)} old messages")

        return len(messages)

async def cleanup_loop():
    """Main cleanup loop - runs hourly."""
    while True:
        try:
            logger.info("Starting cleanup cycle")

            files_deleted = await cleanup_deleted_files()
            events_deleted = await cleanup_old_sync_events()
            messages_deleted = await cleanup_old_messages()

            logger.info(
                f"Cleanup cycle complete: "
                f"{files_deleted} files, "
                f"{events_deleted} events, "
                f"{messages_deleted} messages"
            )

        except Exception as e:
            logger.error(f"Cleanup cycle error: {e}")

        # Wait 1 hour
        await asyncio.sleep(3600)

if __name__ == "__main__":
    logger.info("Starting LLMSync cleanup worker")
    asyncio.run(cleanup_loop())
