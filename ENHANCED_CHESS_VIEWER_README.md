# Enhanced Chess Viewer - Move Evaluation & Pattern Analysis

## Overview

The Enhanced Chess Viewer is a comprehensive chess analysis tool that integrates multiple AI systems for move evaluation, pattern recognition, and visualization. It provides real-time analysis of chess positions using Wave Function Collapse (WFC), Binary Space Partitioning (BSP), guardrails, and pattern matching systems.

## Features

### 🎯 Move Evaluation System
- **Comprehensive Move Object**: Tracks all evaluation stages and results
- **Multi-Stage Analysis**: Pattern matching, WFC analysis, BSP analysis, guardrails, tactical, and positional evaluation
- **Real-time Processing**: Background thread evaluation to prevent UI blocking
- **Detailed Logging**: Complete audit trail of all evaluation decisions

### 🔍 Pattern Recognition
- **COW Opening Patterns**: Specialized opening pattern recognition
- **Tactical Patterns**: Fork, pin, skewer, discovered attack, and deflection patterns
- **Endgame Patterns**: King centralization and pawn promotion patterns
- **Pattern Responder**: Flexible pattern matching system with confidence scoring

### 🧠 AI Engines Integration
- **WFC Engine**: Wave Function Collapse for pattern generation and analysis
- **BSP Engine**: Binary Space Partitioning for spatial zone analysis
- **Guardrails**: Tactical safety checks and move validation
- **Bot Tracking**: Integration with existing chess AI bots

### 🎨 Visualization
- **Mini Chess Board**: Real-time pattern visualization with color-coded zones
- **Heatmap Display**: Interactive heatmap visualization for different piece types
- **Zone Overlays**: WFC zones (blue), BSP zones (light blue), tactical zones (red)
- **Current Move Highlighting**: Green highlighting for current move analysis

### ⚙️ Interactive Controls
- **Auto Play**: Automatic game progression with configurable timing
- **Move Evaluation**: Manual move analysis and evaluation
- **Pattern Selection**: Choose between different pattern types and pieces
- **Timing Control**: Adjustable move delay (100-2000ms)

## Installation

### Prerequisites
```bash
pip install chess numpy PySide6
```

### Quick Start
```bash
python run_enhanced_viewer.py
```

## Architecture

### Core Components

#### 1. Move Evaluation System (`chess_ai/move_evaluation.py`)
- **MoveEvaluation**: Main evaluation object that tracks all analysis stages
- **MoveEvaluator**: Orchestrates evaluation through all engines
- **EvaluationResult**: Individual stage results with status and confidence
- **PatternMatch**: Pattern matching results with tactical/positional values

#### 2. Pattern Recognition (`chess_ai/pattern_responder.py`)
- **PatternResponder**: Loads and matches pattern templates
- **PatternTemplate**: Individual pattern definitions with FEN positions and actions
- **COW Opening Support**: Specialized opening pattern recognition

#### 3. WFC Engine (`chess_ai/wfc_engine.py`)
- **WFCEngine**: Wave Function Collapse algorithm for pattern generation
- **ChessPattern**: Pattern definitions with constraints and frequency
- **Move Analysis**: Compatibility checking and zone identification

#### 4. BSP Engine (`chess_ai/bsp_engine.py`)
- **BSPEngine**: Binary Space Partitioning for spatial analysis
- **BSPNode**: Tree nodes representing board zones
- **Zone Analysis**: Strategic zone classification and control calculation

#### 5. Guardrails (`chess_ai/guardrails.py`)
- **Guardrails**: Tactical safety checks for move validation
- **Risk Analysis**: Blunder detection and high-value piece protection
- **Move Filtering**: Prevents obviously bad moves

### UI Components

#### Enhanced PySide Viewer (`enhanced_pyside_viewer.py`)
- **Main Window**: Central application window with integrated controls
- **Mini Chess Board**: Pattern visualization with color-coded zones
- **Tab System**: Organized views for different analysis aspects
- **Real-time Updates**: Live visualization of analysis results

## Usage

### Basic Operation

1. **Start the Application**:
   ```bash
   python run_enhanced_viewer.py
   ```

2. **Auto Play Mode**:
   - Click "▶ Auto Play" to start automatic game progression
   - Use the delay slider to adjust move timing
   - Click "⏸ Pause" to stop automatic play

3. **Move Evaluation**:
   - Click "🔍 Evaluate Move" to analyze the current position
   - View detailed results in the "Move Evaluation" tab
   - See pattern matches and bot analysis results

4. **Pattern Visualization**:
   - Switch to the "🔥 Heatmaps" tab
   - Select different pieces and pattern types
   - Observe real-time pattern visualization on the mini board

### Advanced Features

#### Pattern Customization
- Edit `patterns/cow_opening.json` to add custom patterns
- Modify pattern confidence and frequency values
- Add new pattern types (tactical, positional, endgame)

#### Move Delay Configuration
- Adjust move delay from 100ms to 2000ms
- Real-time slider control
- Affects both auto-play and evaluation timing

#### Bot Integration
- View bot analysis results in the "Move Evaluation" tab
- Track which bots are applicable for current position
- See detailed reasoning from each bot

## Configuration

### Pattern Files
Patterns are stored in JSON format with the following structure:
```json
{
  "patterns": [
    {
      "situation": "FEN board position",
      "action": "UCI move or action",
      "pattern_type": "opening|tactical|endgame|positional",
      "confidence": 0.0-1.0,
      "frequency": 0.0-1.0,
      "description": "Human-readable description"
    }
  ]
}
```

### Move Delay Settings
- **Minimum**: 100ms (very fast)
- **Default**: 700ms (human-like)
- **Maximum**: 2000ms (slow analysis)

### Visualization Colors
- **WFC Zones**: Blue (100% opacity)
- **BSP Zones**: Light Blue (80% opacity)
- **Tactical Zones**: Red (120% opacity)
- **Current Move**: Green border

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   ```bash
   pip install --upgrade chess numpy PySide6
   ```

2. **Pattern Loading Errors**:
   - Check `patterns/` directory exists
   - Verify JSON syntax in pattern files
   - Check file permissions

3. **UI Not Responding**:
   - Move evaluation runs in background thread
   - Wait for current evaluation to complete
   - Check console for error messages

4. **Visualization Issues**:
   - Ensure mini board is properly initialized
   - Check pattern data format
   - Verify board state synchronization

### Debug Mode
Enable detailed logging by setting:
```python
logging.getLogger().setLevel(logging.DEBUG)
```

## Development

### Adding New Patterns
1. Create pattern template in `PatternTemplate` format
2. Add to pattern file or use `PatternResponder.add_pattern()`
3. Update visualization if needed

### Extending Engines
1. Implement new analysis methods in respective engine classes
2. Add evaluation stages to `EvaluationStage` enum
3. Update `MoveEvaluator` to include new stages

### Custom Visualizations
1. Extend `MiniChessBoard` class
2. Add new zone types and colors
3. Update `MoveEvaluation.get_visualization_data()`

## Performance Considerations

- **Move Evaluation**: Runs in background thread to prevent UI blocking
- **Pattern Matching**: Cached pattern templates for fast lookup
- **Visualization**: Optimized drawing with minimal redraws
- **Memory Usage**: Patterns and evaluations are cleaned up automatically

## Future Enhancements

- **Machine Learning Integration**: Neural network pattern recognition
- **Advanced Tactics**: More sophisticated tactical pattern detection
- **Opening Database**: Integration with chess opening databases
- **Export Features**: Save analysis results and visualizations
- **Multi-threading**: Parallel evaluation of multiple moves
- **Custom Bots**: Easy integration of new chess AI bots

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

## License

This project is part of the chess AI system and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review console output for error messages
3. Enable debug logging for detailed information
4. Create issue with detailed description and logs