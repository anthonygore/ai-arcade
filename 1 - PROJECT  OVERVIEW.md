# Agent Arcade - Project Overview

## Intention

Create a terminal application that allows developers to play games while waiting for AI coding agents (like Claude Code, Codex, Aider, etc.) to process requests. The app provides seamless switching between the AI agent interface and a game runner, with visual indicators showing when the AI is ready for new input.

This solves the problem of context-switching and dead time during AI agent processing, keeping developers engaged in the terminal environment rather than switching to phones or other distractions.

## Core Features

### 1. Launch Interface
- Single command: `agent-arcade`
- On launch, presents a menu allowing users to:
  - Choose which AI CLI tool(s) to launch
  - Go directly to game runner
  - Configure settings
- No need to specify agent via command-line flags
- Can launch multiple AI agents in separate panes if desired

### 2. Dual-Pane Interface
- Top pane: AI coding agent running unmodified
- Bottom pane: Game runner with selection menu and active game
- Managed via tmux for robust terminal multiplexing
- Simple keybindings for pane switching (e.g., Ctrl+A + arrow keys)

### 3. AI Agent Support
- Built-in presets for popular agents:
  - Claude Code
  - GitHub Copilot CLI
  - Aider
  - Cursor CLI
  - Generic fallback for any terminal-based AI tool
- Detection of AI readiness via output pattern monitoring
- Visual/audio notifications when AI completes processing

### 4. Game Library Management
- Curated collection of terminal games shipped with the package
- Initial focus: nbsdgames (MIT licensed, consistent quality)
- Game metadata system tracking:
  - Currently active game
  - Last played game
  - Play time/session count
  - Game-specific high scores (where applicable)
- Package upgrades automatically add new games to library
- Games stored in package directory, not user-modifiable (ensures consistency)

### 5. Game Runner Interface
- Title screen with ASCII art branding
- Scrollable game selection menu with:
  - Game name and brief description
  - Last played timestamp
  - Quick resume option for paused games
- Status bar showing:
  - AI agent status (Thinking... / Ready / Processing)
  - Current game info
  - Quick-switch keybinding hints
- Pause/resume game state preservation
- Return to menu without losing game progress

### 6. Installation & Distribution
- Installable via pip: `pip install agent-arcade`
- Alternative: Homebrew formula for Mac users
- Automated setup script that:
  - Installs tmux if not present
  - Downloads and compiles nbsdgames collection
  - Creates config directory at `~/.agent-arcade/`
  - Sets up default configuration

### 7. Configuration
- YAML config file at `~/.agent-arcade/config.yaml`
- Configurable options:
  - Available AI agents and their commands
  - Keybindings for switching panes
  - Game library location
  - Notification preferences (visual/audio/both)
  - Status check interval for AI monitoring

## Proposed Plan

### Phase 1: Foundation (Week 1)
1. Set up Python project structure with Poetry/setuptools
2. Implement main launcher menu for selecting AI agent or games
3. Implement tmux wrapper for dual-pane management
4. Create basic launcher that can start selected AI agent
5. Verify AI agent runs unmodified in top pane

### Phase 2: Game Infrastructure (Week 1-2)
1. Build game metadata system (SQLite database or JSON file)
2. Create game launcher that can execute individual games
3. Implement game state persistence (pause/resume)
4. Integrate nbsdgames as initial game library
5. Build game selection TUI using Textual or curses

### Phase 3: AI Monitoring (Week 2)
1. Implement AI agent output monitoring
2. Create pattern detection for common AI agent prompts:
   - Claude Code: waiting for user input
   - Aider: prompt indicators
   - Generic: inactivity timeout
3. Build notification system for game pane
4. Add status bar with real-time AI status

### Phase 4: Polish & UX (Week 3)
1. Design title screen and branding
2. Implement smooth pane switching
3. Add keyboard shortcuts overlay/help screen
4. Create session management (resume last session)
5. Build metadata tracking (play time, last played, etc.)

### Phase 5: Distribution (Week 3-4)
1. Write comprehensive README with screenshots
2. Create installation script for dependencies
3. Package for PyPI distribution
4. Create Homebrew formula (optional)
5. Write contribution guidelines for adding new games

## Technical Implementation

### Technology Stack
- **Language**: Python 3.9+
- **Terminal Multiplexing**: tmux
- **TUI Framework**: Textual (modern, well-documented) or blessed (lightweight alternative)
- **Game Library**: nbsdgames (initial), extensible for future additions
- **Config**: PyYAML for configuration files
- **Metadata Storage**: JSON or SQLite for game metadata
- **Process Management**: subprocess module for AI agent launching
- **Package Management**: Poetry or setuptools for distribution

### Project Structure
```
agent-arcade/
├── agent_arcade/
│   ├── __init__.py
│   ├── cli.py              # Main entry point, launcher menu
│   ├── tmux_manager.py     # tmux session creation and management
│   ├── ai_monitor.py       # AI agent output monitoring
│   ├── game_runner.py      # Game launcher and state management
│   ├── game_library.py     # Game metadata and library management
│   ├── ui/
│   │   ├── launcher_menu.py   # Initial menu for selecting AI/games
│   │   ├── title_screen.py
│   │   ├── game_selector.py
│   │   ├── status_bar.py
│   │   └── notifications.py
│   ├── agents/
│   │   ├── base.py         # Base AI agent class
│   │   ├── claude_code.py  # Claude Code specific config
│   │   ├── aider.py        # Aider specific config
│   │   └── generic.py      # Generic fallback
│   └── config.py           # Configuration management
├── games/                  # Bundled games directory
│   └── nbsdgames/          # Downloaded during setup
├── scripts/
│   └── setup.sh            # Post-install setup script
├── tests/
├── pyproject.toml
├── README.md
└── LICENSE
```

### Key Components

#### 1. CLI Entry Point (`cli.py`)
```python
# Pseudocode
def main():
    config = load_config()
    
    # Show launcher menu
    choice = show_launcher_menu(config)
    
    if choice.type == "ai_agent":
        # Initialize tmux session
        session = TmuxManager(config)
        
        # Launch selected AI agent in top pane
        session.launch_agent(choice.agent)
        
        # Launch game runner in bottom pane
        session.launch_game_runner()
        
        # Start monitoring loop
        monitor = AIMonitor(session, config)
        monitor.start()
        
        # Attach to tmux session
        session.attach()
    
    elif choice.type == "games_only":
        # Launch just the game runner (no AI agent)
        game_runner = GameRunner()
        game_runner.run()
    
    elif choice.type == "settings":
        # Open configuration editor
        edit_config()

def show_launcher_menu(config):
    # Display TUI menu with options:
    # 1. Launch Claude Code + Games
    # 2. Launch Aider + Games
    # 3. Launch Copilot + Games
    # 4. Games Only
    # 5. Settings
    # 6. Exit
    return user_selection
```

#### 2. Launcher Menu (`ui/launcher_menu.py`)
```python
# Pseudocode
class LauncherMenu:
    def __init__(self, config):
        self.config = config
        self.available_agents = self.detect_installed_agents()
    
    def detect_installed_agents(self):
        # Check which AI CLI tools are installed
        agents = []
        for agent in self.config.agents:
            if is_command_available(agent.command):
                agents.append(agent)
        return agents
    
    def show(self):
        # Display menu using Textual or curses
        # Return user's choice
        options = [
            f"🤖 {agent.name} + Games" for agent in self.available_agents
        ]
        options.extend([
            "🎮 Games Only",
            "⚙️  Settings",
            "❌ Exit"
        ])
        
        return select_from_list(options)
```

#### 3. Tmux Manager (`tmux_manager.py`)
```python
# Pseudocode
class TmuxManager:
    def __init__(self, config):
        self.session_name = "agent-arcade"
        self.config = config
    
    def create_session(self):
        # Create new tmux session with split panes
        # Top pane: 70% height for AI agent
        # Bottom pane: 30% height for games
    
    def launch_agent(self, agent_command):
        # Execute AI agent in top pane
    
    def launch_game_runner(self):
        # Execute game runner TUI in bottom pane
    
    def send_to_pane(self, pane_id, command):
        # Send commands to specific pane
```

#### 4. AI Monitor (`ai_monitor.py`)
```python
# Pseudocode
class AIMonitor:
    def __init__(self, tmux_session, config):
        self.session = tmux_session
        self.patterns = load_agent_patterns(config.agent_type)
        self.check_interval = config.check_interval
    
    def start(self):
        # Background thread monitoring AI pane output
        while True:
            output = self.session.capture_pane("ai-pane")
            if self.is_ready(output):
                self.notify_game_pane()
            sleep(self.check_interval)
    
    def is_ready(self, output):
        # Check for ready patterns (e.g., prompt, inactivity)
        for pattern in self.patterns:
            if re.search(pattern, output):
                return True
        return False
```

#### 5. Game Runner (`game_runner.py`)
```python
# Pseudocode
class GameRunner:
    def __init__(self):
        self.library = GameLibrary()
        self.current_game = None
        self.metadata = load_metadata()
    
    def run(self):
        # Main TUI loop
        while True:
            if not self.current_game:
                game = self.show_selector()
                self.launch_game(game)
            else:
                # Game is running, monitor for exit/pause
                if user_requests_menu():
                    self.pause_current_game()
    
    def show_selector(self):
        # Display game selection TUI with metadata
    
    def launch_game(self, game):
        # Execute game binary, track metadata
        self.metadata.update_last_played(game)
    
    def pause_current_game(self):
        # Save game state, return to selector
```

#### 6. Game Library (`game_library.py`)
```python
# Pseudocode
class GameLibrary:
    def __init__(self):
        self.games = self.load_games()
        self.metadata_db = MetadataDB()
    
    def load_games(self):
        # Scan games directory for executables
        # Return list of Game objects with metadata
    
    def add_game(self, game_info):
        # Called during package upgrade to add new games
    
    def get_game_info(self, game_id):
        # Return game metadata including play stats

class Game:
    def __init__(self, name, path, description):
        self.name = name
        self.path = path
        self.description = description
        self.last_played = None
        self.play_count = 0
```

### Installation Flow

```bash
# User installs via pip
pip install agent-arcade

# Post-install script runs automatically:
# 1. Check for tmux, install if missing (brew install tmux on Mac)
# 2. Create ~/.agent-arcade/ directory
# 3. Download and compile nbsdgames
# 4. Generate default config.yaml
# 5. Initialize metadata database

# User launches
agent-arcade

# Shows launcher menu where user selects:
# - Which AI agent to use (or none)
# - Or go directly to games
# - Or configure settings
```

### Configuration Example (`config.yaml`)

```yaml
# AI agent presets
agents:
  - name: "Claude Code"
    command: "claude-code"
    ready_patterns:
      - "What would you like to do\\?"
      - "^> "
  
  - name: "Aider"
    command: "aider"
    ready_patterns:
      - "^> "
  
  - name: "GitHub Copilot"
    command: "github-copilot-cli"
    ready_patterns:
      - "^\\? "
  
  - name: "Cursor"
    command: "cursor-cli"
    ready_patterns:
      - "^> "
  
# Keybindings (tmux style)
keybindings:
  prefix: "C-a"  # Ctrl+A
  switch_up: "Up"
  switch_down: "Down"
  help: "?"

# Games configuration
games:
  directory: "~/.agent-arcade/games"
  auto_update: true

# Monitoring
check_interval: 1.0  # seconds
inactivity_timeout: 3.0  # seconds of no output = ready

# Notifications
notifications:
  visual: true
  audio: false  # Optional beep when AI ready
  message: "🤖 AI Ready"

# UI preferences
ui:
  theme: "default"
  show_last_played: true
  confirm_exit: true
```

## User Flow Examples

### Example 1: Launch with AI Agent
```
$ agent-arcade

┌─────────────────────────────────────┐
│         🎮 AI ARCADE 🎮            │
├─────────────────────────────────────┤
│  1. 🤖 Claude Code + Games         │
│  2. 🤖 Aider + Games               │
│  3. 🎮 Games Only                  │
│  4. ⚙️  Settings                   │
│  5. ❌ Exit                        │
└─────────────────────────────────────┘

Select option: 1

[Launches tmux session with Claude Code in top pane, game menu in bottom pane]
```

### Example 2: Games Only
```
$ agent-arcade

[User selects "Games Only"]

[Full-screen game selection interface appears]
[No AI agent launched, no pane splitting]
```

### Example 3: First-time Setup
```
$ agent-arcade

⚠️  No AI agents detected!

Would you like to:
  1. Install Claude Code (recommended)
  2. Configure manually
  3. Continue with games only

[Guides user through setup]
```

## Future Enhancements (Post-MVP)

1. **Expanded Game Library**: Add more curated games with each release
2. **Game Categories**: Organize games by type (puzzle, arcade, strategy)
3. **Achievements System**: Track milestones across sessions
4. **Multiplayer Support**: Games that can be played with other developers
5. **AI Agent Plugins**: Let community add support for new AI tools
6. **Themes**: Customizable color schemes and UI themes
7. **Statistics Dashboard**: Overall play time, favorite games, etc.
8. **Cloud Sync**: Sync game progress and metadata across machines
9. **Custom Game Integration**: Allow users to add personal games via config
10. **Web Dashboard**: Optional web UI for game library management
11. **Multiple AI Agents**: Launch multiple agents in different panes simultaneously
12. **Agent Profiles**: Save preferred agent + game combinations

## Success Metrics

- Clean installation process (<2 minutes from pip install to first run)
- Zero modifications required to AI agent CLIs
- <100ms latency on pane switching
- Reliable AI readiness detection (>95% accuracy)
- Game state preservation across sessions
- Cross-platform compatibility (macOS, Linux)
- Intuitive launcher menu requiring no documentation

## Deliverables

1. Functional Python package on PyPI
2. Comprehensive documentation with examples
3. Installation guide for different platforms
4. Contribution guidelines for adding games
5. Demo video/GIF showing the tool in action
6. GitHub repository with CI/CD pipeline

This project should take approximately 3-4 weeks for a solo developer to build the MVP, with iterative improvements possible afterward based on user feedback.
