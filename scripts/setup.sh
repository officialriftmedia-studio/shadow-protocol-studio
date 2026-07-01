#!/usr/bin/env bash
# setup.sh — initialize Shadow Protocol Studio for development
set -euo pipefail

echo "=== Shadow Protocol Studio Setup ==="

# Check Python version
python3 --version 2>/dev/null || { echo "ERROR: Python 3.11+ required"; exit 1; }

# Create virtualenv
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Install
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .

# Copy env template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env — edit it with your API keys"
fi

# Verify directory structure
echo "Verifying structure..."
for dir in bible agents prompts workflows projects memory templates config; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/"
    else
        echo "  ✗ $dir/  MISSING"
    fi
done

echo ""
echo "Setup complete! Run: create-video <case_id>"
