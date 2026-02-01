"""2048 puzzle game implementation."""

import random
from typing import Any, Dict, List, Tuple

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Static

from .base_game import BaseGame, GameMetadata, GameState


class Game2048(BaseGame):
    """2048 puzzle game."""

    def __init__(self):
        """Initialize 2048 game."""
        super().__init__()

    @property
    def metadata(self) -> GameMetadata:
        """Return game metadata."""
        return GameMetadata(
            id="2048",
            name="2048",
            description="Combine tiles to reach 2048! Addictive number puzzle game.",
            category="puzzle",
            author="AI Arcade Team",
            controls_help="",
            min_terminal_size=(40, 20)
        )

    @property
    def key_bindings(self) -> Tuple[str, ...]:
        """Key bindings used by 2048."""
        return ("Arrows: Slide", "P: Pause", "R: Restart", "Q: Quit")

    def run(self) -> None:
        """Run the 2048 game."""
        app = Game2048App(self)
        app.run()
        self.score = app.score
        self.state = app.game_state

    def get_save_state(self) -> Dict[str, Any]:
        """Get current game state for saving."""
        # For MVP, just save score
        # Full implementation would save the entire grid
        return {
            "score": self.score
        }

    def load_save_state(self, state: Dict[str, Any]) -> None:
        """Load game from saved state."""
        self.score = state.get("score", 0)


class Game2048App(App):
    """Textual app for 2048 game."""

    CSS = """
    Screen {
        align: center middle;
    }

    #game-container {
        width: 50;
        height: 28;
        border: solid cyan;
        background: $panel;
    }

    #score-display {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        color: $text;
        text-style: bold;
    }

    #game-board {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }

    #instructions {
        dock: bottom;
        height: 3;
        content-align: center middle;
        background: $panel;
    }
    """

    BINDINGS = [
        ("p", "toggle_pause", "Pause"),
        ("q", "quit_game", "Quit"),
        ("r", "restart", "Restart"),
    ]

    def __init__(self, game: Game2048):
        """Initialize the app."""
        super().__init__()
        self.game_ref = game
        self.score = 0
        self.game_state = GameState.PLAYING

        # Initialize 4x4 grid
        self.grid: List[List[int]] = [[0] * 4 for _ in range(4)]
        self._add_new_tile()
        self._add_new_tile()

        # Game state
        self.is_paused = False
        self.game_over = False
        self.won = False

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        with Container(id="game-container"):
            yield Static(id="score-display")
            yield Static(id="game-board")

        yield Static(id="instructions")
    def on_mount(self) -> None:
        """Called when app starts."""
        self._update_display()

    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        if self.game_over or self.is_paused:
            return

        # Map keys to move directions
        moved = False
        if event.key == "up":
            moved = self._move_up()
        elif event.key == "down":
            moved = self._move_down()
        elif event.key == "left":
            moved = self._move_left()
        elif event.key == "right":
            moved = self._move_right()

        if moved:
            self._add_new_tile()
            self._check_game_state()
            self._update_display()

    def _move_left(self) -> bool:
        """Move tiles left. Returns True if any tile moved."""
        return self._apply_move(self._slide_row_left)

    def _move_right(self) -> bool:
        """Move tiles right. Returns True if any tile moved."""
        return self._apply_move(lambda row: list(reversed(self._slide_row_left(list(reversed(row))))))

    def _move_up(self) -> bool:
        """Move tiles up. Returns True if any tile moved."""
        return self._apply_move_vertical(self._slide_row_left)

    def _move_down(self) -> bool:
        """Move tiles down. Returns True if any tile moved."""
        return self._apply_move_vertical(lambda col: list(reversed(self._slide_row_left(list(reversed(col))))))

    def _slide_row_left(self, row: List[int]) -> List[int]:
        """
        Slide a single row to the left and merge tiles.

        Args:
            row: List of 4 integers

        Returns:
            New row after sliding and merging
        """
        # Remove zeros
        non_zero = [x for x in row if x != 0]

        # Merge adjacent equal tiles
        merged = []
        i = 0
        while i < len(non_zero):
            if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
                # Merge tiles
                merged_value = non_zero[i] * 2
                merged.append(merged_value)
                self.score += merged_value
                i += 2
            else:
                merged.append(non_zero[i])
                i += 1

        # Pad with zeros
        while len(merged) < 4:
            merged.append(0)

        return merged

    def _apply_move(self, slide_func) -> bool:
        """
        Apply a move function to all rows.

        Args:
            slide_func: Function to apply to each row

        Returns:
            True if grid changed
        """
        new_grid = [slide_func(row[:]) for row in self.grid]

        # Check if grid changed
        changed = new_grid != self.grid

        if changed:
            self.grid = new_grid

        return changed

    def _apply_move_vertical(self, slide_func) -> bool:
        """
        Apply a move function to all columns.

        Args:
            slide_func: Function to apply to each column

        Returns:
            True if grid changed
        """
        # Transpose
        columns = [[self.grid[row][col] for row in range(4)] for col in range(4)]

        # Apply slide function
        new_columns = [slide_func(col[:]) for col in columns]

        # Check if changed
        changed = new_columns != columns

        if changed:
            # Transpose back
            self.grid = [[new_columns[col][row] for col in range(4)] for row in range(4)]

        return changed

    def _add_new_tile(self) -> None:
        """Add a new tile (2 or 4) to a random empty cell."""
        empty_cells = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]

        if empty_cells:
            r, c = random.choice(empty_cells)
            # 90% chance of 2, 10% chance of 4
            self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def _check_game_state(self) -> None:
        """Check if game is won or lost."""
        # Check for 2048 (win)
        for row in self.grid:
            if 2048 in row:
                self.won = True
                self.game_over = True
                self.game_state = GameState.GAME_OVER
                return

        # Check if any moves possible
        # First check for empty cells
        for row in self.grid:
            if 0 in row:
                return  # Game continues

        # Check for possible merges horizontally
        for row in self.grid:
            for i in range(3):
                if row[i] == row[i + 1]:
                    return  # Game continues

        # Check for possible merges vertically
        for col in range(4):
            for row in range(3):
                if self.grid[row][col] == self.grid[row + 1][col]:
                    return  # Game continues

        # No moves possible - game over
        self.game_over = True
        self.game_state = GameState.GAME_OVER

    def _update_display(self) -> None:
        """Update the game display."""
        # Update score
        score_widget = self.query_one("#score-display", Static)
        score_widget.update(f"2048 | Score: {self.score}")

        # Update game board
        board_widget = self.query_one("#game-board", Static)
        board_text = self._render_board()
        board_widget.update(board_text)

        # Update instructions
        instructions_widget = self.query_one("#instructions", Static)
        if self.game_over:
            if self.won:
                instructions_widget.update(f"YOU WON! Score: {self.score}")
            else:
                instructions_widget.update(f"GAME OVER! Score: {self.score}")
        elif self.is_paused:
            instructions_widget.update("PAUSED")
        else:
            instructions_widget.update("")

    def _render_board(self) -> str:
        """Render the game board as text."""
        lines = []
        lines.append("┌──────┬──────┬──────┬──────┐")

        for row_idx, row in enumerate(self.grid):
            # Tile row
            tile_line = "│"
            for tile in row:
                if tile == 0:
                    tile_line += "      │"
                else:
                    tile_line += f" {tile:4d} │"
            lines.append(tile_line)

            # Separator
            if row_idx < 3:
                lines.append("├──────┼──────┼──────┼──────┤")

        lines.append("└──────┴──────┴──────┴──────┘")

        return "\n".join(lines)

    def action_toggle_pause(self) -> None:
        """Toggle pause state."""
        if not self.game_over:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.game_state = GameState.PAUSED
            else:
                self.game_state = GameState.PLAYING
            self._update_display()

    def action_restart(self) -> None:
        """Restart the game."""
        self.score = 0
        self.grid = [[0] * 4 for _ in range(4)]
        self._add_new_tile()
        self._add_new_tile()
        self.game_over = False
        self.won = False
        self.is_paused = False
        self.game_state = GameState.PLAYING
        self._update_display()

    def action_quit_game(self) -> None:
        """Quit the game."""
        self.game_state = GameState.QUIT
        self.exit()
