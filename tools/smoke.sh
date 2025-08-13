#!/bin/bash
# Smoke test script for Studying Coach API endpoints

echo "==== STUDYING COACH SMOKE TEST ===="
echo "Testing API endpoints..."
echo

BASE_URL="http://127.0.0.1:5000"

# Function to start the server if needed
start_server() {
    echo "Starting server..."
    if [ -f "./start-coach.command" ]; then
        echo "Using start-coach.command..."
        ./start-coach.command &
    elif [ -f "app.py" ]; then
        echo "Using python app.py..."
        if [ -d ".venv" ]; then
            source .venv/bin/activate
        fi
        python app.py &
    else
        echo "❌ No startup script found"
        return 1
    fi
    
    SERVER_PID=$!
    echo "Server started with PID: $SERVER_PID"
    
    # Wait for server to start
    echo "Waiting for server to be ready..."
    for i in {1..30}; do
        if curl -s "$BASE_URL/api/health" >/dev/null 2>&1; then
            echo "✅ Server is ready!"
            return 0
        fi
        sleep 1
    done
    
    echo "❌ Server failed to start within 30 seconds"
    return 1
}

# Test API endpoints
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -n "Testing $description..."
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint" 2>/dev/null)
    elif [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint" 2>/dev/null)
        else
            response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" 2>/dev/null)
        fi
    fi
    
    if [ -n "$response" ]; then
        http_code=$(echo "$response" | tail -n1)
        response_body=$(echo "$response" | head -n -1)
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            echo " ✅ ($http_code)"
            echo "   Response: $response_body"
        else
            echo " ❌ ($http_code)"
            echo "   Response: $response_body"
        fi
    else
        echo " ❌ (No response)"
    fi
    echo
}

# Check if server is already running
if ! curl -s "$BASE_URL/api/health" >/dev/null 2>&1; then
    start_server || exit 1
    STARTED_SERVER=true
else
    echo "✅ Server already running"
    STARTED_SERVER=false
fi

echo
echo "==== TESTING ENDPOINTS ===="

# Test health endpoints
test_endpoint "GET" "/api/health" "Health endpoint"
test_endpoint "GET" "/api/health/llm" "LLM health endpoint"

# Test upload endpoint (with a test file)
if [ -f "README.md" ]; then
    echo "Testing file upload..."
    upload_response=$(curl -s -w "\n%{http_code}" -F "file=@README.md" -F "use_advanced=false" "$BASE_URL/api/upload" 2>/dev/null || true)
    if [ -n "$upload_response" ]; then
        http_code=$(echo "$upload_response" | tail -n1)
        response_body=$(echo "$upload_response" | head -n -1)
        echo "Upload test: HTTP $http_code"
        echo "Response: $response_body"
    else
        echo "Upload test: ❌ No response"
    fi
    echo
fi

# Test improve endpoint
test_endpoint "POST" "/api/improve" "AI improve endpoint" '{"text":"test"}'

# Test offline analyze endpoint
test_endpoint "POST" "/api/offline/analyze" "Offline analyze endpoint" '{"text":"This is a test text for analysis."}'

echo "==== SMOKE TEST COMPLETE ===="

# Cleanup: kill server if we started it
if [ "$STARTED_SERVER" = true ] && [ -n "$SERVER_PID" ]; then
    echo "Stopping server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
fi