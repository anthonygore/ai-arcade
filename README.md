# 🎮 AI Arcade

**Play terminal games while AI coding agents think.**

Stop context-switching to your phone while waiting for Claude Code, Aider, or other AI tools. Stay in the terminal, stay productive.

---

## ✨ Features

- 🤖 **Multi-Agent Support**: Works with Claude Code, Aider, Cursor, and more
- 🎮 **Built-in Games**: Snake, 2048, and more puzzle games
- 🔄 **Save States**: Pause and resume games anytime
- 📊 **Smart Monitoring**: Detects when AI is ready for input
- ⌨️ **Seamless Switching**: Quick keybindings to switch between AI and games
- 🎯 **Zero Config**: Works out of the box with sensible defaults

---

## 📦 Installation

### Prerequisites

- **Python 3.9 or higher**
- **tmux** - Install with:
  - macOS: `brew install tmux`
  - Linux (Debian/Ubuntu): `sudo apt-get install tmux`
  - Linux (RedHat/CentOS): `sudo yum install tmux`

### Via pip (Recommended)

```bash
pip install ai-arcade
ai-arcade
```

### From Source

```bash
git clone https://github.com/anthonygore/ai-arcade
cd ai-arcade
pip install -e .
ai-arcade
```

### With Poetry (for development)

```bash
git clone https://github.com/anthonygore/ai-arcade
cd ai-arcade
poetry install
poetry run ai-arcade
```

---

## 🚀 Quick Start

1. **Launch AI Arcade**:
   ```bash
   ai-arcade
   ```

2. **Select your AI agent** from the menu (or choose "Games Only")

3. **Switch between windows**:
   - `Ctrl+Space` - Toggle between AI and Games windows

4. **Play games while AI thinks!** 🎮

---

## 🎮 Built-in Games

### Snake 🐍
Classic arcade action. Eat food, grow longer, avoid walls and yourself!
- **Controls**: Arrow keys to move, P to pause, Q to quit
- **Goal**: Get the highest score possible

### 2048 🔢
Addictive number puzzle. Combine tiles to reach 2048!
- **Controls**: Arrow keys to slide, P to pause, R to restart, Q to quit
- **Goal**: Combine tiles to create a 2048 tile

---

## 🤖 Supported AI Agents

| Agent | Status | Command |
|-------|--------|---------|
| Claude Code | ✅ Fully Supported | `claude` |
| Aider | ✅ Fully Supported | `aider` |
| Cursor AI | ✅ Supported | `cursor-cli` |
| Generic | ✅ Fallback | Any CLI tool |

---

## ⚙️ Configuration

Configuration file location: `~/.ai-arcade/config.yaml`

The configuration file is created automatically on first run with sensible defaults.

### Example Configuration

```yaml
# AI Agents
agents:
  claude_code:
    name: "Claude Code"
    command: "claude"
    ready_patterns:
      - "What would you like to do\\?"
      - "^> "

# tmux Settings
tmux:
  session_name: "ai-arcade"
  mouse_mode: true
  status_bar: true

# Keybindings
keybindings:
  toggle_window: "C-Space"  # Ctrl+Space to toggle between windows

# Notifications
notifications:
  enabled: true
  visual: true
  message: "🤖 AI Ready"
```

### Adding Custom AI Agents

To add a custom AI agent, edit `~/.ai-arcade/config.yaml`:

```yaml
agents:
  my_agent:
    name: "My AI Tool"
    command: "my-ai-cli"
    args: []
    ready_patterns:
      - "Ready>"  # Regex pattern to detect when agent is ready
```

---

## 🎯 How It Works

1. **Dual-Window Setup**: AI Arcade creates a tmux session with two full-screen windows:
   - **Window 0 (AI Agent)**: Your AI coding agent runs here with full terminal space
   - **Window 1 (Games)**: Game runner with full terminal space

2. **Smart Monitoring**: AI Arcade watches the AI agent's output for:
   - Configured regex patterns (e.g., prompt indicators)
   - Inactivity timeout (no output for N seconds = ready)

3. **Notifications**: When the AI is ready for input, you get a notification in the game window

4. **Seamless Switching**: Use configured keybindings to instantly switch between windows - both stay running with full state preserved

---

## 📁 Project Structure

```
~/.ai-arcade/
├── config.yaml          # Main configuration
├── games_metadata.json  # Game stats and metadata
└── save_states/         # Saved game states
    ├── snake.json
    └── 2048.json
```

---

## 🐛 Troubleshooting

### tmux not found

**Error**: `tmux is not installed`

**Solution**: Install tmux:
```bash
# macOS
brew install tmux

# Linux (Debian/Ubuntu)
sudo apt-get install tmux

# Linux (RedHat/CentOS)
sudo yum install tmux
```

### No AI agents detected

**Issue**: Launcher shows "No AI agents detected"

**Solution**: Install an AI CLI tool:
```bash
# Claude Code
pip install claude-code

# Aider
pip install aider-chat
```

### Games are slow or laggy

**Issue**: Game performance is poor

**Solution**:
- Increase terminal font size
- Close other applications
- Check terminal emulator performance settings

---

## 🛠️ Development

### Running Tests

```bash
poetry install
poetry run pytest
```

### Code Formatting

```bash
poetry run black ai_arcade/
poetry run ruff check ai_arcade/
```

### Type Checking

```bash
poetry run mypy ai_arcade/
```

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

- Built with [Textual](https://textual.textualize.io/) - Modern Python TUI framework
- Powered by [tmux](https://github.com/tmux/tmux) - Terminal multiplexer
- Inspired by the need to stay productive while AI agents think

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Adding New Games

1. Create a new game class in `ai_arcade/games/`
2. Inherit from `BaseGame` and implement required methods
3. Add game metadata
4. Test your game
5. Submit a PR!

---

## 📮 Support

- **Issues**: [GitHub Issues](https://github.com/anthonygore/ai-arcade/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anthonygore/ai-arcade/discussions)

---

Made with ❤️ by developers, for developers.
