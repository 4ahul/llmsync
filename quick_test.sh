#!/bin/bash

# LLMSync Quick Test - Automated E2E Test
# Run this after docker-compose up -d

set -e

API_URL="http://localhost:8000"
EMAIL="quicktest@example.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════╗"
echo "║   LLMSync Quick Test Suite                ║"
echo "║   Testing all critical functionality       ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    echo -e "${RED}Test failed. Check docker-compose logs for details.${NC}"
    exit 1
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Test 1: Health Check
info "Test 1/10: Health check"
HEALTH=$(curl -s "$API_URL/api/health" || echo "failed")
if echo "$HEALTH" | grep -q "healthy"; then
    pass "API is healthy"
else
    fail "Health check failed: $HEALTH"
fi

# Test 2: Magic Link
info "Test 2/10: Request magic link"
MAGIC=$(curl -s -X POST "$API_URL/api/auth/login/magic-link" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}" || echo "failed")

if echo "$MAGIC" | grep -q "Check your email"; then
    pass "Magic link requested"
else
    fail "Magic link failed: $MAGIC"
fi

# Test 3: Extract token
info "Test 3/10: Extract token from logs"
sleep 2
TOKEN=$(docker-compose logs api 2>/dev/null | grep "Magic link for $EMAIL" | tail -1 | sed -n 's/.*token=\([^?]*\).*/\1/p')

if [ -z "$TOKEN" ]; then
    fail "Could not extract token from logs"
fi

# Verify token
VERIFY=$(curl -s "$API_URL/api/auth/verify?token=$TOKEN" || echo "failed")
ACCESS_TOKEN=$(echo "$VERIFY" | jq -r '.access_token' 2>/dev/null || echo "")

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    fail "Token verification failed: $VERIFY"
fi

pass "Token obtained and verified"

# Test 4: User info
info "Test 4/10: Get user info"
USER=$(curl -s "$API_URL/api/users/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" || echo "failed")

USER_ID=$(echo "$USER" | jq -r '.id' 2>/dev/null || echo "")
if [ -n "$USER_ID" ] && [ "$USER_ID" != "null" ]; then
    pass "User info retrieved (ID: ${USER_ID:0:8}...)"
else
    fail "User info failed: $USER"
fi

# Test 5: Setup encryption
info "Test 5/10: Setup encryption"
SETUP=$(curl -s -X POST "$API_URL/api/users/setup-encryption" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "encrypted_master_key_backup": "dGVzdC1lbmNyeXB0ZWQtYmFja3Vw",
    "salt": "dGVzdC1zYWx0LTE2Ynl0ZXM=",
    "recovery_phrase_hash": "test-hash"
  }' || echo "failed")

if echo "$SETUP" | grep -q "Encryption setup complete"; then
    pass "Encryption configured"
else
    fail "Encryption setup failed: $SETUP"
fi

# Test 6: Register device
info "Test 6/10: Register device"
DEVICE=$(curl -s -X POST "$API_URL/api/devices" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Test Device",
    "device_fingerprint": "test-fp-'$(date +%s)'",
    "public_key": "test-pubkey"
  }' || echo "failed")

DEVICE_ID=$(echo "$DEVICE" | jq -r '.id' 2>/dev/null || echo "")
if [ -n "$DEVICE_ID" ] && [ "$DEVICE_ID" != "null" ]; then
    pass "Device registered (ID: ${DEVICE_ID:0:8}...)"
else
    fail "Device registration failed: $DEVICE"
fi

# Test 7: Create thread
info "Test 7/10: Create thread"
THREAD=$(curl -s -X POST "$API_URL/api/threads" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Quick Test Thread"}' || echo "failed")

THREAD_ID=$(echo "$THREAD" | jq -r '.id' 2>/dev/null || echo "")
if [ -n "$THREAD_ID" ] && [ "$THREAD_ID" != "null" ]; then
    pass "Thread created (ID: ${THREAD_ID:0:8}...)"
else
    fail "Thread creation failed: $THREAD"
fi

# Test 8: Create message
info "Test 8/10: Create message"
MESSAGE_ID=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null || uuidgen)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

MESSAGE=$(curl -s -X POST "$API_URL/api/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$MESSAGE_ID\",
    \"thread_seq\": 1,
    \"encrypted_content\": \"$(echo 'Test message' | base64)\",
    \"encrypted_key\": \"$(echo 'test-key' | base64)\",
    \"nonce\": \"$(echo 'test-nonce' | base64)\",
    \"role\": \"user\",
    \"timestamp\": \"$TIMESTAMP\"
  }" || echo "failed")

MSG_ID=$(echo "$MESSAGE" | jq -r '.id' 2>/dev/null || echo "")
if [ -n "$MSG_ID" ] && [ "$MSG_ID" != "null" ]; then
    pass "Message created (ID: ${MSG_ID:0:8}...)"
else
    fail "Message creation failed: $MESSAGE"
fi

# Test 9: List messages
info "Test 9/10: List messages"
MESSAGES=$(curl -s "$API_URL/api/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $ACCESS_TOKEN" || echo "failed")

MSG_COUNT=$(echo "$MESSAGES" | jq '.messages | length' 2>/dev/null || echo "0")
if [ "$MSG_COUNT" -ge 1 ]; then
    pass "Messages listed (count: $MSG_COUNT)"
else
    fail "Message listing failed: $MESSAGES"
fi

# Test 10: Sync events
info "Test 10/10: Get sync events"
EVENTS=$(curl -s "$API_URL/api/sync/events?cursor=0&limit=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN" || echo "failed")

EVENT_COUNT=$(echo "$EVENTS" | jq '.events | length' 2>/dev/null || echo "0")
if [ "$EVENT_COUNT" -ge 1 ]; then
    pass "Sync events retrieved (count: $EVENT_COUNT)"
else
    fail "Sync events failed: $EVENTS"
fi

# Summary
echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════╗"
echo "║   ✓ All Tests Passed!                     ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "System is working correctly!"
echo ""
echo "Quick Stats:"
echo "  User ID:    $USER_ID"
echo "  Device ID:  $DEVICE_ID"
echo "  Thread ID:  $THREAD_ID"
echo "  Messages:   $MSG_COUNT"
echo "  Events:     $EVENT_COUNT"
echo ""
echo "Next steps:"
echo "  1. Test WebSocket: wscat -c 'ws://localhost:8000/api/sync/ws?token=$ACCESS_TOKEN'"
echo "  2. Full test suite: ./test_e2e.sh"
echo "  3. Load testing: See TESTING_GUIDE.md"
echo ""
echo "Access token (save this):"
echo "  export TOKEN='$ACCESS_TOKEN'"
echo ""
