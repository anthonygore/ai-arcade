"""Classic Snake game implementation."""

import random
from typing import Any, Dict, List, Tuple

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Static

from .base_game import BaseGame, GameMetadata, GameState


class SnakeGame(BaseGame):
    """Classic Snake game."""

    def __init__(self):
        """Initialize Snake game."""
        super().__init__()
        self.app = None  # Reference to running SnakeApp

    @property
    def metadata(self) -> GameMetadata:
        """Return game metadata."""
        return GameMetadata(
            id="snake",
            name="Snake",
            description="Classic snake game. Eat food, grow longer, avoid walls and yourself!",
            category="arcade",
            author="AI Arcade Team",
            controls_help="",
            min_terminal_size=(40, 20)
        )

    @property
    def key_bindings(self) -> Tuple[str, ...]:
        """Key bindings used by Snake."""
        return ("Arrows: Move", "P: Pause", "Q: Quit")

    def run(self) -> None:
        """Run the Snake game."""
        self.app = SnakeApp(self)
        self.app.run()
        self.score = self.app.score
        self.state = self.app.game_state
        self.app = None  # Clear reference after game ends

    def get_save_state(self) -> Dict[str, Any]:
        """Get current game state for saving."""
        # Snake doesn't implement save/resume for MVP
        # Would need to save snake position, direction, food, score
        return {
            "score": self.score
        }

    def load_save_state(self, state: Dict[str, Any]) -> None:
        """Load game from saved state."""
        # Snake doesn't implement save/resume for MVP
        self.score = state.get("score", 0)

    def pause(self) -> None:
        """Pause the game when switching away from game window."""
        super().pause()
        if self.app and not self.app.game_over:
            self.app.external_pause()

    def resume(self) -> None:
        """Resume the game when switching back to game window."""
        super().resume()
        if self.app and not self.app.game_over:
            self.app.external_resume()


class SnakeApp(App):
    """Textual app for Snake game."""

    CSS = """
    Screen {
        align: center middle;
    }

    #game-container {
        width: 60;
        height: 30;
        border: solid green;
        background: $panel;
    }

    #game-board {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }

    #score-display {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        color: $text;
        text-style: bold;
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
    ]

    def __init__(self, game: SnakeGame):
        """Initialize the app."""
        super().__init__()
        self.game_ref = game
        self.score = 0
        self.game_state = GameState.PLAYING

        # Game board settings
        self.board_width = 30
        self.board_height = 20

        # Snake
        self.snake: List[Tuple[int, int]] = [(15, 10), (14, 10), (13, 10)]
        self.direction = (1, 0)  # (dx, dy) - moving right initially
        self.next_direction = (1, 0)

        # Food
        self.food = self._spawn_food()

        # Game state
        self.is_paused = False
        self.game_over = False

        # Timer for game updates
        self.update_timer = None

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
        # Start game loop (update every 150ms)
        self.update_timer = self.set_interval(0.15, self._game_tick)

    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        if self.game_over or self.is_paused:
            return

        # Map keys to directions
        key_to_direction = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }

        if event.key in key_to_direction:
            new_direction = key_to_direction[event.key]

            # Prevent reversing into itself
            if (new_direction[0] + self.direction[0] != 0 or
                new_direction[1] + self.direction[1] != 0):
                self.next_direction = new_direction

    def _game_tick(self) -> None:
        """Update game state each tick."""
        if self.game_over or self.is_paused:
            return

        # Update direction
        self.direction = self.next_direction

        # Calculate new head position
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Check wall collision FIRST
        if (new_head[0] < 0 or new_head[0] >= self.board_width or
            new_head[1] < 0 or new_head[1] >= self.board_height):
            self._game_over()
            return

        # Check if we're eating food
        ate_food = (new_head == self.food)

        # Move snake - add new head
        self.snake.insert(0, new_head)

        # Handle food and growth
        if ate_food:
            # Grow: keep the tail, spawn new food
            self.score += 10
            self.food = self._spawn_food()
        else:
            # Don't grow: remove the tail
            self.snake.pop()

        # Check self collision AFTER moving
        # The new head shouldn't collide with any other part of the snake body
        # snake[0] is the new head, so check snake[1:] for collision
        if len(self.snake) > 1:
            if self.snake[0] in self.snake[1:]:
                self._game_over()
                return

        self._update_display()

    def _spawn_food(self) -> Tuple[int, int]:
        """Spawn food at random position not occupied by snake."""
        while True:
            food = (random.randint(0, self.board_width - 1),
                   random.randint(0, self.board_height - 1))
            if food not in self.snake:
                return food

    def _update_display(self) -> None:
        """Update the game display."""
        # Update score
        score_widget = self.query_one("#score-display", Static)
        score_widget.update(f"🐍 SNAKE | Score: {self.score}")

        # Update game board
        board_widget = self.query_one("#game-board", Static)
        board_text = self._render_board()
        board_widget.update(board_text)

        # Update instructions
        instructions_widget = self.query_one("#instructions", Static)
        if self.game_over:
            instructions_widget.update(f"GAME OVER! Final Score: {self.score}")
        elif self.is_paused:
            instructions_widget.update("PAUSED")
        else:
            instructions_widget.update("")

    def _render_board(self) -> str:
        """Render the game board as text."""
        lines = []

        for y in range(self.board_height):
            line = ""
            for x in range(self.board_width):
                pos = (x, y)

                if pos == self.snake[0]:
                    # Snake head
                    line += "●"
                elif pos in self.snake:
                    # Snake body
                    line += "○"
                elif pos == self.food:
                    # Food
                    line += "◆"
                else:
                    # Empty space
                    line += " "

            lines.append(line)

        return "\n".join(lines)

    def _game_over(self) -> None:
        """Handle game over."""
        self.game_over = True
        self.game_state = GameState.GAME_OVER
        self._update_display()

    def action_toggle_pause(self) -> None:
        """Toggle pause state."""
        if not self.game_over:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.game_state = GameState.PAUSED
            else:
                self.game_state = GameState.PLAYING
            self._update_display()

    def action_quit_game(self) -> None:
        """Quit the game."""
        self.game_state = GameState.QUIT
        self.exit()

    def external_pause(self) -> None:
        """Pause game from external trigger (window switch)."""
        if not self.game_over and not self.is_paused:
            self.is_paused = True
            self.game_state = GameState.PAUSED
            self._update_display()

    def external_resume(self) -> None:
        """Resume game from external trigger (window switch)."""
        if not self.game_over and self.is_paused:
            self.is_paused = False
            self.game_state = GameState.PLAYING
            self._update_display()
