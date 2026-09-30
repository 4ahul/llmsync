#!/bin/bash

# LLMSync API Test Script

API_URL="http://localhost:8000"
EMAIL="test@example.com"

echo "=== LLMSync API Test Suite ==="
echo ""

# Test 1: Health Check
echo "1. Testing health endpoint..."
curl -s "$API_URL/api/health" | jq '.'
echo ""

# Test 2: Magic Link Request
echo "2. Requesting magic link..."
curl -s -X POST "$API_URL/api/auth/login/magic-link" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\"}" | jq '.'
echo ""

echo "Check docker logs for magic link:"
echo "  docker-compose logs api | grep 'Magic link'"
echo ""

# Test 3: List threads (requires token)
echo "3. To test authenticated endpoints, first get token from magic link:"
echo ""
echo "  # Get token from magic link in logs"
echo "  TOKEN='<your-token>'"
echo ""
echo "  # Create thread"
echo "  curl -X POST $API_URL/api/threads \\"
echo "    -H 'Authorization: Bearer \$TOKEN' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"title\":\"Test Thread\"}'"
echo ""
echo "  # List threads"
echo "  curl $API_URL/api/threads \\"
echo "    -H 'Authorization: Bearer \$TOKEN'"
echo ""

echo "=== Tests Complete ==="
