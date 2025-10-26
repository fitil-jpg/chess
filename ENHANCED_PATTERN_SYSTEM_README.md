# Enhanced Chess Pattern System

## Overview

This enhanced chess pattern system provides advanced pattern detection, management, and visualization capabilities. It includes:

- **Pattern Management**: Store patterns as individual JSON files for easy creation and deletion
- **Advanced Pattern Filtering**: Filter out irrelevant pieces to focus on pattern causes
- **Exchange Pattern Detection**: Recognize predictable 2-3 move sequences as patterns
- **Enhanced DynamicBot**: Improved bot designed to defeat Stockfish
- **Interactive PySide Viewer**: Real-time pattern display during gameplay

## Key Features

### 1. Pattern Management System

The new `PatternManager` class stores each pattern in its own JSON file:

```python
from chess_ai.pattern_manager import PatternManager

manager = PatternManager("patterns")
pattern_id = manager.add_pattern(chess_pattern)
patterns = manager.search_patterns(pattern_types=["fork", "pin"])
```

**Pattern JSON Structure:**
```json
{
  "id": "uuid-string",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": "e4",
  "pattern_types": ["tactical_moment", "fork"],
  "description": "Central pawn advance with tactical potential",
  "influencing_pieces": ["e4", "d2", "f2"],
  "evaluation": {
    "before": {"total": 0},
    "after": {"total": 20},
    "change": 20
  },
  "metadata": {
    "created_at": "2025-01-27T10:30:00Z",
    "modified_at": "2025-01-27T10:30:00Z",
    "complexity": "moderate",
    "game_phase": "opening",
    "confidence": 0.85
  }
}
```

### 2. Pattern Filtering System

The `PatternFilter` class identifies relevant pieces and filters out non-participating pieces:

```python
from chess_ai.pattern_filter import PatternFilter

filter_system = PatternFilter()
result = filter_system.analyze_pattern_relevance(board, move, pattern_types)

# Result contains:
# - relevant_pieces: Set of squares with important pieces
# - irrelevant_pieces: Set of squares with unimportant pieces  
# - filtered_fen: FEN with irrelevant pieces removed
# - pattern_analysis: Detailed analysis by pattern type
```

### 3. Exchange Pattern Detection

The system recognizes exchange patterns (predictable 2-3 move sequences):

```python
exchange_info = filter_system.detect_exchange_pattern(board, move)
if exchange_info:
    print(f"Exchange detected: {exchange_info['exchange_value']} points")
    print(f"Forced: {exchange_info['is_forced']}")
```

### 4. Enhanced DynamicBot

The improved DynamicBot uses advanced pattern recognition and strategic planning:

```python
from chess_ai.enhanced_dynamic_bot import make_enhanced_dynamic_bot

bot = make_enhanced_dynamic_bot(chess.WHITE)
move = bot.choose_move(board)
```

**Bot Features:**
- Pattern-based move evaluation
- Tactical and positional analysis
- Safety scoring
- Game phase awareness
- Confidence-based move selection

### 5. Interactive PySide Viewer

The enhanced viewer provides real-time pattern display and management:

```bash
python run_enhanced_viewer.py
```

**Viewer Features:**
- Real-time pattern detection during gameplay
- Pattern library management
- Filtered pattern visualization
- Game controls (start/stop/reset/new game)
- Bot configuration
- Pattern search and filtering

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Stockfish is available:
```bash
# Set STOCKFISH_PATH environment variable
export STOCKFISH_PATH="/path/to/stockfish"
```

## Usage

### Running the Enhanced Viewer

```bash
python run_enhanced_viewer.py
```

### Using Pattern Management

```python
from chess_ai.pattern_manager import PatternManager
from chess_ai.pattern_detector import PatternDetector

# Initialize components
manager = PatternManager()
detector = PatternDetector()

# Detect patterns in a game
patterns = detector.detect_patterns(board, move, eval_before, eval_after)

# Save patterns
for pattern in patterns:
    pattern_id = manager.add_pattern(pattern)
    print(f"Saved pattern: {pattern_id}")

# Search patterns
fork_patterns = manager.search_patterns(pattern_types=["fork"])
print(f"Found {len(fork_patterns)} fork patterns")
```

### Using Pattern Filtering

```python
from chess_ai.pattern_filter import PatternFilter

filter_system = PatternFilter()

# Analyze pattern relevance
result = filter_system.analyze_pattern_relevance(
    board, move, ["fork", "pin"]
)

# Get filtered FEN (only relevant pieces)
filtered_fen = result["filtered_fen"]
print(f"Filtered position: {filtered_fen}")

# Check which pieces to show
for square in chess.SQUARES:
    if filter_system.should_show_piece(square, result):
        piece = board.piece_at(square)
        if piece:
            print(f"Show {piece.symbol()} at {chess.square_name(square)}")
```

## File Structure

```
chess_ai/
├── pattern_manager.py      # Pattern storage and management
├── pattern_filter.py       # Pattern filtering and analysis
├── pattern_detector.py     # Pattern detection logic
├── enhanced_dynamic_bot.py # Enhanced bot implementation
└── pattern_storage.py      # Legacy pattern storage (deprecated)

patterns/                   # Individual pattern JSON files
├── pattern_<uuid1>.json
├── pattern_<uuid2>.json
└── ...

enhanced_pyside_viewer.py   # Enhanced PySide viewer
run_enhanced_viewer.py      # Viewer launcher script
```

## Configuration

### Bot Configuration

The Enhanced DynamicBot can be configured through its constructor:

```python
bot = EnhancedDynamicBot(
    color=chess.WHITE,
    stockfish_path="/path/to/stockfish",
    aggression_level=0.7,    # 0.0 = defensive, 1.0 = aggressive
    pattern_weight=0.4,      # Weight of pattern-based evaluation
    tactical_weight=0.3,     # Weight of tactical evaluation
    positional_weight=0.3    # Weight of positional evaluation
)
```

### Pattern Detection Settings

Pattern detection can be configured in the viewer:

- **Auto-detect patterns**: Enable/disable automatic pattern detection
- **Filter irrelevant pieces**: Show only pieces involved in patterns
- **Complexity filter**: Filter patterns by complexity (simple/moderate/complex)

## Advanced Features

### Custom Pattern Creation

You can create custom patterns programmatically:

```python
from chess_ai.pattern_detector import ChessPattern

custom_pattern = ChessPattern(
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    move="e4",
    pattern_types=["custom_opening"],
    description="Custom opening pattern",
    influencing_pieces=["e4", "d2"],
    evaluation={"before": {"total": 0}, "after": {"total": 10}, "change": 10},
    metadata={"custom": True, "created_by": "user"}
)

pattern_id = manager.add_pattern(custom_pattern)
```

### Pattern Export/Import

Export patterns to a single file:

```python
# Export all patterns
manager.export_patterns("all_patterns.json")

# Export specific patterns
manager.export_patterns("fork_patterns.json", pattern_ids=["id1", "id2"])

# Import patterns
imported_count = manager.import_patterns("patterns_to_import.json")
```

### Pattern Statistics

Get statistics about your pattern library:

```python
stats = manager.get_pattern_statistics()
print(f"Total patterns: {stats['total_patterns']}")
print(f"By type: {stats['by_type']}")
print(f"By piece: {stats['by_piece']}")
print(f"By phase: {stats['by_phase']}")
```

## Troubleshooting

### Common Issues

1. **Stockfish not found**: Set the `STOCKFISH_PATH` environment variable
2. **PySide6 import error**: Install PySide6 with `pip install PySide6`
3. **Pattern detection not working**: Check that the board position is valid
4. **Memory issues with large pattern libraries**: Use pattern filtering to reduce memory usage

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. **Use pattern filtering**: Only load patterns you need
2. **Index optimization**: The PatternManager uses indexes for fast searching
3. **Batch operations**: Use batch methods when processing many patterns
4. **Memory management**: Clear unused patterns from memory periodically

## Future Enhancements

- Machine learning-based pattern recognition
- Advanced pattern similarity detection
- Pattern recommendation system
- Multi-threaded pattern detection
- Cloud pattern synchronization
- Advanced visualization options

## Contributing

To contribute to the enhanced pattern system:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License.