"""Game library management for Agent Arcade."""

import importlib
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .config import get_data_dir
from .games.base_game import BaseGame, GameMetadata


class GameLibrary:
    """Manages game discovery and metadata."""

    def __init__(self, metadata_path: Optional[Path] = None):
        """
        Initialize game library.

        Args:
            metadata_path: Path to metadata JSON. Defaults to ~/.agent-arcade/games_metadata.json (or ~/.agent-arcade-dev in dev mode)
        """
        if metadata_path is None:
            metadata_path = Path.home() / get_data_dir() / "games_metadata.json"

        self.metadata_path = Path(metadata_path).expanduser()
        self.metadata: Dict[str, Any] = self._load_metadata()
        self.available_games: Dict[str, Type[BaseGame]] = self._discover_games()

    def _load_metadata(self) -> Dict[str, Any]:
        """
        Load metadata from JSON file.

        Returns:
            Metadata dictionary
        """
        if not self.metadata_path.exists():
            return {"games": {}}

        try:
            with open(self.metadata_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load metadata: {e}")
            return {"games": {}}

    def _save_metadata(self) -> None:
        """Persist metadata to disk."""
        # Ensure directory exists
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save metadata: {e}")

    def _discover_games(self) -> Dict[str, Type[BaseGame]]:
        """
        Discover all game classes in agent_arcade.games package.

        Returns:
            Dictionary mapping game_id -> game_class
        """
        games: Dict[str, Type[BaseGame]] = {}

        try:
            # Import games package
            from . import games as games_pkg

            # Get the games package directory
            games_dir = Path(games_pkg.__file__).parent

            # Find all Python files in games directory (except __init__ and base_game)
            for py_file in games_dir.glob("*.py"):
                if py_file.stem in ("__init__", "base_game"):
                    continue

                try:
                    # Import the module
                    module_name = f"agent_arcade.games.{py_file.stem}"
                    module = importlib.import_module(module_name)

                    # Find all classes that inherit from BaseGame
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseGame) and obj is not BaseGame:
                            # Instantiate to get metadata
                            try:
                                instance = obj()
                                game_id = instance.metadata.id
                                games[game_id] = obj

                                # Initialize metadata if not exists
                                if game_id not in self.metadata["games"]:
                                    self._initialize_game_metadata(game_id, instance.metadata)
                            except Exception as e:
                                print(f"Warning: Could not instantiate {name}: {e}")

                except Exception as e:
                    print(f"Warning: Could not import {py_file.stem}: {e}")

        except Exception as e:
            print(f"Warning: Could not discover games: {e}")

        return games

    def _initialize_game_metadata(self, game_id: str, metadata: GameMetadata) -> None:
        """
        Initialize metadata for a new game.

        Args:
            game_id: Game identifier
            metadata: Game metadata
        """
        self.metadata["games"][game_id] = {
            "last_played": None,
            "play_count": 0,
            "total_play_time_seconds": 0,
            "high_score": 0,
        }
        self._save_metadata()

    def list_games(self, sort_by: str = "name") -> List[GameMetadata]:
        """
        List all available games.

        In production, only published games are returned.
        In dev mode, all games are returned.

        Args:
            sort_by: Sort criteria ("name", "last_played", "play_count", "category")

        Returns:
            List of GameMetadata objects
        """
        games = []
        is_dev = get_data_dir() == ".agent-arcade-dev"

        for game_id, game_class in self.available_games.items():
            try:
                instance = game_class()
                metadata = instance.metadata

                # In production, skip unpublished games
                if not is_dev and not metadata.published:
                    continue

                games.append(metadata)
            except Exception as e:
                print(f"Warning: Could not get metadata for {game_id}: {e}")

        # Sort games
        if sort_by == "last_played":
            games.sort(key=lambda g: self._get_last_played(g.id), reverse=True)
        elif sort_by == "play_count":
            games.sort(key=lambda g: self._get_play_count(g.id), reverse=True)
        elif sort_by == "category":
            games.sort(key=lambda g: (g.category, g.name))
        else:  # name
            games.sort(key=lambda g: g.name)

        return games

    def get_game(self, game_id: str) -> Optional[BaseGame]:
        """
        Instantiate and return game by ID.

        Args:
            game_id: Game identifier

        Returns:
            Game instance if found, None otherwise
        """
        game_class = self.available_games.get(game_id)
        if game_class:
            try:
                return game_class()
            except Exception as e:
                print(f"Error: Could not instantiate game {game_id}: {e}")
                return None
        return None

    def update_play_stats(
        self,
        game_id: str,
        play_time_seconds: int,
        score: Optional[int] = None
    ) -> None:
        """
        Update game metadata after a play session.

        Args:
            game_id: Game identifier
            play_time_seconds: Duration of play session
            score: Final score (if applicable)
        """
        if game_id not in self.metadata["games"]:
            # Game metadata doesn't exist, skip
            self._initialize_game_metadata(game_id, GameMetadata(
                id=game_id,
                name="",
                description="",
                category="",
                author="",
                controls_help="",
                min_terminal_size=(0, 0),
            ))

        meta = self.metadata["games"][game_id]
        meta["last_played"] = datetime.utcnow().isoformat() + "Z"
        meta["play_count"] = meta.get("play_count", 0) + 1
        meta["total_play_time_seconds"] = meta.get("total_play_time_seconds", 0) + play_time_seconds

        # Update high score if applicable
        if score is not None and score > meta.get("high_score", 0):
            meta["high_score"] = score

        self._save_metadata()

    def _get_last_played(self, game_id: str) -> datetime:
        """
        Get last played timestamp for sorting.

        Args:
            game_id: Game identifier

        Returns:
            Datetime of last play, or datetime.min if never played
        """
        meta = self.metadata["games"].get(game_id, {})
        last_played = meta.get("last_played")
        if last_played:
            try:
                return datetime.fromisoformat(last_played.replace('Z', '+00:00'))
            except:
                pass
        # Return timezone-aware datetime.min to match timezone-aware parsed dates
        return datetime.min.replace(tzinfo=timezone.utc)

    def _get_play_count(self, game_id: str) -> int:
        """
        Get play count for sorting.

        Args:
            game_id: Game identifier

        Returns:
            Number of times game has been played
        """
        return self.metadata["games"].get(game_id, {}).get("play_count", 0)

    def get_game_stats(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a game.

        Args:
            game_id: Game identifier

        Returns:
            Statistics dictionary if game exists
        """
        return self.metadata["games"].get(game_id)
