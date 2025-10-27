#!/bin/bash

echo "🏆 Installing Chess Tournament Web System"
echo "=========================================="
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "Installing Python dependencies..."
pip3 install -r requirements_web_tournament.txt

if [ $? -eq 0 ]; then
    echo
    echo "✅ Installation completed successfully!"
    echo
    echo "To start the tournament system, run:"
    echo "  python3 run_tournament_web.py"
    echo
    echo "Or directly:"
    echo "  python3 tournament_web.py --serve"
    echo
    echo "Then open your browser to: http://localhost:5000"
else
    echo
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi