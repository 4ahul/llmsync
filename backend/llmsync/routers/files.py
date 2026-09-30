from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from datetime import datetime, timezone
from io import BytesIO
from llmsync.database import get_db
from llmsync.models import File, Message, User, SyncEvent
from llmsync.dependencies import get_current_user
from llmsync.services.minio_client import minio_client, infer_mime_type
from llmsync.crypto import encrypt_file, decrypt_file, generate_master_key
from llmsync.routers.sync import broadcast_event_to_user
from llmsync.schemas import FileUploadMetadata
import base64

router = APIRouter(prefix="/api/files", tags=["files"])

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

@router.post("/encrypted", status_code=201)
async def upload_encrypted_file(
    metadata: FileUploadMetadata = Form(...),
    encrypted_file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload pre-encrypted file (proper E2EE).

    Client should:
    1. Generate ephemeral file key
    2. Encrypt file with AES-256-GCM
    3. Encrypt file key with user's master key
    4. Upload encrypted file + metadata
    """
    # Verify message exists
    result = await db.execute(
        select(Message).where(
            Message.id == metadata.message_id,
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

    # Read encrypted file data
    encrypted_data = await encrypted_file.read()

    if len(encrypted_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_FILE_SIZE} bytes)"
        )

    # Upload to MinIO (already encrypted)
    file_id = uuid4()
    storage_path = minio_client.upload_file(
        user_id=current_user.id,
        file_id=file_id,
        data=encrypted_data,
        content_type="application/octet-stream"
    )

    # Create file record
    file_record = File(
        id=file_id,
        message_id=metadata.message_id,
        user_id=current_user.id,
        filename=metadata.filename,
        mime_type=metadata.mime_type,
        size_bytes=metadata.size_bytes,
        storage_path=storage_path,
        encrypted_key=metadata.encrypted_key,
        nonce=metadata.nonce
    )
    db.add(file_record)

    # Create sync event
    sync_event = SyncEvent(
        user_id=current_user.id,
        event_type="file_uploaded",
        entity_id=file_id,
        entity_type="file",
        payload={"message_id": str(metadata.message_id)}
    )
    db.add(sync_event)

    await db.commit()
    await db.refresh(file_record)
    await db.refresh(sync_event)

    # Broadcast
    await broadcast_event_to_user(str(current_user.id), {
        "id": sync_event.id,
        "event_type": sync_event.event_type,
        "entity_id": str(sync_event.entity_id),
        "entity_type": sync_event.entity_type,
        "payload": sync_event.payload,
        "timestamp": sync_event.timestamp.isoformat()
    })

    return {
        "id": str(file_record.id),
        "message_id": str(file_record.message_id),
        "filename": file_record.filename,
        "mime_type": file_record.mime_type,
        "size_bytes": file_record.size_bytes,
        "uploaded_at": file_record.uploaded_at.isoformat() if file_record.uploaded_at else None
    }

@router.post("", status_code=201)
async def upload_file(
    message_id: UUID = Form(...),
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload encrypted file."""
    # Verify message exists and belongs to user
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

    # Read file data
    file_data = await file.read()
    file_size = len(file_data)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_FILE_SIZE} bytes)"
        )

    # Infer MIME type
    mime_type = infer_mime_type(file.filename, file.content_type)

    # Encrypt file (using temporary master key - TODO: use user's actual master key)
    master_key = generate_master_key()
    encrypted = encrypt_file(file_data, master_key)

    # Upload to MinIO
    file_id = uuid4()
    storage_path = minio_client.upload_file(
        user_id=current_user.id,
        file_id=file_id,
        data=bytes.fromhex(encrypted["encrypted_data"]) if isinstance(encrypted["encrypted_data"], str) else encrypted["encrypted_data"],
        content_type="application/octet-stream"
    )

    # Create file record
    file_record = File(
        id=file_id,
        message_id=message_id,
        user_id=current_user.id,
        filename=file.filename,
        mime_type=mime_type,
        size_bytes=file_size,
        storage_path=storage_path,
        encrypted_key=encrypted["encrypted_key"],
        nonce=encrypted["nonce"]
    )
    db.add(file_record)

    # Create sync event
    sync_event = SyncEvent(
        user_id=current_user.id,
        event_type="file_uploaded",
        entity_id=file_id,
        entity_type="file",
        payload={"message_id": str(message_id)}
    )
    db.add(sync_event)

    await db.commit()
    await db.refresh(file_record)
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

    return {
        "id": str(file_record.id),
        "message_id": str(file_record.message_id),
        "filename": file_record.filename,
        "mime_type": file_record.mime_type,
        "size_bytes": file_record.size_bytes,
        "uploaded_at": file_record.uploaded_at.isoformat() if file_record.uploaded_at else None
    }

@router.get("/{file_id}/metadata")
async def get_file_metadata(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get file metadata (for client-side decryption)."""
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == current_user.id,
            File.deleted_at.is_(None)
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return {
        "id": str(file_record.id),
        "filename": file_record.filename,
        "mime_type": file_record.mime_type,
        "size_bytes": file_record.size_bytes,
        "encrypted_key": file_record.encrypted_key,
        "nonce": file_record.nonce,
        "message_id": str(file_record.message_id)
    }

@router.get("/{file_id}/download")
async def download_encrypted_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download encrypted file data (client decrypts locally)."""
    # Get file record
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == current_user.id,
            File.deleted_at.is_(None)
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Download encrypted data from MinIO
    encrypted_data = minio_client.download_file(file_record.storage_path)

    # Return encrypted data with encryption metadata in headers
    return StreamingResponse(
        BytesIO(encrypted_data),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file_record.filename}.enc"',
            "X-Encrypted-Key": file_record.encrypted_key,
            "X-Nonce": file_record.nonce,
            "X-Original-Filename": file_record.filename,
            "X-Original-MimeType": file_record.mime_type or "application/octet-stream"
        }
    )

@router.delete("/{file_id}")
async def delete_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft-delete file."""
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == current_user.id,
            File.deleted_at.is_(None)
        )
    )
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_record.deleted_at = datetime.now(timezone.utc)

    # Create sync event
    sync_event = SyncEvent(
        user_id=current_user.id,
        event_type="file_deleted",
        entity_id=file_id,
        entity_type="file",
        payload={"message_id": str(file_record.message_id)}
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

    return {"message": "File deleted successfully"}
