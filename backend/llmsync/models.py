from sqlalchemy import Column, String, Text, BigInteger, Integer, ForeignKey, Index, TIMESTAMP, LargeBinary, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4
from llmsync.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    encrypted_master_key_backup = Column(Text, nullable=False)
    salt = Column(LargeBinary, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)

class Device(Base):
    __tablename__ = "devices"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(255), nullable=True)
    device_fingerprint = Column(String(255), unique=True, nullable=False, index=True)
    public_key = Column(Text, nullable=False)
    added_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_seen_at = Column(TIMESTAMP(timezone=True), nullable=True)

class Thread(Base):
    __tablename__ = "threads"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_message_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_threads_user_updated", "user_id", updated_at.desc()),
    )

class Message(Base):
    __tablename__ = "messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)  # UUID v7, generated client-side
    thread_id = Column(PG_UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(PG_UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)

    thread_seq = Column(BigInteger, nullable=False)
    global_seq = Column(BigInteger, autoincrement=True, nullable=False)

    encrypted_content = Column(Text, nullable=False)
    encrypted_key = Column(Text, nullable=False)
    nonce = Column(Text, nullable=False)

    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    model = Column(String(100), nullable=True)
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)

    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_messages_thread_seq", "thread_id", "thread_seq", unique=True),
        Index("idx_messages_global", "global_seq"),
        Index("idx_messages_timestamp", timestamp.desc()),
        Index("idx_messages_user_timestamp", "user_id", timestamp.desc()),
    )

class File(Base):
    __tablename__ = "files"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(PG_UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(BigInteger, nullable=False)

    storage_path = Column(Text, nullable=False)

    encrypted_key = Column(Text, nullable=False)
    nonce = Column(Text, nullable=False)

    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_files_user_uploaded", "user_id", uploaded_at.desc()),
    )

class SyncEvent(Base):
    __tablename__ = "sync_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    entity_id = Column(PG_UUID(as_uuid=True), nullable=False)
    entity_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_sync_events_user_id", "user_id", "id"),
        Index("idx_sync_events_timestamp", "timestamp"),
    )
