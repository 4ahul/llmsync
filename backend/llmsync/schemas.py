from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class ThreadCreate(BaseModel):
    title: Optional[str] = None

class ThreadUpdate(BaseModel):
    title: Optional[str] = None

class ThreadResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    id: UUID  # UUID v7, generated client-side
    thread_seq: int
    encrypted_content: str
    encrypted_key: str
    nonce: str
    role: str = Field(..., pattern="^(user|assistant)$")
    model: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    timestamp: datetime

class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    user_id: UUID
    device_id: Optional[UUID]
    thread_seq: int
    global_seq: int
    encrypted_content: str
    encrypted_key: str
    nonce: str
    role: str
    model: Optional[str]
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Encryption setup schemas
class EncryptionSetup(BaseModel):
    encrypted_master_key_backup: str
    salt: str  # base64 encoded
    recovery_phrase_hash: str  # SHA-256 hash of normalized recovery phrase

class EncryptionKeyResponse(BaseModel):
    encrypted_master_key_backup: str
    salt: str
    has_backup: bool

class RecoveryRequest(BaseModel):
    recovery_phrase: str

# Device schemas
class DeviceCreate(BaseModel):
    device_name: Optional[str] = None
    device_fingerprint: str
    public_key: str

class DeviceResponse(BaseModel):
    id: UUID
    user_id: UUID
    device_name: Optional[str]
    device_fingerprint: str
    public_key: str
    added_at: datetime
    last_seen_at: Optional[datetime]

    class Config:
        from_attributes = True

# File upload with pre-encryption
class FileUploadMetadata(BaseModel):
    message_id: UUID
    filename: str
    mime_type: str
    size_bytes: int  # Original size before encryption
    encrypted_key: str  # base64
    nonce: str  # base64
