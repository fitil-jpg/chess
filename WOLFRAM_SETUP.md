# Wolfram Engine Setup Guide

This guide explains how to install and configure the Wolfram Engine for use with the chess AI project.

## Overview

The Wolfram Engine integration provides advanced mathematical analysis capabilities for chess position evaluation, including:

- Pattern recognition and matching
- Tactical sequence analysis
- Strategic position assessment
- Advanced mathematical modeling of chess positions

## Installation

### 1. Download Wolfram Engine

1. Visit the [Wolfram Engine download page](https://www.wolfram.com/engine/)
2. Sign up for a free Wolfram Engine account
3. Download the appropriate version for your operating system:
   - **Linux**: `.deb` package for Ubuntu/Debian or `.rpm` for Red Hat/CentOS
   - **macOS**: `.dmg` package
   - **Windows**: `.exe` installer

### 2. Install Wolfram Engine

#### Linux (Ubuntu/Debian)
```bash
# Install the .deb package
sudo dpkg -i wolfram-engine_*.deb

# Fix any dependency issues
sudo apt-get install -f

# Verify installation
wolframscript --version
```

#### Linux (Red Hat/CentOS/Fedora)
```bash
# Install the .rpm package
sudo rpm -i wolfram-engine-*.rpm

# Verify installation
wolframscript --version
```

#### macOS
1. Open the downloaded `.dmg` file
2. Run the installer package
3. Follow the installation wizard
4. Verify installation:
   ```bash
   wolframscript --version
   ```

#### Windows
1. Run the downloaded `.exe` installer
2. Follow the installation wizard
3. Add the Wolfram Engine installation directory to your PATH
4. Verify installation:
   ```cmd
   wolframscript --version
   ```

### 3. Verify Installation

After installation, verify that the Wolfram Engine is working:

```bash
# Test basic functionality
wolframscript -c "2+2"

# Test chess evaluation script
wolframscript -file chess_ai/wolfram_evaluation.wl --help
```

## Usage

### Basic WolframBot Usage

```python
from chess_ai.wolfram_bot import WolframBot
import chess

# Create a WolframBot instance
bot = WolframBot(
    color=chess.WHITE,
    evaluation_depth=3,
    use_pattern_analysis=True,
    use_tactical_analysis=True,
    use_strategic_analysis=True
)

# Use in a game
board = chess.Board()
move, confidence = bot.choose_move(board)
print(f"Best move: {move} (confidence: {confidence})")
```

### Heatmap Generation with Wolfram

```python
from utils.integration import generate_heatmaps

# Generate heatmaps using Wolfram Engine
fens = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
heatmaps = generate_heatmaps(
    fens, 
    use_wolfram=True,
    pattern_set="wolfram_analysis"
)
```

### Command Line Usage

```bash
# Generate heatmaps using Wolfram
python scripts/generate_heatmaps_from_runs.py --wolfram runs/

# Use Wolfram for position analysis
wolframscript -file chess_ai/wolfram_evaluation.wl --position-analysis position.json
```

## Configuration

### Environment Variables

You can configure Wolfram Engine behavior using environment variables:

```bash
# Set Wolfram Engine timeout (seconds)
export WOLFRAM_TIMEOUT=30

# Set Wolfram evaluation depth (1-5)
export WOLFRAM_DEPTH=3

# Enable debug output
export WOLFRAM_DEBUG=1
```

### Bot Configuration

The WolframBot can be configured with various analysis options:

```python
bot = WolframBot(
    color=chess.WHITE,
    evaluation_depth=4,              # Analysis depth (1-5)
    use_pattern_analysis=True,       # Enable pattern recognition
    use_tactical_analysis=True,      # Enable tactical analysis
    use_strategic_analysis=True,     # Enable strategic analysis
    confidence_threshold=0.7         # Minimum confidence for moves
)
```

## Troubleshooting

### Common Issues

1. **"wolframscript not found"**
   - Ensure Wolfram Engine is installed
   - Check that `wolframscript` is in your PATH
   - Try running `which wolframscript` to verify location

2. **"Wolfram Engine verification timed out"**
   - Increase timeout: `export WOLFRAM_TIMEOUT=60`
   - Check system resources (CPU/memory)
   - Verify Wolfram Engine is not already running

3. **"Wolfram script failed"**
   - Check script syntax: `wolframscript -file chess_ai/wolfram_evaluation.wl --help`
   - Verify input JSON format
   - Check file permissions

4. **"Permission denied"**
   - Ensure script files are executable: `chmod +x chess_ai/wolfram_evaluation.wl`
   - Check file ownership and permissions

### Debug Mode

Enable debug mode to see detailed Wolfram Engine output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

bot = WolframBot(chess.WHITE)
move, confidence = bot.choose_move(board, debug=True)
```

### Performance Optimization

For better performance:

1. **Increase evaluation depth gradually** (start with 2-3)
2. **Disable unused analysis types** if not needed
3. **Use appropriate confidence thresholds** to avoid over-analysis
4. **Monitor system resources** during analysis

## Advanced Usage

### Custom Wolfram Scripts

You can create custom Wolfram scripts for specialized analysis:

```wolfram
(* Custom analysis script *)
Begin["`CustomAnalysis`"];

customEvaluation[board_List] := Module[{score},
    (* Your custom evaluation logic here *)
    score = 0;
    (* ... *)
    score
];

End[];
```

### Integration with Other Bots

WolframBot can be integrated with the DynamicBot ensemble:

```python
from chess_ai.dynamic_bot import DynamicBot

bot = DynamicBot(
    color=chess.WHITE,
    weights={
        "wolfram": 1.5,      # WolframBot weight
        "aggressive": 1.0,   # Other bot weights
        "fortify": 0.8
    }
)
```

## Support

For issues related to:

- **Wolfram Engine installation**: Contact Wolfram Support
- **Chess AI integration**: Check the project's GitHub issues
- **Script errors**: Review the Wolfram Language documentation

## License

Note that Wolfram Engine has its own license terms. Please review the Wolfram Engine license agreement during installation.