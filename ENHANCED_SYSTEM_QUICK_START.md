# Enhanced Chess Pattern System - Quick Start Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Test the System
```bash
python test_enhanced_system.py
```

### 3. Run Demo
```bash
python demo_enhanced_system.py
```

### 4. Launch Interactive Viewer
```bash
python run_enhanced_viewer.py
```

## 🎯 Key Features Implemented

### ✅ Pattern Management
- **Individual JSON files** for each pattern (easy creation/deletion)
- **Advanced search and filtering** by type, piece, phase, evaluation
- **Pattern statistics** and analytics
- **Export/import** functionality

### ✅ Advanced Pattern Filtering
- **Relevance analysis** - identifies pieces that participate in patterns
- **Filtered FEN generation** - removes irrelevant pieces for clear visualization
- **Exchange pattern detection** - recognizes 2-3 move sequences as patterns
- **Complexity assessment** - categorizes patterns as simple/moderate/complex

### ✅ Enhanced DynamicBot
- **Pattern-based evaluation** - uses detected patterns in move selection
- **Tactical and positional analysis** - comprehensive position evaluation
- **Safety scoring** - considers king safety and piece security
- **Game phase awareness** - adapts strategy based on opening/midgame/endgame
- **Confidence-based selection** - chooses moves with highest confidence scores

### ✅ Interactive PySide Viewer
- **Real-time pattern detection** during gameplay
- **Pattern library management** with search and filtering
- **Game controls** - start/stop/reset/new game buttons
- **Bot configuration** - switch between different agents
- **Pattern visualization** - shows filtered patterns with relevant pieces only

## 📁 File Structure

```
chess_ai/
├── pattern_manager.py      # ✅ Pattern storage and management
├── pattern_filter.py       # ✅ Pattern filtering and analysis  
├── pattern_detector.py     # ✅ Pattern detection logic
├── enhanced_dynamic_bot.py # ✅ Enhanced bot implementation
└── pattern_storage.py      # Legacy (deprecated)

patterns/                   # ✅ Individual pattern JSON files
├── pattern_<uuid1>.json
├── pattern_<uuid2>.json
└── ...

enhanced_pyside_viewer.py   # ✅ Enhanced PySide viewer
run_enhanced_viewer.py      # ✅ Viewer launcher
test_enhanced_system.py     # ✅ System tests
demo_enhanced_system.py     # ✅ Demo script
```

## 🎮 Usage Examples

### Pattern Detection and Filtering
```python
from chess_ai.pattern_detector import PatternDetector
from chess_ai.pattern_filter import PatternFilter

# Detect patterns
detector = PatternDetector()
patterns = detector.detect_patterns(board, move, eval_before, eval_after)

# Filter irrelevant pieces
filter_system = PatternFilter()
result = filter_system.analyze_pattern_relevance(board, move, pattern_types)
filtered_fen = result["filtered_fen"]  # Only relevant pieces
```

### Pattern Management
```python
from chess_ai.pattern_manager import PatternManager

# Manage patterns
manager = PatternManager()
pattern_id = manager.add_pattern(chess_pattern)
patterns = manager.search_patterns(pattern_types=["fork", "pin"])
stats = manager.get_pattern_statistics()
```

### Enhanced Bot
```python
from chess_ai.enhanced_dynamic_bot import make_enhanced_dynamic_bot

# Create enhanced bot
bot = make_enhanced_dynamic_bot(chess.WHITE)
move = bot.choose_move(board)
```

## 🔧 Configuration

### Bot Settings
The Enhanced DynamicBot can be configured for different playing styles:

```python
bot = EnhancedDynamicBot(
    color=chess.WHITE,
    aggression_level=0.7,    # 0.0 = defensive, 1.0 = aggressive
    pattern_weight=0.4,      # Weight of pattern-based evaluation
    tactical_weight=0.3,     # Weight of tactical evaluation
    positional_weight=0.3    # Weight of positional evaluation
)
```

### Pattern Detection Settings
In the PySide viewer:
- **Auto-detect patterns**: Enable/disable during gameplay
- **Filter irrelevant pieces**: Show only pattern-relevant pieces
- **Complexity filter**: Filter by simple/moderate/complex

## 🧪 Testing

### Run All Tests
```bash
python test_enhanced_system.py
```

### Individual Component Tests
```python
# Test pattern detection
from chess_ai.pattern_detector import PatternDetector
detector = PatternDetector()
patterns = detector.detect_patterns(board, move, eval_before, eval_after)

# Test pattern filtering
from chess_ai.pattern_filter import PatternFilter
filter_system = PatternFilter()
result = filter_system.analyze_pattern_relevance(board, move, pattern_types)

# Test pattern management
from chess_ai.pattern_manager import PatternManager
manager = PatternManager()
pattern_id = manager.add_pattern(pattern)
```

## 🎯 Pattern JSON Structure

Each pattern is stored as an individual JSON file:

```json
{
  "id": "uuid-string",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": "e4",
  "pattern_types": ["tactical_moment", "opening"],
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

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Stockfish Not Found**
   ```bash
   export STOCKFISH_PATH="/path/to/stockfish"
   ```

3. **PySide6 Issues**
   ```bash
   pip install PySide6
   ```

4. **Pattern Detection Not Working**
   - Check that board position is valid
   - Ensure evaluation values are provided
   - Verify pattern types are recognized

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Performance Tips

1. **Use pattern filtering** to reduce memory usage
2. **Batch operations** when processing many patterns
3. **Clear unused patterns** from memory periodically
4. **Use indexes** for fast pattern searching

## 🔮 Next Steps

1. **Run the interactive viewer**: `python run_enhanced_viewer.py`
2. **Experiment with different bot configurations**
3. **Create custom patterns** using the pattern editor
4. **Analyze games** with pattern detection enabled
5. **Export patterns** for sharing or backup

## 📚 Additional Resources

- [Full Documentation](ENHANCED_PATTERN_SYSTEM_README.md)
- [API Reference](chess_ai/)
- [Pattern Examples](patterns/)
- [Test Suite](test_enhanced_system.py)

---

**Ready to start?** Run `python run_enhanced_viewer.py` to launch the interactive chess pattern system! 🎉