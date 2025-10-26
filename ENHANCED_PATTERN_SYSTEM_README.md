# Enhanced Chess Pattern Recognition System

## Overview

This enhanced chess system provides advanced pattern detection, management, and visualization capabilities, along with an improved DynamicBot designed to compete against Stockfish.

## Features

### 1. Enhanced Pattern Detection (`chess_ai/enhanced_pattern_detector.py`)

- **Piece Filtering**: Only shows pieces that actively participate in pattern creation
- **Exchange Prediction**: Predicts exchange sequences 2-3 moves ahead
- **Advanced Pattern Types**:
  - Tactical moments
  - Forks and pins
  - Hanging pieces
  - Exchanges
  - Sacrifices
  - Critical decisions
  - Opening tricks
  - Endgame techniques

### 2. Pattern Management System (`chess_ai/pattern_manager.py`)

- **Active Pattern Selection**: Choose which patterns are active for detection
- **Custom Pattern Creation**: Add your own patterns
- **Pattern Storage**: Individual JSON files for easy management
- **Configuration Management**: Store settings in `pattern_config.json`

### 3. Enhanced JSON Structure (`patterns/`)

- **Detailed Pattern Information**: Comprehensive piece relationships and metadata
- **Exchange Sequences**: Full move sequences for exchanges
- **Pattern Strength**: Calculated based on evaluation changes and piece involvement
- **Game Context**: Opening, phase, time control, and rating information

### 4. PySide Viewer Integration (`ui/pattern_display.py`)

- **Real-time Pattern Display**: Shows detected patterns during games
- **Pattern Filtering**: Filter by type and active status
- **Detailed Pattern Information**: View participating pieces and exchange sequences
- **Game Controls**: Start, Stop, and Reset buttons

### 5. Enhanced DynamicBot (`chess_ai/enhanced_dynamic_bot.py`)

- **Pattern-Based Strategy**: Uses pattern recognition for move selection
- **Phase-Aware Play**: Different strategies for opening, middlegame, and endgame
- **Stockfish Counter-Strategies**: Optimized to compete against Stockfish
- **Strategic Planning**: Opening book and endgame database integration

## File Structure

```
/workspace/
├── chess_ai/
│   ├── enhanced_pattern_detector.py    # Advanced pattern detection
│   ├── enhanced_dynamic_bot.py         # Improved DynamicBot
│   └── pattern_manager.py              # Pattern management system
├── ui/
│   └── pattern_display.py              # PySide pattern display widget
├── patterns/
│   ├── pattern_schema.json             # JSON schema definition
│   ├── enhanced_pattern_catalog.json   # Example pattern catalog
│   ├── pattern_config.json             # Pattern configuration
│   └── custom_patterns.json            # User-created patterns
└── test_enhanced_system.py             # Test script
```

## Usage

### Running the Enhanced PySide Viewer

```bash
python pyside_viewer.py
```

The viewer now includes:
- **🎯 Patterns Tab**: Real-time pattern detection and display
- **🔄 Reset Button**: Reset game to starting position
- **Enhanced DynamicBot**: Automatically used for black pieces against Stockfish

### Pattern Management

```python
from chess_ai.pattern_manager import PatternManager

# Create pattern manager
manager = PatternManager()

# Create custom pattern
pattern_id = manager.create_custom_pattern(
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    move="e4",
    pattern_types=["opening_trick"],
    description="Test opening move"
)

# Set active patterns
manager.set_active_patterns({pattern_id})

# Get active patterns
active_patterns = manager.get_active_patterns()
```

### Pattern Detection

```python
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector

detector = EnhancedPatternDetector()

# Detect patterns for a move
patterns = detector.detect_patterns(
    board, move, 
    evaluation_before, 
    evaluation_after
)
```

## JSON Pattern Structure

Each pattern includes:

```json
{
  "pattern_id": "unique_identifier",
  "fen": "board_position",
  "move": "move_in_san_notation",
  "pattern_types": ["fork", "tactical_moment"],
  "description": "Human readable description",
  "influencing_pieces": [
    {
      "square": "e4",
      "piece": "Knight",
      "color": "white",
      "relationship": "attacker",
      "value": 3,
      "mobility": 8,
      "threats": ["d5", "e4", "g4"],
      "defends": ["e5", "g5"]
    }
  ],
  "evaluation": {
    "before": {"total": 0},
    "after": {"total": 300},
    "change": 300,
    "confidence": 0.95
  },
  "metadata": {
    "pattern_id": "unique_identifier",
    "is_custom": false,
    "added_at": "2025-01-27T10:30:00.000Z",
    "fullmove_number": 3,
    "turn": "black",
    "pattern_strength": 8.5,
    "difficulty_level": "intermediate",
    "tags": ["fork", "tactical", "knight"],
    "source": "detected"
  },
  "exchange_sequence": {
    "moves": ["Nf6", "Qxd8+", "Kxd8"],
    "total_ply": 3,
    "material_balance": 0,
    "positional_advantage": "black"
  }
}
```

## Pattern Types

- **tactical_moment**: Significant evaluation change
- **fork**: Piece attacks multiple enemy pieces
- **pin**: Piece is pinned to king or valuable piece
- **hanging_piece**: Undefended piece under attack
- **exchange**: Predicted exchange sequence (2-3 moves)
- **sacrifice**: Piece sacrifice for positional/tactical gain
- **critical_decision**: Position with multiple alternatives
- **opening_trick**: Unusual opening move
- **endgame_technique**: Endgame-specific pattern

## Piece Relationships

- **mover**: Piece that made the move
- **target**: Piece being attacked or targeted
- **attacker**: Piece doing the attacking
- **defender**: Piece defending a square or piece
- **pinned**: Piece that is pinned
- **hanging**: Piece that is undefended
- **exchanger**: Piece involved in exchange
- **exchanged**: Piece being exchanged
- **sacrificed**: Piece being sacrificed
- **beneficiary**: Piece benefiting from sacrifice
- **center_control**: Piece controlling center squares
- **endgame_piece**: Important piece in endgame
- **threatened**: Piece under threat

## Testing

Run the test script to verify all components:

```bash
python test_enhanced_system.py
```

## Configuration

### Pattern Configuration (`patterns/pattern_config.json`)

```json
{
  "version": "1.0",
  "active_patterns": ["pattern_id_1", "pattern_id_2"],
  "pattern_filters": {
    "min_eval_change": 50,
    "max_patterns_per_type": 100,
    "enable_custom_patterns": true
  }
}
```

### Environment Variables

- `CHESS_USE_R`: Enable R-based evaluation (set to "1")
- `CHESS_DYNAMIC_DIVERSITY`: Enable diversity bonus (set to "1")
- `CHESS_DYNAMIC_BANDIT`: Enable contextual bandit (set to "1")

## Improvements Made

1. **Pattern Filtering**: Only shows relevant pieces in patterns
2. **Exchange Detection**: Recognizes exchange sequences as patterns
3. **JSON Storage**: Individual pattern files for easy management
4. **PySide Integration**: Real-time pattern display during games
5. **Enhanced DynamicBot**: Optimized to compete against Stockfish
6. **Game Controls**: Start/Stop/Reset buttons in viewer
7. **Pattern Management**: Active pattern selection and custom patterns

## Future Enhancements

- Machine learning-based pattern recognition
- Advanced opening book integration
- Endgame tablebase support
- Pattern-based move suggestions
- Tournament mode with pattern statistics
- Pattern difficulty rating system