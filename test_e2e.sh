#!/bin/bash

# LLMSync End-to-End Test Script

set -e

API_URL="http://localhost:8000"
EMAIL="test-e2e@example.com"

echo "========================================="
echo "  LLMSync End-to-End Test Suite"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Test 1: Health Check
info "Test 1: Health check"
HEALTH=$(curl -s "$API_URL/api/health")
if echo "$HEALTH" | grep -q "healthy"; then
    success "API is healthy"
else
    error "Health check failed"
fi
echo ""

# Test 2: Request Magic Link
info "Test 2: Request magic link for $EMAIL"
MAGIC_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login/magic-link" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}")

if echo "$MAGIC_RESPONSE" | grep -q "Check your email"; then
    success "Magic link requested"
else
    error "Magic link request failed"
fi
echo ""

# Test 3: Get token from logs
info "Test 3: Extracting token from logs..."
echo "Run this command to get your magic link:"
echo ""
echo -e "  ${YELLOW}docker-compose logs api | grep 'Magic link for $EMAIL'${NC}"
echo ""
echo "Then extract the token and run:"
echo ""
echo -e "  ${YELLOW}export TOKEN='your-token-here'${NC}"
echo ""
echo "Then continue with authenticated tests:"
echo ""

cat << 'EOF'
# Test authenticated endpoints
TOKEN="your-token-here"

# Test 4: Get user info
curl -s "$API_URL/api/users/me" -H "Authorization: Bearer $TOKEN" | jq '.'

# Test 5: Register device
curl -s -X POST "$API_URL/api/devices" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Test Device",
    "device_fingerprint": "test-fp-123",
    "public_key": "test-pubkey-base64"
  }' | jq '.'

# Test 6: Create thread
THREAD_RESPONSE=$(curl -s -X POST "$API_URL/api/threads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"E2E Test Thread"}')
THREAD_ID=$(echo $THREAD_RESPONSE | jq -r '.id')
echo "Created thread: $THREAD_ID"

# Test 7: Create message
MESSAGE_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
curl -s -X POST "$API_URL/api/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"$MESSAGE_ID\",
    \"thread_seq\": 1,
    \"encrypted_content\": \"$(echo 'Test message' | base64)\",
    \"encrypted_key\": \"$(echo 'test-key' | base64)\",
    \"nonce\": \"$(echo 'test-nonce' | base64)\",
    \"role\": \"user\",
    \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
  }" | jq '.'

# Test 8: List messages
curl -s "$API_URL/api/threads/$THREAD_ID/messages" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Test 9: Test WebSocket (requires wscat: npm install -g wscat)
# wscat -c "ws://localhost:8000/api/sync/ws?token=$TOKEN"
# > {"type":"ping"}
# Expected: {"type":"pong"}

# Test 10: Get sync events (polling)
curl -s "$API_URL/api/sync/events?cursor=0&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo ""
echo "✓ All tests passed!"
EOF

echo ""
echo "========================================="
echo "  Test Suite Complete"
echo "========================================="
echo ""
echo "✓ Public endpoints working"
echo "! Authenticated tests require manual token extraction"
echo ""
echo "For WebSocket testing, install wscat:"
echo "  npm install -g wscat"
echo ""
echo "Then connect:"
echo "  wscat -c 'ws://localhost:8000/api/sync/ws?token=YOUR_TOKEN'"
echo ""
