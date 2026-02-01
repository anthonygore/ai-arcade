# Agent Arcade - Window-Based UI Update

## ✅ Complete - All Changes Implemented

Successfully updated Agent Arcade from split-pane layout to full-screen window-based layout for better visibility and UX.

---

## 🔄 What Changed

### Before (Split Panes):
- Top pane (70%): AI agent in cramped space
- Bottom pane (30%): Games in cramped space
- Both visible simultaneously but hard to read

### After (Full-Screen Windows):
- **Window 0**: AI agent with full terminal space
- **Window 1**: Games with full terminal space
- Switch between windows instantly - both maintain full state
- Much better visibility and usability

---

## 📝 Files Modified

### 1. `agent_arcade/tmux_manager.py` ✅
**Changes**:
- Changed from `split-window` to `new-window` for creating separate full-screen windows
- Updated from pane IDs to window indices (0 and 1)
- Renamed methods:
  - `ai_pane_id` → `ai_window_index`
  - `game_pane_id` → `game_window_index`
  - `send_to_pane()` → `send_to_window()`
  - `capture_pane_output()` → `capture_window_output()`
- Added window naming: "AI Agent" and "Games"
- Updated keybindings to use `next-window`, `previous-window`, and direct selection (0, 1)
- Enhanced status bar to show current window info

### 2. `agent_arcade/ai_monitor.py` ✅
**Changes**:
- Updated to use `capture_window_output()` instead of `capture_pane_output()`
- Changed from `ai_pane_id` to `ai_window_index`
- Updated notification target to use window index instead of pane ID

### 3. `agent_arcade/config.py` ✅
**Changes**:
- **KeybindingsConfig dataclass updated**:
  - Removed: `switch_to_ai` and `switch_to_game`
  - Added: `next_window` (default: "n") and `previous_window` (default: "p")
- **Default configuration updated**:
  - Removed `pane_split_ratio`
  - Added `status_bar: true`
  - Updated keybindings in `get_default_config()`
  - Updated keybindings parsing in `from_dict()`

### 4. `agent_arcade/cli.py` ✅
**Changes**:
- Updated usage instructions to show:
  - `Ctrl+A + n`: Next window
  - `Ctrl+A + p`: Previous window
  - `Ctrl+A + 0`: Go to AI window
  - `Ctrl+A + 1`: Go to Games window
- Removed old pane switching instructions

### 5. `README.md` ✅
**Changes**:
- **Quick Start section**: Updated keybindings
- **Configuration example**: Removed `pane_split_ratio`, updated keybindings
- **How It Works section**: Changed from "Dual-Pane Setup" to "Dual-Window Setup"
  - Emphasized full-screen windows
  - Updated all references from pane → window

### 6. `2 - PROJECT PLAN.md` ✅
**Changes**:
- **Overview**: Updated to describe window-based approach
- **Phase 3 (tmux Manager)**:
  - Changed from split panes to separate windows
  - Updated all method names and descriptions
  - Added new design decision justification
- **Phase 4 (AI Monitor)**: Updated pane references to window
- **Phase 5 (Game Runner)**: Updated pane references to window
- **Phase 6 (CLI)**: Updated flow to mention two windows
- **Configuration examples**: Removed pane_split_ratio
- **Critical Technical Decisions**: Added benefit of full-screen windows
- **Success Criteria**: Updated to reflect window-based UI

---

## 🎮 New Keybindings

| Key Combination | Action |
|----------------|--------|
| `Ctrl+A` then `n` | Next window (AI → Games → AI...) |
| `Ctrl+A` then `p` | Previous window (Games → AI → Games...) |
| `Ctrl+A` then `0` | Jump directly to AI window |
| `Ctrl+A` then `1` | Jump directly to Games window |
| `Ctrl+A` then `q` | Quit session |
| `Ctrl+A` then `?` | Show help |

---

## ✨ Benefits of Window-Based Approach

### 1. **Better Visibility** 📺
- Full terminal space for both AI and games
- No cramped split panes
- Easier to read code and game interfaces

### 2. **Simpler Mental Model** 🧠
- Think of it like browser tabs or IDE tabs
- Natural window switching workflow
- Familiar to tmux users

### 3. **State Preservation** 💾
- Both windows remain fully running
- Perfect state preservation when switching
- No interruption to either process

### 4. **Cleaner UI** ✨
- No visible split line
- Full-screen real estate
- Professional appearance

### 5. **Better Game Experience** 🎮
- Games have full terminal to work with
- Better for games that need space (Snake)
- Easier to see game elements

---

## 🧪 Testing

To test the new window-based UI:

```bash
# Kill any existing session
tmux kill-session -t agent-arcade

# Run Agent Arcade
export PATH="/Users/anthonygore/.local/bin:$PATH"
cd /Users/anthonygore/Workspace/agent-arcade
poetry run agent-arcade
```

**Expected behavior**:
1. Launcher menu appears
2. Select an option
3. Two full-screen windows created (if using AI agent mode)
4. Use `Ctrl+A + n` to switch between windows
5. Both windows maintain full state when switching

---

## 📊 Code Statistics

- **Files modified**: 6
- **Lines changed**: ~150+
- **Breaking changes**: Config file (old configs need to regenerate)
- **Backward compatibility**: ⚠️ Users will need to delete old `~/.agent-arcade/config.yaml` to get new keybindings

---

## 🔧 Migration for Users

If users have an existing config file, they should:

1. **Option A - Start fresh** (recommended):
   ```bash
   rm ~/.agent-arcade/config.yaml
   agent-arcade  # Will create new config with window keybindings
   ```

2. **Option B - Manual update**:
   Edit `~/.agent-arcade/config.yaml` and change:
   ```yaml
   # Old
   keybindings:
     prefix: "C-a"
     switch_to_ai: "Up"
     switch_to_game: "Down"

   # New
   keybindings:
     prefix: "C-a"
     next_window: "n"
     previous_window: "p"
   ```

---

## ✅ Verification Checklist

- [x] tmux_manager.py uses windows instead of split panes
- [x] ai_monitor.py updated to use window capture
- [x] config.py has new keybindings (next_window, previous_window)
- [x] cli.py shows correct usage instructions
- [x] README.md reflects window-based UI
- [x] Project plan documents updated
- [x] All pane references changed to window references
- [x] Keybinding examples updated everywhere
- [x] Status bar updated to show window info
- [x] No references to pane_split_ratio remain

---

## 🎉 Result

Agent Arcade now provides a superior user experience with full-screen windows for both the AI agent and games, making it much more comfortable to use during AI wait times!

**Date**: January 31, 2026
**Status**: ✅ Complete and ready to test
