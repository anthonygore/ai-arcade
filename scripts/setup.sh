#!/bin/bash
# Post-install setup script for Agent Arcade

set -e

echo "🎮 Setting up Agent Arcade..."
echo ""

# Check for tmux
if ! command -v tmux &> /dev/null; then
    echo "⚠️  tmux not found!"
    echo ""

    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Install tmux on macOS:"
        echo "  brew install tmux"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Install tmux on Linux:"
        echo "  Debian/Ubuntu: sudo apt-get install tmux"
        echo "  RedHat/CentOS: sudo yum install tmux"
        echo "  Arch Linux: sudo pacman -S tmux"
    fi

    echo ""
    echo "After installing tmux, run: agent-arcade"
    exit 1
fi

echo "✓ tmux found: $(tmux -V)"
echo ""

# Create config directory
CONFIG_DIR="$HOME/.agent-arcade"
mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/save_states"

echo "✓ Created config directory: $CONFIG_DIR"
echo ""

# Check if config exists
if [ -f "$CONFIG_DIR/config.yaml" ]; then
    echo "✓ Existing config found at $CONFIG_DIR/config.yaml"
else
    echo "✓ Config will be created on first run at $CONFIG_DIR/config.yaml"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Quick Start:"
echo "  1. Run: agent-arcade"
echo "  2. Select an AI agent or 'Games Only'"
echo "  3. Press Ctrl+A + Up/Down to switch panes"
echo ""
echo "📝 Configuration: $CONFIG_DIR/config.yaml"
echo ""
echo "🎮 Have fun!"
