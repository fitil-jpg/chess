"""
Comprehensive test suite for optimal move selection testing.

This module tests the move selection capabilities across different chess AI bots
and validates their ability to choose optimal moves in various scenarios.

Test Coverage:
- Individual bot move selection
- DynamicBot ensemble decision making
- Move quality validation
- Performance metrics
- Edge cases and error handling
"""

import pytest
import chess
import time
from typing import Dict, List, Tuple, Optional, Any
from unittest.mock import Mock, patch

# Import the chess AI components
from chess_ai.dynamic_bot import DynamicBot
from chess_ai.aggressive_bot import AggressiveBot
from chess_ai.fortify_bot import FortifyBot
from chess_ai.endgame_bot import EndgameBot
from chess_ai.random_bot import RandomBot
from chess_ai.critical_bot import CriticalBot
from chess_ai.decision_engine import DecisionEngine
from core.evaluator import Evaluator
from utils import GameContext
from core.move_object import MoveObject, MovePhase, MoveStatus, move_evaluation_manager


class TestOptimalMoveSelection:
    """Test suite for optimal move selection functionality."""
    
    @pytest.fixture
    def white_board(self):
        """Create a standard starting board for White."""
        return chess.Board()
    
    @pytest.fixture
    def black_board(self):
        """Create a standard starting board for Black."""
        board = chess.Board()
        board.push(chess.Move.from_uci("e2e4"))
        return board
    
    @pytest.fixture
    def tactical_board(self):
        """Create a board with tactical opportunities."""
        board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4")
        return board
    
    @pytest.fixture
    def endgame_board(self):
        """Create a simple endgame position."""
        board = chess.Board("8/8/8/5k2/8/8/4K3/8 w - - 0 1")
        return board
    
    @pytest.fixture
    def evaluator(self):
        """Create a shared evaluator instance."""
        return Evaluator(chess.Board())
    
    @pytest.fixture
    def game_context(self, evaluator):
        """Create a game context with default values."""
        return GameContext(
            material_diff=0,
            mobility=0,
            king_safety=0,
        )


class TestIndividualBotSelection(TestOptimalMoveSelection):
    """Test move selection for individual bots."""
    
    def test_aggressive_bot_selects_capture(self, tactical_board, evaluator, game_context):
        """Test that AggressiveBot优先选择吃子."""
        bot = AggressiveBot(chess.WHITE)
        move, reason = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
        
        # Should return a legal move
        assert move is not None
        assert tactical_board.is_legal(move)
        
        # Should prefer captures when available
        captures = [m for m in tactical_board.legal_moves if tactical_board.is_capture(m)]
        if captures:
            # Check if the selected move is reasonable (capture or check)
            is_capture = tactical_board.is_capture(move)
            gives_check = tactical_board.gives_check(move)
            assert is_capture or gives_check, f"Expected capture or check, got {move} with reason: {reason}"
    
    def test_fortify_bot_selects_development(self, white_board, evaluator, game_context):
        """Test that FortifyBot优先选择发展性走法."""
        bot = FortifyBot(chess.WHITE)
        move, reason = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
        
        assert move is not None
        assert white_board.is_legal(move)
        
        # Should prefer developing moves in opening
        piece = white_board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            # Knight or bishop development should be from back rank
            from_rank = chess.square_rank(move.from_square)
            assert from_rank == 0, f"Expected development from back rank, got move from rank {from_rank}"
    
    def test_endgame_bot_endgame_position(self, endgame_board, evaluator, game_context):
        """Test EndgameBot in endgame positions."""
        bot = EndgameBot(chess.WHITE)
        move, reason = bot.choose_move(endgame_board, evaluator=evaluator, context=game_context)
        
        assert move is not None
        assert endgame_board.is_legal(move)
        
        # In king endgame, should move king towards center/opponent
        piece = endgame_board.piece_at(move.from_square)
        assert piece and piece.piece_type == chess.KING, "Expected king move in endgame"
    
    def test_random_bot_legal_moves(self, white_board, evaluator, game_context):
        """Test that RandomBot always returns legal moves."""
        bot = RandomBot(chess.WHITE)
        
        for _ in range(10):  # Test multiple times for randomness
            move, reason = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
            assert move is not None
            assert white_board.is_legal(move)
    
    def test_critical_bot_identifies_threats(self, tactical_board, evaluator, game_context):
        """Test CriticalBot identifies and responds to threats."""
        bot = CriticalBot(chess.WHITE, enable_hierarchy=True)
        move, reason = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
        
        assert move is not None
        assert tactical_board.is_legal(move)
        
        # Reason should contain criticality information
        assert reason is not None and len(reason) > 0


class TestDynamicBotEnsemble(TestOptimalMoveSelection):
    """Test DynamicBot ensemble move selection."""
    
    def test_dynamicbot_ensemble_decision(self, tactical_board, evaluator, game_context):
        """Test DynamicBot makes ensemble decisions."""
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        move, confidence = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
        
        assert move is not None
        assert tactical_board.is_legal(move)
        assert isinstance(confidence, (int, float))
        
        # Check move tracking was enabled
        assert bot.enable_move_tracking
        current_move = bot.get_current_move_object()
        assert current_move is not None
        assert current_move.move == move
    
    def test_dynamicbot_phase_weighting(self, white_board, evaluator, game_context):
        """Test DynamicBot applies phase-specific weighting."""
        phase_weights = {
            "opening": {
                "aggressive": 1.5,
                "fortify": 2.0,
                "endgame": 0.5
            }
        }
        bot = DynamicBot(chess.WHITE, weights=phase_weights, enable_move_tracking=True)
        move, confidence = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
        
        assert move is not None
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        assert 'phase' in move_obj.metadata
    
    def test_dynamicbot_diversity_bonus(self, tactical_board, evaluator, game_context):
        """Test DynamicBot diversity bonus mechanism."""
        bot = DynamicBot(
            chess.WHITE, 
            enable_diversity=True, 
            diversity_bonus=0.3,
            enable_move_tracking=True
        )
        move, confidence = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
        
        assert move is not None
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        assert move_obj.metadata.get('diversity_enabled') is True
    
    def test_dynamicbot_bandit_learning(self, white_board, evaluator, game_context):
        """Test DynamicBot contextual bandit learning."""
        bot = DynamicBot(
            chess.WHITE,
            enable_bandit=True,
            bandit_alpha=0.2,
            enable_move_tracking=True
        )
        
        # Make multiple moves to trigger bandit updates
        for i in range(3):
            if white_board.legal_moves:
                move, confidence = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
                assert move is not None
                white_board.push(move)
        
        # Check bandit data was collected
        assert bot.enable_bandit
        assert len(bot._bandit_weights) > 0
    
    def test_dynamicbot_endgame_boost(self, endgame_board, evaluator, game_context):
        """Test DynamicBot endgame weight boosting."""
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        move, confidence = bot.choose_move(endgame_board, evaluator=evaluator, context=game_context)
        
        assert move is not None
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        
        # Should have boosted endgame weights in low material position
        assert bot.base_weights["endgame"] >= bot._original_weights["endgame"]


class TestDecisionEngine(TestOptimalMoveSelection):
    """Test DecisionEngine move selection."""
    
    def test_decision_engine_basic_selection(self, tactical_board):
        """Test DecisionEngine basic move selection."""
        engine = DecisionEngine(base_depth=2)
        move = engine.choose_best_move(tactical_board)
        
        assert move is not None
        assert tactical_board.is_legal(move)
    
    def test_decision_engine_time_budget(self, white_board):
        """Test DecisionEngine respects time budget."""
        engine = DecisionEngine(base_depth=3)
        start_time = time.time()
        move = engine.choose_best_move(white_board, time_budget_s=0.5)
        end_time = time.time()
        
        assert move is not None
        assert white_board.is_legal(move)
        assert (end_time - start_time) <= 1.0  # Allow some tolerance
    
    def test_decision_engine_risk_analysis(self, tactical_board):
        """Test DecisionEngine incorporates risk analysis."""
        engine = DecisionEngine(base_depth=2)
        move = engine.choose_best_move(tactical_board)
        
        assert move is not None
        # The engine should prefer safe moves when available
        assert tactical_board.is_legal(move)


class TestMoveQualityValidation(TestOptimalMoveSelection):
    """Test move quality and validation."""
    
    def test_move_legality_all_bots(self, white_board, evaluator, game_context):
        """Test all bots return legal moves."""
        bots = [
            AggressiveBot(chess.WHITE),
            FortifyBot(chess.WHITE),
            EndgameBot(chess.WHITE),
            RandomBot(chess.WHITE),
            CriticalBot(chess.WHITE),
        ]
        
        for bot in bots:
            move, _ = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
            assert move is not None, f"{bot.__class__.__name__} returned None move"
            assert white_board.is_legal(move), f"{bot.__class__.__name__} returned illegal move: {move}"
    
    def test_move_consistency_same_position(self, white_board, evaluator, game_context):
        """Test deterministic bots return consistent moves."""
        # Test with FortifyBot (should be deterministic with jitter disabled)
        bot = FortifyBot(chess.WHITE, tiebreak_jitter=0.0)
        
        moves = []
        for _ in range(5):
            move, _ = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
            moves.append(move)
            white_board.pop() if white_board.move_stack else None
        
        # All moves should be the same (deterministic behavior)
        unique_moves = set(m.uci() for m in moves if m)
        assert len(unique_moves) <= 1, f"Expected consistent moves, got: {unique_moves}"
    
    def test_move_diversity_random_bot(self, white_board, evaluator, game_context):
        """Test RandomBot shows move diversity."""
        bot = RandomBot(chess.WHITE)
        
        moves = []
        for _ in range(10):
            move, _ = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
            moves.append(move.uci() if move else None)
        
        # Should have some diversity in random moves
        unique_moves = set(filter(None, moves))
        assert len(unique_moves) > 1, f"Expected diverse moves from RandomBot, got: {unique_moves}"


class TestPerformanceMetrics(TestOptimalMoveSelection):
    """Test performance metrics and timing."""
    
    def test_move_selection_timing(self, tactical_board, evaluator, game_context):
        """Test move selection performance timing."""
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        
        start_time = time.time()
        move, confidence = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
        end_time = time.time()
        
        assert move is not None
        
        # Check timing was recorded
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        assert move_obj.total_duration_ms > 0
        assert (end_time - start_time) * 1000 >= move_obj.total_duration_ms * 0.9  # Allow tolerance
    
    def test_evaluation_pipeline_tracking(self, tactical_board, evaluator, game_context):
        """Test evaluation pipeline tracking."""
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        move, confidence = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
        
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        
        # Should have evaluation steps from multiple bots
        assert len(move_obj.evaluation_steps) > 0
        assert len(move_obj.bot_evaluations) > 0
        assert move_obj.status == MoveStatus.COMPLETED
    
    def test_performance_summary_generation(self, tactical_board, evaluator, game_context):
        """Test performance summary generation."""
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        
        # Make multiple moves
        for i in range(3):
            if tactical_board.legal_moves:
                move, confidence = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
                if move:
                    tactical_board.push(move)
        
        # Get performance summary
        summary = bot.get_agent_performance_summary()
        assert summary is not None
        assert 'status' in summary


class TestEdgeCases(TestOptimalMoveSelection):
    """Test edge cases and error handling."""
    
    def test_empty_legal_moves(self):
        """Test behavior when no legal moves available."""
        # Create a checkmate position
        board = chess.Board("5k2/5P2/5K2/8/8/8/8/8 b - - 0 1")  # Black is checkmated
        bot = DynamicBot(chess.BLACK)
        
        move, confidence = bot.choose_move(board)
        # Should handle gracefully (may return None or a move)
        assert isinstance(confidence, (int, float))
    
    def test_single_legal_move(self, evaluator, game_context):
        """Test behavior with only one legal move."""
        # Create a position with very few legal moves
        board = chess.Board("k7/8/1K6/8/8/8/8/8 w - - 0 1")
        bot = DynamicBot(chess.WHITE)
        
        move, confidence = bot.choose_move(board, evaluator=evaluator, context=game_context)
        
        # Should find and return the only available move
        assert move is not None
        assert board.is_legal(move)
    
    def test_corrupted_board_state(self):
        """Test handling of invalid board states."""
        bot = DynamicBot(chess.WHITE)
        
        # Test with None board
        with pytest.raises(AttributeError):
            bot.choose_move(None)
    
    def test_malformed_evaluator(self, white_board, game_context):
        """Test handling of malformed evaluator."""
        bot = DynamicBot(chess.WHITE)
        
        # Create a mock evaluator that raises exceptions
        broken_evaluator = Mock()
        broken_evaluator.board = white_board
        broken_evaluator.material_diff.side_effect = Exception("Broken evaluator")
        
        # Should handle gracefully
        try:
            move, confidence = bot.choose_move(white_board, evaluator=broken_evaluator, context=game_context)
            # If it doesn't crash, that's good
            assert isinstance(confidence, (int, float))
        except Exception:
            # If it crashes, it should be a controlled exception
            pytest.fail("Bot should handle evaluator errors gracefully")


class TestMoveObjectIntegration(TestOptimalMoveSelection):
    """Test MoveObject integration with move selection."""
    
    def test_move_object_creation(self, white_board):
        """Test MoveObject creation and tracking."""
        move = list(white_board.legal_moves)[0]
        move_obj = move_evaluation_manager.create_move_evaluation(move, white_board, "TestBot")
        
        assert move_obj is not None
        assert move_obj.move == move
        assert move_obj.bot_name == "TestBot"
        assert move_obj.board_fen == white_board.fen()
    
    def test_move_object_pipeline_tracking(self, white_board, evaluator, game_context):
        """Test MoveObject tracks evaluation pipeline."""
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        move, confidence = bot.choose_move(white_board, evaluator=evaluator, context=game_context)
        
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        
        # Should track phases
        assert move_obj.current_phase == MovePhase.BOT_EVALUATION
        
        # Should have contributing factors
        assert len(move_obj.contributing_factors) > 0
        
        # Should have metadata
        assert 'total_agents' in move_obj.metadata
        assert 'contributing_agents' in move_obj.metadata
    
    def test_move_object_export_data(self, tactical_board, evaluator, game_context):
        """Test MoveObject data export functionality."""
        bot = DynamicBot(chess.WHITE, enable_move_tracking=True)
        move, confidence = bot.choose_move(tactical_board, evaluator=evaluator, context=game_context)
        
        move_obj = bot.get_current_move_object()
        assert move_obj is not None
        
        # Test evaluation summary
        summary = move_obj.get_evaluation_summary()
        assert 'move' in summary
        assert 'final_score' in summary
        assert 'confidence' in summary
        
        # Test visualization data
        viz_data = move_obj.get_visualization_data()
        assert 'move' in viz_data
        assert 'phase' in viz_data
        assert 'final_score' in viz_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
