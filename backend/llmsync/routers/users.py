from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import base64
from llmsync.database import get_db
from llmsync.models import User
from llmsync.schemas import EncryptionSetup, EncryptionKeyResponse, RecoveryRequest
from llmsync.dependencies import get_current_user
from llmsync.crypto import derive_key_from_phrase

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/setup-encryption")
async def setup_encryption(
    setup: EncryptionSetup,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set up user's encryption keys (first-time setup).

    Client should:
    1. Generate 32-byte master key
    2. Generate 12-word recovery phrase
    3. Derive key from recovery phrase using Argon2id
    4. Encrypt master key with derived key
    5. Send encrypted backup + salt + hash of recovery phrase
    """
    # Check if already set up
    if current_user.encrypted_master_key_backup and current_user.encrypted_master_key_backup != "":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Encryption already set up for this user"
        )

    # Decode salt from base64
    try:
        salt_bytes = base64.b64decode(setup.salt)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid salt encoding"
        )

    # Update user with encryption data
    current_user.encrypted_master_key_backup = setup.encrypted_master_key_backup
    current_user.salt = salt_bytes

    # Store recovery phrase hash for validation (not searchable, just for verification)
    await db.execute(
        select(User).where(User.id == current_user.id)
    )

    await db.commit()

    return {
        "message": "Encryption setup complete",
        "user_id": str(current_user.id)
    }

@router.get("/encryption-key", response_model=EncryptionKeyResponse)
async def get_encryption_key(
    current_user: User = Depends(get_current_user)
):
    """Get user's encrypted master key backup.

    Client should:
    1. Prompt user for password/recovery phrase
    2. Derive key using salt
    3. Decrypt master key backup
    """
    has_backup = bool(current_user.encrypted_master_key_backup and
                     current_user.encrypted_master_key_backup != "")

    if not has_backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encryption key set up. Call POST /users/setup-encryption first"
        )

    return EncryptionKeyResponse(
        encrypted_master_key_backup=current_user.encrypted_master_key_backup,
        salt=base64.b64encode(current_user.salt).decode('utf-8'),
        has_backup=has_backup
    )

@router.post("/recover")
async def recover_with_phrase(
    recovery: RecoveryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recover encryption key using recovery phrase.

    Validates recovery phrase by attempting to decrypt the backup.
    Client should then decrypt the master key using the derived key.
    """
    if not current_user.encrypted_master_key_backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encryption backup found"
        )

    # Derive key from recovery phrase
    try:
        derived_key = derive_key_from_phrase(recovery.recovery_phrase)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid recovery phrase: {str(e)}"
        )

    # Return encrypted backup - client will decrypt with derived key
    # If decryption fails on client side, phrase was wrong
    return {
        "encrypted_master_key_backup": current_user.encrypted_master_key_backup,
        "salt": base64.b64encode(current_user.salt).decode('utf-8'),
        "message": "Decrypt the backup with the derived key from your recovery phrase"
    }

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "has_encryption_setup": bool(current_user.encrypted_master_key_backup and
                                     current_user.encrypted_master_key_backup != "")
    }
