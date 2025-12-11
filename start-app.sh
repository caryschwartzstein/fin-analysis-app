#!/bin/bash

echo "Starting Financial Analysis Dashboard..."
echo ""
echo "1. Starting API server..."
cd fin-analysis-api
source .venv/bin/activate
python main.py &
API_PID=$!
echo "API running on http://localhost:8000 (PID: $API_PID)"
echo ""

echo "2. Starting React app..."
cd ../fin-analysis-app
npm run dev &
APP_PID=$!
echo "React app will be available on http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $API_PID $APP_PID; exit" INT
wait
