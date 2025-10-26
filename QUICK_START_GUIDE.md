# Quick Start Guide - Enhanced Chess AI

## Getting Started in 5 Minutes

### Step 1: Run the Viewer

```bash
python pyside_viewer.py
```

### Step 2: Explore the Tabs

#### Main Board
- Watch the chess game play automatically
- Click "Авто" (Auto) to start
- Click "Пауза" (Pause) to pause

#### 📊 Статуси (Status) Tab
- Shows current module and features
- Displays ThreatMap statistics
- King safety coefficient

#### 📈 Usage Tab
- Dynamic usage charts for White and Black
- Usage timeline showing module usage per move
- **NEW: Method Status Pipeline** showing all evaluation methods

#### 🔥 Heatmaps Tab
- **NEW: Mini Board Widget** with overlay visualization
- Select heatmap piece from dropdown
- View heatmap statistics
- See all 4 gradient overlays in action

### Step 3: Watch the Mini Board

In the Heatmaps tab, you'll see:

1. **Red areas** = Heatmap intensities (where pieces like to move)
2. **Blue areas** = BSP zones (strategic board zones)
3. **Purple areas** = Tactical opportunities (minimax > 10%)
4. **Green pulsing cell** = Currently evaluating this square (animated!)

### Step 4: Check Method Status

In the Usage tab, scroll down to Method Status Pipeline:

- See all evaluation methods
- Check which are **🟢 ACTIVE** (apply to current position)
- View processing times
- Toggle "Show Only Active" to filter

### Step 5: Adjust Move Time

Edit `configs/move_timing.json`:

```json
{
  "timing": {
    "move_time_ms": 1000
  }
}
```

Save and reload the viewer.

---

## What to Look For

### COW Opening System (90% Frequency)

Watch the opening moves - you should see:
- e4 and d4 pawn advances (central control)
- Nf3 or Nc3 knight development
- Early castling preparation
- High frequency of COW patterns in usage stats

### Method Status Display

Look for these methods in the pipeline:
- **PatternResponder** - Pattern matching
- **WFCEngine** - Wave Function Collapse
- **BSPEngine** - Zone analysis
- **HeatmapEval** - Piece positioning
- **TacticalAnalyzer** - Tactical motifs
- **Guardrails** - Safety checks
- **Minimax** - Depth search

Methods marked **🟢 ACTIVE** are the ones that apply to the current board position.

### Guardrails Statistics

On the mini board, check the yellow panel:
- ✅ **Guardrails: PASSED** = Safe move
- ⚠️ **Guardrails: FAILED** = Risky move with warnings

---

## Common Actions

### Start Auto-Play
Click "▶ Авто" button

### Play 10 Games Automatically
Click "🎮 10 Игр" button

### Copy Move Notation
Click "⧉ SAN" for move list or "⧉ PGN" for full game

### Save Board Screenshot
Click "📷 PNG" to save with metadata

### Refresh ELO Ratings
Click "🔄 ELO" to reload ratings from file

---

## Keyboard Shortcuts

None currently - all interactions via mouse/buttons.

---

## Configuration Files

### Timing: `configs/move_timing.json`
Control all timing parameters:
- move_time_ms (default: 700)
- visualization delays
- animation speeds

### Module Colors: Built-in
Each module has a distinct color in the usage timeline.

### Heatmaps: `heatmaps/*.json`
Pre-generated heatmap data for each piece type.

---

## Troubleshooting

### Green Cell Not Animating?
Check `configs/move_timing.json`:
```json
{
  "visualization": {
    "animate_transitions": true,
    "highlight_current_cell": true
  }
}
```

### COW Opening Not Showing?
- Play more games to see frequency statistics
- Check usage timeline after several moves
- COW patterns should dominate opening phase

### Mini Board Not Updating?
- Ensure you are on the Heatmaps tab
- Check that auto-play is running
- Widget updates on each move

### Method Status Empty?
- Widget updates during move evaluation
- May appear empty between moves
- Start auto-play to see real-time updates

---

## Example Session

1. Launch viewer: `python pyside_viewer.py`
2. Go to Heatmaps tab
3. Click "▶ Авто" to start auto-play
4. Watch the mini board:
   - Red gradient shows piece movement preferences
   - Blue gradient shows zone control
   - Purple appears for strong tactical moves
   - Green cell pulses on current evaluation
5. Go to Usage tab
6. Scroll to Method Status Pipeline
7. Click "[Show Only Active]" to see only applicable methods
8. Watch as methods complete with ✅ icons
9. See processing times for each method

---

## Tips

1. **Watch the green cell animation** - it shows you exactly which square is being evaluated in real-time (50ms updates)

2. **Filter active methods** - use the "Show Only Active" toggle to see only methods that apply to the current position (e.g., opening patterns only apply in opening phase)

3. **Adjust timing for visualization** - increase `visualization_delay_ms` if animations are too fast to follow

4. **Check guardrails** - if a move fails guardrails, you'll see warnings about high-value hangs or blunders

5. **Monitor bot names** - the bot name changes to show which engine was primary for each move (e.g., "HybridBot > WFC")

6. **Use auto-play for testing** - the "🎮 10 Игр" button runs 10 games automatically, great for testing and statistics

---

## Advanced Usage

### Custom Patterns

Edit `chess_ai/wfc_engine.py` and add patterns in `add_opening_patterns()`:

```python
custom_pattern = ChessPattern(
    pattern_type=PatternType.OPENING,
    squares=(chess.C2, chess.C4),
    pieces=(chess.Piece(chess.PAWN, chess.WHITE),
            chess.Piece(chess.PAWN, chess.WHITE)),
    constraints=(("center_control", True),),
    frequency=0.8
)
self.add_pattern(custom_pattern)
```

### Adjust Evaluation Weights

Edit `core/move_object.py` in `calculate_final_score()`:

```python
weights = {
    'pattern': 0.20,  # Increased from 0.15
    'wfc': 0.15,      # Increased from 0.10
    'bsp': 0.10,
    'heatmap': 0.15,
    'tactical': 0.20,
    'positional': 0.10,
    'minimax': 0.10   # Decreased from 0.20
}
```

### Change Bot in Viewer

Edit `pyside_viewer.py`:

```python
WHITE_AGENT = "HybridBot"  # Use new hybrid bot
BLACK_AGENT = "StockfishBot"
```

---

## Next Steps

1. ✅ Read `ENHANCED_CHESS_AI_README.md` for detailed documentation
2. ✅ Experiment with timing configurations
3. ✅ Play games and watch the visualizations
4. ✅ Try different bot combinations
5. ✅ Adjust evaluation weights to your preference
6. ✅ Add custom patterns to WFC engine
7. ✅ Extend the pipeline with new evaluation methods

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review `ENHANCED_CHESS_AI_README.md`
3. Check `IMPLEMENTATION_SUMMARY.md` for technical details

---

Enjoy your enhanced chess AI system! 🎉
