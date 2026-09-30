# Getting Started with LLMSync

This guide will help you set up and test LLMSync in under 10 minutes.

## Prerequisites

- Docker Desktop installed and running
- Git
- curl or a REST client (Postman, Insomnia, etc.)

## Step 1: Clone and Configure

```bash
# Clone the repository
git clone <repository-url> llmsync
cd llmsync

# Copy environment file
cp .env.example .env

# (Optional) Edit .env to customize ports or credentials
# nano .env
```

## Step 2: Start the Stack

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

You should see all services running:
- llmsync-api
- llmsync-postgres
- llmsync-redis
- llmsync-minio

## Step 3: Verify Installation

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected"
# }
```

## Step 4: Create Your First User

```bash
# Request magic link
curl -X POST http://localhost:8000/api/auth/login/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'

# Response:
# {"message":"Check your email for login link"}
```

## Step 5: Get Your Access Token

Since we're in development mode without SMTP, the magic link is printed in the logs:

```bash
# View API logs
docker-compose logs api | grep "Magic link"

# You'll see something like:
# INFO:llmsync.services.email:Magic link for you@example.com: http://localhost:8000/api/auth/verify?token=abc123...
```

Copy the token from the URL and verify it:

```bash
# Replace TOKEN with the actual token from logs
curl "http://localhost:8000/api/auth/verify?token=TOKEN"

# Response includes access_token and refresh_token:
# {
#   "access_token": "eyJ0eXAi...",
#   "refresh_token": "eyJ0eXAi...",
#   "token_type": "bearer",
#   "user": {
#     "id": "uuid",
#     "email": "you@example.com",
#     "created_at": "2026-09-30T12:00:00"
#   }
# }
```

Save the `access_token` to an environment variable:

```bash
export TOKEN="eyJ0eXAi..."
```

## Step 6: Create a Thread

```bash
curl -X POST http://localhost:8000/api/threads \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My First Conversation"}'

# Response:
# {
#   "id": "thread-uuid",
#   "user_id": "user-uuid",
#   "title": "My First Conversation",
#   "created_at": "2026-09-30T12:00:00",
#   "updated_at": "2026-09-30T12:00:00",
#   "last_message_at": null
# }
```

Save the thread ID:

```bash
export THREAD_ID="thread-uuid"
```

## Step 7: Add a Message

```bash
# Generate a UUID for the message (or use an online UUID generator)
export MESSAGE_ID=$(python3 -c "import uuid; print(str(uuid.uuid4()))")

# Create an encrypted message (for testing, we'll use dummy encrypted data)
curl -X POST "http://localhost:8000/api/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$MESSAGE_ID\",
    \"thread_seq\": 1,
    \"encrypted_content\": \"test-encrypted-content\",
    \"encrypted_key\": \"test-encrypted-key\",
    \"nonce\": \"test-nonce\",
    \"role\": \"user\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }"
```

## Step 8: List Messages

```bash
curl "http://localhost:8000/api/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "messages": [
#     {
#       "id": "message-uuid",
#       "thread_id": "thread-uuid",
#       "user_id": "user-uuid",
#       "thread_seq": 1,
#       "encrypted_content": "test-encrypted-content",
#       ...
#     }
#   ],
#   "has_more": false
# }
```

## Step 9: Test File Upload

```bash
# Create a test file
echo "Hello LLMSync!" > test.txt

# Upload file
curl -X POST http://localhost:8000/api/files \
  -H "Authorization: Bearer $TOKEN" \
  -F "message_id=$MESSAGE_ID" \
  -F "file=@test.txt"

# Response:
# {
#   "id": "file-uuid",
#   "message_id": "message-uuid",
#   "filename": "test.txt",
#   "mime_type": "text/plain",
#   "size_bytes": 15,
#   "uploaded_at": "2026-09-30T12:00:00"
# }
```

## Step 10: Test WebSocket Sync

Create a simple WebSocket client:

```javascript
// test-websocket.js
const WebSocket = require('ws');

const token = process.env.TOKEN || 'your-token-here';
const ws = new WebSocket(`ws://localhost:8000/api/sync/ws?token=${token}`);

ws.on('open', () => {
  console.log('Connected to sync server');
  
  // Send ping
  ws.send(JSON.stringify({ type: 'ping' }));
});

ws.on('message', (data) => {
  console.log('Received:', JSON.parse(data.toString()));
});

ws.on('close', () => {
  console.log('Disconnected');
});

ws.on('error', (error) => {
  console.error('Error:', error);
});

// Keep alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

Run it:

```bash
node test-websocket.js
```

## Step 11: Explore MinIO

Open the MinIO console to see your encrypted files:

```
http://localhost:9001

Username: llmsync
Password: llmsync123
```

## Troubleshooting

### Services not starting

```bash
# Check service status
docker-compose ps

# View logs for specific service
docker-compose logs api
docker-compose logs postgres
```

### Database connection errors

```bash
# Restart services
docker-compose restart

# Or rebuild
docker-compose down
docker-compose up -d
```

### Port conflicts

Edit `.env` and change port numbers:

```env
API_PORT=8080
POSTGRES_PORT=5433
REDIS_PORT=6380
MINIO_PORT=9001
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

## Next Steps

- **Production Setup**: See README.md for production deployment guidelines
- **Client SDKs**: Build or integrate with TypeScript/Python SDKs
- **OAuth**: Configure Google/GitHub OAuth in `.env`
- **SMTP**: Configure real email delivery for magic links
- **Monitoring**: Add Prometheus/Grafana for metrics

## Cleanup

To stop and remove all services:

```bash
# Stop services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v
```

## Support

- Issues: Create a GitHub issue
- Docs: Check `/docs` directory
- Logs: `docker-compose logs -f`

Happy syncing! 🚀
