#!/bin/bash
# Launch script for AI-Native CFO Operating System

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "========================================================="
echo "AI-NATIVE CFO OPERATING SYSTEM"
echo "========================================================="
echo ""
echo "📍 Project directory: $PROJECT_DIR"
echo ""

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
python3 -c "import streamlit; import pandas; import plotly; import sklearn" 2>/dev/null || {
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
}

echo "✅ All dependencies ready"
echo ""
echo "🚀 Launching Streamlit UI..."
echo ""
echo "The dashboard will open at: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================================="
echo ""

streamlit run app.py
