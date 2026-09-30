from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone
from llmsync.database import get_db
from llmsync.models import Device, User
from llmsync.schemas import DeviceCreate, DeviceResponse
from llmsync.dependencies import get_current_user

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.post("", response_model=DeviceResponse, status_code=201)
async def register_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a new device for the user.

    Device fingerprint should be unique per device (e.g., hash of hardware info).
    Public key is used for device-to-device encrypted communication.
    """
    # Check if device already exists (idempotent)
    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.device_fingerprint == device_data.device_fingerprint
        )
    )
    existing_device = result.scalar_one_or_none()

    if existing_device:
        # Update last_seen_at
        existing_device.last_seen_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing_device)
        return existing_device

    # Create new device
    device = Device(
        user_id=current_user.id,
        device_name=device_data.device_name,
        device_fingerprint=device_data.device_fingerprint,
        public_key=device_data.public_key,
        last_seen_at=datetime.now(timezone.utc)
    )

    try:
        db.add(device)
        await db.commit()
        await db.refresh(device)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device fingerprint already registered"
        )

    return device

@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all registered devices for the user."""
    result = await db.execute(
        select(Device).where(
            Device.user_id == current_user.id
        ).order_by(Device.added_at.desc())
    )
    devices = result.scalars().all()

    return devices

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific device."""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    return device

@router.delete("/{device_id}")
async def unregister_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unregister a device."""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    await db.delete(device)
    await db.commit()

    return {"message": "Device unregistered successfully"}

@router.post("/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update device last_seen_at timestamp."""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    device.last_seen_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Heartbeat recorded", "last_seen_at": device.last_seen_at.isoformat()}
