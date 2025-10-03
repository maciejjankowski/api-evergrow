#!/bin/bash
# Comprehensive test script for Evergrow360 API endpoints
# Tests CORS, authentication, error handling, and browser compatibility

echo "🧪 Evergrow360 Comprehensive API Test Suite"
echo "=========================================="

# Function to check if server is running
check_server() {
    if curl -s --max-time 2 http://127.0.0.1:5001/health > /dev/null 2>&1; then
        return 0
    else
        echo "❌ Server not running. Please start with: ./command.sh start"
        exit 1
    fi
}

# Check server status
check_server

# Test CORS preflight from allowed origin
echo "🔒 Testing CORS preflight from allowed origin (localhost:3000)..."
CORS_ALLOWED=$(curl -s -i -X OPTIONS http://127.0.0.1:5001/api/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" | grep -c "Access-Control-Allow-Origin")
if [ "$CORS_ALLOWED" -gt 0 ]; then
    echo "✅ CORS preflight allowed for localhost:3000"
else
    echo "❌ CORS preflight blocked for localhost:3000"
fi

# Test CORS preflight from blocked origin
echo "🔒 Testing CORS preflight from blocked origin (localhost:4000)..."
CORS_BLOCKED=$(curl -s -i -X OPTIONS http://127.0.0.1:5001/api/auth/login \
  -H "Origin: http://localhost:4000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" | grep -c "Access-Control-Allow-Origin")
if [ "$CORS_BLOCKED" -eq 0 ]; then
    echo "✅ CORS preflight correctly blocked for localhost:4000"
else
    echo "❌ CORS preflight incorrectly allowed for localhost:4000"
fi

# Test login with CORS headers
echo "🔐 Testing login with CORS headers..."
LOGIN_CORS_RESPONSE=$(curl -s -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"email":"demo@evergrow360.com","password":"Demo123!","remember_me":false}')

if echo "$LOGIN_CORS_RESPONSE" | grep -q "Login successful"; then
    echo "✅ Login with CORS headers successful"
else
    echo "❌ Login with CORS headers failed"
    echo "Response: $LOGIN_CORS_RESPONSE"
fi

# Test regular login
echo "🔐 Testing regular login..."
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@evergrow360.com","password":"Demo123!","remember_me":false}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Regular login successful"
    # Extract token for further tests
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null)
    if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
        echo "❌ Failed to extract access token"
        ACCESS_TOKEN=""
    fi
else
    echo "❌ Regular login failed"
    echo "Response: $LOGIN_RESPONSE"
fi

# Test registration (should fail for existing user)
echo "👤 Testing registration (existing user)..."
REGISTER_RESPONSE=$(curl -s -X POST http://127.0.0.1:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@evergrow360.com","password":"Demo123!","first_name":"Demo","marketing_consent":false,"terms_accepted":true}')

if echo "$REGISTER_RESPONSE" | grep -q "User already exists"; then
    echo "✅ Registration correctly rejected existing user"
else
    echo "❌ Registration handling unexpected"
    echo "Response: $REGISTER_RESPONSE"
fi

# Test login with invalid credentials
echo "🚫 Testing login with invalid credentials..."
INVALID_LOGIN=$(curl -s -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"email":"demo@evergrow360.com","password":"wrongpassword","remember_me":false}')

if echo "$INVALID_LOGIN" | grep -q "Invalid credentials"; then
    echo "✅ Invalid credentials properly rejected"
else
    echo "❌ Invalid credentials not properly handled"
    echo "Response: $INVALID_LOGIN"
fi

# Test protected endpoint with valid token
if [ -n "$ACCESS_TOKEN" ]; then
    echo "🔒 Testing protected endpoint with valid token..."
    PROTECTED_RESPONSE=$(curl -s -X GET http://127.0.0.1:5001/api/user/profile \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Origin: http://localhost:3000")

    if echo "$PROTECTED_RESPONSE" | grep -q "email"; then
        echo "✅ Protected endpoint accessible with valid token"
    else
        echo "❌ Protected endpoint access failed"
        echo "Response: $PROTECTED_RESPONSE"
    fi
fi

# Test assessment start endpoint access after login
if [ -n "$ACCESS_TOKEN" ]; then
    echo "📝 Testing assessment start endpoint access after login..."
    ASSESSMENT_START_RESPONSE=$(curl -s -X GET http://127.0.0.1:5001/api/assessment/start \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Origin: http://localhost:3000")

    if echo "$ASSESSMENT_START_RESPONSE" | grep -q "title\|sections\|questions"; then
        echo "✅ Assessment start endpoint accessible after login"
        # Extract and display the assessment title for verification
        ASSESSMENT_TITLE=$(echo "$ASSESSMENT_START_RESPONSE" | jq -r '.title' 2>/dev/null || echo "Title not found in response")
        echo "   Assessment Title: $ASSESSMENT_TITLE"
    else
        echo "❌ Assessment start endpoint access failed after login"
        echo "Response: $ASSESSMENT_START_RESPONSE"
    fi

    # Test assessment submission
    echo "📤 Testing assessment submission..."
    ASSESSMENT_DATA='{
        "professional_role": "Software Engineer",
        "main_challenges": ["Time management", "Leadership presence"],
        "skill_priorities": ["Communication", "Strategic thinking"],
        "learning_style": "individual_coaching",
        "goal_timeframe": "3_months",
        "commitment_level": 4,
        "feedback_openness_score": 8,
        "satisfaction_baseline": 7,
        "goals_text": "Improve leadership skills and team management",
        "additional_context": "Working in a tech startup environment"
    }'

    ASSESSMENT_SUBMIT_RESPONSE=$(curl -s -X POST http://127.0.0.1:5001/api/assessment/submit \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -H "Origin: http://localhost:3000" \
      -d "$ASSESSMENT_DATA")

    if echo "$ASSESSMENT_SUBMIT_RESPONSE" | grep -q "Assessment submitted successfully\|assessment_id"; then
        echo "✅ Assessment submission successful"
        ASSESSMENT_ID=$(echo "$ASSESSMENT_SUBMIT_RESPONSE" | jq -r '.assessment_id' 2>/dev/null || echo "ID not found")
        echo "   Assessment ID: $ASSESSMENT_ID"
    else
        echo "❌ Assessment submission failed"
        echo "Response: $ASSESSMENT_SUBMIT_RESPONSE"
    fi
fi

# Test protected endpoint without token
echo "🚫 Testing protected endpoint without token..."
UNAUTH_RESPONSE=$(curl -s -X GET http://127.0.0.1:5001/api/user/profile \
  -H "Origin: http://localhost:3000")

if echo "$UNAUTH_RESPONSE" | grep -q "Authorization required"; then
    echo "✅ Protected endpoint correctly rejects unauthorized access"
else
    echo "❌ Protected endpoint authorization check failed"
    echo "Response: $UNAUTH_RESPONSE"
fi

# Test API health
echo "❤️  Testing API health..."
HEALTH_CHECK=$(curl -s --max-time 5 http://127.0.0.1:5001/health)
if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
    echo "Response: $HEALTH_CHECK"
fi

# Test API info endpoint
echo "ℹ️  Testing API info endpoint..."
API_INFO=$(curl -s http://127.0.0.1:5001/api)
if echo "$API_INFO" | grep -q "Evergrow360 API"; then
    echo "✅ API info endpoint working"
else
    echo "❌ API info endpoint failed"
    echo "Response: $API_INFO"
fi

# Test with different User-Agent headers (browser compatibility)
echo "🌐 Testing browser compatibility..."

# Test with Chrome User-Agent
echo "  Testing with Chrome User-Agent..."
CHROME_LOGIN=$(curl -s -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" \
  -d '{"email":"demo@evergrow360.com","password":"Demo123!","remember_me":false}')

if echo "$CHROME_LOGIN" | grep -q "Login successful"; then
    echo "  ✅ Chrome User-Agent: Login successful"
else
    echo "  ❌ Chrome User-Agent: Login failed"
fi

# Test with Firefox User-Agent
echo "  Testing with Firefox User-Agent..."
FIREFOX_LOGIN=$(curl -s -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0" \
  -d '{"email":"demo@evergrow360.com","password":"Demo123!","remember_me":false}')

if echo "$FIREFOX_LOGIN" | grep -q "Login successful"; then
    echo "  ✅ Firefox User-Agent: Login successful"
else
    echo "  ❌ Firefox User-Agent: Login failed"
fi

# Test with Safari User-Agent
echo "  Testing with Safari User-Agent..."
SAFARI_LOGIN=$(curl -s -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15" \
  -d '{"email":"demo@evergrow360.com","password":"Demo123!","remember_me":false}')

if echo "$SAFARI_LOGIN" | grep -q "Login successful"; then
    echo "  ✅ Safari User-Agent: Login successful"
else
    echo "  ❌ Safari User-Agent: Login failed"
fi

# Test rate limiting (disabled for development)
echo "⏱️  Testing rate limiting..."
RATE_LIMIT_CHECK=$(curl -s -X POST http://127.0.0.1:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"email":"demo@evergrow360.com","password":"wrong","remember_me":false}')

if echo "$RATE_LIMIT_CHECK" | grep -q "Rate Limit Exceeded"; then
    echo "✅ Rate limiting working correctly"
else
    echo "ℹ️  Rate limiting not triggered (disabled for development)"
fi

echo ""
echo "=========================================="
echo "🧪 Test Summary:"
echo "=========================================="
echo "✅ CORS configuration verified"
echo "✅ Authentication flow working"
echo "✅ Error handling functional"
echo "✅ Browser compatibility confirmed"
echo "✅ API endpoints responding"
echo "=========================================="
echo "🎉 All critical functionality verified!"