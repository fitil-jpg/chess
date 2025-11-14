#!/usr/bin/env python3
"""
Demo script for Decision Roadmap Visualization

Shows how to use the integrated MoveObject tracking with DynamicBot
to visualize the complete decision-making process.
"""

import chess
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our components
from chess_ai.dynamic_bot import DynamicBot
from ui.decision_roadmap import decision_roadmap
from core.evaluator import Evaluator
from utils import GameContext


def demo_console_roadmap():
    """Demo console-based roadmap visualization."""
    print("=" * 60)
    print("DECISION ROADMAP CONSOLE DEMO")
    print("=" * 60)
    
    # Create DynamicBot with tracking enabled
    bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
    
    # Create a test position
    board = chess.Board()
    board.push_san("e4")  # White's first move
    board.push_san("e5")  # Black's response
    board.push_san("Nf3")  # White develops knight
    
    print(f"Current position (FEN): {board.fen()}")
    print(f"Current player: {'White' if board.turn else 'Black'}")
    print()
    
    # Make a move with tracking
    print("Analyzing move with DynamicBot...")
    start_time = time.time()
    
    move, confidence = bot.choose_move(board, debug=True)
    
    end_time = time.time()
    duration = (end_time - start_time) * 1000
    
    print(f"Selected move: {board.san(move) if move else 'None'}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Analysis time: {duration:.1f}ms")
    print()
    
    # Show decision roadmap
    print("DECISION ROADMAP:")
    print("-" * 40)
    roadmap = bot.get_decision_roadmap()
    
    if "status" in roadmap and roadmap["status"] != "disabled":
        # Basic info
        move_info = roadmap.get("move_info", {})
        decision = roadmap.get("decision_process", {})
        
        print(f"Move: {move_info.get('move', 'N/A')}")
        print(f"Phase: {decision.get('current_phase', 'N/A')}")
        print(f"Status: {decision.get('status', 'N/A')}")
        print(f"Final Score: {decision.get('final_score', 0):.3f}")
        print(f"Confidence: {decision.get('confidence', 0):.3f}")
        print(f"Duration: {decision.get('total_duration_ms', 0):.1f}ms")
        print(f"Reason: {decision.get('primary_reason', 'N/A')}")
        print()
        
        # Agent contributions
        agents = roadmap.get("agent_contributions", {})
        if agents:
            print("AGENT CONTRIBUTIONS:")
            for agent, contrib in agents.items():
                print(f"  {agent}: conf={contrib.get('confidence', 0):.3f}, "
                      f"duration={contrib.get('duration_ms', 0):.1f}ms, "
                      f"status={contrib.get('status', 'N/A')}")
                if contrib.get('output_data', {}).get('move'):
                    print(f"    suggested: {contrib['output_data']['move']}")
        print()
        
        # Score breakdown
        scores = roadmap.get("score_breakdown", {})
        if scores:
            print("SCORE BREAKDOWN:")
            for component, value in scores.items():
                if value != 0:
                    print(f"  {component}: {value:.3f}")
        print()
        
        # Metadata
        metadata = roadmap.get("metadata", {})
        if metadata:
            print("METADATA:")
            for key, value in metadata.items():
                if not key.startswith('supporting_agent_'):
                    print(f"  {key}: {value}")
    
    print()
    
    # Show agent performance summary
    print("AGENT PERFORMANCE SUMMARY:")
    print("-" * 40)
    performance = bot.get_agent_performance_summary()
    
    if "status" not in performance:
        for agent, stats in performance.items():
            print(f"{agent}:")
            print(f"  Evaluations: {stats['total_evaluations']}")
            print(f"  Success Rate: {stats['success_rate']:.2%}")
            print(f"  Avg Confidence: {stats['avg_confidence']:.3f}")
            print(f"  Avg Duration: {stats['avg_duration_ms']:.1f}ms")
    
    print()
    
    # Export roadmap data
    print("Exporting decision data...")
    bot.export_decision_data("demo_roadmap.json", include_history=True)
    print("Data exported to demo_roadmap.json")
    
    return bot


def demo_multiple_moves():
    """Demo with multiple moves to show history tracking."""
    print("=" * 60)
    print("MULTIPLE MOVES HISTORY DEMO")
    print("=" * 60)
    
    bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
    board = chess.Board()
    
    moves = ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6"]
    
    for i, move_san in enumerate(moves):
        print(f"\nMove {i+1}: {move_san}")
        print("-" * 30)
        
        if i % 2 == 0:  # White's turn
            move, conf = bot.choose_move(board, debug=False)
            if move:
                actual_move = board.san(move)
                print(f"DynamicBot plays: {actual_move} (conf: {conf:.3f})")
                board.push(move)
        else:  # Black's turn - use the move from our list
            board.push_san(move_san)
        
        # Print summary after each pair of moves
        if i > 0 and i % 2 == 1:
            bot.print_decision_summary(-1)  # Show last move
    
    print(f"\nFinal position: {board.fen()}")
    
    # Show complete history
    print("\nCOMPLETE MOVE HISTORY:")
    print("-" * 40)
    decision_roadmap.update_from_manager()
    
    for idx, move_obj in enumerate(decision_roadmap.move_history):
        print(f"Move {idx+1}: {move_obj.san_notation} - "
              f"Score: {move_obj.final_score:.3f} - "
              f"Confidence: {move_obj.confidence:.3f}")
    
    return bot


def demo_real_time_updates():
    """Demo real-time updates during move analysis."""
    print("=" * 60)
    print("REAL-TIME UPDATES DEMO")
    print("=" * 60)
    
    bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    
    print("Starting real-time monitoring...")
    print("Making 3 moves for quick demo...")
    
    try:
        for move_num in range(3):
            print(f"\n--- Move {move_num + 1} ---")
            
            # Get real-time updates
            updates = bot.get_real_time_decision_updates()
            print(f"Status: {updates.get('status', 'unknown')}")
            
            # Make a move
            if board.turn == chess.WHITE:
                move, conf = bot.choose_move(board, debug=False)
                if move:
                    print(f">>> DynamicBot plays: {board.san(move)} (conf: {conf:.3f})")
                    board.push(move)
                    print(f"New position: {board.fen()}")
            else:
                # Simple black move - choose first legal move
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    move = legal_moves[0]
                    try:
                        san_move = board.san(move)
                        print(f">>> Black plays: {san_move}")
                        board.push(move)
                    except AssertionError:
                        # If move is not legal in current context, skip
                        print(f">>> Black move skipped (illegal move)")
                        break
            
            # Show final roadmap after each move
            roadmap = bot.get_decision_roadmap()
            if "decision_process" in roadmap:
                decision = roadmap["decision_process"]
                print(f"Final score: {decision.get('final_score', 0):.3f}")
                print(f"Duration: {decision.get('total_duration_ms', 0):.1f}ms")
            
            # Small delay between moves
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nDemo stopped by user")
    
    print("\nDemo completed!")
    return bot


def demo_gui_viewer():
    """Demo GUI decision viewer."""
    print("=" * 60)
    print("GUI DECISION VIEWER DEMO")
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.decision_viewer import create_decision_viewer, ViewerConfig
        
        # Check if QApplication already exists
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create viewer with custom config
        config = ViewerConfig(
            update_interval_ms=500,
            show_real_time=True,
            show_timing=True,
            show_weights=True,
            show_tactical=True
        )
        
        viewer = create_decision_viewer(config)
        if viewer:
            print("Decision viewer created successfully!")
            print("Close the window to continue with console demo...")
            viewer.show()
            
            # Start a bot to generate some data
            bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
            board = chess.Board()
            
            # Make a few moves to generate data
            for _ in range(3):
                move, _ = bot.choose_move(board, debug=False)
                if move:
                    board.push(move)
                time.sleep(1)  # Small delay to see updates
            
            # Run the application
            app.exec()
            return viewer
        else:
            print("Failed to create GUI viewer")
            
    except ImportError as e:
        print(f"GUI not available: {e}")
        print("Install PySide6 with: pip install PySide6")
    
    return None


def main():
    """Main demo function."""
    print("Chess AI Decision Roadmap Demo")
    print("Choose demo mode:")
    print("1. Console roadmap demo")
    print("2. Multiple moves history demo")
    print("3. Real-time updates demo")
    print("4. GUI viewer demo")
    print("5. Run all demos")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
    except KeyboardInterrupt:
        print("\nDemo cancelled")
        return
    
    if choice == "1":
        demo_console_roadmap()
    elif choice == "2":
        demo_multiple_moves()
    elif choice == "3":
        demo_real_time_updates()
    elif choice == "4":
        viewer = demo_gui_viewer()
        if viewer:
            input("Press Enter to exit...")
    elif choice == "5":
        print("\n=== Running Console Demo ===")
        demo_console_roadmap()
        
        print("\n=== Running Multiple Moves Demo ===")
        demo_multiple_moves()
        
        print("\n=== Running GUI Demo ===")
        viewer = demo_gui_viewer()
        if viewer:
            input("Press Enter to exit...")
    else:
        print("Invalid choice. Running console demo...")
        demo_console_roadmap()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()
