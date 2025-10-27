#!/usr/bin/env python3
"""
Professional PySide6 Chess Tournament Application

A complete tournament system with:
- Real-time chess board visualization
- Interactive tournament controls
- Live statistics and standings
- Game replay functionality
- Professional Qt interface

Usage:
    python tournament_pyside.py
"""

import sys
import time
import threading
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# PySide6 imports
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                               QTableWidget, QTableWidgetItem, QComboBox, 
                               QSpinBox, QProgressBar, QTextEdit, QSplitter,
                               QGroupBox, QFrame, QScrollArea, QListWidget,
                               QListWidgetItem, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap, QIcon

# Chess imports
import chess
import chess.svg

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

class ChessBoardWidget(QWidget):
    """Custom chess board widget with piece visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.square_size = 60
        self.setFixedSize(8 * self.square_size, 8 * self.square_size)
        
        # Piece symbols
        self.piece_symbols = {
            'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
            'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'
        }
        
        # Colors
        self.light_square = QColor(240, 217, 181)
        self.dark_square = QColor(181, 136, 99)
        self.highlight = QColor(255, 255, 0, 100)
        
    def set_board(self, board: chess.Board):
        """Update the board state"""
        self.board = board
        self.update()
    
    def paintEvent(self, event):
        """Paint the chess board and pieces"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw squares
        for rank in range(8):
            for file in range(8):
                x = file * self.square_size
                y = (7 - rank) * self.square_size
                rect = QRect(x, y, self.square_size, self.square_size)
                
                # Alternate square colors
                if (rank + file) % 2 == 0:
                    painter.fillRect(rect, self.light_square)
                else:
                    painter.fillRect(rect, self.dark_square)
        
        # Draw pieces
        painter.setFont(QFont("Arial", 40))
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                piece = self.board.piece_at(square)
                if piece:
                    x = file * self.square_size + self.square_size // 2
                    y = rank * self.square_size + self.square_size // 2
                    painter.drawText(x - 20, y + 15, self.piece_symbols[piece.symbol()])
        
        # Draw board coordinates
        painter.setFont(QFont("Arial", 12))
        painter.setPen(QPen(Qt.black))
        for i in range(8):
            # Files (a-h)
            painter.drawText(i * self.square_size + 5, self.height() - 5, chr(97 + i))
            # Ranks (1-8)
            painter.drawText(5, (7 - i) * self.square_size + 15, str(i + 1))

class TournamentEngine(QThread):
    """Tournament engine running in separate thread"""
    
    game_started = Signal(dict)
    move_made = Signal(dict)
    game_finished = Signal(dict)
    tournament_finished = Signal(dict)
    progress_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.state = None
        self.stop_event = threading.Event()
        
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
        self.start()
    
    def run(self):
        """Main tournament loop"""
        try:
            if self.state.mode == "rr":
                self._run_round_robin()
            else:
                self._run_single_elimination()
        except Exception as e:
            print(f"Tournament error: {e}")
        finally:
            self.state.is_running = False
            self.tournament_finished.emit({'standings': self.state.standings})
    
    def _run_round_robin(self):
        """Run round-robin tournament"""
        agents = self.state.agents
        pairs = [(a, b) for i, a in enumerate(agents) for b in agents[i+1:]]
        
        for pair_idx, (a, b) in enumerate(pairs):
            if self.stop_event.is_set():
                break
                
            self.state.current_pair = (a, b)
            
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
                self.progress_updated.emit({
                    'completed': self.state.completed_games,
                    'total': self.state.total_games,
                    'current_pair': f"{a} vs {b}",
                    'standings': self.state.standings
                })
                
                time.sleep(0.1)  # Small delay for UI updates
    
    def _run_single_elimination(self):
        """Run single-elimination tournament"""
        current_round = self.state.agents.copy()
        round_num = 1
        
        while len(current_round) > 1:
            if self.stop_event.is_set():
                break
                
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
    
    def _play_match(self, a: str, b: str, round_num: int) -> str:
        """Play a match between two players"""
        self.state.current_pair = (a, b)
        
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
            time.sleep(0.1)
        
        # Determine winner
        if wins_a > wins_b:
            return a
        elif wins_b > wins_a:
            return b
        else:
            return a  # Tie - return first player
    
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
        self.game_started.emit({
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
                self.move_made.emit({
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
        self.game_finished.emit({
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
    
    def stop_tournament(self):
        """Stop the tournament"""
        self.stop_event.set()
        self.state.is_running = False

class TournamentMainWindow(QMainWindow):
    """Main tournament application window"""
    
    def __init__(self):
        super().__init__()
        self.tournament_engine = TournamentEngine()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("🏆 Chess AI Tournament - PySide6")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls and info
        left_panel = QVBoxLayout()
        
        # Tournament controls
        controls_group = QGroupBox("Tournament Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Agent selection
        agent_layout = QHBoxLayout()
        agent_layout.addWidget(QLabel("Agents:"))
        self.agent_combo = QComboBox()
        self.agent_combo.addItems(get_agent_names())
        self.agent_combo.setMaximumWidth(200)
        agent_layout.addWidget(self.agent_combo)
        controls_layout.addLayout(agent_layout)
        
        # Tournament settings
        settings_layout = QGridLayout()
        settings_layout.addWidget(QLabel("Mode:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Round Robin", "Single Elimination"])
        settings_layout.addWidget(self.mode_combo, 0, 1)
        
        settings_layout.addWidget(QLabel("Games per pair:"), 1, 0)
        self.games_spin = QSpinBox()
        self.games_spin.setRange(1, 7)
        self.games_spin.setValue(3)
        settings_layout.addWidget(self.games_spin, 1, 1)
        
        settings_layout.addWidget(QLabel("Time per move (s):"), 2, 0)
        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 300)
        self.time_spin.setValue(60)
        settings_layout.addWidget(self.time_spin, 2, 1)
        
        controls_layout.addLayout(settings_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Tournament")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)
        controls_layout.addLayout(button_layout)
        
        left_panel.addWidget(controls_group)
        
        # Progress info
        progress_group = QGroupBox("Tournament Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Ready to start")
        self.current_pair_label = QLabel("No active pair")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.current_pair_label)
        
        left_panel.addWidget(progress_group)
        
        # Standings table
        standings_group = QGroupBox("Standings")
        standings_layout = QVBoxLayout(standings_group)
        
        self.standings_table = QTableWidget()
        self.standings_table.setColumnCount(6)
        self.standings_table.setHorizontalHeaderLabels(["Rank", "Agent", "Points", "W", "D", "L"])
        self.standings_table.setMaximumHeight(200)
        standings_layout.addWidget(self.standings_table)
        
        left_panel.addWidget(standings_group)
        
        # Moves list
        moves_group = QGroupBox("Recent Moves")
        moves_layout = QVBoxLayout(moves_group)
        
        self.moves_list = QListWidget()
        self.moves_list.setMaximumHeight(150)
        moves_layout.addWidget(self.moves_list)
        
        left_panel.addWidget(moves_group)
        
        # Right panel - Chess board
        right_panel = QVBoxLayout()
        
        # Chess board
        board_group = QGroupBox("Chess Board")
        board_layout = QVBoxLayout(board_group)
        
        self.chess_board = ChessBoardWidget()
        board_layout.addWidget(self.chess_board, alignment=Qt.AlignCenter)
        
        # Game info
        self.game_info_label = QLabel("No active game")
        self.game_info_label.setAlignment(Qt.AlignCenter)
        board_layout.addWidget(self.game_info_label)
        
        right_panel.addWidget(board_group)
        
        # Add panels to main layout
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(400)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
    
    def connect_signals(self):
        """Connect signals and slots"""
        # Button connections
        self.start_btn.clicked.connect(self.start_tournament)
        self.pause_btn.clicked.connect(self.pause_tournament)
        self.stop_btn.clicked.connect(self.stop_tournament)
        
        # Tournament engine connections
        self.tournament_engine.game_started.connect(self.on_game_started)
        self.tournament_engine.move_made.connect(self.on_move_made)
        self.tournament_engine.game_finished.connect(self.on_game_finished)
        self.tournament_engine.tournament_finished.connect(self.on_tournament_finished)
        self.tournament_engine.progress_updated.connect(self.on_progress_updated)
    
    def start_tournament(self):
        """Start a new tournament"""
        agents = [self.agent_combo.currentText()]  # For now, single agent selection
        mode = "rr" if self.mode_combo.currentText() == "Round Robin" else "se"
        games_per_pair = self.games_spin.value()
        time_per_move = self.time_spin.value()
        
        # For demo, use multiple agents
        all_agents = get_agent_names()
        if len(all_agents) >= 2:
            agents = all_agents[:4]  # Use first 4 agents for demo
        
        self.tournament_engine.start_tournament(agents, mode, games_per_pair, time_per_move)
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_label.setText("Tournament running...")
    
    def pause_tournament(self):
        """Pause the tournament"""
        # Implementation for pause functionality
        pass
    
    def stop_tournament(self):
        """Stop the tournament"""
        self.tournament_engine.stop_tournament()
        
        # Update UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("Tournament stopped")
    
    def on_game_started(self, data):
        """Handle game started signal"""
        white = data['white']
        black = data['black']
        self.game_info_label.setText(f"Game: {white} (White) vs {black} (Black)")
        
        # Update board
        board = chess.Board()
        self.chess_board.set_board(board)
    
    def on_move_made(self, data):
        """Handle move made signal"""
        move = data['move']
        move_number = data['move_number']
        
        # Add move to list
        move_text = f"{move_number}. {move}"
        self.moves_list.addItem(move_text)
        self.moves_list.scrollToBottom()
        
        # Update board
        board = chess.Board(data['board_fen'])
        self.chess_board.set_board(board)
    
    def on_game_finished(self, data):
        """Handle game finished signal"""
        result = data['result']
        self.game_info_label.setText(f"Game finished: {result}")
        
        # Clear moves list
        self.moves_list.clear()
    
    def on_tournament_finished(self, data):
        """Handle tournament finished signal"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("Tournament finished")
        self.progress_bar.setValue(100)
        
        # Show final standings
        self.update_standings(data['standings'])
        
        QMessageBox.information(self, "Tournament Finished", "Tournament completed successfully!")
    
    def on_progress_updated(self, data):
        """Handle progress update signal"""
        completed = data['completed']
        total = data['total']
        current_pair = data['current_pair']
        
        self.progress_label.setText(f"Progress: {completed}/{total} games")
        self.progress_bar.setValue(int((completed / total) * 100))
        self.current_pair_label.setText(f"Current: {current_pair}")
        
        # Update standings
        if 'standings' in data:
            self.update_standings(data['standings'])
    
    def update_standings(self, standings):
        """Update the standings table"""
        if not standings:
            return
        
        # Sort by points
        sorted_standings = sorted(standings.items(), key=lambda x: x[1]['points'], reverse=True)
        
        self.standings_table.setRowCount(len(sorted_standings))
        
        for i, (agent, stats) in enumerate(sorted_standings):
            self.standings_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.standings_table.setItem(i, 1, QTableWidgetItem(agent))
            self.standings_table.setItem(i, 2, QTableWidgetItem(f"{stats['points']:.1f}"))
            self.standings_table.setItem(i, 3, QTableWidgetItem(str(stats['wins'])))
            self.standings_table.setItem(i, 4, QTableWidgetItem(str(stats['draws'])))
            self.standings_table.setItem(i, 5, QTableWidgetItem(str(stats['losses'])))

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = TournamentMainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()