# 🏆 Chess Bot Tournament Setup Guide

## 🚀 Quick Start Options

### Option 1: Simple Python Tournament (Recommended)
```bash
python3 run_simple_tournament.py
```
- No Docker required
- Runs directly with Python
- All bots participate
- Results saved automatically

### Option 2: Full Docker Tournament
```bash
./quick_tournament_start.sh
```
- Uses Docker containers
- More isolated environment
- Same functionality as Python version

### Option 3: Manual Python Tournament
```bash
python3 tournament_runner.py
```
- Direct execution of main tournament script
- Full control over environment variables

## 📋 What Happens During Tournament

### Tournament Format
- **Participants**: 8 chess bots (RandomBot, AggressiveBot, FortifyBot, EndgameBot, DynamicBot, KingValueBot, PieceMateBot, ChessBot)
- **Format**: Round-robin (each bot plays every other bot)
- **Matches**: Best of 3 games (Bo3)
- **Time Control**: 3 minutes per game
- **Total Matches**: 28 matches between all bot pairs

### Bot Descriptions
- **RandomBot**: Makes random legal moves with basic evaluation
- **AggressiveBot**: Seeks material gain and aggressive play
- **FortifyBot**: Focuses on defense and pawn structure
- **EndgameBot**: Specialized for endgame positions
- **DynamicBot**: Meta-agent combining multiple strategies
- **KingValueBot**: Evaluates based on king safety and piece values
- **PieceMateBot**: Attempts to trap enemy pieces
- **ChessBot**: Balanced general-purpose bot

## 📊 Results and Output

### Automatic Output Files
- `tournament_logs/tournament.log` - Detailed tournament logs
- `tournament_patterns/patterns.json` - Extracted game patterns
- `tournament_stats/final_results_[timestamp].json` - Complete results
- `tournament_stats/tournament_report_[timestamp].txt` - Human-readable report

### Real-time Monitoring
```bash
# Watch tournament progress
tail -f tournament_logs/tournament.log
```

## 🎮 Viewing Results

### GUI Pattern Viewer
```bash
python3 run_tournament_pattern_viewer.py
```
Features:
- Browse all tournament games
- Filter by bots and results
- View chess board positions
- Analyze move sequences
- Export data

### Command Line Results
```bash
# View latest report
cat tournament_stats/tournament_report_*.txt

# View detailed JSON results
ls tournament_stats/final_results_*.json
```

## 🔧 Customization

### Environment Variables
```bash
export GAMES_PER_MATCH=5      # Games per match (default: 3)
export TIME_PER_GAME=300      # Seconds per game (default: 180)
python3 tournament_runner.py
```

### Configuration File
Edit `tournament_config.json` to customize:
- Participating bots
- Tournament settings
- Pattern detection options
- Output directories

## 🧪 Testing

### Run System Tests
```bash
python3 test_tournament.py
```

### Test Individual Components
```bash
# Test tournament runner
python3 -c "from tournament_runner import TournamentRunner; print('✅ TournamentRunner OK')"

# Test pattern viewer
python3 -c "from tournament_pattern_viewer import TournamentPatternViewer; print('✅ PatternViewer OK')"
```

## 🐳 Docker Options (Optional)

### Build and Run
```bash
docker-compose -f docker-compose.tournament.yml up --build
```

### Clean Up
```bash
docker-compose -f docker-compose.tournament.yml down
docker system prune -a
```

## 📁 Directory Structure After Tournament
```
chess/
├── tournament_logs/
│   └── tournament.log              # Detailed logs
├── tournament_patterns/
│   └── patterns.json               # Game patterns
├── tournament_stats/
│   ├── final_results_20251027_155241.json  # Complete results
│   ├── tournament_report_20251027_155241.txt # Human report
│   └── matches.json                # Match-by-match data
└── [existing files...]
```

## 🆘 Troubleshooting

### Common Issues

1. **Python dependencies missing**
   ```bash
   pip install -r requirements.txt
   ```

2. **Permission errors**
   ```bash
   chmod +x run_simple_tournament.py
   chmod +x quick_tournament_start.sh
   ```

3. **Docker issues** (if using Docker)
   ```bash
   docker system prune -a
   docker-compose -f docker-compose.tournament.yml down
   ```

4. **Tournament hangs**
   - Check logs: `tail -f tournament_logs/tournament.log`
   - Reduce time per game: `export TIME_PER_GAME=60`

### Getting Help

1. Check the logs in `tournament_logs/tournament.log`
2. Run tests: `python3 test_tournament.py`
3. Review configuration: `cat tournament_config.json`
4. Check bot availability: `python3 -c "from chess_ai.bot_agent import get_agent_names; print(get_agent_names())"`

## 🎉 Success!

When you see "✅ Tournament completed successfully!", your tournament is done! Check the results in `tournament_stats/` and use the pattern viewer to analyze the games.

**Example Output:**
```
=== РЕЙТИНГ БОТОВ ===
1. DynamicBot:
   Матчи: 7W-0L-0D
   Игры: 21W-0L-0D

2. AggressiveBot:
   Матчи: 6W-1L-0D
   Игры: 18W-3L-0D

[...]
```

Happy tournament running! 🏆
