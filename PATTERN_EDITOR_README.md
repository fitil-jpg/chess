# Chess Pattern Editor/Viewer

## Overview

The Chess Pattern Editor/Viewer is an advanced chess analysis tool that transforms the basic interactive viewer into a comprehensive pattern detection and analysis system. It automatically identifies interesting chess patterns during bot games and provides tools for categorizing, saving, and analyzing these patterns.

## Features

### 🎯 Pattern Detection
- **Automatic Detection**: Identifies critical moves and positions with multiple viable options during bot games
- **Multi-Bot Analysis**: Compares evaluations from different chess engines to find decisive moments
- **Complexity Analysis**: Measures move complexity based on number of alternatives and piece activity
- **Context Awareness**: Considers game phase, material balance, and position characteristics

### 📊 Pattern Categories
The system automatically categorizes patterns into:
- **Tactical**: Captures, checks, forks, pins, skewers
- **Opening**: Early game patterns and traps
- **Middlegame**: Complex positional and tactical themes
- **Endgame**: Endgame-specific patterns
- **Positional**: Long-term strategic moves
- **Defensive**: Defensive maneuvers and blocks
- **Attacking**: Aggressive moves and combinations

### 💾 Pattern Storage & Management
- **Persistent Storage**: Patterns saved to JSON files for future analysis
- **Search & Filter**: Find patterns by description, tags, or categories
- **Pattern Editing**: Add descriptions, tags, and modify categorization
- **Pattern Deletion**: Remove unwanted patterns from the database

### 🎮 Interactive Interface
- **Real-time Detection**: Patterns detected and displayed as games progress
- **Chess Board Visualization**: Visual representation of pattern positions
- **Detailed Analysis**: View bot evaluations, alternative moves, and game context
- **Scrollable Pattern List**: Browse through all detected patterns
- **Pattern Details Table**: Comprehensive information about each pattern

## Usage

### Starting the Pattern Editor
```bash
python run_pattern_editor.py
```

### Basic Workflow
1. **Start Auto Play**: Click "▶ Start Auto Play" to begin bot games
2. **Pattern Detection**: Patterns are automatically detected and added to the list
3. **Pattern Review**: Click on patterns in the list to view details
4. **Pattern Editing**: Use "✏️ Edit Pattern" to add descriptions and tags
5. **Pattern Management**: Save, edit, or delete patterns as needed

### Game Controls
- **▶ Start Auto Play**: Begin automatic game playing with pattern detection
- **⏸ Pause**: Pause the current game session
- **⏹ Stop**: Stop all games and pattern detection
- **🔄 Reset**: Reset the system to initial state

### Pattern Management
- **💾 Save Pattern**: Save current pattern with any modifications
- **✏️ Edit Pattern**: Open dialog to edit pattern details
- **🗑️ Delete Pattern**: Remove pattern from storage
- **Search**: Filter patterns by text search
- **Category Filter**: Filter patterns by category

## Pattern Data Structure

Each detected pattern contains:

```python
{
    "id": "unique_pattern_id",
    "position_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "move_san": "e4",
    "move_uci": "e2e4",
    "categories": ["opening", "tactical"],
    "confidence": 0.85,
    "piece_positions": {
        "P": ["a2", "b2", "c2", "d2", "f2", "g2", "h2"],
        "R": ["a1", "h1"],
        # ... other pieces
    },
    "heatmap_influences": {
        "e4": 0.8,
        "d4": 0.6,
        # ... other squares
    },
    "bot_evaluations": {
        "StockfishBot": {
            "confidence": 0.9,
            "evaluation_score": 0.2,
            "reason": "Opening principle"
        }
    },
    "alternative_moves": [
        {
            "move_san": "d4",
            "move_uci": "d2d4",
            "is_capture": false,
            "is_check": false,
            "evaluation_score": 0.15
        }
    ],
    "game_context": {
        "move_number": 1,
        "turn": "white",
        "material_balance": 0,
        "game_phase": "opening"
    },
    "timestamp": 1640995200.0,
    "description": "King's pawn opening - central control",
    "tags": ["e4", "opening", "central-control"]
}
```

## Configuration

### Bot Selection
The system uses two bots by default:
- **White**: StockfishBot (if available, falls back to RandomBot)
- **Black**: DynamicBot (if available, falls back to RandomBot)

### Pattern Detection Thresholds
- **Minimum Alternatives**: 3 (minimum legal moves to consider pattern)
- **Confidence Threshold**: 0.6 (minimum confidence to save pattern)
- **Evaluation Threshold**: 0.5 (minimum evaluation difference for significance)

### Storage Location
Patterns are stored in the `patterns/` directory as JSON files.

## Technical Details

### Architecture
- **PatternDetector**: Core pattern detection logic
- **PatternStorage**: Handles saving/loading patterns to/from disk
- **GameWorker**: Background thread for playing games and detecting patterns
- **PatternEditorViewer**: Main GUI application
- **ChessBoardWidget**: Custom widget for displaying chess positions

### Dependencies
- **PySide6**: GUI framework
- **python-chess**: Chess logic and board representation
- **Standard Library**: JSON, threading, pathlib, etc.

### Performance
- Games run in background threads to keep UI responsive
- Pattern detection is optimized for real-time analysis
- JSON storage provides fast loading and saving

## Troubleshooting

### Common Issues

1. **Grayed Out Start Button**: Fixed in this version - button should be enabled on startup
2. **No Patterns Detected**: Check that bots are properly initialized and games are running
3. **Import Errors**: Ensure PySide6 and python-chess are installed
4. **Stockfish Not Found**: Set STOCKFISH_PATH environment variable or place binary in bin/

### Error Messages
- Check the console output for detailed error messages
- Enable debug logging by setting logging level to DEBUG

## Future Enhancements

Potential improvements for future versions:
- **Machine Learning**: Train models on detected patterns for better classification
- **Pattern Matching**: Find similar patterns in databases
- **Export/Import**: Share pattern collections between users
- **Advanced Visualization**: Heatmaps and arrow overlays on the board
- **Pattern Statistics**: Analytics on pattern frequency and success rates
- **Integration**: Connect with chess databases and opening books

## Contributing

To contribute to the pattern editor:
1. Follow the existing code style and patterns
2. Add comprehensive docstrings and comments
3. Test new features thoroughly
4. Update this README for any new functionality

## License

This pattern editor is part of the chess analysis project and follows the same licensing terms.