#!/usr/bin/env python3
"""
Beautiful examples of the enhanced Chess Viewer Factory interface.
Demonstrates the clean, intuitive API for creating configured chess viewers.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.enhanced_chess_viewer_factory import (
    EnhancedChessViewerFactory,
    ChessViewerBuilder,
    TabPosition,
    Theme,
    ViewerPreset,
    viewer,
    minimal_viewer,
    standard_viewer,
    professional_viewer
)


def example_1_basic_fluent():
    """Example 1: Basic fluent interface usage."""
    print("=== Example 1: Basic Fluent Interface ===")
    
    app = QApplication([])
    
    # Clean, readable fluent interface
    viewer = (ChessViewerBuilder()
              .window(title="My Chess Viewer")
              .layout(board_size=600)
              .features(debug_mode=True)
              .build())
    
    viewer.show()
    print("✅ Created basic viewer with fluent interface")
    return app


def example_2_preset_configurations():
    """Example 2: Using preset configurations."""
    print("\n=== Example 2: Preset Configurations ===")
    
    app = QApplication([])
    
    # Professional preset
    pro_viewer = (EnhancedChessViewerFactory.professional()
                  .window(title="Professional Analysis")
                  .build())
    
    # Analysis preset with customizations
    analysis_viewer = (EnhancedChessViewerFactory.analysis()
                      .layout(tab_position=TabPosition.WEST)
                      .features(theme=Theme.DARK)
                      .build())
    
    pro_viewer.show()
    analysis_viewer.show()
    print("✅ Created professional and analysis viewers")
    return app


def example_3_convenience_functions():
    """Example 3: Super convenient shortcuts."""
    print("\n=== Example 3: Convenience Functions ===")
    
    app = QApplication([])
    
    # One-liner viewer creation
    viewer1 = minimal_viewer()
    viewer2 = standard_viewer()
    viewer3 = professional_viewer()
    
    viewer1.show()
    viewer2.show()
    print("✅ Created viewers with convenience functions")
    return app


def example_4_advanced_configuration():
    """Example 4: Advanced configuration with all options."""
    print("\n=== Example 4: Advanced Configuration ===")
    
    app = QApplication([])
    
    # Complex configuration with all options
    viewer = (viewer()
              .window(
                  title="Advanced Chess Analysis Studio",
                  min_size=(1000, 700),
                  default_size=(1600, 1000),
                  center_on_screen=True
              )
              .layout(
                  board_size=700,
                  console_height=180,
                  tab_position=TabPosition.WEST,
                  subtab_position=TabPosition.SOUTH,
                  enable_scroll=True,
                  spacing={'main': 15, 'controls': 5, 'board': 0}
              )
              .features(
                  auto_save_geometry=True,
                  compact_mode=False,
                  debug_mode=True,
                  elo_refresh=True,
                  theme=Theme.DARK,
                  show_console=True,
                  show_status_bar=True,
                  enable_tooltips=True
              )
              .build())
    
    viewer.show()
    print("✅ Created advanced configuration viewer")
    return app


def example_5_quick_creation():
    """Example 5: Quick creation for common use cases."""
    print("\n=== Example 5: Quick Creation ===")
    
    app = QApplication([])
    
    # Quick viewer with common parameters
    debug_viewer = EnhancedChessViewerFactory.quick_viewer(
        title="Debug Chess Viewer",
        board_size=500,
        debug=True
    )
    
    # Presentation viewer
    presentation_viewer = (EnhancedChessViewerFactory.presentation()
                          .window(title="Chess Presentation - Tournament Analysis")
                          .build())
    
    debug_viewer.show()
    print("✅ Created quick viewers")
    return app


def example_6_configuration_from_file():
    """Example 6: Loading configuration from file."""
    print("\n=== Example 6: Configuration from File ===")
    
    app = QApplication([])
    
    # Load from custom config file
    viewer = (EnhancedChessViewerFactory.from_config("config/window_config.json")
              .window(title="Custom Config Viewer")
              .build())
    
    viewer.show()
    print("✅ Created viewer from configuration file")
    return app


def example_7_programmatic_configuration():
    """Example 7: Programmatic configuration based on conditions."""
    print("\n=== Example 7: Programmatic Configuration ===")
    
    app = QApplication([])
    
    # Configuration based on user preferences or environment
    is_developer = True
    screen_size = (1920, 1080)
    is_presentation_mode = False
    
    builder = ChessViewerBuilder()
    
    if is_developer:
        builder.features(debug_mode=True, theme=Theme.DARK)
    
    if screen_size[0] > 1500:  # Large screen
        builder.layout(board_size=700, tab_position=TabPosition.WEST)
    else:
        builder.layout(board_size=500, tab_position=TabPosition.NORTH)
    
    if is_presentation_mode:
        builder.preset(ViewerPreset.PRESENTATION)
    else:
        builder.preset(ViewerPreset.STANDARD)
    
    viewer = builder.build()
    viewer.show()
    print("✅ Created programmatically configured viewer")
    return app


def example_8_comparison_old_vs_new():
    """Example 8: Comparison of old vs new interface."""
    print("\n=== Example 8: Old vs New Interface Comparison ===")
    
    print("OLD WAY:")
    print("""
    from ui.chess_viewer_factory import ChessViewerFactory
    
    viewer = ChessViewerFactory.create_viewer(
        window_title="Chess Viewer",
        window_min_size=[800, 600],
        layout_board_size=560,
        layout_tab_position="west",
        features_debug_mode=True
    )
    """)
    
    print("NEW WAY:")
    print("""
    from ui.enhanced_chess_viewer_factory import viewer, TabPosition, Theme
    
    viewer = (viewer()
              .window(title="Chess Viewer")
              .layout(board_size=560, tab_position=TabPosition.WEST)
              .features(debug_mode=True)
              .build())
    """)
    
    print("✅ New interface is more readable and type-safe!")


def main():
    """Run all examples."""
    print("🎯 Enhanced Chess Viewer Factory - Beautiful Interface Examples")
    print("=" * 70)
    
    # Show comparison first
    example_8_comparison_old_vs_new()
    
    print("\n🚀 Running interactive examples...")
    
    # Run examples (comment out ones you don't want to test)
    examples = [
        ("Basic Fluent Interface", example_1_basic_fluent),
        ("Preset Configurations", example_2_preset_configurations),
        ("Convenience Functions", example_3_convenience_functions),
        ("Advanced Configuration", example_4_advanced_configuration),
        ("Quick Creation", example_5_quick_creation),
        ("Configuration from File", example_6_configuration_from_file),
        ("Programmatic Configuration", example_7_programmatic_configuration),
    ]
    
    # For demonstration, we'll run just one example
    # In real usage, you would choose the example you want to test
    selected_example = examples[0]  # Change index to test different examples
    
    print(f"\n🎨 Running: {selected_example[0]}")
    app = selected_example[1]()
    
    print("\n✨ All examples completed successfully!")
    print("\n📚 Available features:")
    print("• Fluent interface with method chaining")
    print("• Type-safe enums for configuration")
    print("• Preset configurations for common use cases")
    print("• Convenience functions for quick creation")
    print("• Configuration file loading")
    print("• Programmatic configuration support")
    print("• Beautiful, readable syntax")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
