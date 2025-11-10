# Enhanced Chess Viewer Factory - Beautiful Interface

## Overview

The Enhanced Chess Viewer Factory provides a clean, intuitive, and beautiful interface for creating configured chess viewers. It combines the power of fluent interface design with type safety and preset configurations.

## ✨ Key Features

- **🔗 Fluent Interface**: Method chaining for readable configuration
- **🎯 Type Safety**: Enums for all configuration options
- **📋 Preset Configurations**: Ready-to-use setups for common scenarios
- **⚡ Convenience Functions**: One-liner creation for common cases
- **📁 File Support**: Load configurations from JSON files
- **🎨 Beautiful Syntax**: Clean, readable, and maintainable code

## 🚀 Quick Start

### Basic Usage

```python
from ui.enhanced_chess_viewer_factory import viewer, TabPosition, Theme

# Beautiful fluent interface
viewer = (viewer()
          .window(title="My Chess Viewer")
          .layout(board_size=600, tab_position=TabPosition.WEST)
          .features(debug_mode=True, theme=Theme.DARK)
          .build())

viewer.show()
```

### Preset Configurations

```python
from ui.enhanced_chess_viewer_factory import (
    EnhancedChessViewerFactory,
    minimal_viewer,
    standard_viewer,
    professional_viewer
)

# One-liner presets
viewer1 = minimal_viewer()
viewer2 = standard_viewer()
viewer3 = professional_viewer()

# Factory presets with customization
viewer = (EnhancedChessViewerFactory.professional()
          .window(title="Analysis Studio")
          .layout(tab_position=TabPosition.WEST)
          .build())
```

## 📖 Interface Reference

### ChessViewerBuilder

The main builder class with fluent interface:

#### Window Configuration
```python
.window(
    title="Chess Viewer",
    min_size=(800, 600),
    default_size=(1200, 800),
    resizable=True,
    restore_geometry=True,
    center_on_screen=True
)
```

#### Layout Configuration
```python
.layout(
    board_size=560,
    console_height=140,
    tab_position=TabPosition.NORTH,
    subtab_position=TabPosition.SOUTH,
    enable_scroll=True,
    spacing={'main': 10, 'controls': 2, 'board': 0}
)
```

#### Features Configuration
```python
.features(
    auto_save_geometry=True,
    compact_mode=True,
    debug_mode=False,
    elo_refresh=True,
    theme=Theme.DEFAULT,
    show_console=True,
    show_status_bar=True,
    enable_tooltips=True
)
```

### Enums

#### TabPosition
- `TabPosition.NORTH` - Tabs on top
- `TabPosition.SOUTH` - Tabs on bottom
- `TabPosition.WEST` - Tabs on left
- `TabPosition.EAST` - Tabs on right

#### Theme
- `Theme.DEFAULT` - Default theme
- `Theme.DARK` - Dark theme
- `Theme.LIGHT` - Light theme
- `Theme.COMPACT` - Compact theme

#### ViewerPreset
- `ViewerPreset.MINIMAL` - Minimal configuration
- `ViewerPreset.STANDARD` - Standard setup
- `ViewerPreset.PROFESSIONAL` - Professional features
- `ViewerPreset.ANALYSIS` - Analysis-focused
- `ViewerPreset.PRESENTATION` - Presentation mode

## 🎨 Preset Configurations

### Minimal
```python
viewer = EnhancedChessViewerFactory.minimal().build()
```
- Small window (800x500)
- Compact board (400px)
- Debug mode enabled
- Minimal UI elements

### Standard
```python
viewer = EnhancedChessViewerFactory.standard().build()
```
- Default window (1200x800)
- Standard board (560px)
- All features enabled
- Balanced layout

### Professional
```python
viewer = EnhancedChessViewerFactory.professional().build()
```
- Large window (1400x900)
- Large board (640px)
- Dark theme
- Professional features

### Analysis
```python
viewer = EnhancedChessViewerFactory.analysis().build()
```
- Extra large window (1600x1000)
- Large board (700px)
- West tab position
- Analysis features

### Presentation
```python
viewer = EnhancedChessViewerFactory.presentation().build()
```
- Full HD window (1920x1080)
- Extra large board (800px)
- Light theme
- Presentation layout

## ⚡ Convenience Functions

```python
from ui.enhanced_chess_viewer_factory import (
    viewer,
    minimal_viewer,
    standard_viewer,
    professional_viewer
)

# Quick creation
viewer1 = minimal_viewer()
viewer2 = standard_viewer()
viewer3 = professional_viewer()

# Quick viewer with parameters
viewer = viewer().window(title="Quick Viewer").build()
```

## 📁 Configuration Files

### Loading from JSON
```python
viewer = (EnhancedChessViewerFactory.from_config("config/my_config.json")
          .window(title="Loaded from Config")
          .build())
```

### Example JSON Configuration
```json
{
    "window": {
        "title": "My Chess Viewer",
        "min_size": [800, 600],
        "default_size": [1200, 800],
        "resizable": true,
        "restore_geometry": true
    },
    "layout": {
        "board_size": 560,
        "console_height": 140,
        "tab_position": "north",
        "subtab_position": "south",
        "enable_scroll": true,
        "spacing": {
            "main": 10,
            "controls": 2,
            "board": 0
        }
    },
    "features": {
        "auto_save_geometry": true,
        "compact_mode": true,
        "debug_mode": false,
        "elo_refresh": true,
        "theme": "default",
        "show_console": true,
        "show_status_bar": true,
        "enable_tooltips": true
    }
}
```

## 🎯 Use Cases

### Development/Testing
```python
viewer = (EnhancedChessViewerFactory.minimal()
          .features(debug_mode=True, theme=Theme.DARK)
          .build())
```

### Professional Analysis
```python
viewer = (EnhancedChessViewerFactory.professional()
          .window(title="Professional Analysis Studio")
          .layout(tab_position=TabPosition.WEST)
          .features(debug_mode=True)
          .build())
```

### Presentation Mode
```python
viewer = (EnhancedChessViewerFactory.presentation()
          .window(title="Tournament Analysis Presentation")
          .build())
```

### Custom Configuration
```python
viewer = (viewer()
          .window(title="Custom Setup", min_size=(1000, 700))
          .layout(board_size=650, tab_position=TabPosition.EAST)
          .features(theme=Theme.DARK, debug_mode=True)
          .build())
```

## 🔄 Migration from Old Factory

### Old Way
```python
from ui.chess_viewer_factory import ChessViewerFactory

viewer = ChessViewerFactory.create_viewer(
    window_title="Chess Viewer",
    window_min_size=[800, 600],
    layout_board_size=560,
    layout_tab_position="west",
    features_debug_mode=True
)
```

### New Way
```python
from ui.enhanced_chess_viewer_factory import viewer, TabPosition

viewer = (viewer()
          .window(title="Chess Viewer", min_size=(800, 600))
          .layout(board_size=560, tab_position=TabPosition.WEST)
          .features(debug_mode=True)
          .build())
```

**Benefits of New Interface:**
- ✅ Type safety with enums
- ✅ Better readability
- ✅ Method chaining
- ✅ IDE autocompletion
- ✅ Preset configurations
- ✅ Consistent parameter naming

## 🧪 Testing

Run the examples to see the interface in action:

```bash
python examples/beautiful_factory_examples.py
```

## 📝 Best Practices

1. **Use presets** for common configurations
2. **Chain methods** for readable configuration
3. **Use enums** for type safety
4. **Store configurations** in JSON for reuse
5. **Use convenience functions** for quick creation
6. **Customize presets** rather than building from scratch

## 🎉 Conclusion

The Enhanced Chess Viewer Factory brings modern, beautiful interface design to chess viewer creation. With fluent chaining, type safety, and preset configurations, creating the perfect chess viewer has never been easier or more enjoyable.
