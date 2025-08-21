#!/bin/bash

# User Search Functionality Test Runner
# This script helps test the user search option

echo "🚀 Starting User Search Functionality Tests..."
echo "================================================"

# Check if backend is running
echo "Checking if backend is running..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Backend is running on localhost:8000"
else
    echo "❌ Backend is not running. Please start the backend first:"
    echo "   cd tapcard-backend && uvicorn main:app --reload"
    exit 1
fi

# Run the user search tests
echo ""
echo "Running user search tests..."
python test_user_search.py

echo ""
echo "🎯 User search testing completed!"
echo "================================================"
echo "To test manually, you can use these endpoints:"
echo "1. GET http://localhost:8000/api/social/search?username=alice"
echo "2. GET http://localhost:8000/api/social/search?username=dev"
echo "3. GET http://localhost:8000/api/social/search?username=nonexistent"
echo ""
echo "Remember to include the Authorization header with your Bearer token!"
