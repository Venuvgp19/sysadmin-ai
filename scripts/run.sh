#!/usr/bin/env bash
# SysAdmin AI Launcher for Linux/macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "WARNING: No virtual environment found. Using system Python."
fi

export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export SYSADMIN_MODEL="${SYSADMIN_MODEL:-qwen2.5:7b}"
export PYTHONPATH="$PWD"

echo ""
echo " ================================================"
echo "  SysAdmin AI Agent"
echo " ================================================"
echo ""

python3 agent/main.py
