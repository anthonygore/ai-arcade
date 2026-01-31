# AI Arcade - Implementation Plan

## Overview
Build a terminal application that lets developers play games while waiting for AI coding agents (Claude Code, Aider, etc.) to process requests. Uses tmux with separate full-screen windows (Window 0: AI agent, Window 1: Games) that you can switch between instantly while maintaining full state in each window.

## User Requirements
- **Scope**: Full MVP with all core features
- **TUI Framework**: Textual (modern, well-documented)
- **Games**: Simple built-in Python games (Snake, 2048) - not nbsdgames initially
- **Packaging**: Proper Python packaging with Poetry for PyPI distribution

## Technology Stack
- **Language**: Python 3.9+
- **Terminal Multiplexing**: tmux
- **TUI Framework**: Textual
- **Config**: PyYAML
- **Package Management**: Poetry
- **Metadata Storage**: JSON

## Project Structure
```
ai-arcade/
├── ai_arcade/
│   ├── cli.py                    # Main entry point
│   ├── config.py                 # Configuration management
│   ├── tmux_manager.py           # tmux session orchestration
│   ├── ai_monitor.py             # AI output monitoring
│   ├── game_runner.py            # Game execution orchestration
│   ├── game_library.py           # Game metadata management
│   ├── ui/
│   │   ├── launcher_menu.py      # Initial menu (select AI/games)
│   │   └── game_selector.py      # Game selection interface
│   ├── agents/
│   │   ├── base.py               # Base agent class
│   │   ├── claude_code.py        # Claude Code preset
│   │   ├── aider.py              # Aider preset
│   │   └── generic.py            # Generic fallback
│   └── games/
│       ├── base_game.py          # Abstract game interface
│       ├── snake.py              # Snake game
│       └── game_2048.py          # 2048 puzzle
├── scripts/setup.sh
├── tests/
├── pyproject.toml
└── README.md
```

## Implementation Phases

### Phase 0: Project Initialization (Build First)
**Goal**: Set up project structure and dependencies

**Steps**:
1. Initialize Poetry project with pyproject.toml
2. Add dependencies: textual, pyyaml
3. Add dev dependencies: pytest, black, mypy, ruff
4. Create directory structure
5. Set up .gitignore
6. Define Poetry script entry point: `ai-arcade = "ai_arcade.cli:main"`

**Critical Files**:
- `pyproject.toml` - Project config with Poetry
- `ai_arcade/__init__.py` - Package initialization

### Phase 1: Configuration System
**Goal**: Robust config management with YAML

**Implementation**: `ai_arcade/config.py`

**Key Features**:
- Load config from `~/.ai-arcade/config.yaml`
- Create default config on first run
- Dataclass-based validation
- Agent lookup methods

**Config Structure** (default):
```yaml
agents:
  claude_code:
    name: "Claude Code"
    command: "claude"
    ready_patterns: ["What would you like to do\\?", "^> "]
  aider:
    name: "Aider"
    command: "aider"
    ready_patterns: ["^> "]

tmux:
  session_name: "ai-arcade"
  mouse_mode: true
  status_bar: true

monitoring:
  check_interval: 0.5
  inactivity_timeout: 2.0
  buffer_lines: 50

games:
  metadata_file: "~/.ai-arcade/games_metadata.json"
  save_state_dir: "~/.ai-arcade/save_states"
```

### Phase 2: Game Infrastructure
**Goal**: Create game system with base interface and implementations

#### 2.1 Base Game Interface
**File**: `ai_arcade/games/base_game.py`

**Key Classes**:
- `GameState` enum (MENU, PLAYING, PAUSED, GAME_OVER, QUIT)
- `GameMetadata` dataclass (id, name, description, category, etc.)
- `BaseGame` abstract class with methods:
  - `run()` - Main game loop (blocking)
  - `get_save_state()` - Return serializable state
  - `load_save_state()` - Restore from state

#### 2.2 Game Library Manager
**File**: `ai_arcade/game_library.py`

**Key Features**:
- Discover all game classes via importlib
- Load/save metadata JSON (`~/.ai-arcade/games_metadata.json`)
- Track play stats (last_played, play_count, high_score)
- Manage save states (`~/.ai-arcade/save_states/{game_id}.json`)

**Methods**:
- `list_games(sort_by)` - List with sorting options
- `get_game(game_id)` - Instantiate game
- `update_play_stats()` - Update after session

#### 2.3 Implement Snake Game
**File**: `ai_arcade/games/snake.py`

**Features**:
- Textual App with game rendering
- Arrow key controls
- Collision detection (walls, self)
- Score tracking
- Pause/resume with 'p'
- Save/load state (snake position, direction, food)

#### 2.4 Implement 2048 Game
**File**: `ai_arcade/games/game_2048.py`

**Features**:
- 4x4 grid rendering
- Arrow keys for sliding tiles
- Tile merging logic
- Win/lose detection
- Save/load grid state

### Phase 3: tmux Manager
**Goal**: Robust tmux session management

**File**: `ai_arcade/tmux_manager.py`

**Key Features**:
- Check tmux availability (fail fast if missing)
- Create session with separate full-screen windows (Window 0: AI, Window 1: Games)
- Launch AI agent in AI window
- Launch game runner in game window
- Capture window output for monitoring
- Configure keybindings from config (next/previous window, direct window selection)
- Clean session shutdown

**Key Methods**:
- `create_session(working_dir)` - Set up dual windows
- `launch_ai_agent(command, args)` - Start AI in window 0
- `launch_game_runner()` - Start games in window 1
- `send_to_window(window_index, command)` - Execute in window
- `capture_window_output(window_index, lines)` - Read output
- `attach()` - Attach to session (blocking)
- `kill_session()` - Clean shutdown

**Design Decision**: Use tmux windows instead of split panes for full-screen real estate and better visibility

### Phase 4: AI Agent Integration
**Goal**: Extensible agent system with readiness detection

#### 4.1 Base Agent
**File**: `ai_arcade/agents/base.py`

**Key Classes**:
- `AgentStatus` dataclass (is_ready, confidence, matched_pattern)
- `BaseAgent` abstract class

**Key Methods**:
- `check_ready(output)` - Pattern matching on output
- `get_launch_command()` - Return (command, args)

#### 4.2 Agent Implementations
**Files**:
- `ai_arcade/agents/claude_code.py` - Claude Code config
- `ai_arcade/agents/aider.py` - Aider config
- `ai_arcade/agents/generic.py` - Generic fallback

**Agent Factory**: In `agents/__init__.py`, provide `create_agent(id, config)` factory

#### 4.3 AI Monitor
**File**: `ai_arcade/ai_monitor.py`

**Key Features**:
- Background thread monitoring AI window
- Poll every N seconds (configurable)
- Check agent patterns + inactivity timeout
- Notify game window when ready state changes (via tmux display-message)
- Thread-safe shutdown

**Design Decision**: Use tmux `display-message` to notify game window

### Phase 5: Game Runner & UI
**Goal**: Orchestrate game selection and execution

#### 5.1 Launcher Menu
**File**: `ai_arcade/ui/launcher_menu.py`

**Features**:
- Textual App with ASCII art title
- Buttons for each detected AI agent
- "Games Only" option
- Settings option (placeholder for MVP)
- Detect installed agents (check `which <command>`)

**Returns**: Dict with selected agent or games_only flag

#### 5.2 Game Selector
**File**: `ai_arcade/ui/game_selector.py`

**Features**:
- Textual Screen with DataTable
- Show game name, category, last played, play count, high score
- Indicate resume availability
- Arrow keys to navigate, Enter to play, R to resume

#### 5.3 Game Runner
**File**: `ai_arcade/game_runner.py`

**Features**:
- Show game selector screen
- Launch selected game (blocking)
- Update metadata after game session
- Save state on pause, delete on game over
- Loop back to selector after game

**Design Decision**: Runner is re-invoked in tmux game window after each game

### Phase 6: Main CLI Orchestration
**Goal**: Tie everything together

**File**: `ai_arcade/cli.py`

**Flow**:
1. Load config
2. Show launcher menu
3. If games-only: Run game runner standalone
4. If agent selected:
   - Create tmux session with two windows
   - Launch AI agent in window 0 (full screen)
   - Launch game runner in window 1 (full screen)
   - Start AI monitor
   - Attach to tmux (blocking)
   - Cleanup on exit

**Error Handling**:
- Handle KeyboardInterrupt
- Ensure tmux cleanup with atexit and signal handlers
- Show helpful errors for missing dependencies

### Phase 7: Packaging & Distribution
**Goal**: Prepare for PyPI distribution

#### 7.1 Setup Script
**File**: `scripts/setup.sh`

**Tasks**:
- Check for tmux (show install instructions if missing)
- Create `~/.ai-arcade/` directory
- Create save_states subdirectory

#### 7.2 Documentation
**File**: `README.md`

**Sections**:
- Features overview
- Installation (pip install ai-arcade)
- Quick start guide
- Keybinding reference
- Configuration guide
- Supported AI agents

#### 7.3 Testing
**Files**: `tests/test_*.py`

**Coverage**:
- Config loading/validation
- Game library discovery
- Agent pattern matching
- tmux manager (requires tmux)
- End-to-end manual testing

#### 7.4 PyPI Publishing
**Steps**:
1. `poetry build`
2. Test locally
3. Publish to Test PyPI first
4. Publish to real PyPI

## Implementation Order

### Week 1: Foundation
1. **Day 1**: Poetry setup, directory structure, config.py
2. **Day 2**: base_game.py, game_library.py
3. **Day 3-4**: Snake game implementation
4. **Day 5**: 2048 game implementation

### Week 2: Integration
5. **Day 6-7**: tmux_manager.py with testing
6. **Day 8**: Agent base classes and implementations
7. **Day 9-10**: ai_monitor.py with integration testing

### Week 3: UI & Orchestration
8. **Day 11**: launcher_menu.py
9. **Day 12**: game_selector.py
10. **Day 13**: game_runner.py
11. **Day 14**: cli.py integration
12. **Day 15**: End-to-end testing and bug fixes

### Week 4: Polish & Distribution
13. **Day 16-17**: Documentation, setup scripts
14. **Day 18**: Testing infrastructure
15. **Day 19**: Package refinement
16. **Day 20**: PyPI publication

## Critical Technical Decisions

### 1. Textual Inside tmux
- **Decision**: Games run as Textual apps in tmux windows (full screen)
- **Validation**: Textual works well in tmux with proper terminal setup
- **Mitigation**: Check minimum terminal size before launching games
- **Benefit**: Full-screen windows provide better visibility than split panes

### 2. AI Readiness Detection
- **Primary**: Regex pattern matching on recent output (last N lines)
- **Fallback**: Inactivity timeout (no output change for N seconds)
- **Configurable**: Users can customize patterns per agent

### 3. Game State Persistence
- **Format**: JSON files in `~/.ai-arcade/save_states/{game_id}.json`
- **Save on**: Pause
- **Delete on**: Game over
- **Responsibility**: Each game implements own serialization

### 4. Game Runner Re-entry
- **Approach**: Runner script re-invokes itself in tmux game window after game exits
- **Reason**: Keeps games isolated and simpler than parent process management

### 5. Process Cleanup
- **Mechanisms**: atexit handlers + signal handlers (SIGINT, SIGTERM)
- **tmux**: kill_session() is idempotent, safe to call multiple times
- **Goal**: Always clean up tmux session, even on crashes

## Potential Challenges

### 1. tmux Not Installed
**Mitigation**: Check early, show platform-specific install instructions

### 2. AI Agent Pattern Matching
**Mitigation**: Provide good defaults, allow customization, use inactivity fallback

### 3. Terminal Size
**Mitigation**: Check size before game launch, handle resize events

### 4. Cross-Platform Compatibility
**Scope**: macOS and Linux (Windows out of scope for MVP)
**Testing**: Test on both platforms during development

## Critical Files to Build (Priority Order)

1. **`ai_arcade/config.py`** - Foundation for everything
2. **`ai_arcade/games/base_game.py`** - Game interface
3. **`ai_arcade/games/snake.py`** - First concrete game
4. **`ai_arcade/game_library.py`** - Game management
5. **`ai_arcade/tmux_manager.py`** - Core infrastructure
6. **`ai_arcade/agents/base.py`** - Agent abstraction
7. **`ai_arcade/ai_monitor.py`** - Key differentiator
8. **`ai_arcade/ui/launcher_menu.py`** - First user touchpoint
9. **`ai_arcade/ui/game_selector.py`** - Game selection
10. **`ai_arcade/game_runner.py`** - Game orchestration
11. **`ai_arcade/cli.py`** - Main integration

## Success Criteria
- Clean installation via pip
- Launcher menu shows installed agents
- tmux session with dual windows (Window 0: AI, Window 1: Games)
- Games run in full-screen game window
- AI agent runs unmodified in full-screen AI window
- Window switching works (Ctrl+A + n/p or 0/1)
- AI monitoring detects ready state
- Game state persists across sessions
- Clean exit with proper cleanup

## Next Steps
Once approved, begin with Phase 0 (project initialization) and proceed through phases sequentially.
