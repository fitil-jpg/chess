1"""
Centralized Timing Configuration for Chess AI.

This module provides centralized timing configuration that can be easily
adjusted across all chess AI scripts and components.
"""

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TimingConfig:
    """Configuration for various timing parameters in the chess AI system."""
    
    # Move evaluation timing
    move_time_ms: int = 700
    min_move_time_ms: int = 100
    max_move_time_ms: int = 5000
    
    # Real-time visualization timing
    visualization_delay_ms: int = 50
    cell_highlight_duration_ms: int = 200
    heatmap_update_delay_ms: int = 100
    
    # Bot evaluation timing
    pattern_matching_timeout_ms: int = 100
    wfc_analysis_timeout_ms: int = 150
    bsp_analysis_timeout_ms: int = 150
    guardrails_timeout_ms: int = 50
    bot_evaluation_timeout_ms: int = 200
    
    # Enhanced WFC/BSP processing delays (0.05ms increments for human visualization)
    wfc_processing_delay_ms: int = 50
    bsp_processing_delay_ms: int = 50
    green_cell_pulse_delay_ms: int = 50
    tactical_pattern_delay_ms: int = 30
    step_visualization_delay_ms: int = 50  # For real-time step-by-step visualization
    engine_switch_delay_ms: int = 50      # Delay when switching between WFC/BSP
    bot_evaluation_delay_ms: int = 50     # Delay for bot evaluation visualization
    
    # Thresholds for visualization
    minimax_value_threshold_percent: int = 10
    wfc_confidence_threshold: float = 0.3
    bsp_zone_threshold: float = 0.2
    tactical_pattern_threshold: float = 0.6
    
    # Engine settings
    wfc_enabled: bool = True
    bsp_enabled: bool = True
    log_bot_usage: bool = True
    bot_usage_format: str = "{BOT_NAME} > {ENGINE}"
    wfc_max_iterations: int = 100
    bsp_max_depth: int = 4
    
    # Auto-play timing
    auto_play_interval_ms: int = 1000
    game_over_pause_ms: int = 2000
    between_games_pause_ms: int = 1000
    
    # UI update timing
    status_update_interval_ms: int = 100
    heatmap_refresh_interval_ms: int = 500
    usage_chart_update_interval_ms: int = 200
    
    # Visualization settings
    show_intermediate_steps: bool = True
    highlight_current_cell: bool = True
    animate_transitions: bool = True
    show_method_status: bool = True
    
    # Debug and logging timing
    debug_output_delay_ms: int = 10
    log_flush_interval_ms: int = 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimingConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate timing configuration."""
        if self.move_time_ms < self.min_move_time_ms:
            logger.warning(f"move_time_ms ({self.move_time_ms}) is below minimum ({self.min_move_time_ms})")
            return False
        
        if self.move_time_ms > self.max_move_time_ms:
            logger.warning(f"move_time_ms ({self.move_time_ms}) is above maximum ({self.max_move_time_ms})")
            return False
        
        if self.visualization_delay_ms < 10:
            logger.warning(f"visualization_delay_ms ({self.visualization_delay_ms}) is too low")
            return False
        
        return True
    
    def adjust_for_performance(self, performance_factor: float = 1.0) -> None:
        """Adjust timing based on system performance."""
        if performance_factor < 0.5:
            # Slow system - increase timeouts
            self.move_time_ms = int(self.move_time_ms * 1.5)
            self.visualization_delay_ms = int(self.visualization_delay_ms * 2)
            self.pattern_matching_timeout_ms = int(self.pattern_matching_timeout_ms * 1.5)
            self.wfc_analysis_timeout_ms = int(self.wfc_analysis_timeout_ms * 1.5)
            self.bsp_analysis_timeout_ms = int(self.bsp_analysis_timeout_ms * 1.5)
        elif performance_factor > 2.0:
            # Fast system - decrease timeouts
            self.move_time_ms = max(self.min_move_time_ms, int(self.move_time_ms * 0.7))
            self.visualization_delay_ms = max(10, int(self.visualization_delay_ms * 0.5))
            self.pattern_matching_timeout_ms = max(50, int(self.pattern_matching_timeout_ms * 0.7))
            self.wfc_analysis_timeout_ms = max(75, int(self.wfc_analysis_timeout_ms * 0.7))
            self.bsp_analysis_timeout_ms = max(75, int(self.bsp_analysis_timeout_ms * 0.7))


class TimingManager:
    """Manages timing configuration across the chess AI system."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "timing_config.json"
        self.config = TimingConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load timing configuration from file."""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with config_path.open('r') as f:
                    data = json.load(f)
                self.config = TimingConfig.from_dict(data)
                logger.info(f"Loaded timing configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load timing configuration: {e}")
                logger.info("Using default timing configuration")
        else:
            logger.info(f"No timing configuration file found at {self.config_file}, using defaults")
            self.save_config()  # Save default config
    
    def save_config(self) -> None:
        """Save timing configuration to file."""
        try:
            config_path = Path(self.config_file)
            with config_path.open('w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            logger.info(f"Saved timing configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save timing configuration: {e}")
    
    def get_move_time_ms(self) -> int:
        """Get the current move time in milliseconds."""
        return self.config.move_time_ms
    
    def set_move_time_ms(self, time_ms: int) -> None:
        """Set the move time in milliseconds."""
        self.config.move_time_ms = max(
            self.config.min_move_time_ms,
            min(time_ms, self.config.max_move_time_ms)
        )
        self.save_config()
        logger.info(f"Move time set to {self.config.move_time_ms}ms")
    
    def get_visualization_delay_ms(self) -> int:
        """Get the visualization delay in milliseconds."""
        return self.config.visualization_delay_ms
    
    def set_visualization_delay_ms(self, delay_ms: int) -> None:
        """Set the visualization delay in milliseconds."""
        self.config.visualization_delay_ms = max(10, delay_ms)
        self.save_config()
        logger.info(f"Visualization delay set to {self.config.visualization_delay_ms}ms")
    
    def get_auto_play_interval_ms(self) -> int:
        """Get the auto-play interval in milliseconds."""
        return self.config.auto_play_interval_ms
    
    def set_auto_play_interval_ms(self, interval_ms: int) -> None:
        """Set the auto-play interval in milliseconds."""
        self.config.auto_play_interval_ms = max(100, interval_ms)
        self.save_config()
        logger.info(f"Auto-play interval set to {self.config.auto_play_interval_ms}ms")
    
    def get_timeout_for_method(self, method_name: str) -> int:
        """Get timeout for a specific evaluation method."""
        timeout_map = {
            'pattern_matching': self.config.pattern_matching_timeout_ms,
            'wfc_analysis': self.config.wfc_analysis_timeout_ms,
            'bsp_analysis': self.config.bsp_analysis_timeout_ms,
            'guardrails_check': self.config.guardrails_timeout_ms,
            'bot_evaluation': self.config.bot_evaluation_timeout_ms,
        }
        return timeout_map.get(method_name, 200)  # Default 200ms
    
    def adjust_for_system_performance(self) -> None:
        """Automatically adjust timing based on system performance."""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Calculate performance factor based on system load
            performance_factor = 2.0 - (cpu_percent + memory_percent) / 100.0
            performance_factor = max(0.3, min(3.0, performance_factor))
            
            self.config.adjust_for_performance(performance_factor)
            self.save_config()
            
            logger.info(f"Adjusted timing for system performance (factor: {performance_factor:.2f})")
            
        except ImportError:
            logger.warning("psutil not available, cannot adjust timing for system performance")
        except Exception as e:
            logger.error(f"Failed to adjust timing for system performance: {e}")
    
    def create_timing_profile(self, profile_name: str) -> None:
        """Create a named timing profile."""
        profile_file = f"timing_profile_{profile_name}.json"
        try:
            with open(profile_file, 'w') as f:
                json.dump(self.config.to_dict(), f, indent=2)
            logger.info(f"Created timing profile '{profile_name}' in {profile_file}")
        except Exception as e:
            logger.error(f"Failed to create timing profile: {e}")
    
    def load_timing_profile(self, profile_name: str) -> bool:
        """Load a named timing profile."""
        profile_file = f"timing_profile_{profile_name}.json"
        profile_path = Path(profile_file)
        
        if profile_path.exists():
            try:
                with profile_path.open('r') as f:
                    data = json.load(f)
                self.config = TimingConfig.from_dict(data)
                self.save_config()  # Save as current config
                logger.info(f"Loaded timing profile '{profile_name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to load timing profile '{profile_name}': {e}")
        else:
            logger.warning(f"Timing profile '{profile_name}' not found")
        
        return False
    
    def get_predefined_profiles(self) -> Dict[str, TimingConfig]:
        """Get predefined timing profiles."""
        profiles = {
            'fast': TimingConfig(
                move_time_ms=300,
                visualization_delay_ms=25,
                pattern_matching_timeout_ms=50,
                wfc_analysis_timeout_ms=75,
                bsp_analysis_timeout_ms=75,
                auto_play_interval_ms=500
            ),
            'normal': TimingConfig(),  # Default values
            'slow': TimingConfig(
                move_time_ms=1500,
                visualization_delay_ms=100,
                pattern_matching_timeout_ms=200,
                wfc_analysis_timeout_ms=300,
                bsp_analysis_timeout_ms=300,
                auto_play_interval_ms=2000
            ),
            'debug': TimingConfig(
                move_time_ms=2000,
                visualization_delay_ms=200,
                pattern_matching_timeout_ms=500,
                wfc_analysis_timeout_ms=500,
                bsp_analysis_timeout_ms=500,
                auto_play_interval_ms=3000,
                debug_output_delay_ms=50
            )
        }
        return profiles
    
    def apply_predefined_profile(self, profile_name: str) -> bool:
        """Apply a predefined timing profile."""
        profiles = self.get_predefined_profiles()
        if profile_name in profiles:
            self.config = profiles[profile_name]
            self.save_config()
            logger.info(f"Applied predefined timing profile '{profile_name}'")
            return True
        else:
            logger.warning(f"Unknown predefined profile '{profile_name}'")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current timing configuration."""
        return {
            'move_time_ms': self.config.move_time_ms,
            'visualization_delay_ms': self.config.visualization_delay_ms,
            'auto_play_interval_ms': self.config.auto_play_interval_ms,
            'total_evaluation_timeout_ms': (
                self.config.pattern_matching_timeout_ms +
                self.config.wfc_analysis_timeout_ms +
                self.config.bsp_analysis_timeout_ms +
                self.config.guardrails_timeout_ms +
                self.config.bot_evaluation_timeout_ms
            ),
            'config_file': self.config_file,
            'is_valid': self.config.validate()
        }


# Global timing manager instance
timing_manager = TimingManager()


def get_move_time_ms() -> int:
    """Get the current move time in milliseconds."""
    return timing_manager.get_move_time_ms()


def set_move_time_ms(time_ms: int) -> None:
    """Set the move time in milliseconds."""
    timing_manager.set_move_time_ms(time_ms)


def get_visualization_delay_ms() -> int:
    """Get the visualization delay in milliseconds."""
    return timing_manager.get_visualization_delay_ms()


def set_visualization_delay_ms(delay_ms: int) -> None:
    """Set the visualization delay in milliseconds."""
    timing_manager.set_visualization_delay_ms(delay_ms)


def get_timeout_for_method(method_name: str) -> int:
    """Get timeout for a specific evaluation method."""
    return timing_manager.get_timeout_for_method(method_name)


# Environment variable overrides
if os.getenv('CHESS_MOVE_TIME_MS'):
    try:
        move_time = int(os.getenv('CHESS_MOVE_TIME_MS'))
        timing_manager.set_move_time_ms(move_time)
        logger.info(f"Move time set from environment variable: {move_time}ms")
    except ValueError:
        logger.warning("Invalid CHESS_MOVE_TIME_MS environment variable")

if os.getenv('CHESS_VISUALIZATION_DELAY_MS'):
    try:
        delay = int(os.getenv('CHESS_VISUALIZATION_DELAY_MS'))
        timing_manager.set_visualization_delay_ms(delay)
        logger.info(f"Visualization delay set from environment variable: {delay}ms")
    except ValueError:
        logger.warning("Invalid CHESS_VISUALIZATION_DELAY_MS environment variable")

if os.getenv('CHESS_TIMING_PROFILE'):
    profile_name = os.getenv('CHESS_TIMING_PROFILE')
    if timing_manager.apply_predefined_profile(profile_name):
        logger.info(f"Applied timing profile from environment variable: {profile_name}")
    else:
        logger.warning(f"Unknown timing profile in environment variable: {profile_name}")