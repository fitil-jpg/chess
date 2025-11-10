"""
Enhanced Chess Viewer Factory with beautiful fluent interface.
Provides a clean, intuitive API for creating configured chess viewers.
"""

import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QSettings


class TabPosition(Enum):
    """Tab position options."""
    NORTH = "north"
    SOUTH = "south"
    WEST = "west"
    EAST = "east"


class Theme(Enum):
    """Available themes."""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    COMPACT = "compact"


class ViewerPreset(Enum):
    """Predefined viewer configurations."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ANALYSIS = "analysis"
    PRESENTATION = "presentation"


@dataclass
class WindowConfig:
    """Window configuration data."""
    title: str = "Chess Viewer — ThreatMap & Metrics"
    min_width: int = 800
    min_height: int = 600
    default_width: int = 1200
    default_height: int = 800
    resizable: bool = True
    restore_geometry: bool = True
    center_on_screen: bool = True


@dataclass
class LayoutConfig:
    """Layout configuration data."""
    board_size: int = 560
    console_height: int = 140
    console_min_height: int = 90
    tab_position: TabPosition = TabPosition.NORTH
    subtab_position: TabPosition = TabPosition.SOUTH
    enable_scroll: bool = True
    main_spacing: int = 10
    controls_spacing: int = 2
    board_spacing: int = 0


@dataclass
class FeaturesConfig:
    """Features configuration data."""
    auto_save_geometry: bool = True
    compact_mode: bool = True
    debug_mode: bool = False
    elo_refresh: bool = True
    theme: Theme = Theme.DEFAULT
    show_console: bool = True
    show_status_bar: bool = True
    enable_tooltips: bool = True


@dataclass
class ViewerConfig:
    """Complete viewer configuration."""
    window: WindowConfig = field(default_factory=WindowConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    features: FeaturesConfig = field(default_factory=FeaturesConfig)


class ChessViewerBuilder:
    """
    Fluent builder for creating ChessViewer instances with beautiful interface.
    
    Usage:
        viewer = (ChessViewerBuilder()
                 .window(title="My Chess Viewer")
                 .layout(board_size=600, tab_position=TabPosition.WEST)
                 .features(debug_mode=True, theme=Theme.DARK)
                 .build())
    """
    
    def __init__(self):
        self.config = ViewerConfig()
    
    def window(self, 
               title: Optional[str] = None,
               min_size: Optional[tuple] = None,
               default_size: Optional[tuple] = None,
               resizable: Optional[bool] = None,
               restore_geometry: Optional[bool] = None,
               center_on_screen: Optional[bool] = None) -> 'ChessViewerBuilder':
        """Configure window settings."""
        if title is not None:
            self.config.window.title = title
        if min_size is not None:
            self.config.window.min_width, self.config.window.min_height = min_size
        if default_size is not None:
            self.config.window.default_width, self.config.window.default_height = default_size
        if resizable is not None:
            self.config.window.resizable = resizable
        if restore_geometry is not None:
            self.config.window.restore_geometry = restore_geometry
        if center_on_screen is not None:
            self.config.window.center_on_screen = center_on_screen
        return self
    
    def layout(self,
               board_size: Optional[int] = None,
               console_height: Optional[int] = None,
               console_min_height: Optional[int] = None,
               tab_position: Optional[TabPosition] = None,
               subtab_position: Optional[TabPosition] = None,
               enable_scroll: Optional[bool] = None,
               spacing: Optional[Dict[str, int]] = None) -> 'ChessViewerBuilder':
        """Configure layout settings."""
        if board_size is not None:
            self.config.layout.board_size = board_size
        if console_height is not None:
            self.config.layout.console_height = console_height
        if console_min_height is not None:
            self.config.layout.console_min_height = console_min_height
        if tab_position is not None:
            self.config.layout.tab_position = tab_position
        if subtab_position is not None:
            self.config.layout.subtab_position = subtab_position
        if enable_scroll is not None:
            self.config.layout.enable_scroll = enable_scroll
        if spacing is not None:
            self.config.layout.main_spacing = spacing.get('main', self.config.layout.main_spacing)
            self.config.layout.controls_spacing = spacing.get('controls', self.config.layout.controls_spacing)
            self.config.layout.board_spacing = spacing.get('board', self.config.layout.board_spacing)
        return self
    
    def features(self,
                 auto_save_geometry: Optional[bool] = None,
                 compact_mode: Optional[bool] = None,
                 debug_mode: Optional[bool] = None,
                 elo_refresh: Optional[bool] = None,
                 theme: Optional[Theme] = None,
                 show_console: Optional[bool] = None,
                 show_status_bar: Optional[bool] = None,
                 enable_tooltips: Optional[bool] = None) -> 'ChessViewerBuilder':
        """Configure feature settings."""
        if auto_save_geometry is not None:
            self.config.features.auto_save_geometry = auto_save_geometry
        if compact_mode is not None:
            self.config.features.compact_mode = compact_mode
        if debug_mode is not None:
            self.config.features.debug_mode = debug_mode
        if elo_refresh is not None:
            self.config.features.elo_refresh = elo_refresh
        if theme is not None:
            self.config.features.theme = theme
        if show_console is not None:
            self.config.features.show_console = show_console
        if show_status_bar is not None:
            self.config.features.show_status_bar = show_status_bar
        if enable_tooltips is not None:
            self.config.features.enable_tooltips = enable_tooltips
        return self
    
    def preset(self, preset: ViewerPreset) -> 'ChessViewerBuilder':
        """Apply a predefined preset configuration."""
        if preset == ViewerPreset.MINIMAL:
            self._apply_minimal_preset()
        elif preset == ViewerPreset.STANDARD:
            self._apply_standard_preset()
        elif preset == ViewerPreset.PROFESSIONAL:
            self._apply_professional_preset()
        elif preset == ViewerPreset.ANALYSIS:
            self._apply_analysis_preset()
        elif preset == ViewerPreset.PRESENTATION:
            self._apply_presentation_preset()
        return self
    
    def _apply_minimal_preset(self):
        """Apply minimal configuration."""
        self.window(
            title="Chess Viewer - Minimal",
            min_size=(600, 400),
            default_size=(800, 500)
        ).layout(
            board_size=400,
            console_height=100,
            enable_scroll=False
        ).features(
            debug_mode=True,
            compact_mode=True,
            show_console=True,
            show_status_bar=False
        )
    
    def _apply_standard_preset(self):
        """Apply standard configuration."""
        # Uses defaults, just ensures standard setup
        pass
    
    def _apply_professional_preset(self):
        """Apply professional configuration."""
        self.window(
            title="Chess Viewer - Professional Edition",
            min_size=(1000, 700),
            default_size=(1400, 900)
        ).layout(
            board_size=640,
            console_height=160
        ).features(
            debug_mode=False,
            compact_mode=False,
            theme=Theme.DARK,
            enable_tooltips=True
        )
    
    def _apply_analysis_preset(self):
        """Apply analysis-focused configuration."""
        self.window(
            title="Chess Viewer - Analysis Mode",
            default_size=(1600, 1000)
        ).layout(
            board_size=700,
            tab_position=TabPosition.WEST,
            console_height=180
        ).features(
            debug_mode=True,
            elo_refresh=True,
            enable_tooltips=True
        )
    
    def _apply_presentation_preset(self):
        """Apply presentation configuration."""
        self.window(
            title="Chess Viewer - Presentation Mode",
            default_size=(1920, 1080)
        ).layout(
            board_size=800,
            tab_position=TabPosition.SOUTH,
            console_height=200
        ).features(
            theme=Theme.LIGHT,
            compact_mode=False,
            debug_mode=False,
            show_status_bar=True
        )
    
    def from_config_file(self, config_path: str) -> 'ChessViewerBuilder':
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Apply window config
            if 'window' in data:
                w = data['window']
                self.window(
                    title=w.get('title'),
                    min_size=tuple(w.get('min_size', [800, 600])),
                    default_size=tuple(w.get('default_size', [1200, 800])),
                    resizable=w.get('resizable'),
                    restore_geometry=w.get('restore_geometry')
                )
            
            # Apply layout config
            if 'layout' in data:
                l = data['layout']
                self.layout(
                    board_size=l.get('board_size'),
                    console_height=l.get('console_height'),
                    console_min_height=l.get('console_min_height'),
                    tab_position=TabPosition(l.get('tab_position', 'north')),
                    subtab_position=TabPosition(l.get('subtab_position', 'south')),
                    enable_scroll=l.get('enable_scroll'),
                    spacing=l.get('spacing', {})
                )
            
            # Apply features config
            if 'features' in data:
                f = data['features']
                self.features(
                    auto_save_geometry=f.get('auto_save_geometry'),
                    compact_mode=f.get('compact_mode'),
                    debug_mode=f.get('debug_mode'),
                    elo_refresh=f.get('elo_refresh'),
                    theme=Theme(f.get('theme', 'default')),
                    show_console=f.get('show_console', True),
                    show_status_bar=f.get('show_status_bar', True),
                    enable_tooltips=f.get('enable_tooltips', True)
                )
                
        except FileNotFoundError:
            print(f"Config file not found: {config_path}, using current configuration")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config file: {e}, using current configuration")
        
        return self
    
    def build(self):
        """Build the ChessViewer instance with current configuration."""
        from pyside_viewer import ChessViewer
        
        # Convert config to dict format
        config_dict = self._config_to_dict()
        
        # Create viewer
        viewer = ChessViewer()
        viewer.apply_config(config_dict)
        
        # Apply additional builder-specific features
        if self.config.window.center_on_screen:
            viewer._center_on_screen()
        
        return viewer
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """Convert dataclass config to dictionary format."""
        return {
            "window": {
                "title": self.config.window.title,
                "min_size": [self.config.window.min_width, self.config.window.min_height],
                "default_size": [self.config.window.default_width, self.config.window.default_height],
                "resizable": self.config.window.resizable,
                "restore_geometry": self.config.window.restore_geometry
            },
            "layout": {
                "board_size": self.config.layout.board_size,
                "console_height": self.config.layout.console_height,
                "console_min_height": self.config.layout.console_min_height,
                "tab_position": self.config.layout.tab_position.value,
                "subtab_position": self.config.layout.subtab_position.value,
                "enable_scroll": self.config.layout.enable_scroll,
                "spacing": {
                    "main": self.config.layout.main_spacing,
                    "controls": self.config.layout.controls_spacing,
                    "board": self.config.layout.board_spacing
                }
            },
            "features": {
                "auto_save_geometry": self.config.features.auto_save_geometry,
                "compact_mode": self.config.features.compact_mode,
                "debug_mode": self.config.features.debug_mode,
                "elo_refresh": self.config.features.elo_refresh,
                "theme": self.config.features.theme.value,
                "show_console": self.config.features.show_console,
                "show_status_bar": self.config.features.show_status_bar,
                "enable_tooltips": self.config.features.enable_tooltips
            }
        }


class EnhancedChessViewerFactory:
    """
    Enhanced factory with beautiful interface and preset configurations.
    
    This provides both simple factory methods and fluent builder pattern.
    """
    
    @staticmethod
    def create() -> ChessViewerBuilder:
        """Create a new builder instance."""
        return ChessViewerBuilder()
    
    @staticmethod
    def minimal() -> ChessViewerBuilder:
        """Create minimal viewer builder."""
        return ChessViewerBuilder().preset(ViewerPreset.MINIMAL)
    
    @staticmethod
    def standard() -> ChessViewerBuilder:
        """Create standard viewer builder."""
        return ChessViewerBuilder().preset(ViewerPreset.STANDARD)
    
    @staticmethod
    def professional() -> ChessViewerBuilder:
        """Create professional viewer builder."""
        return ChessViewerBuilder().preset(ViewerPreset.PROFESSIONAL)
    
    @staticmethod
    def analysis() -> ChessViewerBuilder:
        """Create analysis-focused viewer builder."""
        return ChessViewerBuilder().preset(ViewerPreset.ANALYSIS)
    
    @staticmethod
    def presentation() -> ChessViewerBuilder:
        """Create presentation viewer builder."""
        return ChessViewerBuilder().preset(ViewerPreset.PRESENTATION)
    
    @staticmethod
    def from_config(config_path: str) -> ChessViewerBuilder:
        """Create builder from configuration file."""
        return ChessViewerBuilder().from_config_file(config_path)
    
    @staticmethod
    def quick_viewer(title: str = "Chess Viewer", 
                    board_size: int = 560,
                    debug: bool = False):
        """Quick creation with common parameters."""
        return (ChessViewerBuilder()
                .window(title=title)
                .layout(board_size=board_size)
                .features(debug_mode=debug)
                .build())


# Convenience functions for even shorter syntax
def viewer() -> ChessViewerBuilder:
    """Create a new viewer builder."""
    return EnhancedChessViewerFactory.create()


def minimal_viewer() -> 'ChessViewer':
    """Create minimal viewer immediately."""
    return EnhancedChessViewerFactory.minimal().build()


def standard_viewer() -> 'ChessViewer':
    """Create standard viewer immediately."""
    return EnhancedChessViewerFactory.standard().build()


def professional_viewer() -> 'ChessViewer':
    """Create professional viewer immediately."""
    return EnhancedChessViewerFactory.professional().build()
