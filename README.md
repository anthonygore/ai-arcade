# Agent Arcade

**Play fun arcade games while waiting on AI agent tasks.**

![Demo](demo.gif)

Stop context-switching to your phone or social media while waiting for Claude Code or Codex to finish. Stay in the terminal, stay productive!

## Installation

### macOS

```bash
brew install tmux pipx
pipx install agent-arcade
```

### Linux

```bash
# Ubuntu/Debian
sudo apt-get install tmux
pipx install agent-arcade

# RedHat/CentOS
sudo yum install tmux
pipx install agent-arcade
```

### Windows (WSL)

```bash
# Install WSL first: wsl --install
# Then in your WSL terminal:
sudo apt-get install tmux
pipx install agent-arcade
```

## Quick Start

1. Launch Agent Arcade in your project directory:
   ```bash
   agent-arcade
   ```

2. Select your AI agent

3. Switch between agent/game view:
   - `Ctrl+Space`

4. Give your agent tasks and then play games while you wait!

## Supported AI Agents

- Claude Code
- Cursor

Want to add more agents? Submit a PR.

## Games

### Snake

Classic Snake game. Eat food, grow longer, avoid walls and yourself!

### In progress games

More games are coming soon. I'm currently working on:

- 2048
- Minesweeper
- Pong
- Sudoku

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

- Built with [Textual](https://textual.textualize.io/) - Modern Python TUI framework
- Powered by [tmux](https://github.com/tmux/tmux) - Terminal multiplexer

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone and setup
git clone https://github.com/anthonygore/agent-arcade
cd agent-arcade
poetry install

# Run in dev mode (uses ~/.agent-arcade-dev for data)
poetry run agent-arcade
```

## Support

- **Issues**: [GitHub Issues](https://github.com/anthonygore/agent-arcade/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anthonygore/agent-arcade/discussions)
