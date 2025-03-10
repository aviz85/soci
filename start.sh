#!/bin/bash

# Start the Django backend server
echo "Starting Django backend server on port 8080..."
python manage.py runserver 8080 &
BACKEND_PID=$!

# Start the frontend server
echo "Starting frontend server on port 3000..."
node server.js &
FRONTEND_PID=$!

# Function to handle script termination
function cleanup {
    echo "Shutting down servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

echo "Both servers are running!"
echo "Backend: http://localhost:8080"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both servers."

# Wait for both processes
wait 