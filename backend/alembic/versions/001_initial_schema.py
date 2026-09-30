"""Initial schema

Revision ID: 001
Create Date: 2026-09-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('encrypted_master_key_backup', sa.Text(), nullable=False),
        sa.Column('salt', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_name', sa.String(255), nullable=True),
        sa.Column('device_fingerprint', sa.String(255), unique=True, nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('added_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_devices_user_id', 'devices', ['user_id'])
    op.create_index('idx_devices_fingerprint', 'devices', ['device_fingerprint'])

    op.create_table(
        'threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('last_message_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_threads_user_updated', 'threads', ['user_id', sa.desc(sa.column('updated_at'))])

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thread_seq', sa.BigInteger(), nullable=False),
        sa.Column('global_seq', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('encrypted_content', sa.Text(), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('nonce', sa.Text(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('tokens_input', sa.Integer(), nullable=True),
        sa.Column('tokens_output', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_messages_thread_seq', 'messages', ['thread_id', 'thread_seq'], unique=True)
    op.create_index('idx_messages_global', 'messages', ['global_seq'])
    op.create_index('idx_messages_timestamp', 'messages', [sa.desc(sa.column('timestamp'))])
    op.create_index('idx_messages_user_timestamp', 'messages', ['user_id', sa.desc(sa.column('timestamp'))])

    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('nonce', sa.Text(), nullable=False),
        sa.Column('uploaded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_files_message_id', 'files', ['message_id'])
    op.create_index('idx_files_user_uploaded', 'files', ['user_id', sa.desc(sa.column('uploaded_at'))])

    op.create_table(
        'sync_events',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_sync_events_user_id', 'sync_events', ['user_id', 'id'])
    op.create_index('idx_sync_events_timestamp', 'sync_events', ['timestamp'])

def downgrade() -> None:
    op.drop_table('sync_events')
    op.drop_table('files')
    op.drop_table('messages')
    op.drop_table('threads')
    op.drop_table('devices')
    op.drop_table('users')
