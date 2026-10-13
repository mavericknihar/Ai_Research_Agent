#!/bin/bash
# Autonomous Research Agent Launcher

# Resolve script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Check if .venv exists
if [ ! -d "$DIR/.venv" ]; then
    echo "Virtual environment not found at $DIR/.venv"
    echo "Please ensure the .venv is set up."
    exit 1
fi

echo "⚡ Starting Autonomous Research Agent..."
echo "📍 Access UI in your browser once Streamlit starts."

# Launch Streamlit app
"$DIR/.venv/bin/streamlit" run "$DIR/research_agent/app.py"
