#!/usr/bin/env python3
"""
Enhanced Guardrails Statistics Demo

This script demonstrates the comprehensive guardrails statistics
functionality added to the piece viewer widget.

Features demonstrated:
- Guardrails analysis summary display
- Individual move risk statistics
- Visual highlighting of risky moves
- Comprehensive statistics panel with safety rates
"""

import sys
import time
import chess
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import QTimer

# Import the enhanced widget and guardrails components
from ui.enhanced_heatmap_widget import EnhancedHeatmapWidget
from chess_ai.risk_analyzer import RiskAnalyzer
from chess_ai.guardrails import Guardrails


class GuardrailsDemoWindow(QMainWindow):
    """Demo window for enhanced guardrails statistics."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛡️ Enhanced Guardrails Statistics Demo")
        self.setGeometry(100, 100, 800, 900)
        
        # Create UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create the enhanced heatmap widget
        self.heatmap_widget = EnhancedHeatmapWidget()
        layout.addWidget(self.heatmap_widget)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.analyze_button = QPushButton("🔍 Analyze Position")
        self.analyze_button.clicked.connect(self.analyze_current_position)
        button_layout.addWidget(self.analyze_button)
        
        self.clear_button = QPushButton("🧹 Clear Visualization")
        self.clear_button.clicked.connect(self.clear_visualization)
        button_layout.addWidget(self.clear_button)
        
        self.next_position_button = QPushButton("⏭️ Next Position")
        self.next_position_button.clicked.connect(self.load_next_position)
        button_layout.addWidget(self.next_position_button)
        
        layout.addLayout(button_layout)
        
        # Initialize components
        self.risk_analyzer = RiskAnalyzer()
        self.guardrails = Guardrails()
        self.current_position_index = 0
        
        # Test positions (FEN strings with interesting tactical situations)
        self.test_positions = [
            # Starting position
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            
            # Position with tactical opportunities
            "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4",
            
            # Complex middlegame position
            "r2q1rk1/ppp2ppp/2n1bn2/2bp4/3NP3/2N1B3/PPP2PPP/R2QKB1R w KQ - 0 8",
            
            # Endgame position
            "8/8/8/5k2/5p2/5P2/5K2/8 w - - 0 50",
            
            # Position with hanging pieces
            "rnbqk2r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 0 4",
        ]
        
        # Load initial position
        self.load_next_position()
        
        # Setup timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def load_next_position(self):
        """Load the next test position."""
        if self.current_position_index < len(self.test_positions):
            fen = self.test_positions[self.current_position_index]
            board = chess.Board(fen)
            self.heatmap_widget.set_board(board)
            self.current_board = board
            self.current_position_index += 1
            print(f"📍 Loaded position {self.current_position_index}: {fen}")
        else:
            self.current_position_index = 0
            self.load_next_position()
    
    def analyze_current_position(self):
        """Perform comprehensive guardrails analysis of current position."""
        if not hasattr(self, 'current_board'):
            return
        
        print("🔍 Starting comprehensive guardrails analysis...")
        start_time = time.time()
        
        # Perform position analysis with risk analyzer
        analysis_summary = self.risk_analyzer.analyze_position(
            self.current_board, 
            depth=2,
            chosen_move=None,
            chosen_by_bot=False
        )
        
        # Collect individual move statistics
        move_stats = {}
        for move_stat in self.risk_analyzer.move_stats:
            move_stats[move_stat.move_uci] = move_stat
        
        # Update the widget with guardrails data
        self.heatmap_widget.set_guardrails_stats(analysis_summary)
        self.heatmap_widget.set_move_risk_stats(move_stats)
        
        analysis_time = (time.time() - start_time) * 1000
        print(f"✅ Analysis completed in {analysis_time:.2f}ms")
        print(f"   Total moves: {analysis_summary.total_moves_evaluated}")
        print(f"   Safe moves: {analysis_summary.safe_moves_found}")
        print(f"   Risky moves: {analysis_summary.risky_moves_rejected}")
        print(f"   Safety rate: {(analysis_summary.safe_moves_found / analysis_summary.total_moves_evaluated * 100):.1f}%")
    
    def clear_visualization(self):
        """Clear all visualization data."""
        self.heatmap_widget.clear_visualization()
        print("🧹 Visualization cleared")
    
    def update_statistics(self):
        """Periodic statistics update (simulates real-time analysis)."""
        if hasattr(self, 'current_board') and self.heatmap_widget.guardrails_stats is None:
            # Auto-analyze if no data exists
            self.analyze_current_position()


def main():
    """Run the guardrails demo."""
    app = QApplication(sys.argv)
    
    # Create and show the demo window
    window = GuardrailsDemoWindow()
    window.show()
    
    print("🛡️ Enhanced Guardrails Statistics Demo Started")
    print("=" * 50)
    print("Features:")
    print("• Comprehensive guardrails analysis display")
    print("• Individual move risk statistics")
    print("• Visual highlighting of risky moves (magenta borders)")
    print("• Safety rates and rejection reasons")
    print("• Real-time analysis updates")
    print("=" * 50)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
