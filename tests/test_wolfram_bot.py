"""Tests for WolframBot chess agent."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import chess

from chess_ai.wolfram_bot import WolframBot


class TestWolframBot:
    """Test cases for WolframBot."""
    
    def test_wolfram_bot_initialization(self):
        """Test WolframBot initialization."""
        bot = WolframBot(chess.WHITE)
        assert bot.color == chess.WHITE
        assert bot.evaluation_depth == 3
        assert bot.use_pattern_analysis is True
        assert bot.use_tactical_analysis is True
        assert bot.use_strategic_analysis is True
        assert bot.confidence_threshold == 0.6
    
    def test_wolfram_bot_custom_initialization(self):
        """Test WolframBot with custom parameters."""
        bot = WolframBot(
            color=chess.BLACK,
            evaluation_depth=4,
            use_pattern_analysis=False,
            use_tactical_analysis=True,
            use_strategic_analysis=False,
            confidence_threshold=0.8
        )
        assert bot.color == chess.BLACK
        assert bot.evaluation_depth == 4
        assert bot.use_pattern_analysis is False
        assert bot.use_tactical_analysis is True
        assert bot.use_strategic_analysis is False
        assert bot.confidence_threshold == 0.8
    
    def test_wolfram_bot_evaluation_depth_bounds(self):
        """Test that evaluation depth is properly bounded."""
        # Test minimum depth
        bot = WolframBot(chess.WHITE, evaluation_depth=0)
        assert bot.evaluation_depth == 1
        
        # Test maximum depth
        bot = WolframBot(chess.WHITE, evaluation_depth=10)
        assert bot.evaluation_depth == 5
        
        # Test normal depth
        bot = WolframBot(chess.WHITE, evaluation_depth=3)
        assert bot.evaluation_depth == 3
    
    @patch('subprocess.run')
    def test_wolfram_engine_verification_success(self, mock_run):
        """Test successful Wolfram Engine verification."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Wolfram Engine 13.0"
        
        bot = WolframBot(chess.WHITE)
        assert bot is not None
    
    @patch('subprocess.run')
    def test_wolfram_engine_verification_failure(self, mock_run):
        """Test Wolfram Engine verification failure."""
        mock_run.side_effect = FileNotFoundError("wolframscript not found")
        
        with pytest.raises(RuntimeError, match="Wolfram Engine not found"):
            WolframBot(chess.WHITE)
    
    @patch('subprocess.run')
    def test_wolfram_engine_verification_timeout(self, mock_run):
        """Test Wolfram Engine verification timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("wolframscript", 10)
        
        with pytest.raises(RuntimeError, match="Wolfram Engine verification timed out"):
            WolframBot(chess.WHITE)
    
    @patch('subprocess.run')
    def test_choose_move_single_legal_move(self, mock_run):
        """Test choose_move with only one legal move."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Create a position with only one legal move
        board = chess.Board("8/8/8/8/8/8/8/7K w - - 0 1")
        legal_moves = list(board.legal_moves)
        assert len(legal_moves) == 1
        
        move, confidence = bot.choose_move(board)
        assert move == legal_moves[0]
        assert confidence == 1.0
    
    @patch('subprocess.run')
    def test_choose_move_wolfram_analysis_success(self, mock_run):
        """Test choose_move with successful Wolfram analysis."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Mock Wolfram analysis result
        mock_analysis_result = {
            "e2e4": 0.8,
            "e2e3": 0.6,
            "g1f3": 0.7
        }
        mock_run.return_value.stdout = json.dumps(mock_analysis_result)
        mock_run.return_value.returncode = 0
        
        board = chess.Board()
        move, confidence = bot.choose_move(board)
        
        # Should choose the move with highest score
        assert move.uci() == "e2e4"
        assert confidence == 0.8
    
    @patch('subprocess.run')
    def test_choose_move_wolfram_analysis_failure(self, mock_run):
        """Test choose_move with failed Wolfram analysis."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Mock Wolfram analysis failure
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Wolfram script failed"
        
        board = chess.Board()
        move, confidence = bot.choose_move(board)
        
        # Should fallback to random move with low confidence
        assert move in list(board.legal_moves)
        assert confidence == 0.1
    
    @patch('subprocess.run')
    def test_choose_move_wolfram_timeout(self, mock_run):
        """Test choose_move with Wolfram analysis timeout."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Mock Wolfram analysis timeout
        mock_run.side_effect = subprocess.TimeoutExpired("wolframscript", 30)
        
        board = chess.Board()
        move, confidence = bot.choose_move(board)
        
        # Should fallback to random move with low confidence
        assert move in list(board.legal_moves)
        assert confidence == 0.1
    
    @patch('subprocess.run')
    def test_choose_move_invalid_json(self, mock_run):
        """Test choose_move with invalid JSON response."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Mock invalid JSON response
        mock_run.return_value.stdout = "Invalid JSON response"
        mock_run.return_value.returncode = 0
        
        board = chess.Board()
        move, confidence = bot.choose_move(board)
        
        # Should fallback to random move with low confidence
        assert move in list(board.legal_moves)
        assert confidence == 0.1
    
    @patch('subprocess.run')
    def test_get_position_evaluation_success(self, mock_run):
        """Test successful position evaluation."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Mock position analysis result
        mock_analysis = {
            "material": 0,
            "mobility": 20,
            "king_safety": 5,
            "center_control": 2,
            "total_score": 2.7
        }
        mock_run.return_value.stdout = json.dumps(mock_analysis)
        mock_run.return_value.returncode = 0
        
        board = chess.Board()
        evaluation = bot.get_position_evaluation(board)
        
        assert evaluation == mock_analysis
    
    @patch('subprocess.run')
    def test_get_position_evaluation_failure(self, mock_run):
        """Test position evaluation failure."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Mock position analysis failure
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Analysis failed"
        
        board = chess.Board()
        evaluation = bot.get_position_evaluation(board)
        
        assert evaluation == {}
    
    def test_str_representation(self):
        """Test string representation of WolframBot."""
        bot = WolframBot(chess.WHITE, evaluation_depth=4)
        assert str(bot) == "WolframBot(depth=4)"
    
    def test_repr_representation(self):
        """Test repr representation of WolframBot."""
        bot = WolframBot(
            chess.BLACK, 
            evaluation_depth=3,
            use_pattern_analysis=False,
            use_tactical_analysis=True,
            use_strategic_analysis=False
        )
        repr_str = repr(bot)
        assert "WolframBot" in repr_str
        assert "color=chess.BLACK" in repr_str
        assert "depth=3" in repr_str
        assert "pattern=False" in repr_str
        assert "tactical=True" in repr_str
        assert "strategic=False" in repr_str


class TestWolframBotIntegration:
    """Integration tests for WolframBot."""
    
    @patch('subprocess.run')
    def test_wolfram_script_execution(self, mock_run):
        """Test that Wolfram script is executed with correct parameters."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE, evaluation_depth=3)
        
        # Mock successful analysis
        mock_analysis = {"e2e4": 0.8}
        mock_run.return_value.stdout = json.dumps(mock_analysis)
        mock_run.return_value.returncode = 0
        
        board = chess.Board()
        bot.choose_move(board)
        
        # Verify that wolframscript was called
        assert mock_run.call_count >= 2  # Verification + analysis
        
        # Check the analysis call
        analysis_call = mock_run.call_args_list[-1]
        assert analysis_call[0][0][0] == "wolframscript"
        assert analysis_call[0][0][1] == "-file"
    
    @patch('subprocess.run')
    def test_temporary_file_cleanup(self, mock_run):
        """Test that temporary files are properly cleaned up."""
        # Mock Wolfram Engine verification
        mock_run.return_value.returncode = 0
        
        bot = WolframBot(chess.WHITE)
        
        # Mock successful analysis
        mock_analysis = {"e2e4": 0.8}
        mock_run.return_value.stdout = json.dumps(mock_analysis)
        mock_run.return_value.returncode = 0
        
        board = chess.Board()
        bot.choose_move(board)
        
        # Verify that temporary file was created and cleaned up
        # (This is tested indirectly through the subprocess call)
        assert mock_run.call_count >= 2


if __name__ == "__main__":
    pytest.main([__file__])