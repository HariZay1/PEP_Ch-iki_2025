#!/usr/bin/env bash
# Exit on error
set -o errexit

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install dependencies with binary-only preference
pip install --only-binary :all: -r requirements.txt

# If binary installation fails, fall back to source with optimization
pip install --prefer-binary -r requirements.txt 2>/dev/null || pip install -r requirements.txt

# Run migrations
python -m flask db upgrade

# Collect static files if needed
if [ -d "static" ]; then
    echo "Static files directory found"
fi
