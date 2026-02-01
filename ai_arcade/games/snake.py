"""Classic Snake game implementation."""

import random
from typing import List, Tuple

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Static

from .base_game import BaseGame, GameEvent, GameState
from ..logger import logger


class SnakeGame(BaseGame):
    """Classic Snake game."""

    ID = "snake"
    NAME = "Snake"
    DESCRIPTION = "Classic snake game. Eat food, grow longer, avoid walls and yourself!"
    CATEGORY = "arcade"
    AUTHOR = "AI Arcade Team"
    CONTROLS_HELP = ""
    MIN_TERMINAL_SIZE = (40, 20)

    def __init__(self):
        """Initialize Snake game."""
        super().__init__()
        self.screen = None  # Reference to running SnakeScreen

    @property
    def key_bindings(self) -> Tuple[str, ...]:
        """Key bindings used by Snake (initial display only, updated dynamically during play)."""
        return ("Arrows: Move", "Space: Pause", "Q: Quit")

    def run(self) -> None:
        """Run the Snake game."""
        app = SnakeStandaloneApp(self)
        app.run()

    def create_screen(self) -> "SnakeScreen":
        """Create the game screen for use in the hub app."""
        self.screen = SnakeScreen(self)
        return self.screen

    def pause(self) -> None:
        """Pause the game when switching away from game window."""
        super().pause()
        if self.screen and not self.screen.game_over:
            self.screen.external_pause()

    def resume(self) -> None:
        """Resume the game when switching back to game window."""
        super().resume()
        if self.screen and not self.screen.game_over:
            self.screen.external_resume()


class SnakeScreen(Screen):
    """Textual screen for Snake game."""

    TITLE = "Snake"

    CSS = """
    Screen {
        background: $surface;
    }

    Header {
        dock: top;
    }

    #game-wrapper {
        width: 100%;
        height: 100%;
        align: center middle;
        padding: 1 0;
    }

    #game-card {
        width: 42;
        height: auto;
        background: transparent;
        align: center top;
    }

    #score-display {
        width: 42;
        min-width: 0;
        height: 3;
        content-align: center middle;
        background: $boost;
        color: $text;
        text-style: bold;
        padding: 0 1;
    }

    #game-board-wrap {
        width: 42;
        height: 17;
        border: solid green;
        background: $panel;
        align: center middle;
        padding: 0;
    }

    #game-board {
        width: 40;
        height: 15;
        content-align: left top;
    }

    #instructions {
        width: 42;
        min-width: 0;
        height: 3;
        content-align: center middle;
        background: $panel;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("space", "toggle_pause", "Pause/Resume"),
        ("enter", "restart", "Restart"),
        ("q", "quit_game", "Quit"),
    ]

    def __init__(self, game: SnakeGame):
        """Initialize the screen."""
        super().__init__()
        self.game_ref = game
        self.score = game.score
        self.game_state = GameState.PLAYING

        # Game board settings
        self.board_width = 40
        self.board_height = 15

        # Snake
        self.snake: List[Tuple[int, int]] = [(20, 7), (19, 7), (18, 7)]
        self.direction = (1, 0)  # (dx, dy) - moving right initially
        self.next_direction = (1, 0)

        # Food
        self.food = self._spawn_food()

        # Game state
        self.is_paused = False
        self.game_over = False
        self.game_over_reason = ""

        # External pause/resume requests (thread-safe flags)
        self._pending_pause = False
        self._pending_resume = False

        # Timer for game updates
        self.update_timer = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Container(id="game-wrapper"):
            with Vertical(id="game-card"):
                yield Static(id="score-display")
                with Container(id="game-board-wrap"):
                    yield Static(id="game-board")
                yield Static(id="instructions")

    def on_mount(self) -> None:
        """Called when app starts."""
        logger.info("Snake game started")
        self._update_display()
        self._emit_key_bindings()
        # Start game loop (update every 150ms)
        self.update_timer = self.set_interval(0.15, self._game_tick)
        logger.debug(f"Game loop started with interval 0.15s")

    def _emit_key_bindings(self) -> None:
        """Send current key bindings to the runner."""
        bindings = ["Arrows: Move"]

        if self.game_over:
            bindings.append("Enter: Restart")
        elif self.is_paused:
            bindings.append("Space: Resume")
        else:
            bindings.append("Space: Pause")

        bindings.append("Q: Quit")
        self.game_ref.emit_event(GameEvent.KEY_BINDINGS, tuple(bindings))

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
        # Handle external pause/resume requests (from WindowFocusMonitor thread)
        if self._pending_pause:
            self._pending_pause = False
            if not self.game_over and not self.is_paused:
                logger.info("Game paused (external trigger)")
                self.is_paused = True
                self.game_state = GameState.PAUSED
                self._update_display()
                self._emit_key_bindings()

        if self._pending_resume:
            self._pending_resume = False
            if not self.game_over and self.is_paused:
                logger.info("Game resumed (external trigger)")
                self.is_paused = False
                self.game_state = GameState.PLAYING
                self._update_display()
                self._emit_key_bindings()

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
            logger.warning(f"Wall collision detected: new_head={new_head}, direction={self.direction}, board_size=({self.board_width}, {self.board_height})")
            self._game_over(f"wall collision at {new_head}")
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
            logger.debug(f"Food eaten! Score: {self.score}, snake length: {len(self.snake)}")
        else:
            # Don't grow: remove the tail
            self.snake.pop()

        # Check self collision AFTER moving
        # The new head shouldn't collide with any other part of the snake body
        # snake[0] is the new head, so check snake[1:] for collision
        if len(self.snake) > 1:
            if self.snake[0] in self.snake[1:]:
                logger.warning(f"Self collision detected: head={self.snake[0]}, body={self.snake[1:]}, direction={self.direction}")
                self._game_over(f"self collision at {self.snake[0]}, body: {self.snake[1:]}")
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
        score_widget.update(f"SNAKE | Score: {self.score}")

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
        self._sync_game_ref()

    def _sync_game_ref(self) -> None:
        """Sync game state back to the game instance."""
        self.game_ref.score = self.score
        self.game_ref.update_state(self.game_state)

    def _render_board(self) -> str:
        """Render the game board as text."""
        lines = []

        for y in range(self.board_height):
            line = ""
            for x in range(self.board_width):
                pos = (x, y)

                if pos == self.snake[0]:
                    # Snake head
                    line += "@"
                elif pos in self.snake:
                    # Snake body
                    line += "o"
                elif pos == self.food:
                    # Food
                    line += "*"
                else:
                    # Empty space
                    line += " "

            lines.append(line)

        return "\n".join(lines)

    def _game_over(self, reason: str = "unknown") -> None:
        """Handle game over."""
        logger.error(f"GAME OVER: {reason}, score={self.score}, snake_length={len(self.snake)}")
        self.game_over = True
        self.game_state = GameState.GAME_OVER
        self.game_over_reason = reason  # Store for debugging
        self._update_display()
        self._emit_key_bindings()

    def action_toggle_pause(self) -> None:
        """Toggle pause state."""
        if not self.game_over:
            self.is_paused = not self.is_paused
            if self.is_paused:
                logger.info("Game paused by user (Space key)")
                self.game_state = GameState.PAUSED
            else:
                logger.info("Game resumed by user (Space key)")
                self.game_state = GameState.PLAYING
            self._sync_game_ref()
            self._update_display()
            self._emit_key_bindings()

    def action_restart(self) -> None:
        """Restart the game (only works when game over)."""
        if not self.game_over:
            return  # Only restart when game is over

        logger.info(f"Game restarted by user, previous score: {self.score}")
        # Reset score
        self.score = 0
        self.game_state = GameState.PLAYING

        # Reset snake
        self.snake = [(20, 7), (19, 7), (18, 7)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)

        # Spawn new food
        self.food = self._spawn_food()

        # Reset game state
        self.is_paused = False
        self.game_over = False
        self.game_over_reason = ""

        # Reset pending flags
        self._pending_pause = False
        self._pending_resume = False

        self._sync_game_ref()
        self._update_display()
        self._emit_key_bindings()

    def action_quit_game(self) -> None:
        """Quit the game."""
        logger.info(f"User quit game manually, final score: {self.score}")
        self.game_state = GameState.QUIT
        self._sync_game_ref()
        self.dismiss()

    def external_pause(self) -> None:
        """Pause game from external trigger (window switch)."""
        logger.debug("external_pause() called - setting pause flag")
        # Set flag to be processed in next game tick (thread-safe)
        self._pending_pause = True

    def external_resume(self) -> None:
        """Resume game from external trigger (window switch)."""
        logger.debug("external_resume() called - setting resume flag")
        # Set flag to be processed in next game tick (thread-safe)
        self._pending_resume = True


class SnakeStandaloneApp(App):
    """Standalone app wrapper for the Snake screen."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self, game: SnakeGame):
        """Initialize the standalone app."""
        super().__init__()
        self.game = game

    def compose(self) -> ComposeResult:
        """Compose UI layout."""
        yield from ()

    def on_mount(self) -> None:
        """Mount the game screen."""
        self.push_screen(self.game.create_screen(), self._handle_game_exit)

    def _handle_game_exit(self, _result) -> None:
        """Exit once the game screen dismisses."""
        self.exit()
