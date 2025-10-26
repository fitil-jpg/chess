"""
Timing Configuration Manager

Centralized configuration for move timing, visualization delays, and thresholds.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TimingConfig:
    """Manages timing configuration for the chess AI system."""

    DEFAULT_CONFIG = {
        "timing": {
            "move_time_ms": 700,
            "min_move_delay_ms": 400,
            "visualization_delay_ms": 50,
            "cell_animation_delay_ms": 50,
            "heatmap_update_delay_ms": 100
        },
        "auto_play": {
            "games_count": 10,
            "game_delay_ms": 2000,
            "move_delay_ms": 1000
        },
        "visualization": {
            "show_intermediate_steps": True,
            "highlight_current_cell": True,
            "animate_transitions": True,
            "show_method_status": True
        },
        "thresholds": {
            "minimax_value_threshold_percent": 10,
            "display_move_threshold": 0.1,
            "guardrails_penalty_factor": 0.5
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize timing configuration."""
        self.config_path = config_path or Path("configs/move_timing.json")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Loaded timing configuration from {self.config_path}")
                return config
            except Exception as exc:
                logger.warning(f"Failed to load config from {self.config_path}: {exc}")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.info("Using default timing configuration")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved timing configuration to {self.config_path}")
        except Exception as exc:
            logger.error(f"Failed to save config to {self.config_path}: {exc}")

    # Timing properties
    @property
    def move_time_ms(self) -> int:
        """Get the main move time in milliseconds."""
        return self.config["timing"]["move_time_ms"]

    @move_time_ms.setter
    def move_time_ms(self, value: int):
        """Set the main move time in milliseconds."""
        self.config["timing"]["move_time_ms"] = max(100, int(value))

    @property
    def min_move_delay_ms(self) -> int:
        """Get minimum delay between moves."""
        return self.config["timing"]["min_move_delay_ms"]

    @min_move_delay_ms.setter
    def min_move_delay_ms(self, value: int):
        """Set minimum delay between moves."""
        self.config["timing"]["min_move_delay_ms"] = max(50, int(value))

    @property
    def visualization_delay_ms(self) -> int:
        """Get visualization update delay."""
        return self.config["timing"]["visualization_delay_ms"]

    @property
    def cell_animation_delay_ms(self) -> int:
        """Get cell animation delay for green cell highlighting."""
        return self.config["timing"]["cell_animation_delay_ms"]

    @property
    def heatmap_update_delay_ms(self) -> int:
        """Get heatmap update delay."""
        return self.config["timing"]["heatmap_update_delay_ms"]

    # Auto-play properties
    @property
    def auto_play_games(self) -> int:
        """Get number of games for auto-play."""
        return self.config["auto_play"]["games_count"]

    @property
    def game_delay_ms(self) -> int:
        """Get delay between auto-play games."""
        return self.config["auto_play"]["game_delay_ms"]

    @property
    def auto_play_move_delay_ms(self) -> int:
        """Get delay between moves in auto-play."""
        return self.config["auto_play"]["move_delay_ms"]

    # Visualization properties
    @property
    def show_intermediate_steps(self) -> bool:
        """Check if intermediate evaluation steps should be shown."""
        return self.config["visualization"]["show_intermediate_steps"]

    @property
    def highlight_current_cell(self) -> bool:
        """Check if current cell should be highlighted."""
        return self.config["visualization"]["highlight_current_cell"]

    @property
    def animate_transitions(self) -> bool:
        """Check if transitions should be animated."""
        return self.config["visualization"]["animate_transitions"]

    @property
    def show_method_status(self) -> bool:
        """Check if method status should be displayed."""
        return self.config["visualization"]["show_method_status"]

    # Threshold properties
    @property
    def minimax_threshold_percent(self) -> float:
        """Get minimax value threshold percentage."""
        return self.config["thresholds"]["minimax_value_threshold_percent"]

    @property
    def display_move_threshold(self) -> float:
        """Get threshold for displaying moves in UI."""
        return self.config["thresholds"]["display_move_threshold"]

    @property
    def guardrails_penalty_factor(self) -> float:
        """Get penalty factor for moves that fail guardrails."""
        return self.config["thresholds"]["guardrails_penalty_factor"]

    def get_all_timings(self) -> Dict[str, Any]:
        """Get all timing values."""
        return self.config["timing"].copy()

    def update_timing(self, **kwargs) -> None:
        """Update timing values."""
        for key, value in kwargs.items():
            if key in self.config["timing"]:
                self.config["timing"][key] = value
        self.save_config()

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save_config()


# Global instance
_global_config: Optional[TimingConfig] = None


def get_timing_config() -> TimingConfig:
    """Get or create the global timing configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = TimingConfig()
    return _global_config


def reload_timing_config() -> TimingConfig:
    """Reload timing configuration from file."""
    global _global_config
    _global_config = TimingConfig()
    return _global_config


__all__ = ["TimingConfig", "get_timing_config", "reload_timing_config"]
