# Bot Filtering System

## Overview

The bot filtering system provides intelligent bot selection based on position characteristics and pattern matching. It enables dynamic bot choice according to game state, tactical patterns, and strategic requirements.

## Features

### Position-Based Filtering
- **Game Phase Detection**: Opening, middlegame, endgame recognition
- **Material Analysis**: Balance calculation and advantage detection
- **Tactical Assessment**: Check, capture, and threat identification
- **Positional Evaluation**: Center control, king safety, pawn structure analysis

### Pattern-Based Filtering
- **Pattern Matching**: Integration with existing pattern system
- **Tactical Patterns**: Forks, pins, skewers, discoveries
- **Positional Patterns**: Center control, pawn structures
- **Opening Patterns**: Book moves and development sequences

### Bot Capabilities
- **Specialized Bots**: Each bot has defined strengths and preferences
- **Adaptive Selection**: Bots chosen based on position requirements
- **Performance Scoring**: Quantified suitability for each position
- **Custom Capabilities**: Easy addition of new bot profiles

## Usage

### Basic Filtering

```python
from chess_ai import BotFilter
from chess_ai.bot_filter import create_opening_filter
import chess

# Create filter
bot_filter = BotFilter()

# Define available bots
available_bots = ["AggressiveBot", "FortifyBot", "EndgameBot", "DynamicBot", "RandomBot"]

# Create position
board = chess.Board()

# Filter for opening
opening_filter = create_opening_filter()
filtered_bots = bot_filter.filter_bots(board, available_bots, opening_filter)

print(f"Recommended opening bots: {filtered_bots}")
```

### Get Recommendations with Scores

```python
# Get top 3 recommended bots with suitability scores
recommendations = bot_filter.get_recommended_bots(board, available_bots, top_n=3)

for bot_name, score in recommendations:
    print(f"{bot_name}: {score:.2f} suitability")
```

### Custom Filtering Criteria

```python
from chess_ai.bot_filter import FilterCriteria, GamePhase

# Create custom criteria
custom_filter = FilterCriteria(
    game_phase=GamePhase.MIDDLEGAME,
    tactical_awareness=True,
    material_advantage="advantage",
    center_control_required=True
)

filtered_bots = bot_filter.filter_bots(board, available_bots, custom_filter)
```

### Pattern-Based Filtering

```python
from chess_ai.pattern_responder import PatternResponder

# Create pattern responder
pattern_responder = PatternResponder()

# Create filter with pattern integration
bot_filter = BotFilter(pattern_responder)

# Filter by pattern types
pattern_filter = FilterCriteria(
    pattern_types=["tactical"],
    required_patterns=["fork", "pin"]
)

filtered_bots = bot_filter.filter_bots(board, available_bots, pattern_filter)
```

## Available Filter Types

### Predefined Filters

```python
from chess_ai.bot_filter import (
    create_opening_filter,
    create_middlegame_filter, 
    create_endgame_filter,
    create_tactical_filter,
    create_positional_filter
)

# Use predefined filters
opening_filter = create_opening_filter()
tactical_filter = create_tactical_filter()
```

### Filter Criteria Options

- **Position-based**: Piece count, move number, game phase
- **Material-based**: Advantage, imbalance threshold
- **Tactical-based**: Checks, captures, threats required
- **Pattern-based**: Required/excluded patterns, pattern types
- **Positional**: King safety, center control, pawn structure

## Bot Capabilities

### Default Bot Profiles

- **AggressiveBot**: High aggressive tendency, tactical awareness
- **FortifyBot**: Strong defensive capabilities, pawn structure expertise
- **EndgameBot**: Endgame specialist, king safety focus
- **TrapBot**: Tactical trap specialist, pattern matching
- **CriticalBot**: Targets critical pieces, middlegame focus
- **PieceMateBot**: Piece trapping specialist
- **KingValueBot**: King safety focused, defensive
- **DynamicBot**: Adaptive, all-phase capability
- **RandomBot**: Fallback option

### Adding Custom Bot Capabilities

```python
from chess_ai.bot_filter import BotCapability, GamePhase

# Define custom capability
custom_bot = BotCapability(
    bot_name="CustomExpert",
    bot_class="CustomExpert",
    preferred_phases=[GamePhase.MIDDLEGAME],
    material_situations=["advantage"],
    tactical_awareness=True,
    aggressive_tendency=0.7,
    defensive_strength=0.6,
    center_control_focus=True
)

# Add to filter
bot_filter.add_bot_capability(custom_bot)
```

## Position Analysis

### Detailed Analysis

```python
# Analyze current position
analysis = bot_filter.position_analyzer.analyze_position(board)

print(f"Game Phase: {analysis['game_phase'].value}")
print(f"Material Balance: {analysis['material_balance']}")
print(f"Center Control: {analysis['center_control']}")
print(f"King Safety: {analysis['king_safety']}")
print(f"Tactical Threats: {analysis['threats']}")
```

### Analysis Features

- **Game Phase**: Automatic detection based on piece count and move number
- **Material Balance**: Numerical evaluation of material differences
- **Center Control**: Square-by-square control analysis
- **King Safety**: Attacker count and pawn shield evaluation
- **Pawn Structure**: Doubled pawns, isolated pawns, structural quality
- **Tactical Opportunities**: Checks, captures, forks, pins

## Integration Examples

### Arena Integration

```python
class SmartArena:
    def __init__(self):
        self.bot_filter = BotFilter()
        self.available_bots = ["AggressiveBot", "FortifyBot", "DynamicBot"]
    
    def select_bot_for_position(self, board):
        # Get top recommendation
        recommendations = self.bot_filter.get_recommended_bots(
            board, self.available_bots, top_n=1
        )
        
        if recommendations:
            return recommendations[0][0]  # Return bot name
        return "RandomBot"  # Fallback
```

### Tournament Integration

```python
def select_tournament_bot(board, bot_pool):
    bot_filter = BotFilter()
    
    # Analyze position and select appropriate bot
    position_analysis = bot_filter.position_analyzer.analyze_position(board)
    
    if position_analysis['game_phase'] == GamePhase.ENDGAME:
        criteria = create_endgame_filter()
    elif position_analysis['threats']:
        criteria = create_tactical_filter()
    else:
        criteria = create_positional_filter()
    
    filtered_bots = bot_filter.filter_bots(board, bot_pool, criteria)
    
    # Return best available bot
    recommendations = bot_filter.get_recommended_bots(board, filtered_bots, top_n=1)
    return recommendations[0][0] if recommendations else bot_pool[0]
```

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/test_bot_filter.py -v
```

Run the example demonstration:

```bash
python examples/bot_filter_demo.py
```

## Performance Considerations

- **Caching**: Position analysis results can be cached for repeated positions
- **Parallel Processing**: Multiple bot evaluations can be parallelized
- **Memory Usage**: Bot capability definitions are lightweight
- **Scalability**: System handles large bot pools efficiently

## Extension Points

### Custom Analyzers

```python
class CustomPositionAnalyzer(PositionAnalyzer):
    def analyze_position(self, board):
        base_analysis = super().analyze_position(board)
        
        # Add custom analysis
        base_analysis['custom_feature'] = self.analyze_custom_feature(board)
        
        return base_analysis
```

### Custom Scoring

```python
class CustomBotFilter(BotFilter):
    def _calculate_bot_score(self, bot_name, capability, position):
        base_score = super()._calculate_bot_score(bot_name, capability, position)
        
        # Add custom scoring logic
        if self.custom_condition(bot_name, position):
            base_score += 0.1
        
        return base_score
```

## Configuration

### Environment Variables

```bash
# Optional pattern file location
PATTERN_FILE=/path/to/patterns.json

# Logging level
BOT_FILTER_LOG_LEVEL=INFO
```

### Configuration Files

```json
{
  "bot_filter": {
    "default_bots": ["DynamicBot", "RandomBot"],
    "scoring_weights": {
      "game_phase": 0.3,
      "material": 0.2,
      "tactical": 0.2,
      "positional": 0.3
    }
  }
}
```

This bot filtering system provides a comprehensive foundation for intelligent bot selection in chess applications, with extensive customization and integration capabilities.
