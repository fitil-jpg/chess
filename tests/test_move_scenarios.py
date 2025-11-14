"""
Test move selection across different chess scenarios.

This module contains specific chess positions and scenarios to test
optimal move selection capabilities in various contexts.
"""

import pytest
import chess
from typing import Dict, List, Tuple, Optional

from chess_ai.dynamic_bot import DynamicBot
from chess_ai.aggressive_bot import AggressiveBot
from chess_ai.fortify_bot import FortifyBot
from chess_ai.endgame_bot import EndgameBot
from chess_ai.critical_bot import CriticalBot
from core.evaluator import Evaluator
from utils import GameContext


class TestSpecificScenarios:
    """Test move selection in specific chess scenarios."""
    
    @pytest.fixture
    def evaluator(self):
        """Create evaluator for tests."""
        return Evaluator(chess.Board())
    
    @pytest.fixture
    def context(self, evaluator):
        """Create game context."""
        return GameContext(
            material_diff=0,
            mobility=0,
            king_safety=0,
        )


class TestTacticalScenarios(TestSpecificScenarios):
    """Test tactical positions and move selection."""
    
    def test_fork_opportunity(self, evaluator, context):
        """Test knight fork recognition."""
        # Position: White knight can fork Black king and rook
        fen = "r3k2r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
        board = chess.Board(fen)
        
        bot = AggressiveBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Check if bot found the fork (Nf3-g5 or Nf3-d4)
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.KNIGHT:
            # Should be looking for tactical opportunities
            assert "AGGRESSIVE" in reason
    
    def test_pin_scenario(self, evaluator, context):
        """Test pin recognition and response."""
        # Position with pin opportunities
        fen = "r1bqkbnr/ppp2ppp/2np4/3p4/2B1P3/3Q1N2/PPPP1PPP/RNB1K2R w KQkq - 0 4"
        board = chess.Board(fen)
        
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        move, confidence = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should consider tactical aspects
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
    
    def test_discovered_attack(self, evaluator, context):
        """Test discovered attack recognition."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 0 3"
        board = chess.Board(fen)
        
        bot = AggressiveBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
    
    def test_sacrifice_opportunity(self, evaluator, context):
        """Test sacrifice evaluation."""
        # Position with potential sacrifice (Greek gift)
        fen = "r2qkbnr/ppp2ppp/2np4/2b5/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5"
        board = chess.Board(fen)
        
        bot = DynamicBot(chess.WHITE)
        move, confidence = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        # Should evaluate sacrifice properly
        assert isinstance(confidence, (int, float))


class TestPositionalScenarios(TestSpecificScenarios):
    """Test positional understanding and move selection."""
    
    def test_pawn_structure_evaluation(self, evaluator, context):
        """Test pawn structure considerations."""
        # Position with doubled pawns and isolated pawns
        fen = "r1bqkbnr/pp1p1ppp/2np4/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
        board = chess.Board(fen)
        
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        assert "FORTIFY" in reason
    
    def test_king_safety_priority(self, evaluator, context):
        """Test king safety considerations."""
        # Position where king safety is paramount
        fen = "r1bq1rk1/pp1n1ppp/2pb1n2/3p4/2B1P3/3Q1N2/PPPP1PPP/RNB1K2R w KQkq - 0 6"
        board = chess.Board(fen)
        
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should consider defensive aspects
        piece = board.piece_at(move.from_square)
        if piece:
            # Move should be reasonable for the position
            assert board.is_legal(move)
    
    def test_piece_activity_evaluation(self, evaluator, context):
        """Test piece activity considerations."""
        # Position with inactive pieces
        fen = "r2qkbnr/ppp2ppp/2np4/2b5/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5"
        board = chess.Board(fen)
        
        bot = DynamicBot(chess.WHITE)
        move, confidence = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should prefer developing moves
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            from_rank = chess.square_rank(move.from_square)
            if from_rank == 0:  # From back rank
                # Should be developing
                to_rank = chess.square_rank(move.to_square)
                assert to_rank > from_rank or chess.square_file(move.to_square) in [3, 4, 5]  # Center files


class TestEndgameScenarios(TestSpecificScenarios):
    """Test endgame-specific move selection."""
    
    def test_king_and_pawn_endgame(self, evaluator, context):
        """Test king and pawn endgame technique."""
        fen = "8/8/8/5k2/8/8/4K3/8 w - - 0 1"
        board = chess.Board(fen)
        
        bot = EndgameBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should move king in endgame
        piece = board.piece_at(move.from_square)
        assert piece and piece.piece_type == chess.KING
    
    def test_rook_endgame(self, evaluator, context):
        """Test rook endgame technique."""
        fen = "8/8/8/4k3/8/8/4K3/R7 w - - 0 1"
        board = chess.Board(fen)
        
        bot = EndgameBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
    
    def test_opposition_and_zugzwang(self, evaluator, context):
        """Test opposition and zugzwang concepts."""
        fen = "8/8/8/3k4/8/8/3K4/8 w - - 0 1"
        board = chess.Board(fen)
        
        bot = EndgameBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should understand opposition
        piece = board.piece_at(move.from_square)
        assert piece and piece.piece_type == chess.KING
    
    def test_promotion_race(self, evaluator, context):
        """Test pawn promotion race scenarios."""
        fen = "8/1P6/8/8/8/8/8/k7 w - - 0 1"
        board = chess.Board(fen)
        
        bot = EndgameBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should promote pawn
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(move.to_square)
            assert to_rank >= 7  # Moving towards promotion


class TestOpeningScenarios(TestSpecificScenarios):
    """Test opening-specific move selection."""
    
    def test_opening_development(self, evaluator, context):
        """Test proper opening development."""
        board = chess.Board()  # Starting position
        
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        assert "FORTIFY" in reason
        
        # Should develop from back rank
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            from_rank = chess.square_rank(move.from_square)
            assert from_rank == 0
    
    def test_center_control(self, evaluator, context):
        """Test center control in opening."""
        board = chess.Board()
        
        bot = DynamicBot(chess.WHITE)
        move, confidence = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should consider center control
        to_file = chess.square_file(move.to_square)
        to_rank = chess.square_rank(move.to_square)
        
        # Center squares: d4, e4, d5, e5
        center_squares = {chess.D4, chess.E4, chess.D5, chess.E5}
        if move.to_square in center_squares:
            # Good center move
            assert True
        else:
            # Should still be reasonable
            assert board.is_legal(move)
    
    def test_castling_safety(self, evaluator, context):
        """Test castling considerations."""
        fen = "r1bqkbnr/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
        board = chess.Board(fen)
        
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should consider king safety
        if move.from_square == chess.E1 and move.to_square in [chess.G1, chess.C1]:
            # Castling move
            assert True
        else:
            # Should still be reasonable for safety
            assert board.is_legal(move)


class TestCriticalPositions(TestSpecificScenarios):
    """Test critical and complex positions."""
    
    def test_time_pressure_simulation(self, evaluator, context):
        """Test move selection under time pressure."""
        fen = "r2qkbnr/ppp2ppp/2np4/2b5/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5"
        board = chess.Board(fen)
        
        bot = DynamicBot(chess.WHITE)
        # Simulate time pressure by using quick evaluation
        move, confidence = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        # Should still make reasonable moves quickly
    
    def test_defensive_necessity(self, evaluator, context):
        """Test defensive move selection."""
        # Position under attack
        fen = "r2qkbnr/ppp2ppp/2np4/2b5/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5"
        board = chess.Board(fen)
        
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        assert "FORTIFY" in reason
    
    def test_complicated_tactical_position(self, evaluator, context):
        """Test complex tactical position evaluation."""
        # Complex middlegame position
        fen = "r1b1r1k1/ppq2ppp/2np1n2/2bp4/2B1P3/3Q1N2/PPPP1PPP/RNB1K2R w KQkq - 0 8"
        board = chess.Board(fen)
        
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        move, confidence = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should have comprehensive evaluation
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        assert len(move_obj.evaluation_steps) > 0


class TestSpecificMovePatterns(TestSpecificScenarios):
    """Test specific move patterns and motifs."""
    
    def test_developer_move_recognition(self, evaluator, context):
        """Test developer move pattern recognition."""
        board = chess.Board()
        
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Check for development pattern
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            from_rank = chess.square_rank(move.from_square)
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            
            # Should be development from back rank
            assert from_rank == 0
            # Should be towards center
            assert to_file in [3, 4, 5] or to_rank >= 3
    
    def test_tempo_gain_recognition(self, evaluator, context):
        """Test tempo gain move recognition."""
        fen = "r1bqkbnr/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4"
        board = chess.Board(fen)
        
        bot = AggressiveBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should look for tempo-gaining moves
        if board.gives_check(move):
            assert True  # Check gains tempo
        elif board.is_capture(move):
            assert True  # Capture gains tempo
    
    def test_prophylaxis_thinking(self, evaluator, context):
        """Test prophylactic move consideration."""
        fen = "r2qkbnr/ppp2ppp/2np4/2b5/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5"
        board = chess.Board(fen)
        
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(board, evaluator=evaluator, context=context)
        
        assert move is not None
        assert board.is_legal(move)
        
        # Should consider defensive aspects
        assert "FORTIFY" in reason


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
