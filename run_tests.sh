#!/bin/bash

# Backend User Auth Testing Script
# Make sure the backend server is running before executing this script

echo "🚀 Starting Backend User Auth Testing..."
echo "Make sure your backend server is running on http://localhost:8000"
echo ""

# Check if backend is running
echo "🔍 Checking if backend is running..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running. Please start the backend server first:"
    echo "   python main.py"
    exit 1
fi

# Run the test script
echo "🧪 Running user auth tests..."
python test_user_auth.py

echo ""
echo "✅ Testing complete!"
echo "📊 Check test_results.json for detailed results"
