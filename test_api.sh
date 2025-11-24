#!/bin/bash

BASE_URL="http://127.0.0.1:8000/api/v1"

echo "========================================="
echo "1. SIGNUP - Creating test user"
echo "========================================="
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "testpass123"
  }')
echo "$SIGNUP_RESPONSE" | python3 -m json.tool
echo ""

echo "========================================="
echo "2. LOGIN - Getting access token"
echo "========================================="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test2@example.com",
    "password": "testpass123"
  }')
echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token. Exiting."
  exit 1
fi

echo ""
echo "Access Token: $ACCESS_TOKEN"
echo ""

echo "========================================="
echo "3. SIMULATE USER EVENTS (for trending)"
echo "========================================="
SIMULATE_RESPONSE=$(curl -s -X POST "$BASE_URL/news/trending/simulate-events?num_events=100" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json")
echo "$SIMULATE_RESPONSE" | python3 -m json.tool
echo ""

echo "========================================="
echo "4. GET TRENDING NEWS"
echo "========================================="
TRENDING_RESPONSE=$(curl -s -X GET "$BASE_URL/news/trending?lat=37.7749&lon=-122.4194&limit=5" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$TRENDING_RESPONSE" | python3 -m json.tool
echo ""

echo "========================================="
echo "5. GET NEWS BY CATEGORY"
echo "========================================="
CATEGORY_RESPONSE=$(curl -s -X GET "$BASE_URL/news/category?category=Technology&limit=3" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$CATEGORY_RESPONSE" | python3 -m json.tool
echo ""

echo "========================================="
echo "6. SEARCH NEWS"
echo "========================================="
SEARCH_RESPONSE=$(curl -s -X GET "$BASE_URL/news/search?query=technology&limit=3" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "$SEARCH_RESPONSE" | python3 -m json.tool
echo ""

echo "========================================="
echo "✅ All tests complete!"
echo "========================================="
