# 🏆 Web-Based Chess Tournament System

A modern, real-time web interface for running chess AI tournaments with live visualization and interactive controls.

## ✨ Features

- **Real-time Web Interface** - Live updates during tournament play
- **Interactive Chess Board** - Visual representation of current games
- **Live Statistics** - Real-time standings and progress tracking
- **Tournament Controls** - Start, pause, resume, and stop tournaments
- **Multiple Tournament Modes** - Round-robin and single-elimination
- **Game Replay** - View move sequences and game results
- **Responsive Design** - Works on desktop and mobile devices

## 🚀 Quick Start

### 1. Install Dependencies
```bash
./install_web_tournament.sh
```

### 2. Start the Tournament System
```bash
python3 run_tournament_web.py
```

### 3. Open Your Browser
Go to: http://localhost:5000

## 🎮 How to Use

1. **Select Agents** - Choose which chess bots to include in the tournament
2. **Configure Settings** - Set tournament mode, games per pair, and time limits
3. **Start Tournament** - Click "Start Tournament" to begin
4. **Watch Live** - See games play out in real-time on the chess board
5. **Monitor Progress** - Track standings and tournament progress

## ⚙️ Configuration

### Tournament Modes
- **Round Robin** - Every agent plays every other agent
- **Single Elimination** - Knockout tournament format

### Time Controls
- **Time per move** - Maximum seconds for each move (1-300 seconds)
- **Games per pair** - Number of games in each matchup (1-7)

### Available Agents
- DynamicBot
- FortifyBot  
- AggressiveBot
- EndgameBot
- KingValueBot
- RandomBot
- And more...

## 🔧 Advanced Usage

### Command Line Options
```bash
# Start web server only
python3 tournament_web.py --serve

# Start with specific port
python3 tournament_web.py --serve --port 8080

# Start with specific host
python3 tournament_web.py --serve --host 0.0.0.0
```

### API Endpoints
- `GET /api/agents` - List available chess agents
- `GET /api/state` - Get current tournament state
- WebSocket events for real-time updates

## 📊 Tournament Data

The system automatically saves:
- Tournament results and standings
- Individual game moves and outcomes
- Pattern detection data
- Performance statistics

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   python3 tournament_web.py --serve --port 5001
   ```

2. **Missing dependencies**
   ```bash
   pip3 install -r requirements_web_tournament.txt
   ```

3. **Agents not loading**
   - Check that chess AI modules are properly installed
   - Verify Python path includes the project directory

### Browser Compatibility
- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

## 🔄 Comparison with Original System

| Feature | Original `tournament_onefile.py` | New Web System |
|---------|----------------------------------|----------------|
| Interface | Command line only | Modern web UI |
| Visualization | Text output | Live chess board |
| Real-time Updates | No | Yes |
| Interactive Controls | Limited | Full control panel |
| Mobile Support | No | Yes |
| Game Replay | No | Yes |
| Statistics | Basic | Advanced |

## 🎯 Why Use the Web System?

1. **Better User Experience** - Visual interface instead of text output
2. **Real-time Monitoring** - See games as they happen
3. **Interactive Control** - Start, stop, pause tournaments easily
4. **Modern Interface** - Professional-looking dashboard
5. **Accessibility** - Works from any device with a web browser
6. **Educational Value** - Great for demonstrations and learning

## 🚀 Getting Started Now

```bash
# 1. Install
./install_web_tournament.sh

# 2. Run
python3 run_tournament_web.py

# 3. Open browser to http://localhost:5000
# 4. Select agents and start tournament!
```

Enjoy your chess tournaments! 🏆♟️