#!/bin/bash
# Quick start script for Deafine (Linux/Mac)

set -e

echo "🎤 Deafine Quick Start"
echo "===================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install package
echo "📥 Installing Deafine..."
pip install -e . --quiet

# Try to install webrtcvad (optional)
echo ""
echo "💰 Attempting to install webrtcvad (optional - saves API costs)..."
if pip install webrtcvad --quiet 2>/dev/null; then
    echo "✅ webrtcvad installed - VAD enabled!"
else
    echo "ℹ️  webrtcvad not installed (optional) - app works fine without it"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env file..."
    cp env.template .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ELEVEN_API_KEY!"
    echo ""
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
python test_installation.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your ELEVEN_API_KEY"
echo "  2. Run: source .venv/bin/activate"
echo "  3. Run: deafine run"
echo ""
