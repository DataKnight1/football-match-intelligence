#!/bin/bash

echo "============================================"
echo "  Football Match Visualizer"
echo "  Streamlit App Launcher"
echo "============================================"
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found!"
    echo "Please run setup first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if streamlit is installed
if ! pip show streamlit > /dev/null 2>&1; then
    echo "Streamlit not installed!"
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting Streamlit app..."
echo "App will open in your default browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"
echo ""

# Run streamlit
streamlit run streamlit_app.py
