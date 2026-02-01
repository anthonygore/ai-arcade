"""Base game interface for AI Arcade games."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Tuple

from textual.screen import Screen


class GameState(Enum):
    """Possible states for a game."""

    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    QUIT = "quit"


class GameEvent(Enum):
    """Events emitted by games for the runner to handle."""

    KEY_BINDINGS = "key_bindings"
    STATE = "state"


@dataclass
class GameMetadata:
    """Metadata describing a game."""

    id: str
    name: str
    description: str
    category: str  # "arcade", "puzzle", "strategy", etc.
    author: str
    controls_help: str
    min_terminal_size: Tuple[int, int]  # (cols, rows)


class BaseGame(ABC):
    """Abstract base class for all games."""

    ID: str | None = None
    NAME: str | None = None
    DESCRIPTION: str | None = None
    CATEGORY: str | None = None
    AUTHOR: str | None = None
    CONTROLS_HELP: str | None = None
    MIN_TERMINAL_SIZE: Tuple[int, int] | None = None

    def __init__(self):
        """Initialize the game."""
        self.state = GameState.MENU
        self.score: int = 0
        self._event_callback: Optional[Callable[[GameEvent, Any], None]] = None

    @property
    def metadata(self) -> GameMetadata:
        """
        Return game metadata.

        Returns:
            GameMetadata instance describing this game
        """
        required = {
            "ID": self.ID,
            "NAME": self.NAME,
            "DESCRIPTION": self.DESCRIPTION,
            "CATEGORY": self.CATEGORY,
            "AUTHOR": self.AUTHOR,
            "CONTROLS_HELP": self.CONTROLS_HELP,
            "MIN_TERMINAL_SIZE": self.MIN_TERMINAL_SIZE,
        }
        missing = [key for key, value in required.items() if value is None]
        if missing:
            raise ValueError(f"Missing metadata fields: {', '.join(missing)}")
        return GameMetadata(
            id=self.ID,
            name=self.NAME,
            description=self.DESCRIPTION,
            category=self.CATEGORY,
            author=self.AUTHOR,
            controls_help=self.CONTROLS_HELP,
            min_terminal_size=self.MIN_TERMINAL_SIZE,
        )

    @abstractmethod
    def run(self) -> None:
        """
        Run the game.

        This is the main game loop. It should block until the game exits.
        The game should handle its own rendering and input using Textual.
        """
        pass

    @abstractmethod
    def create_screen(self) -> Screen:
        """
        Return a Textual Screen for rendering the game in the hub app.

        Returns:
            Screen instance for this game.
        """
        pass

    @abstractmethod
    def key_bindings(self) -> Tuple[str, ...]:
        """
        Key bindings used by the game for display in the tmux key bar.

        Returns:
            Tuple of short key binding descriptions.
        """
        return ()

    def pause(self) -> None:
        """
        Pause the game.

        Default implementation just changes state.
        Games can override for custom pause behavior.
        """
        if self.state == GameState.PLAYING:
            self.update_state(GameState.PAUSED)

    def resume(self) -> None:
        """
        Resume from paused state.

        Default implementation just changes state.
        Games can override for custom resume behavior.
        """
        if self.state == GameState.PAUSED:
            self.update_state(GameState.PLAYING)

    def quit(self) -> None:
        """Signal game to quit."""
        self.update_state(GameState.QUIT)

    def set_event_callback(self, callback: Callable[[GameEvent, Any], None]) -> None:
        """Register a callback for game events."""
        self._event_callback = callback

    def emit_event(self, event: GameEvent, payload: Any = None) -> None:
        """Emit a game event to the runner."""
        if self._event_callback:
            self._event_callback(event, payload)

    def update_state(self, state: GameState) -> None:
        """Update state and notify the runner when it changes."""
        if self.state != state:
            self.state = state
            self.emit_event(GameEvent.STATE, state)
