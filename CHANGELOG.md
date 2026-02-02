# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.3] - 2025-02-02

### Fixed
- Skip version check in dev mode (prevents upgrade warnings when running from source)

## [1.1.2] - 2025-02-02

### Fixed
- Use correct Python executable path in production (fixes "python: command not found" error)
- Now uses `sys.executable` to ensure the same Python interpreter is used

## [1.1.1] - 2025-02-02

### Fixed
- Production installations now work correctly (removed hardcoded poetry commands)
- App properly detects dev vs production mode and uses appropriate python commands

## [1.1.0] - 2025-02-02

### Added
- Published/unpublished games feature - games can now be marked for production release
- Only Snake is published in v1.1.0; other games remain in development

### Fixed
- Dev mode detection now works correctly with `poetry run`
- Development instances now use `~/.agent-arcade-dev` for data isolation
- Production instances use `~/.agent-arcade`

## [1.0.0] - 2025-02-02

### Added
- Initial release of Agent Arcade
- Agent selection menu with support for Claude Code and Codex
- Snake game with save states and high scores
- Smart AI monitoring with idle/active state detection
- Dual-pane tmux interface (agent window + game window)
- Quick window switching with Ctrl+Space
- Status bar showing agent state and game info
- Cross-platform support (macOS, Linux, Windows via WSL)
- Automatic version checking on startup

[1.1.3]: https://github.com/anthonygore/agent-arcade/releases/tag/v1.1.3
[1.1.2]: https://github.com/anthonygore/agent-arcade/releases/tag/v1.1.2
[1.1.1]: https://github.com/anthonygore/agent-arcade/releases/tag/v1.1.1
[1.1.0]: https://github.com/anthonygore/agent-arcade/releases/tag/v1.1.0
[1.0.0]: https://github.com/anthonygore/agent-arcade/releases/tag/v1.0.0
