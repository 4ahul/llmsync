# LLMSync API Reference

Base URL: `http://localhost:8000`

All authenticated endpoints require the `Authorization: Bearer <token>` header.

## Authentication

### POST /api/auth/login/magic-link

Request a magic link for email-based authentication.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Check your email for login link"
}
```

### GET /api/auth/verify

Verify magic link token and get access tokens.

**Query Parameters:**
- `token` (required): Magic link token from email

**Response:**
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2026-09-30T12:00:00"
  }
}
```

### POST /api/auth/refresh

Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAi..."
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

### POST /api/auth/logout

Logout and invalidate current session.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

## Threads

### POST /api/threads

Create a new conversation thread.

**Headers:**
- `Authorization: Bearer <token>`

**Request:**
```json
{
  "title": "My Conversation"  // optional
}
```

**Response:**
```json
{
  "id": "thread-uuid",
  "user_id": "user-uuid",
  "title": "My Conversation",
  "created_at": "2026-09-30T12:00:00",
  "updated_at": "2026-09-30T12:00:00",
  "last_message_at": null
}
```

### GET /api/threads

List user's threads with pagination.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional, default: 20, max: 100): Number of threads to return
- `cursor` (optional): UUID of last thread from previous page

**Response:**
```json
{
  "threads": [
    {
      "id": "thread-uuid",
      "user_id": "user-uuid",
      "title": "My Conversation",
      "created_at": "2026-09-30T12:00:00",
      "updated_at": "2026-09-30T12:00:00",
      "last_message_at": "2026-09-30T12:05:00"
    }
  ],
  "next_cursor": "thread-uuid",  // null if no more
  "has_more": false
}
```

### GET /api/threads/{thread_id}

Get a specific thread.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "thread-uuid",
  "user_id": "user-uuid",
  "title": "My Conversation",
  "created_at": "2026-09-30T12:00:00",
  "updated_at": "2026-09-30T12:00:00",
  "last_message_at": "2026-09-30T12:05:00"
}
```

### PUT /api/threads/{thread_id}

Update thread title.

**Headers:**
- `Authorization: Bearer <token>`

**Request:**
```json
{
  "title": "Updated Title"
}
```

**Response:** Same as GET /api/threads/{thread_id}

### DELETE /api/threads/{thread_id}

Soft-delete a thread.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Thread deleted successfully"
}
```

## Messages

### POST /api/threads/{thread_id}/messages

Create a message in a thread.

**Headers:**
- `Authorization: Bearer <token>`

**Request:**
```json
{
  "id": "message-uuid",  // UUID v7, generated client-side
  "thread_seq": 1,
  "encrypted_content": "base64-encrypted-content",
  "encrypted_key": "base64-encrypted-key",
  "nonce": "base64-nonce",
  "role": "user",  // or "assistant"
  "model": "claude-opus-5.5",  // optional
  "tokens_input": 100,  // optional
  "tokens_output": 200,  // optional
  "timestamp": "2026-09-30T12:00:00Z"
}
```

**Response:**
```json
{
  "id": "message-uuid",
  "thread_id": "thread-uuid",
  "user_id": "user-uuid",
  "device_id": null,
  "thread_seq": 1,
  "global_seq": 12345,
  "encrypted_content": "base64-encrypted-content",
  "encrypted_key": "base64-encrypted-key",
  "nonce": "base64-nonce",
  "role": "user",
  "model": "claude-opus-5.5",
  "tokens_input": 100,
  "tokens_output": 200,
  "timestamp": "2026-09-30T12:00:00",
  "created_at": "2026-09-30T12:00:01"
}
```

**Status Codes:**
- `201`: Message created
- `200`: Message already exists (idempotent)
- `404`: Thread not found or deleted
- `409`: Message conflict

### GET /api/threads/{thread_id}/messages

List messages in a thread.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional, default: 100, max: 500): Number of messages
- `seq_from` (optional, default: 0): Starting sequence number

**Response:**
```json
{
  "messages": [
    {
      "id": "message-uuid",
      "thread_id": "thread-uuid",
      "user_id": "user-uuid",
      "thread_seq": 1,
      "encrypted_content": "...",
      "role": "user",
      "timestamp": "2026-09-30T12:00:00"
    }
  ],
  "has_more": false
}
```

### GET /api/messages/{message_id}

Get a specific message.

**Headers:**
- `Authorization: Bearer <token>`

**Response:** Same as message object in POST response

### DELETE /api/messages/{message_id}

Soft-delete a message.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Message deleted successfully"
}
```

## Files

### POST /api/files

Upload an encrypted file.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `message_id`: UUID of associated message
- `file`: File to upload (max 100MB)

**Response:**
```json
{
  "id": "file-uuid",
  "message_id": "message-uuid",
  "filename": "document.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 12345,
  "uploaded_at": "2026-09-30T12:00:00"
}
```

**Status Codes:**
- `201`: File uploaded
- `404`: Message not found
- `413`: File too large (max 100MB)

### GET /api/files/{file_id}

Download and decrypt a file.

**Headers:**
- `Authorization: Bearer <token>`

**Response:** Binary file download with headers:
- `Content-Type`: Original MIME type
- `Content-Disposition`: `attachment; filename="filename.ext"`

### DELETE /api/files/{file_id}

Soft-delete a file.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "File deleted successfully"
}
```

## Sync

### WebSocket /api/sync/ws

Real-time sync connection.

**Query Parameters:**
- `token` (required): Access token

**Client Messages:**
```json
// Ping
{
  "type": "ping"
}

// Update cursor
{
  "type": "cursor",
  "cursor": 12345
}
```

**Server Messages:**
```json
// Pong response
{
  "type": "pong"
}

// Sync event (broadcast)
{
  "type": "sync_event",
  "event": {
    "id": 12345,
    "event_type": "message_created",
    "entity_id": "message-uuid",
    "entity_type": "message",
    "payload": {
      "thread_id": "thread-uuid"
    },
    "timestamp": "2026-09-30T12:00:00"
  }
}
```

### GET /api/sync/events

Polling fallback for sync events.

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `cursor` (optional, default: 0): Last event ID seen
- `limit` (optional, default: 100, max: 500): Number of events

**Response:**
```json
{
  "events": [
    {
      "id": 12345,
      "event_type": "message_created",
      "entity_id": "message-uuid",
      "entity_type": "message",
      "payload": {
        "thread_id": "thread-uuid"
      },
      "timestamp": "2026-09-30T12:00:00"
    }
  ],
  "cursor": 12345
}
```

## Health

### GET /api/health

Check API and database health.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common status codes:
- `400`: Bad request (validation error)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `409`: Conflict (duplicate resource)
- `413`: Payload too large
- `422`: Validation error
- `500`: Internal server error

## Rate Limits

Default limits (configurable):
- Authentication: 10 requests/minute per IP
- Messages: 100 requests/minute per user
- Files: 10 uploads/minute per user
- File upload bandwidth: 100MB/hour per user

Exceeded limits return `429 Too Many Requests`.

## Pagination

List endpoints use cursor-based pagination:

1. First request: Omit `cursor` parameter
2. Check `has_more` in response
3. If `true`, use `next_cursor` for next page

Example:
```bash
# Page 1
curl "/api/threads?limit=20"

# Page 2 (using next_cursor from page 1)
curl "/api/threads?limit=20&cursor=uuid-from-page-1"
```

## Timestamps

All timestamps are ISO 8601 format in UTC:
```
2026-09-30T12:00:00Z
```

## UUIDs

All IDs are UUID v4 format:
```
550e8400-e29b-41d4-a716-446655440000
```

Messages use UUID v7 (time-ordered) for efficient indexing.
