import pytest
from sqlalchemy import select
from llmsync.models import User, Device, Thread, Message, File, SyncEvent
from uuid import uuid4
from datetime import datetime, timezone

def test_user_model_creation():
    """Test User model can be instantiated"""
    user = User(
        email="test@example.com",
        encrypted_master_key_backup="encrypted_backup",
        salt=b"salt_bytes"
    )
    assert user.email == "test@example.com"
    assert user.encrypted_master_key_backup == "encrypted_backup"
    assert user.salt == b"salt_bytes"

def test_device_model_creation():
    """Test Device model can be instantiated"""
    user_id = uuid4()
    device = Device(
        user_id=user_id,
        device_name="Test Device",
        device_fingerprint="fingerprint123",
        public_key="public_key_data"
    )
    assert device.user_id == user_id
    assert device.device_name == "Test Device"
    assert device.device_fingerprint == "fingerprint123"

def test_thread_model_creation():
    """Test Thread model can be instantiated"""
    user_id = uuid4()
    thread = Thread(
        user_id=user_id,
        title="Test Thread"
    )
    assert thread.user_id == user_id
    assert thread.title == "Test Thread"

def test_message_model_creation():
    """Test Message model can be instantiated"""
    thread_id = uuid4()
    user_id = uuid4()
    device_id = uuid4()
    message_id = uuid4()

    message = Message(
        id=message_id,
        thread_id=thread_id,
        user_id=user_id,
        device_id=device_id,
        thread_seq=1,
        encrypted_content="encrypted",
        encrypted_key="key",
        nonce="nonce",
        role="user",
        model="gpt-4",
        tokens_input=100,
        tokens_output=50,
        timestamp=datetime.now(timezone.utc)
    )
    assert message.id == message_id
    assert message.thread_id == thread_id
    assert message.user_id == user_id
    assert message.role == "user"

def test_file_model_creation():
    """Test File model can be instantiated"""
    message_id = uuid4()
    user_id = uuid4()

    file = File(
        message_id=message_id,
        user_id=user_id,
        filename="test.txt",
        mime_type="text/plain",
        size_bytes=1024,
        storage_path="/files/test.txt",
        encrypted_key="key",
        nonce="nonce"
    )
    assert file.message_id == message_id
    assert file.filename == "test.txt"
    assert file.size_bytes == 1024

def test_sync_event_model_creation():
    """Test SyncEvent model can be instantiated"""
    user_id = uuid4()
    entity_id = uuid4()

    sync_event = SyncEvent(
        user_id=user_id,
        event_type="message_created",
        entity_id=entity_id,
        entity_type="message",
        payload={"content": "test"}
    )
    assert sync_event.user_id == user_id
    assert sync_event.event_type == "message_created"
    assert sync_event.payload == {"content": "test"}

@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires live Postgres database")
async def test_create_user_db(db_session):
    """Test creating and fetching a user from database"""
    user = User(
        email="test@example.com",
        encrypted_master_key_backup="encrypted_backup",
        salt=b"salt_bytes"
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    fetched = result.scalar_one()
    assert fetched.email == "test@example.com"
    assert fetched.id is not None
