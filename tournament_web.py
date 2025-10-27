#!/usr/bin/env python3
"""
Modern Web-Based Chess Tournament System

A complete tournament system with:
- Real-time web interface
- Live chess board visualization
- Tournament progress tracking
- Game replay functionality
- Statistics and analytics

Usage:
    python tournament_web.py --run --serve
    python tournament_web.py --serve  # Only serve UI for existing tournament
"""

import argparse
import json
import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import queue
import signal

# Flask imports
try:
    from flask import Flask, render_template, jsonify, request, Response
    from flask_socketio import SocketIO, emit
    import chess
    import chess.svg
    import chess.pgn
    HAVE_FLASK = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install flask flask-socketio python-chess")
    HAVE_FLASK = False

# Project imports
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from chess_ai.bot_agent import get_agent_names, make_agent
    from evaluation import evaluate
    from chess_ai.pattern_detector import PatternDetector
except ImportError as e:
    print(f"Missing chess AI modules: {e}")
    sys.exit(1)

@dataclass
class GameState:
    """Current state of a game being played"""
    game_id: str
    white: str
    black: str
    board: chess.Board
    moves: List[str]
    result: Optional[str] = None
    current_move: int = 0
    time_remaining_white: float = 0.0
    time_remaining_black: float = 0.0
    is_finished: bool = False

@dataclass
class TournamentState:
    """Current state of the tournament"""
    tournament_id: str
    mode: str  # 'rr' or 'se'
    agents: List[str]
    games_per_pair: int
    current_pair: Optional[tuple] = None
    current_game: Optional[GameState] = None
    standings: Dict[str, Dict[str, Any]] = None
    is_running: bool = False
    is_paused: bool = False
    total_games: int = 0
    completed_games: int = 0

class TournamentEngine:
    """Handles the actual tournament logic and game playing"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.state = None
        self.game_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker_thread = None
        
    def start_tournament(self, agents: List[str], mode: str = "rr", games_per_pair: int = 3, 
                        time_per_move: int = 60, max_plies: int = 600):
        """Start a new tournament"""
        tournament_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.state = TournamentState(
            tournament_id=tournament_id,
            mode=mode,
            agents=agents,
            games_per_pair=games_per_pair,
            standings={agent: {"wins": 0, "draws": 0, "losses": 0, "points": 0.0} for agent in agents}
        )
        
        # Calculate total games
        if mode == "rr":
            pairs = [(a, b) for i, a in enumerate(agents) for b in agents[i+1:]]
            self.state.total_games = len(pairs) * games_per_pair
        else:  # single elimination
            self.state.total_games = (len(agents) - 1) * games_per_pair
            
        self.state.is_running = True
        self.stop_event.clear()
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._run_tournament, daemon=True)
        self.worker_thread.start()
        
        # Emit tournament started
        self.socketio.emit('tournament_started', {
            'tournament_id': tournament_id,
            'agents': agents,
            'mode': mode,
            'total_games': self.state.total_games
        })
        
    def _run_tournament(self):
        """Main tournament loop"""
        try:
            if self.state.mode == "rr":
                self._run_round_robin()
            else:
                self._run_single_elimination()
        except Exception as e:
            print(f"Tournament error: {e}")
            self.socketio.emit('tournament_error', {'error': str(e)})
        finally:
            self.state.is_running = False
            self.socketio.emit('tournament_finished', {'standings': self.state.standings})
    
    def _run_round_robin(self):
        """Run round-robin tournament"""
        agents = self.state.agents
        pairs = [(a, b) for i, a in enumerate(agents) for b in agents[i+1:]]
        
        for pair_idx, (a, b) in enumerate(pairs):
            if self.stop_event.is_set():
                break
                
            self.state.current_pair = (a, b)
            self.socketio.emit('pair_started', {'white': a, 'black': b, 'pair': f"{a} vs {b}"})
            
            # Play series of games
            for game_idx in range(self.state.games_per_pair):
                if self.stop_event.is_set():
                    break
                    
                white, black = (a, b) if game_idx % 2 == 0 else (b, a)
                result = self._play_single_game(white, black, f"{a}_vs_{b}_{game_idx}")
                
                # Update standings
                self._update_standings(white, black, result)
                self.state.completed_games += 1
                
                # Emit progress update
                self.socketio.emit('game_completed', {
                    'white': white,
                    'black': black,
                    'result': result,
                    'standings': self.state.standings,
                    'progress': {
                        'completed': self.state.completed_games,
                        'total': self.state.total_games,
                        'percentage': (self.state.completed_games / self.state.total_games) * 100
                    }
                })
                
                time.sleep(0.5)  # Small delay for UI updates
    
    def _run_single_elimination(self):
        """Run single-elimination tournament"""
        current_round = self.state.agents.copy()
        round_num = 1
        
        while len(current_round) > 1:
            if self.stop_event.is_set():
                break
                
            self.socketio.emit('round_started', {'round': round_num, 'players': current_round})
            next_round = []
            
            # Pair up players
            for i in range(0, len(current_round), 2):
                if i + 1 < len(current_round):
                    a, b = current_round[i], current_round[i + 1]
                    winner = self._play_match(a, b, round_num)
                    next_round.append(winner)
                else:
                    # Odd number of players - bye
                    next_round.append(current_round[i])
            
            current_round = next_round
            round_num += 1
        
        if current_round:
            champion = current_round[0]
            self.socketio.emit('champion', {'champion': champion})
    
    def _play_match(self, a: str, b: str, round_num: int) -> str:
        """Play a match between two players"""
        self.state.current_pair = (a, b)
        self.socketio.emit('match_started', {'white': a, 'black': b, 'round': round_num})
        
        wins_a = 0
        wins_b = 0
        
        for game_idx in range(self.state.games_per_pair):
            if self.stop_event.is_set():
                break
                
            white, black = (a, b) if game_idx % 2 == 0 else (b, a)
            result = self._play_single_game(white, black, f"round_{round_num}_{a}_vs_{b}_{game_idx}")
            
            if result == "1-0":
                if white == a:
                    wins_a += 1
                else:
                    wins_b += 1
            elif result == "0-1":
                if white == a:
                    wins_b += 1
                else:
                    wins_a += 1
            
            self.state.completed_games += 1
            
            # Emit match progress
            self.socketio.emit('match_progress', {
                'white': white,
                'black': black,
                'result': result,
                'wins_a': wins_a,
                'wins_b': wins_b,
                'game': game_idx + 1,
                'total_games': self.state.games_per_pair
            })
            
            time.sleep(0.5)
        
        # Determine winner
        if wins_a > wins_b:
            return a
        elif wins_b > wins_a:
            return b
        else:
            # Tie - return first player (could implement tiebreak)
            return a
    
    def _play_single_game(self, white: str, black: str, game_id: str) -> str:
        """Play a single game between two agents"""
        board = chess.Board()
        white_agent = make_agent(white, chess.WHITE)
        black_agent = make_agent(black, chess.BLACK)
        
        # Create game state for live updates
        game_state = GameState(
            game_id=game_id,
            white=white,
            black=black,
            board=board,
            moves=[]
        )
        
        self.state.current_game = game_state
        
        # Emit game started
        self.socketio.emit('game_started', {
            'game_id': game_id,
            'white': white,
            'black': black,
            'board_fen': board.fen()
        })
        
        move_count = 0
        while not board.is_game_over() and move_count < 600:  # Max 600 moves
            if self.stop_event.is_set():
                break
                
            # Get current player
            is_white_turn = board.turn == chess.WHITE
            agent = white_agent if is_white_turn else black_agent
            
            # Get move from agent
            try:
                move = agent.choose_move(board)
                if move is None or not board.is_legal(move):
                    # Illegal move - opponent wins
                    result = "0-1" if is_white_turn else "1-0"
                    break
                
                # Make move
                board.push(move)
                move_count += 1
                game_state.moves.append(move.uci())
                game_state.current_move = move_count
                
                # Emit move update
                self.socketio.emit('move_made', {
                    'game_id': game_id,
                    'move': move.uci(),
                    'move_number': move_count,
                    'board_fen': board.fen(),
                    'is_white_turn': not is_white_turn  # Next to move
                })
                
                time.sleep(0.1)  # Small delay for UI updates
                
            except Exception as e:
                print(f"Agent error: {e}")
                result = "0-1" if is_white_turn else "1-0"
                break
        
        # Determine result
        if board.is_game_over():
            result = board.result()
        else:
            result = "1/2-1/2"  # Draw by move limit
        
        game_state.result = result
        game_state.is_finished = True
        
        # Emit game finished
        self.socketio.emit('game_finished', {
            'game_id': game_id,
            'result': result,
            'moves': game_state.moves,
            'move_count': move_count
        })
        
        return result
    
    def _update_standings(self, white: str, black: str, result: str):
        """Update tournament standings"""
        if result == "1-0":
            self.state.standings[white]["wins"] += 1
            self.state.standings[white]["points"] += 1.0
            self.state.standings[black]["losses"] += 1
        elif result == "0-1":
            self.state.standings[black]["wins"] += 1
            self.state.standings[black]["points"] += 1.0
            self.state.standings[white]["losses"] += 1
        else:  # Draw
            self.state.standings[white]["draws"] += 1
            self.state.standings[white]["points"] += 0.5
            self.state.standings[black]["draws"] += 1
            self.state.standings[black]["points"] += 0.5
    
    def pause_tournament(self):
        """Pause the tournament"""
        self.state.is_paused = True
        self.socketio.emit('tournament_paused')
    
    def resume_tournament(self):
        """Resume the tournament"""
        self.state.is_paused = False
        self.socketio.emit('tournament_resumed')
    
    def stop_tournament(self):
        """Stop the tournament"""
        self.stop_event.set()
        self.state.is_running = False
        self.socketio.emit('tournament_stopped')

def create_app():
    """Create Flask application with SocketIO"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chess_tournament_secret_key'
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize tournament engine
    tournament_engine = TournamentEngine(socketio)
    
    @app.route('/')
    def index():
        return render_template('tournament.html')
    
    @app.route('/api/agents')
    def api_agents():
        return jsonify({'agents': get_agent_names()})
    
    @app.route('/api/state')
    def api_state():
        if tournament_engine.state:
            return jsonify({
                'tournament_id': tournament_engine.state.tournament_id,
                'is_running': tournament_engine.state.is_running,
                'is_paused': tournament_engine.state.is_paused,
                'standings': tournament_engine.state.standings,
                'current_pair': tournament_engine.state.current_pair,
                'progress': {
                    'completed': tournament_engine.state.completed_games,
                    'total': tournament_engine.state.total_games
                }
            })
        return jsonify({'is_running': False})
    
    @socketio.on('start_tournament')
    def handle_start_tournament(data):
        agents = data.get('agents', [])
        mode = data.get('mode', 'rr')
        games_per_pair = data.get('games_per_pair', 3)
        time_per_move = data.get('time_per_move', 60)
        
        if not agents:
            emit('error', {'message': 'No agents selected'})
            return
        
        tournament_engine.start_tournament(agents, mode, games_per_pair, time_per_move)
    
    @socketio.on('pause_tournament')
    def handle_pause_tournament():
        tournament_engine.pause_tournament()
    
    @socketio.on('resume_tournament')
    def handle_resume_tournament():
        tournament_engine.resume_tournament()
    
    @socketio.on('stop_tournament')
    def handle_stop_tournament():
        tournament_engine.stop_tournament()
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('connected', {'message': 'Connected to tournament server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    return app, socketio, tournament_engine

def main():
    parser = argparse.ArgumentParser(description='Modern Web-Based Chess Tournament System')
    parser.add_argument('--run', action='store_true', help='Start tournament engine')
    parser.add_argument('--serve', action='store_true', help='Start web server')
    parser.add_argument('--port', type=int, default=5000, help='Web server port')
    parser.add_argument('--host', default='0.0.0.0', help='Web server host')
    parser.add_argument('--agents', type=str, 
                       default='DynamicBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,RandomBot',
                       help='Comma-separated list of agents')
    parser.add_argument('--mode', choices=['rr', 'se'], default='rr', help='Tournament mode')
    parser.add_argument('--games', type=int, default=3, help='Games per pair')
    parser.add_argument('--time', type=int, default=60, help='Time per move (seconds)')
    
    args = parser.parse_args()
    
    if not HAVE_FLASK:
        print("Flask and dependencies not installed. Install with:")
        print("pip install flask flask-socketio python-chess")
        return 1
    
    if not args.run and not args.serve:
        print("Use --run to start tournament, --serve to start web server, or both")
        return 1
    
    app, socketio, tournament_engine = create_app()
    
    # Create templates directory and HTML template
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Write the HTML template
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chess Tournament Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chess.js/0.10.2/chess.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .controls { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .board-container { text-align: center; }
        .chess-board { display: inline-block; border: 2px solid #333; }
        .square { width: 50px; height: 50px; display: inline-block; position: relative; }
        .square.light { background: #f0d9b5; }
        .square.dark { background: #b58863; }
        .piece { font-size: 40px; line-height: 50px; cursor: pointer; }
        .standings { margin-top: 20px; }
        .standings table { width: 100%; border-collapse: collapse; }
        .standings th, .standings td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .standings th { background: #f8f9fa; }
        .progress-bar { width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: #4CAF50; transition: width 0.3s; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-danger { background: #dc3545; color: white; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .status.running { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.paused { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .status.stopped { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .moves-list { max-height: 300px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 4px; }
        .move-item { padding: 5px; border-bottom: 1px solid #e9ecef; }
        .game-info { background: #e9ecef; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
        @media (max-width: 768px) {
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 Chess AI Tournament Dashboard</h1>
            <p>Real-time tournament monitoring and analysis</p>
        </div>
        
        <div class="controls">
            <h3>Tournament Controls</h3>
            <div>
                <label>Agents:</label>
                <select id="agentSelect" multiple style="width: 300px; height: 100px;">
                    <!-- Populated by JavaScript -->
                </select>
            </div>
            <div style="margin-top: 10px;">
                <label>Mode:</label>
                <select id="modeSelect">
                    <option value="rr">Round Robin</option>
                    <option value="se">Single Elimination</option>
                </select>
                <label>Games per pair:</label>
                <input type="number" id="gamesInput" value="3" min="1" max="7">
                <label>Time per move (s):</label>
                <input type="number" id="timeInput" value="60" min="1" max="300">
            </div>
            <div style="margin-top: 10px;">
                <button id="startBtn" class="btn btn-success">Start Tournament</button>
                <button id="pauseBtn" class="btn btn-warning" disabled>Pause</button>
                <button id="resumeBtn" class="btn btn-primary" disabled>Resume</button>
                <button id="stopBtn" class="btn btn-danger" disabled>Stop</button>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Chess Board</h3>
                <div class="board-container">
                    <div id="chessBoard" class="chess-board"></div>
                </div>
                <div id="gameInfo" class="game-info" style="display: none;">
                    <div id="currentGame"></div>
                    <div id="gameResult"></div>
                </div>
            </div>
            
            <div class="card">
                <h3>Tournament Status</h3>
                <div id="status" class="status stopped">Tournament stopped</div>
                <div id="progress">
                    <div>Progress: <span id="progressText">0/0</span></div>
                    <div class="progress-bar">
                        <div id="progressFill" class="progress-fill" style="width: 0%"></div>
                    </div>
                </div>
                <div id="currentPair" style="margin-top: 10px;"></div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Standings</h3>
                <div id="standings" class="standings">
                    <p>No tournament running</p>
                </div>
            </div>
            
            <div class="card">
                <h3>Recent Moves</h3>
                <div id="movesList" class="moves-list">
                    <p>No moves yet</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let currentGame = null;
        let chess = new Chess();
        
        // DOM elements
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resumeBtn = document.getElementById('resumeBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusDiv = document.getElementById('status');
        const progressText = document.getElementById('progressText');
        const progressFill = document.getElementById('progressFill');
        const standingsDiv = document.getElementById('standings');
        const movesListDiv = document.getElementById('movesList');
        const chessBoardDiv = document.getElementById('chessBoard');
        const gameInfoDiv = document.getElementById('gameInfo');
        const currentGameDiv = document.getElementById('currentGame');
        const gameResultDiv = document.getElementById('gameResult');
        const currentPairDiv = document.getElementById('currentPair');
        
        // Load available agents
        fetch('/api/agents')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('agentSelect');
                data.agents.forEach(agent => {
                    const option = document.createElement('option');
                    option.value = agent;
                    option.textContent = agent;
                    option.selected = true; // Select all by default
                    select.appendChild(option);
                });
            });
        
        // Socket events
        socket.on('connected', (data) => {
            console.log('Connected to server:', data.message);
        });
        
        socket.on('tournament_started', (data) => {
            console.log('Tournament started:', data);
            updateStatus('running', 'Tournament running');
            updateButtons(true, false, false, true);
            updateProgress(0, data.total_games);
        });
        
        socket.on('tournament_finished', (data) => {
            console.log('Tournament finished:', data);
            updateStatus('stopped', 'Tournament finished');
            updateButtons(false, false, false, false);
            updateStandings(data.standings);
        });
        
        socket.on('tournament_paused', () => {
            updateStatus('paused', 'Tournament paused');
            updateButtons(false, false, true, true);
        });
        
        socket.on('tournament_resumed', () => {
            updateStatus('running', 'Tournament running');
            updateButtons(true, false, false, true);
        });
        
        socket.on('tournament_stopped', () => {
            updateStatus('stopped', 'Tournament stopped');
            updateButtons(false, false, false, false);
        });
        
        socket.on('game_started', (data) => {
            console.log('Game started:', data);
            currentGame = data;
            currentGameDiv.innerHTML = `<strong>${data.white}</strong> (White) vs <strong>${data.black}</strong> (Black)`;
            gameInfoDiv.style.display = 'block';
            gameResultDiv.innerHTML = '';
            chess.reset();
            updateBoard();
        });
        
        socket.on('move_made', (data) => {
            console.log('Move made:', data);
            if (currentGame && data.game_id === currentGame.game_id) {
                chess.move(data.move);
                updateBoard();
                addMoveToList(data.move, data.move_number);
            }
        });
        
        socket.on('game_finished', (data) => {
            console.log('Game finished:', data);
            if (currentGame && data.game_id === currentGame.game_id) {
                gameResultDiv.innerHTML = `<strong>Result: ${data.result}</strong>`;
                currentGame = null;
            }
        });
        
        socket.on('game_completed', (data) => {
            console.log('Game completed:', data);
            updateProgress(data.progress.completed, data.progress.total);
            updateStandings(data.standings);
        });
        
        socket.on('pair_started', (data) => {
            currentPairDiv.innerHTML = `<strong>Current Pair:</strong> ${data.pair}`;
        });
        
        socket.on('error', (data) => {
            console.error('Error:', data.message);
            alert('Error: ' + data.message);
        });
        
        // Button event listeners
        startBtn.addEventListener('click', startTournament);
        pauseBtn.addEventListener('click', () => socket.emit('pause_tournament'));
        resumeBtn.addEventListener('click', () => socket.emit('resume_tournament'));
        stopBtn.addEventListener('click', () => socket.emit('stop_tournament'));
        
        function startTournament() {
            const agents = Array.from(document.getElementById('agentSelect').selectedOptions).map(o => o.value);
            const mode = document.getElementById('modeSelect').value;
            const games = parseInt(document.getElementById('gamesInput').value);
            const time = parseInt(document.getElementById('timeInput').value);
            
            if (agents.length < 2) {
                alert('Please select at least 2 agents');
                return;
            }
            
            socket.emit('start_tournament', {
                agents: agents,
                mode: mode,
                games_per_pair: games,
                time_per_move: time
            });
        }
        
        function updateStatus(type, message) {
            statusDiv.className = `status ${type}`;
            statusDiv.textContent = message;
        }
        
        function updateButtons(start, pause, resume, stop) {
            startBtn.disabled = !start;
            pauseBtn.disabled = !pause;
            resumeBtn.disabled = !resume;
            stopBtn.disabled = !stop;
        }
        
        function updateProgress(completed, total) {
            progressText.textContent = `${completed}/${total}`;
            const percentage = total > 0 ? (completed / total) * 100 : 0;
            progressFill.style.width = `${percentage}%`;
        }
        
        function updateStandings(standings) {
            if (!standings) return;
            
            const sorted = Object.entries(standings)
                .sort((a, b) => b[1].points - a[1].points);
            
            let html = '<table><tr><th>Rank</th><th>Agent</th><th>Points</th><th>W</th><th>D</th><th>L</th></tr>';
            sorted.forEach(([agent, stats], index) => {
                html += `<tr>
                    <td>${index + 1}</td>
                    <td>${agent}</td>
                    <td>${stats.points}</td>
                    <td>${stats.wins}</td>
                    <td>${stats.draws}</td>
                    <td>${stats.losses}</td>
                </tr>`;
            });
            html += '</table>';
            standingsDiv.innerHTML = html;
        }
        
        function updateBoard() {
            const fen = chess.fen();
            chessBoardDiv.innerHTML = '';
            
            // Create board
            for (let rank = 7; rank >= 0; rank--) {
                for (let file = 0; file < 8; file++) {
                    const square = document.createElement('div');
                    square.className = `square ${(rank + file) % 2 === 0 ? 'light' : 'dark'}`;
                    square.dataset.square = String.fromCharCode(97 + file) + (rank + 1);
                    
                    const piece = chess.get(String.fromCharCode(97 + file) + (rank + 1));
                    if (piece) {
                        const pieceDiv = document.createElement('div');
                        pieceDiv.className = 'piece';
                        pieceDiv.textContent = getPieceSymbol(piece);
                        square.appendChild(pieceDiv);
                    }
                    
                    chessBoardDiv.appendChild(square);
                }
            }
        }
        
        function getPieceSymbol(piece) {
            const symbols = {
                'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
                'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'
            };
            return symbols[piece.type + (piece.color ? 'P' : 'p')] || '';
        }
        
        function addMoveToList(move, moveNumber) {
            if (movesListDiv.children.length === 0) {
                movesListDiv.innerHTML = '';
            }
            
            const moveDiv = document.createElement('div');
            moveDiv.className = 'move-item';
            moveDiv.textContent = `${moveNumber}. ${move}`;
            movesListDiv.appendChild(moveDiv);
            movesListDiv.scrollTop = movesListDiv.scrollHeight;
        }
        
        // Initialize
        updateBoard();
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'tournament.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Starting Chess Tournament Web Server on {args.host}:{args.port}")
    print("Open your browser and go to: http://localhost:5000")
    
    # Start the server
    socketio.run(app, host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()