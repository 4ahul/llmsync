# LLMSync Testing Guide

Complete guide to test the system end-to-end.

## Prerequisites

```bash
# Install required tools
npm install -g wscat  # For WebSocket testing
pip install httpie    # Better curl alternative (optional)

# OR just use curl (already installed)
```

## 1. Start the System

```bash
cd llmsync

# Copy environment
cp .env.example .env

# Start all services
docker-compose up -d

# Wait 60 seconds for all services to initialize
echo "Waiting for services to start..."
sleep 60

# Check all services are running
docker-compose ps

# Expected output:
# llmsync-api       running  0.0.0.0:8000->8000/tcp
# llmsync-postgres  running  0.0.0.0:5432->5432/tcp
# llmsync-redis     running  0.0.0.0:6379->6379/tcp
# llmsync-minio     running  0.0.0.0:9000-9001->9000-9001/tcp
```

## 2. Verify Services

```bash
# Test API health
curl http://localhost:8000/api/health

# Expected: {"status":"healthy","database":"connected"}

# Check MinIO (optional)
open http://localhost:9001
# Login: llmsync / llmsync123

# Check Redis (optional)
docker exec -it llmsync-redis redis-cli ping
# Expected: PONG
```

## 3. Test Authentication Flow

```bash
# Request magic link
curl -X POST http://localhost:8000/api/auth/login/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com"}' | jq

# Expected: {"message":"Check your email for login link"}

# Get magic link from logs
docker-compose logs api | grep "Magic link for alice"

# Copy the token from URL (after token=)
# Example: http://localhost:8000/api/auth/verify?token=abc123...

# Verify token
TOKEN="<paste-token-here>"
curl "http://localhost:8000/api/auth/verify?token=$TOKEN" | jq

# Expected: 
# {
#   "access_token": "eyJ0eXAi...",
#   "refresh_token": "eyJ0eXAi...",
#   "token_type": "bearer",
#   "user": {...}
# }

# Save access token
export TOKEN="<paste-access-token-here>"

# Test authentication
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: {"id":"...","email":"alice@example.com","has_encryption_setup":false}
```

## 4. Test Encryption Setup (Critical!)

```bash
# Setup encryption for first time
# In real use, client would generate these. For testing, use dummy values.

curl -X POST http://localhost:8000/api/users/setup-encryption \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "encrypted_master_key_backup": "dGVzdC1lbmNyeXB0ZWQtYmFja3Vw",
    "salt": "dGVzdC1zYWx0LTE2Ynl0ZXM=",
    "recovery_phrase_hash": "test-hash-sha256"
  }' | jq

# Expected: {"message":"Encryption setup complete","user_id":"..."}

# Verify encryption is set up
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: {"has_encryption_setup":true}

# Get encryption key
curl http://localhost:8000/api/users/encryption-key \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: Encrypted backup and salt returned
```

## 5. Test Device Registration

```bash
# Register device 1
DEVICE1=$(curl -s -X POST http://localhost:8000/api/devices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "MacBook Pro",
    "device_fingerprint": "device-fp-mac-001",
    "public_key": "pubkey-mac-base64"
  }' | jq -r '.id')

echo "Device 1 ID: $DEVICE1"

# Register device 2 (simulate second device)
DEVICE2=$(curl -s -X POST http://localhost:8000/api/devices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "iPhone",
    "device_fingerprint": "device-fp-iphone-001",
    "public_key": "pubkey-iphone-base64"
  }' | jq -r '.id')

echo "Device 2 ID: $DEVICE2"

# List all devices
curl http://localhost:8000/api/devices \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: Array with 2 devices

# Send heartbeat
curl -X POST "http://localhost:8000/api/devices/$DEVICE1/heartbeat" \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: {"message":"Heartbeat recorded","last_seen_at":"..."}
```

## 6. Test Thread & Messages

```bash
# Create thread
THREAD=$(curl -s -X POST http://localhost:8000/api/threads \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Conversation"}' | jq -r '.id')

echo "Thread ID: $THREAD"

# List threads
curl http://localhost:8000/api/threads \
  -H "Authorization: Bearer $TOKEN" | jq

# Create message
MESSAGE_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
echo "Message ID: $MESSAGE_ID"

curl -s -X POST "http://localhost:8000/api/threads/$THREAD/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$MESSAGE_ID\",
    \"thread_seq\": 1,
    \"encrypted_content\": \"$(echo 'Hello World' | base64)\",
    \"encrypted_key\": \"$(echo 'test-key' | base64)\",
    \"nonce\": \"$(echo 'test-nonce' | base64)\",
    \"role\": \"user\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }" | jq

# List messages in thread
curl "http://localhost:8000/api/threads/$THREAD/messages" \
  -H "Authorization: Bearer $TOKEN" | jq

# Get specific message
curl "http://localhost:8000/api/messages/$MESSAGE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 7. Test File Upload (Pre-Encrypted)

```bash
# Create a test file
echo "This is a test file for LLMSync" > test.txt

# Encrypt it (in real use, client encrypts. For testing, use as-is)
cat test.txt | base64 > test.txt.enc

# Upload encrypted file
FILE_ID=$(curl -s -X POST http://localhost:8000/api/files/encrypted \
  -H "Authorization: Bearer $TOKEN" \
  -F "metadata={\"message_id\":\"$MESSAGE_ID\",\"filename\":\"test.txt\",\"mime_type\":\"text/plain\",\"size_bytes\":35,\"encrypted_key\":\"$(echo 'file-key' | base64)\",\"nonce\":\"$(echo 'file-nonce' | base64)\"}" \
  -F "encrypted_file=@test.txt.enc" | jq -r '.id')

echo "File ID: $FILE_ID"

# Get file metadata
curl "http://localhost:8000/api/files/$FILE_ID/metadata" \
  -H "Authorization: Bearer $TOKEN" | jq

# Download encrypted file
curl "http://localhost:8000/api/files/$FILE_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded.enc

# Verify download
ls -lh downloaded.enc
```

## 8. Test Real-Time Sync (WebSocket)

Open **two terminal windows**.

### Terminal 1 (Device A - Listener):
```bash
export TOKEN="your-access-token"

# Connect WebSocket
wscat -c "ws://localhost:8000/api/sync/ws?token=$TOKEN"

# You should see: Connected

# Send ping
> {"type":"ping"}

# Expected response:
< {"type":"pong"}

# Keep this terminal open and watching...
```

### Terminal 2 (Device B - Sender):
```bash
export TOKEN="your-access-token"
export THREAD="your-thread-id"

# Create a new message
MESSAGE_ID=$(python3 -c "import uuid; print(uuid.uuid4())")

curl -X POST "http://localhost:8000/api/threads/$THREAD/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$MESSAGE_ID\",
    \"thread_seq\": 2,
    \"encrypted_content\": \"$(echo 'Real-time test' | base64)\",
    \"encrypted_key\": \"$(echo 'test-key-2' | base64)\",
    \"nonce\": \"$(echo 'test-nonce-2' | base64)\",
    \"role\": \"user\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }"
```

### Expected in Terminal 1:
```json
{
  "type": "sync_event",
  "event": {
    "id": 123,
    "event_type": "message_created",
    "entity_id": "message-uuid",
    "entity_type": "message",
    "payload": {"thread_id": "thread-uuid"},
    "timestamp": "2026-09-30T12:00:00"
  }
}
```

**✅ If you see this, real-time sync is working!**

## 9. Test Polling Fallback

```bash
# Get sync events via polling (for offline devices)
curl "http://localhost:8000/api/sync/events?cursor=0&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: Array of sync events with cursor

# Get events since specific cursor
CURSOR=5
curl "http://localhost:8000/api/sync/events?cursor=$CURSOR&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 10. Test Multi-User Sync

```bash
# Create second user
curl -X POST http://localhost:8000/api/auth/login/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"bob@example.com"}' | jq

# Get Bob's token from logs
docker-compose logs api | grep "Magic link for bob"

export TOKEN_BOB="bob-access-token"

# Verify Bob has separate data
curl http://localhost:8000/api/threads \
  -H "Authorization: Bearer $TOKEN_BOB" | jq

# Expected: Empty array (Bob has no threads yet)

# Alice's threads should be unchanged
curl http://localhost:8000/api/threads \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected: Alice's threads still there
```

## 11. Stress Test (Basic)

```bash
# Create 100 messages rapidly
for i in {1..100}; do
  MESSAGE_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
  curl -s -X POST "http://localhost:8000/api/threads/$THREAD/messages" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"id\": \"$MESSAGE_ID\",
      \"thread_seq\": $i,
      \"encrypted_content\": \"$(echo "Message $i" | base64)\",
      \"encrypted_key\": \"$(echo "key-$i" | base64)\",
      \"nonce\": \"$(echo "nonce-$i" | base64)\",
      \"role\": \"user\",
      \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
    }" > /dev/null &
done

wait

# List messages (should have 100+)
curl "http://localhost:8000/api/threads/$THREAD/messages?limit=500" \
  -H "Authorization: Bearer $TOKEN" | jq '.messages | length'

# Expected: 100+ messages
```

## 12. Test Error Handling

```bash
# Test invalid token
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer invalid-token" | jq

# Expected: {"detail":"Invalid token: ..."}

# Test accessing another user's thread (should fail)
curl "http://localhost:8000/api/threads/$THREAD/messages" \
  -H "Authorization: Bearer $TOKEN_BOB" | jq

# Expected: {"detail":"Thread not found"}

# Test uploading oversized file (>100MB)
dd if=/dev/zero of=large.bin bs=1M count=101
curl -X POST http://localhost:8000/api/files/encrypted \
  -H "Authorization: Bearer $TOKEN" \
  -F "metadata={...}" \
  -F "encrypted_file=@large.bin"

# Expected: {"detail":"File too large (max 104857600 bytes)"}
```

## 13. Check Logs

```bash
# View all logs
docker-compose logs

# View API logs only
docker-compose logs api

# Follow logs in real-time
docker-compose logs -f api

# Check for errors
docker-compose logs api | grep ERROR
docker-compose logs api | grep CRITICAL
```

## 14. Performance Check

```bash
# Check response times
time curl http://localhost:8000/api/health

# Expected: <50ms

time curl http://localhost:8000/api/threads \
  -H "Authorization: Bearer $TOKEN"

# Expected: <100ms

# Check database connections
docker exec llmsync-postgres psql -U llmsync -c "SELECT count(*) FROM pg_stat_activity;"

# Check Redis memory
docker exec llmsync-redis redis-cli info memory | grep used_memory_human
```

## 15. Cleanup

```bash
# Stop services
docker-compose down

# Remove all data (careful!)
docker-compose down -v

# Remove test files
rm test.txt test.txt.enc downloaded.enc large.bin
```

---

## Common Issues & Solutions

### Issue: Health check fails
```bash
# Check if Postgres is ready
docker exec llmsync-postgres pg_isready -U llmsync

# Check logs
docker-compose logs postgres
```

### Issue: WebSocket won't connect
```bash
# Check Redis is running
docker exec llmsync-redis redis-cli ping

# Check API logs for errors
docker-compose logs api | grep WebSocket
```

### Issue: File upload fails
```bash
# Check MinIO is running
curl http://localhost:9000/minio/health/live

# Check MinIO logs
docker-compose logs minio
```

### Issue: Slow responses
```bash
# Check system resources
docker stats

# Check database query performance
docker exec llmsync-postgres psql -U llmsync -c "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"
```

---

## Success Criteria

✅ **System is working if:**
- All health checks pass
- Magic link auth works
- Messages sync via WebSocket in <1 second
- Files upload and download successfully
- Multiple devices can connect simultaneously
- Polling fallback works when WebSocket unavailable
- No errors in logs during normal operations

---

## Next: Load Testing

After manual testing passes, run proper load tests:

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/api/health

# Test authenticated endpoint (need valid token)
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" \
   http://localhost:8000/api/threads
```

Or use more advanced tools:
- **k6** - Modern load testing
- **Locust** - Python-based load testing
- **Artillery** - Node.js load testing

---

## Monitoring

```bash
# Watch live metrics
watch -n 1 'curl -s http://localhost:8000/api/health | jq'

# Watch Docker stats
docker stats

# Watch Postgres queries
watch -n 1 'docker exec llmsync-postgres psql -U llmsync -c "SELECT count(*) FROM pg_stat_activity WHERE state = '\''active'\''"'
```

---

**You're ready to test!** Start from step 1 and work through each section. If everything passes, your system is working correctly.
