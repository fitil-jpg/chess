"""
Tests for Bot Filter Module

This module contains comprehensive tests for the bot filtering system,
including position analysis, pattern matching, and bot selection.
"""

import unittest
import chess
from chess_ai.bot_filter import (
    BotFilter, FilterCriteria, BotCapability, GamePhase, PositionAnalyzer,
    create_bot_filter, create_opening_filter, create_middlegame_filter,
    create_endgame_filter, create_tactical_filter, create_positional_filter
)


class TestPositionAnalyzer(unittest.TestCase):
    """Test cases for PositionAnalyzer."""
    
    def setUp(self):
        self.analyzer = PositionAnalyzer()
    
    def test_initial_position_analysis(self):
        """Test analysis of the initial chess position."""
        board = chess.Board()
        analysis = self.analyzer.analyze_position(board)
        
        self.assertEqual(analysis["piece_count"], 32)
        self.assertEqual(analysis["move_number"], 0)
        self.assertEqual(analysis["game_phase"], GamePhase.OPENING)
        self.assertEqual(analysis["material_advantage"], "equal")
        self.assertFalse(analysis["checks_available"])
        self.assertFalse(analysis["captures_available"])
    
    def test_endgame_position_analysis(self):
        """Test analysis of an endgame position."""
        # Simple endgame: kings and pawns only
        fen = "8/8/8/8/8/8/4k3/4K3 w - - 0 1"
        board = chess.Board(fen)
        analysis = self.analyzer.analyze_position(board)
        
        self.assertEqual(analysis["piece_count"], 2)
        self.assertEqual(analysis["game_phase"], GamePhase.ENDGAME)
        self.assertEqual(analysis["material_advantage"], "equal")
    
    def test_material_balance_calculation(self):
        """Test material balance calculation."""
        # Position with white having extra pawn
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1"
        board = chess.Board(fen)
        analysis = self.analyzer.analyze_position(board)
        
        self.assertEqual(analysis["material_balance"], -1.0)  # Black has extra pawn
        self.assertEqual(analysis["material_advantage"], "black")
    
    def test_center_control_analysis(self):
        """Test center control analysis."""
        board = chess.Board()
        analysis = self.analyzer.analyze_position(board)
        center_control = analysis["center_control"]
        
        # In initial position, both sides should have some center control
        self.assertIn("white_control", center_control)
        self.assertIn("black_control", center_control)
        self.assertIn("dominance", center_control)
    
    def test_king_safety_analysis(self):
        """Test king safety analysis."""
        board = chess.Board()
        analysis = self.analyzer.analyze_position(board)
        king_safety = analysis["king_safety"]
        
        # Both kings should be safe in initial position
        self.assertIn(chess.WHITE, king_safety)
        self.assertIn(chess.BLACK, king_safety)
        self.assertTrue(king_safety[chess.WHITE]["safe"])
        self.assertTrue(king_safety[chess.BLACK]["safe"])
    
    def test_tactical_threats_identification(self):
        """Test tactical threats identification."""
        # Position with tactical opportunities
        fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        board = chess.Board(fen)
        analysis = self.analyzer.analyze_position(board)
        
        self.assertIsInstance(analysis["threats"], list)
    
    def test_pawn_structure_analysis(self):
        """Test pawn structure analysis."""
        board = chess.Board()
        analysis = self.analyzer.analyze_position(board)
        pawn_structure = analysis["pawn_structure"]
        
        self.assertIn("doubled_pawns", pawn_structure)
        self.assertIn("isolated_pawns", pawn_structure)
        self.assertIn("quality", pawn_structure)
        self.assertIn(pawn_structure["quality"], ["good", "fair", "poor"])


class TestFilterCriteria(unittest.TestCase):
    """Test cases for FilterCriteria."""
    
    def test_default_criteria(self):
        """Test default filter criteria."""
        criteria = FilterCriteria()
        
        self.assertIsNone(criteria.piece_count_range)
        self.assertFalse(criteria.king_safety_required)
        self.assertEqual(criteria.required_patterns, [])
        self.assertEqual(criteria.excluded_patterns, [])
        self.assertIsNone(criteria.game_phase)
    
    def test_custom_criteria(self):
        """Test custom filter criteria."""
        criteria = FilterCriteria(
            piece_count_range=(20, 30),
            king_safety_required=True,
            game_phase=GamePhase.MIDDLEGAME,
            required_patterns=["fork", "pin"]
        )
        
        self.assertEqual(criteria.piece_count_range, (20, 30))
        self.assertTrue(criteria.king_safety_required)
        self.assertEqual(criteria.game_phase, GamePhase.MIDDLEGAME)
        self.assertEqual(criteria.required_patterns, ["fork", "pin"])


class TestBotCapability(unittest.TestCase):
    """Test cases for BotCapability."""
    
    def test_default_capability(self):
        """Test default bot capability."""
        capability = BotCapability(
            bot_name="TestBot",
            bot_class="TestBot"
        )
        
        self.assertEqual(capability.bot_name, "TestBot")
        self.assertEqual(capability.preferred_phases, [])
        self.assertEqual(capability.material_situations, [])
        self.assertFalse(capability.tactical_awareness)
        self.assertEqual(capability.aggressive_tendency, 0.0)
    
    def test_custom_capability(self):
        """Test custom bot capability."""
        capability = BotCapability(
            bot_name="AggressiveTestBot",
            bot_class="AggressiveTestBot",
            preferred_phases=[GamePhase.MIDDLEGAME],
            material_situations=["advantage"],
            tactical_awareness=True,
            aggressive_tendency=0.8
        )
        
        self.assertEqual(capability.bot_name, "AggressiveTestBot")
        self.assertEqual(capability.preferred_phases, [GamePhase.MIDDLEGAME])
        self.assertTrue(capability.tactical_awareness)
        self.assertEqual(capability.aggressive_tendency, 0.8)


class TestBotFilter(unittest.TestCase):
    """Test cases for BotFilter."""
    
    def setUp(self):
        self.filter = create_bot_filter()
        self.board = chess.Board()
    
    def test_initialization(self):
        """Test bot filter initialization."""
        self.assertIsInstance(self.filter.position_analyzer, PositionAnalyzer)
        self.assertIsInstance(self.filter.bot_capabilities, dict)
        self.assertGreater(len(self.filter.bot_capabilities), 0)
    
    def test_available_bots(self):
        """Test listing available bot capabilities."""
        available = self.filter.list_available_capabilities()
        
        self.assertIsInstance(available, list)
        self.assertIn("AggressiveBot", available)
        self.assertIn("FortifyBot", available)
        self.assertIn("DynamicBot", available)
    
    def test_get_bot_capability(self):
        """Test getting specific bot capability."""
        capability = self.filter.get_bot_capability("AggressiveBot")
        
        self.assertIsNotNone(capability)
        self.assertEqual(capability.bot_name, "AggressiveBot")
        self.assertTrue(capability.tactical_awareness)
        self.assertGreater(capability.aggressive_tendency, 0.5)
    
    def test_add_bot_capability(self):
        """Test adding custom bot capability."""
        custom_capability = BotCapability(
            bot_name="CustomTestBot",
            bot_class="CustomTestBot",
            preferred_phases=[GamePhase.ENDGAME],
            tactical_awareness=True
        )
        
        self.filter.add_bot_capability(custom_capability)
        retrieved = self.filter.get_bot_capability("CustomTestBot")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.bot_name, "CustomTestBot")
        self.assertEqual(retrieved.preferred_phases, [GamePhase.ENDGAME])
    
    def test_filter_bots_opening(self):
        """Test filtering bots for opening position."""
        opening_filter = create_opening_filter()
        available_bots = ["AggressiveBot", "FortifyBot", "EndgameBot", "DynamicBot", "RandomBot"]
        
        filtered = self.filter.filter_bots(self.board, available_bots, opening_filter)
        
        self.assertIsInstance(filtered, list)
        # DynamicBot and RandomBot should be available for opening
        self.assertIn("DynamicBot", filtered)
        self.assertIn("RandomBot", filtered)
    
    def test_filter_bots_endgame(self):
        """Test filtering bots for endgame position."""
        endgame_filter = create_endgame_filter()
        available_bots = ["AggressiveBot", "FortifyBot", "EndgameBot", "DynamicBot", "RandomBot"]
        
        # Use endgame position
        endgame_board = chess.Board("8/8/8/8/8/8/4k3/4K3 w - - 0 1")
        filtered = self.filter.filter_bots(endgame_board, available_bots, endgame_filter)
        
        self.assertIsInstance(filtered, list)
        # EndgameBot should be preferred
        self.assertIn("EndgameBot", filtered)
    
    def test_filter_bots_tactical(self):
        """Test filtering bots for tactical position."""
        tactical_filter = create_tactical_filter()
        available_bots = ["AggressiveBot", "FortifyBot", "TrapBot", "DynamicBot", "RandomBot"]
        
        # Use tactical position with checks available
        tactical_board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKB1R w KQkq - 0 2")
        filtered = self.filter.filter_bots(tactical_board, available_bots, tactical_filter)
        
        self.assertIsInstance(filtered, list)
        # Tactical bots should be preferred
        self.assertIn("AggressiveBot", filtered)
        self.assertIn("TrapBot", filtered)
    
    def test_get_recommended_bots(self):
        """Test getting recommended bots with scores."""
        available_bots = ["AggressiveBot", "FortifyBot", "EndgameBot", "DynamicBot", "RandomBot"]
        
        recommendations = self.filter.get_recommended_bots(self.board, available_bots, top_n=3)
        
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 3)
        
        for bot_name, score in recommendations:
            self.assertIsInstance(bot_name, str)
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        
        # Should be sorted by score (descending)
        if len(recommendations) > 1:
            self.assertGreaterEqual(recommendations[0][1], recommendations[1][1])
    
    def test_bot_scoring(self):
        """Test bot scoring calculation."""
        available_bots = ["DynamicBot", "RandomBot"]
        
        recommendations = self.filter.get_recommended_bots(self.board, available_bots)
        
        self.assertEqual(len(recommendations), 2)
        
        # DynamicBot should score well in opening position
        dynamic_score = next(score for name, score in recommendations if name == "DynamicBot")
        random_score = next(score for name, score in recommendations if name == "RandomBot")
        
        self.assertGreater(dynamic_score, 0.0)
        self.assertGreater(random_score, 0.0)
    
    def test_filter_with_nonexistent_bot(self):
        """Test filtering with non-existent bot names."""
        available_bots = ["NonExistentBot", "AnotherFakeBot"]
        
        filtered = self.filter.filter_bots(self.board, available_bots)
        
        self.assertEqual(len(filtered), 0)
    
    def test_filter_criteria_combinations(self):
        """Test complex filter criteria combinations."""
        complex_filter = FilterCriteria(
            game_phase=GamePhase.OPENING,
            piece_count_range=(30, 32),
            tactical_awareness=False
        )
        
        available_bots = ["AggressiveBot", "FortifyBot", "DynamicBot", "RandomBot"]
        filtered = self.filter.filter_bots(self.board, available_bots, complex_filter)
        
        # Should only include bots that match all criteria
        self.assertIsInstance(filtered, list)


class TestFilterFactories(unittest.TestCase):
    """Test cases for filter factory functions."""
    
    def test_create_opening_filter(self):
        """Test opening filter factory."""
        filter_criteria = create_opening_filter()
        
        self.assertEqual(filter_criteria.game_phase, GamePhase.OPENING)
        self.assertEqual(filter_criteria.move_number_range, (0, 15))
        self.assertEqual(filter_criteria.piece_count_range, (28, 32))
    
    def test_create_middlegame_filter(self):
        """Test middlegame filter factory."""
        filter_criteria = create_middlegame_filter()
        
        self.assertEqual(filter_criteria.game_phase, GamePhase.MIDDLEGAME)
        self.assertEqual(filter_criteria.move_number_range, (15, 35))
        self.assertEqual(filter_criteria.piece_count_range, (20, 28))
        self.assertTrue(filter_criteria.tactical_awareness)
    
    def test_create_endgame_filter(self):
        """Test endgame filter factory."""
        filter_criteria = create_endgame_filter()
        
        self.assertEqual(filter_criteria.game_phase, GamePhase.ENDGAME)
        self.assertEqual(filter_criteria.move_number_range, (35, 100))
        self.assertEqual(filter_criteria.piece_count_range, (10, 20))
        self.assertTrue(filter_criteria.king_safety_required)
    
    def test_create_tactical_filter(self):
        """Test tactical filter factory."""
        filter_criteria = create_tactical_filter()
        
        self.assertEqual(filter_criteria.pattern_types, ["tactical"])
        self.assertTrue(filter_criteria.checks_available)
        self.assertTrue(filter_criteria.captures_available)
        self.assertTrue(filter_criteria.threats_required)
    
    def test_create_positional_filter(self):
        """Test positional filter factory."""
        filter_criteria = create_positional_filter()
        
        self.assertEqual(filter_criteria.pattern_types, ["positional"])
        self.assertTrue(filter_criteria.center_control_required)
        self.assertTrue(filter_criteria.pawn_structure_required)
        self.assertTrue(filter_criteria.king_safety_required)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete filtering system."""
    
    def setUp(self):
        self.filter = create_bot_filter()
    
    def test_complete_filtering_workflow(self):
        """Test complete filtering workflow."""
        # Test different positions and filters
        test_cases = [
            {
                "board": chess.Board(),
                "filter": create_opening_filter(),
                "expected_bots": ["DynamicBot", "RandomBot"]
            },
            {
                "board": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
                "filter": create_positional_filter(),
                "expected_bots": ["DynamicBot"]
            }
        ]
        
        for case in test_cases:
            available_bots = ["AggressiveBot", "FortifyBot", "EndgameBot", "DynamicBot", "RandomBot"]
            filtered = self.filter.filter_bots(case["board"], available_bots, case["filter"])
            
            self.assertIsInstance(filtered, list)
            # At least some expected bots should be in the filtered list
            for expected_bot in case["expected_bots"]:
                if expected_bot in available_bots:
                    self.assertIn(expected_bot, filtered)
    
    def test_performance_with_large_bot_list(self):
        """Test performance with large number of bots."""
        # Create many test bots
        available_bots = []
        for i in range(100):
            bot_name = f"TestBot{i}"
            available_bots.append(bot_name)
            
            # Add capability for every 10th bot
            if i % 10 == 0:
                capability = BotCapability(
                    bot_name=bot_name,
                    bot_class=f"TestBot{i}",
                    preferred_phases=[GamePhase.OPENING]
                )
                self.filter.add_bot_capability(capability)
        
        # Test filtering
        opening_filter = create_opening_filter()
        filtered = self.filter.filter_bots(self.board, available_bots, opening_filter)
        
        # Should only include bots with matching capabilities
        self.assertLessEqual(len(filtered), 10)  # Only every 10th bot has opening preference
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty bot list
        filtered = self.filter.filter_bots(self.board, [])
        self.assertEqual(len(filtered), 0)
        
        # None criteria
        available_bots = ["DynamicBot", "RandomBot"]
        filtered = self.filter.filter_bots(self.board, available_bots, None)
        self.assertGreater(len(filtered), 0)
        
        # Invalid FEN (should handle gracefully)
        try:
            invalid_board = chess.Board("invalid_fen")
        except ValueError:
            # Expected to fail, test with empty board instead
            filtered = self.filter.filter_bots(self.board, available_bots)
            self.assertIsInstance(filtered, list)


if __name__ == "__main__":
    unittest.main()
