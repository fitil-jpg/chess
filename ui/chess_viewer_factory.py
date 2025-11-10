"""
Factory module for creating ChessViewer instances with configuration support.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication


class ChessViewerFactory:
    """Factory for creating ChessViewer instances with configuration."""
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "window_config.json"
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if config_path is None:
            config_path = cls.DEFAULT_CONFIG_PATH
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}, using defaults")
            return cls._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config file: {e}, using defaults")
            return cls._get_default_config()
    
    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration if file loading fails."""
        return {
            "window": {
                "title": "Chess Viewer — ThreatMap & Metrics",
                "min_size": [800, 600],
                "default_size": [1200, 800],
                "resizable": True,
                "restore_geometry": True
            },
            "layout": {
                "board_size": 560,
                "console_height": 140,
                "console_min_height": 90,
                "tab_position": "north",
                "subtab_position": "south",
                "enable_scroll": True,
                "spacing": {
                    "main": 10,
                    "controls": 2,
                    "board": 0
                }
            },
            "features": {
                "auto_save_geometry": True,
                "compact_mode": True,
                "debug_mode": False,
                "elo_refresh": True,
                "theme": "default"
            }
        }
    
    @classmethod
    def create_viewer(cls, config_path: Optional[str] = None, **kwargs):
        """Create a ChessViewer instance with configuration."""
        from pyside_viewer import ChessViewer
        
        config = cls.load_config(config_path)
        
        # Override config with provided kwargs
        for key, value in kwargs.items():
            if '.' in key:
                # Support nested keys like "window.title"
                keys = key.split('.')
                current = config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                config[key] = value
        
        # Create viewer with config
        viewer = ChessViewer()
        viewer.apply_config(config)
        return viewer
    
    @classmethod
    def create_minimal_viewer(cls):
        """Create a minimal ChessViewer for testing."""
        return cls.create_viewer(
            window_title="Chess Viewer - Minimal",
            window_min_size=[600, 400],
            layout_board_size=400,
            features_debug_mode=True
        )
    
    @classmethod
    def create_full_viewer(cls):
        """Create a full-featured ChessViewer."""
        return cls.create_viewer()  # Uses default full config


class ConfigurableViewerMixin:
    """Mixin class to add configuration support to ChessViewer."""
    
    def apply_config(self, config: Dict[str, Any]):
        """Apply configuration to the viewer."""
        self.config = config
        self._setup_window_from_config()
        self._setup_layout_from_config()
        self._setup_features_from_config()
    
    def _setup_window_from_config(self):
        """Setup window properties from config."""
        window_config = self.config.get("window", {})
        
        if "title" in window_config:
            self.setWindowTitle(window_config["title"])
        
        if "min_size" in window_config:
            min_w, min_h = window_config["min_size"]
            self.setMinimumSize(min_w, min_h)
        
        if "default_size" in window_config:
            default_w, default_h = window_config["default_size"]
            self.resize(default_w, default_h)
        
        if window_config.get("restore_geometry", True):
            self.settings = QSettings("ChessViewer", "Preferences")
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
    
    def _setup_layout_from_config(self):
        """Setup layout properties from config."""
        layout_config = self.config.get("layout", {})
        
        # Store layout config for later use in setup
        self.layout_config = layout_config
    
    def _setup_features_from_config(self):
        """Setup feature flags from config."""
        features_config = self.config.get("features", {})
        
        self.debug_mode = features_config.get("debug_mode", False)
        self.compact_mode_enabled = features_config.get("compact_mode", True)
        self.elo_refresh_enabled = features_config.get("elo_refresh", True)
    
    def save_geometry(self):
        """Save window geometry if enabled."""
        if self.config.get("features", {}).get("auto_save_geometry", True):
            if hasattr(self, 'settings'):
                self.settings.setValue("geometry", self.saveGeometry())
