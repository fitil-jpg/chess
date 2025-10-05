# WFC and BSP Integration with Chess AI

This directory contains examples demonstrating how **Wave Function Collapse (WFC)** and **Binary Space Partitioning (BSP)** engines can be integrated with the chess AI system.

## Overview

### Wave Function Collapse (WFC)
- **Purpose**: Constraint-based procedural generation of chess patterns
- **Applications**: Opening generation, tactical pattern creation, training data synthesis
- **Language**: Python (with NumPy for mathematical operations)

### Binary Space Partitioning (BSP)
- **Purpose**: Spatial organization and analysis of chess board positions
- **Applications**: Zone control analysis, piece interaction detection, strategic area identification
- **Language**: Python (pure implementation)

## Files

- `wfc_bsp_integration.py` - Complete demonstration script
- `README_WFC_BSP.md` - This documentation

## Key Features

### WFC Engine (`chess_ai/wfc_engine.py`)
- **Pattern Types**: Opening, Tactical, Endgame, Positional
- **Constraint Solving**: Automatic compatibility checking between patterns
- **Frequency-based Selection**: Weighted random pattern selection
- **Chess Integration**: Direct Board object generation

### BSP Engine (`chess_ai/bsp_engine.py`)
- **Zone Classification**: Center, Flank, Edge, Corner, General
- **Spatial Analysis**: Piece distribution and zone control calculation
- **Adjacency Detection**: Finding neighboring zones and piece interactions
- **Visualization**: ASCII representation of board zones

## Usage Examples

### Basic WFC Pattern Generation
```python
from chess_ai.wfc_engine import create_chess_wfc_engine

# Create engine with built-in patterns
wfc_engine = create_chess_wfc_engine()

# Generate a pattern
board = wfc_engine.generate_pattern()
print(board)
```

### Basic BSP Board Analysis
```python
from chess_ai.bsp_engine import create_chess_bsp_engine
import chess

# Create engine
bsp_engine = create_chess_bsp_engine()

# Analyze a board
board = chess.Board()
zone_stats = bsp_engine.analyze_board(board)
print(zone_stats)
```

### Integration with Existing AI
```python
from chess_ai.wfc_engine import create_chess_wfc_engine
from chess_ai.bsp_engine import create_chess_bsp_engine
from chess_ai.dynamic_bot import DynamicBot

# Create engines
wfc_engine = create_chess_wfc_engine()
bsp_engine = create_chess_bsp_engine()
bot = DynamicBot(chess.WHITE)

# Generate pattern and analyze
board = wfc_engine.generate_pattern()
zone_control = bsp_engine.calculate_zone_control(board, chess.WHITE)
move, score = bot.choose_move(board)
```

## Running the Examples

```bash
# Run the complete demonstration
python examples/wfc_bsp_integration.py

# Or run individual components
python chess_ai/wfc_engine.py
python chess_ai/bsp_engine.py
```

## Applications in Chess AI

### 1. Pattern Recognition Training
- Generate synthetic positions for neural network training
- Create opening databases with WFC
- Generate tactical puzzles automatically

### 2. Spatial Analysis
- Analyze piece coordination using BSP zones
- Calculate zone control for position evaluation
- Detect piece interactions efficiently

### 3. Opening Preparation
- Generate opening variations with WFC
- Analyze spatial characteristics of openings
- Create opening databases with spatial metadata

### 4. Endgame Analysis
- Generate endgame patterns for study
- Analyze king safety using BSP zones
- Create endgame training positions

## Performance Considerations

### WFC Engine
- **Time Complexity**: O(n²) where n is grid size
- **Memory Usage**: Moderate (stores pattern library and grid)
- **Scalability**: Good for 8x8 chess board

### BSP Engine
- **Time Complexity**: O(log n) for spatial queries
- **Memory Usage**: Low (tree structure)
- **Scalability**: Excellent for real-time analysis

## Customization

### Adding Custom Patterns (WFC)
```python
from chess_ai.wfc_engine import ChessPattern, PatternType

# Create custom pattern
custom_pattern = ChessPattern(
    pattern_type=PatternType.TACTICAL,
    squares=[chess.E4, chess.F5, chess.G6],
    pieces=[chess.Piece(chess.PAWN, chess.WHITE), 
            chess.Piece(chess.KNIGHT, chess.BLACK),
            chess.Piece(chess.BISHOP, chess.BLACK)],
    constraints={"tactical": True, "fork": True},
    frequency=0.5
)

# Add to engine
wfc_engine.add_pattern(custom_pattern)
```

### Custom Zone Types (BSP)
```python
# Modify _determine_zone_type method in BSPEngine
def _determine_zone_type(self, x: int, y: int, node: BSPNode) -> str:
    # Add custom zone classification logic
    if 3 <= x <= 4 and 3 <= y <= 4:
        return "critical_center"
    # ... other custom zones
    return "general"
```

## Future Enhancements

1. **Machine Learning Integration**: Use ML to learn pattern constraints
2. **Real-time Generation**: Optimize for real-time pattern generation
3. **Advanced Constraints**: Add more sophisticated constraint types
4. **Visualization**: Add GUI for pattern and zone visualization
5. **Database Integration**: Store patterns and zones in databases

## Dependencies

- `chess` - Chess board representation
- `numpy` - Mathematical operations for WFC
- `random` - Random pattern selection
- `typing` - Type hints

## Notes

- Both engines are designed to work with the existing chess AI system
- WFC is particularly useful for content generation and training data
- BSP is excellent for spatial analysis and optimization
- The engines can be used independently or together for hybrid approaches