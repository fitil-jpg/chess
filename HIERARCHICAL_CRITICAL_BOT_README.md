# Hierarchical CriticalBot System

## Overview

The Hierarchical CriticalBot system implements a sophisticated delegation mechanism where CriticalBot can call specialized sub-bots based on position characteristics. This creates a more intelligent and context-aware decision-making process.

## Architecture

```
CriticalBot (Hierarchical)
├── AggressiveBot (material gain, tactics)
├── PawnBot (pawn structure, doubled pawns, king pressure)
└── KingValueBot (king safety, heatmap-based zone control)
```

## When CriticalBot is Called

CriticalBot is activated in every turn within the DynamicBot meta-agent system. The delegation logic works as follows:

### 1. Priority Order (Original CriticalBot Logic)
1. **Mate-in-1 detection** - Immediate winning moves
2. **Depth-2 forcing threats** - Checks, forks, hanging captures via ThreatScout
3. **Critical piece targeting** - Using `Evaluator.criticality()` for high-threat pieces

### 2. Hierarchical Delegation (New)
If no critical targets are found, CriticalBot delegates to sub-bots based on:

#### Game Phase Analysis:
- **Opening** (moves 1-15): `PawnBot → AggressiveBot → KingValueBot`
- **Middlegame with tactics**: `AggressiveBot → PawnBot → KingValueBot`
- **Middlegame without tactics**: `PawnBot → KingValueBot → AggressiveBot`
- **Endgame** (moves 40+): `KingValueBot → AggressiveBot → PawnBot`

#### Material Considerations:
- **Material advantage** (>200): Prioritize AggressiveBot
- **Material disadvantage** (<-200): Prioritize PawnBot

## Sub-Bots Specialization

### PawnBot
**Focus**: Pawn structure optimization and king pressure

**Heuristics**:
- **Doubled Pawns Creation**: Bonus for creating 2+ pawns on same file
- **King Pressure**: Proximity-based bonus for pawns near opponent king
- **Passed Pawn Potential**: Advanced pawn evaluation with clear path bonus
- **Pawn Chains**: Supporting pawn formations on adjacent files

**Scoring Examples**:
- Doubled pawns: +50 points per additional pawn
- King pressure: Up to +80 points based on distance
- Passed pawn: +10-15 points per rank, +50% bonus for clear path

### KingValueBot (Enhanced)
**Focus**: King safety and heatmap-based zone control

**Features**:
- **Original**: Dynamic king material pressure, king safety deltas
- **New**: Heatmap-based king zone analysis
- **Zone Control**: Analyzes controlled vs attacked squares around kings
- **Heatmap Integration**: Uses existing heatmap system for position evaluation

**Heatmap Analysis**:
- Defensive: Rewards controlled squares, penalizes attacked squares
- Offensive: Rewards attacks on opponent's king zone
- Zone radius: Configurable (default: 2 squares around king)

### AggressiveBot (Existing)
**Focus**: Material gain and tactical opportunities

## Heatmap Integration

The system leverages the existing heatmap infrastructure:

### Available Heatmap Modules:
- `utils.heatmap_generator.HeatmapGenerator`
- `utils.heatmap_analyzer.HeatmapAnalyzer`

### King Zone Heatmap Logic:
```python
# Generate control heatmap
control_heatmap = generate_control_heatmap(board, defensive=True)

# Analyze king zone (2-square radius)
king_zone = get_king_zone_squares(king_square)

# Calculate control ratios
controlled_squares = count_positive_values(king_zone, control_heatmap)
attacked_squares = count_negative_values(king_zone, control_heatmap)
```

## Usage Examples

### Basic Usage:
```python
from chess_ai.critical_bot import CriticalBot
from core.evaluator import Evaluator
from utils import GameContext

# Create hierarchical CriticalBot
critical_bot = CriticalBot(color=chess.WHITE, enable_hierarchy=True)

# Get move suggestion
board = chess.Board()
evaluator = Evaluator(board)
context = GameContext(material_diff=0, mobility=0, king_safety=0)

move, score = critical_bot.choose_move(board, context, evaluator, debug=True)
```

### DynamicBot Integration:
```python
from chess_ai.dynamic_bot import DynamicBot

# DynamicBot automatically uses hierarchical CriticalBot
dynamic_bot = DynamicBot(
    color=chess.WHITE,
    weights={
        'critical': 1.0,    # Hierarchical CriticalBot
        'pawn': 0.8,        # Standalone PawnBot
        'king': 0.9,        # Standalone KingValueBot
        'aggressive': 1.0   # Standalone AggressiveBot
    }
)
```

### Custom Sub-bot Configuration:
```python
# Disable hierarchy for original behavior
critical_bot = CriticalBot(color=chess.WHITE, enable_hierarchy=False)

# Custom weights in DynamicBot
dynamic_bot = DynamicBot(
    color=chess.WHITE,
    weights={
        'critical': 0.5,    # Reduce CriticalBot influence
        'pawn': 1.2,        # Increase pawn structure focus
        'king': 1.0,        # Standard king safety
    }
)
```

## Testing

Run the test script to verify functionality:

```bash
python3 test_hierarchical_critical_bot.py
```

The test demonstrates:
1. Hierarchical delegation in different game phases
2. PawnBot heuristics for doubled pawns and king pressure
3. KingValueBot heatmap integration
4. Sub-bot comparison analysis

## Configuration Options

### CriticalBot Parameters:
- `capture_bonus`: Bonus for capturing critical pieces (default: 100.0)
- `enable_hierarchy`: Enable/disable delegation (default: True)

### PawnBot Parameters:
- `doubled_pawn_bonus`: Bonus for doubled pawns (default: 50.0)
- `king_pressure_bonus`: Bonus for king proximity (default: 80.0)

### KingValueBot Parameters:
- `enable_heatmaps`: Enable heatmap analysis (default: True)
- `king_zone_radius`: Zone analysis radius (default: 2)

## Performance Considerations

### Benefits:
- **Context-aware decisions**: Sub-bots specialize in different aspects
- **Flexibility**: Can be enabled/disabled per configuration
- **Scalability**: Easy to add new sub-bots
- **Backward compatibility**: Original CriticalBot behavior preserved

### Overhead:
- Additional sub-bot instantiations
- Extra evaluation calls for delegation
- Minimal performance impact for gained intelligence

## Future Extensions

### Potential Sub-bots:
- **EndgameBot**: Specialized endgame techniques
- **PositionalBot**: Long-term positional advantages
- **TacticalBot**: Complex tactical combinations
- **DefensiveBot**: Counter-attacking and defense

### Enhanced Heatmap Features:
- Pattern recognition integration
- Learning from historical games
- Dynamic heatmap weighting
- Real-time heatmap updates

## File Structure

```
chess_ai/
├── critical_bot.py          # Enhanced with hierarchy
├── pawn_bot.py             # New specialized bot
├── king_value_bot.py       # Enhanced with heatmaps
├── aggressive_bot.py       # Existing
└── dynamic_bot.py          # Updated integration

utils/
├── heatmap_generator.py    # Existing heatmap system
└── heatmap_analyzer.py     # Existing analysis tools

test_hierarchical_critical_bot.py  # Test suite
HIERARCHICAL_CRITICAL_BOT_README.md # This documentation
```

## Summary

The Hierarchical CriticalBot system provides intelligent delegation to specialized sub-bots, enabling more nuanced and context-aware chess decisions. By combining the strengths of different bot specializations with heatmap-based analysis, the system offers both tactical precision and strategic depth while maintaining backward compatibility and configurability.
