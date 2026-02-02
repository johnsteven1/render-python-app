#!/bin/bash
# Startup script for Ethical Monitor

echo "Starting Ethical Website Monitor..."
echo "==================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Virtual environment not found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
    fi
fi

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run database migrations
echo "Initializing database..."
python3 -c "from server import init_database; init_database()"

# Start the server
echo "Starting server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""
echo "Access the dashboard at: http://localhost:5000"
echo ""

# Run the server
python3 server.py
