"""Base game interface for AI Arcade games."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


class GameState(Enum):
    """Possible states for a game."""

    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    QUIT = "quit"


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

    def __init__(self):
        """Initialize the game."""
        self.state = GameState.MENU
        self.score: int = 0
        self._save_data: Dict[str, Any] = {}

    @property
    @abstractmethod
    def metadata(self) -> GameMetadata:
        """
        Return game metadata.

        Returns:
            GameMetadata instance describing this game
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """
        Run the game.

        This is the main game loop. It should block until the game exits.
        The game should handle its own rendering and input using Textual.
        """
        pass

    @abstractmethod
    def get_save_state(self) -> Dict[str, Any]:
        """
        Get current game state for persistence.

        Returns:
            Dictionary containing all state needed to resume the game.
            Must be JSON-serializable.
        """
        pass

    @abstractmethod
    def load_save_state(self, state: Dict[str, Any]) -> None:
        """
        Restore game from saved state.

        Args:
            state: Dictionary containing saved game state
        """
        pass

    @property
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
            self.state = GameState.PAUSED

    def resume(self) -> None:
        """
        Resume from paused state.

        Default implementation just changes state.
        Games can override for custom resume behavior.
        """
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    def quit(self) -> None:
        """Signal game to quit."""
        self.state = GameState.QUIT
