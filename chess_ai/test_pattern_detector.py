"""
Comprehensive Testing Suite for Enhanced Chess Pattern Detector

This module provides:
1. Unit tests for all pattern detection components
2. Integration tests for the complete system
3. Performance benchmarks
4. Validation test cases
5. Example usage demonstrations
"""

import unittest
import chess
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# Import the pattern detection system
from chess_ai.enhanced_chess_pattern_detector import (
    EnhancedPatternDetector, PatternMatch, ChessPatternEnhanced, 
    PatternCategory, PatternPiece, ExchangeSequence,
    TacticalAnalyzer, ExchangeAnalyzer, PatternMatcher
)
from chess_ai.pattern_matching_engine import (
    AdvancedPatternMatcher, PatternValidator, PatternTestingFramework,
    MatchingConfig, ValidationLevel, TacticalFeatureExtractor
)


class TestTacticalAnalyzer(unittest.TestCase):
    """Test cases for TacticalAnalyzer"""
    
    def setUp(self):
        self.analyzer = TacticalAnalyzer()
    
    def test_detect_knight_forks(self):
        """Test knight fork detection"""
        # Position with knight fork opportunity
        fen = "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        board = chess.Board(fen)
        
        forks = self.analyzer.detect_forks(board)
        
        self.assertGreater(len(forks), 0)
        knight_forks = [f for f in forks if f['type'] == 'knight_fork']
        self.assertGreater(len(knight_forks), 0)
        
        # Check fork structure
        fork = knight_forks[0]
        self.assertIn('move', fork)
        self.assertIn('targets', fork)
        self.assertGreaterEqual(len(fork['targets']), 2)
        self.assertGreater(fork['value'], 0)
    
    def test_detect_pins(self):
        """Test pin detection"""
        # Position with pin opportunity
        fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 5 5"
        board = chess.Board(fen)
        
        pins = self.analyzer.detect_pins(board)
        
        # Should find potential pins
        self.assertIsInstance(pins, list)
        
        if pins:
            pin = pins[0]
            self.assertIn('move', pin)
            self.assertIn('type', pin)
            self.assertEqual(pin['type'], 'pin')
    
    def test_detect_hanging_pieces(self):
        """Test hanging piece detection"""
        # Position with hanging piece
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 2 2"
        board = chess.Board(fen)
        
        hanging = self.analyzer.detect_hanging_pieces(board)
        
        self.assertIsInstance(hanging, list)
        
        # Each hanging piece should have required fields
        for hang in hanging:
            self.assertIn('square', hang)
            self.assertIn('piece', hang)
            self.assertIn('capture_move', hang)
            self.assertIn('value', hang)
            self.assertGreater(hang['value'], 0)
    
    def test_piece_values(self):
        """Test piece value calculations"""
        self.assertEqual(self.analyzer.piece_values[chess.PAWN], 100)
        self.assertEqual(self.analyzer.piece_values[chess.KNIGHT], 320)
        self.assertEqual(self.analyzer.piece_values[chess.BISHOP], 330)
        self.assertEqual(self.analyzer.piece_values[chess.ROOK], 500)
        self.assertEqual(self.analyzer.piece_values[chess.QUEEN], 900)
        self.assertEqual(self.analyzer.piece_values[chess.KING], 20000)


class TestExchangeAnalyzer(unittest.TestCase):
    """Test cases for ExchangeAnalyzer"""
    
    def setUp(self):
        self.analyzer = ExchangeAnalyzer()
    
    def test_analyze_simple_capture(self):
        """Test analysis of simple capture"""
        fen = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        board = chess.Board(fen)
        
        # Simple pawn capture
        move = chess.Move.from_uci("d4e5")
        exchange = self.analyzer.analyze_exchange(board, move)
        
        self.assertIsNotNone(exchange)
        self.assertIsInstance(exchange, ExchangeSequence)
        self.assertGreater(len(exchange.moves), 0)
        self.assertEqual(exchange.moves[0], "d4e5")
        self.assertGreater(exchange.material_balance, 0)
    
    def test_analyze_en_passant(self):
        """Test analysis of en passant capture"""
        fen = "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3"
        board = chess.Board(fen)
        
        # En passant capture
        move = chess.Move.from_uci("e5f6")
        exchange = self.analyzer.analyze_exchange(board, move)
        
        self.assertIsNotNone(exchange)
        self.assertIsInstance(exchange, ExchangeSequence)
        self.assertGreater(exchange.material_balance, 0)
    
    def test_analyze_non_capture(self):
        """Test analysis of non-capture move"""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        board = chess.Board(fen)
        
        # Non-capture move
        move = chess.Move.from_uci("e2e4")
        exchange = self.analyzer.analyze_exchange(board, move)
        
        self.assertIsNone(exchange)
    
    def test_exchange_probability(self):
        """Test exchange probability calculation"""
        # Favorable exchange
        prob_favorable = self.analyzer._calculate_exchange_probability(300)
        self.assertGreater(prob_favorable, 0.5)
        
        # Equal exchange
        prob_equal = self.analyzer._calculate_exchange_probability(0)
        self.assertEqual(prob_equal, 0.5)
        
        # Unfavorable exchange
        prob_unfavorable = self.analyzer._calculate_exchange_probability(-300)
        self.assertLess(prob_unfavorable, 0.5)


class TestPatternMatcher(unittest.TestCase):
    """Test cases for PatternMatcher"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.matcher = PatternMatcher(self.temp_dir)
        
        # Create test pattern
        self.test_pattern = ChessPatternEnhanced(
            id="test_pattern",
            name="Test Pattern",
            description="A test pattern for unit testing",
            category=PatternCategory.TACTICAL,
            fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            key_move="g1f3",
            participating_pieces=[
                PatternPiece(
                    square="g1",
                    piece_type="knight",
                    color="white",
                    role="attacker",
                    importance=1.0
                )
            ],
            frequency=0.5,
            success_rate=0.7,
            game_phase="opening",
            tags=["test", "tactical"]
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_pattern_similarity_calculation(self):
        """Test pattern similarity calculation"""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        board = chess.Board(fen)
        
        similarity = self.matcher._calculate_pattern_similarity(
            board, self.test_pattern, board.fen(), board.board_fen()
        )
        
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
    
    def test_piece_similarity(self):
        """Test piece similarity calculation"""
        fen1 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        fen2 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 1 2"
        
        board1 = chess.Board(fen1)
        board2 = chess.Board(fen2)
        
        similarity = self.matcher._calculate_piece_similarity(board1, self.test_pattern)
        
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)


class TestEnhancedPatternDetector(unittest.TestCase):
    """Test cases for EnhancedPatternDetector"""
    
    def setUp(self):
        self.detector = EnhancedPatternDetector()
    
    def test_detect_patterns_initial_position(self):
        """Test pattern detection from initial position"""
        board = chess.Board()
        
        patterns = self.detector.detect_patterns(board)
        
        self.assertIsInstance(patterns, list)
        
        # Each pattern should be a PatternMatch
        for pattern in patterns:
            self.assertIsInstance(pattern, PatternMatch)
            self.assertGreaterEqual(pattern.confidence, 0.0)
            self.assertLessEqual(pattern.confidence, 1.0)
            self.assertIsInstance(pattern.pattern, ChessPatternEnhanced)
    
    def test_detect_patterns_tactical_position(self):
        """Test pattern detection from tactical position"""
        # Position with tactical opportunities
        fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"
        board = chess.Board(fen)
        
        patterns = self.detector.detect_patterns(board)
        
        self.assertIsInstance(patterns, list)
        
        # Should detect tactical patterns
        tactical_patterns = [p for p in patterns if p.pattern.category == PatternCategory.TACTICAL]
        self.assertGreater(len(tactical_patterns), 0)
    
    def test_detect_patterns_endgame_position(self):
        """Test pattern detection from endgame position"""
        # Simple endgame position
        fen = "8/8/8/8/8/8/4K3/6k1 w - - 0 50"
        board = chess.Board(fen)
        
        patterns = self.detector.detect_patterns(board)
        
        self.assertIsInstance(patterns, list)
    
    def test_pattern_statistics(self):
        """Test pattern statistics calculation"""
        board = chess.Board()
        self.detector.detect_patterns(board)
        
        stats = self.detector.get_pattern_statistics()
        
        self.assertIn('total_patterns', stats)
        self.assertGreaterEqual(stats['total_patterns'], 0)
        
        if stats['total_patterns'] > 0:
            self.assertIn('categories', stats)
            self.assertIn('avg_confidence', stats)
            self.assertIn('avg_tactical_value', stats)
            self.assertIn('avg_strategic_value', stats)
            self.assertIn('avg_risk', stats)


class TestAdvancedPatternMatcher(unittest.TestCase):
    """Test cases for AdvancedPatternMatcher"""
    
    def setUp(self):
        self.config = MatchingConfig(
            strategies=[MatchingStrategy.HYBRID_APPROACH],
            min_confidence_threshold=0.3,
            enable_parallel_processing=False  # Disable for testing
        )
        self.matcher = AdvancedPatternMatcher(self.config)
    
    def test_exact_fen_matching(self):
        """Test exact FEN matching strategy"""
        board = chess.Board()
        
        # Create pattern with exact FEN
        pattern = ChessPatternEnhanced(
            id="exact_test",
            name="Exact FEN Test",
            description="Test exact FEN matching",
            category=PatternCategory.POSITIONAL,
            fen=board.fen(),
            key_move="e2e4"
        )
        
        matches = self.matcher._exact_fen_match(board, [pattern])
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0].id, "exact_test")
        self.assertEqual(matches[0][1], 1.0)  # Perfect match
    
    def test_hybrid_matching(self):
        """Test hybrid matching strategy"""
        board = chess.Board()
        
        pattern = ChessPatternEnhanced(
            id="hybrid_test",
            name="Hybrid Test",
            description="Test hybrid matching",
            category=PatternCategory.POSITIONAL,
            fen=board.fen(),
            key_move="e2e4",
            participating_pieces=[
                PatternPiece(
                    square="e2",
                    piece_type="pawn",
                    color="white",
                    role="attacker",
                    importance=0.8
                )
            ]
        )
        
        matches = self.matcher._hybrid_match(board, [pattern])
        
        self.assertGreater(len(matches), 0)
        if matches:
            self.assertGreaterEqual(matches[0][1], 0.0)
            self.assertLessEqual(matches[0][1], 1.0)
    
    def test_cache_functionality(self):
        """Test pattern matching cache"""
        board = chess.Board()
        pattern = ChessPatternEnhanced(
            id="cache_test",
            name="Cache Test",
            description="Test caching functionality",
            category=PatternCategory.POSITIONAL,
            fen=board.fen(),
            key_move="e2e4"
        )
        
        # Enable caching
        config = MatchingConfig(enable_caching=True, cache_size_limit=10)
        matcher = AdvancedPatternMatcher(config)
        
        # First match
        matches1 = matcher.match_patterns(board, [pattern])
        
        # Check cache stats
        stats = matcher.get_cache_stats()
        self.assertTrue(stats['enabled'])
        self.assertEqual(stats['size'], 1)
        
        # Second match should use cache
        matches2 = matcher.match_patterns(board, [pattern])
        
        self.assertEqual(len(matches1), len(matches2))
        
        # Clear cache
        matcher.clear_cache()
        stats = matcher.get_cache_stats()
        self.assertEqual(stats['size'], 0)
        
        matcher.shutdown()


class TestPatternValidator(unittest.TestCase):
    """Test cases for PatternValidator"""
    
    def setUp(self):
        self.validator = PatternValidator(ValidationLevel.INTERMEDIATE)
    
    def test_validate_valid_pattern(self):
        """Test validation of a valid pattern"""
        pattern = ChessPatternEnhanced(
            id="valid_test",
            name="Valid Test Pattern",
            description="A valid pattern for testing",
            category=PatternCategory.TACTICAL,
            fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            key_move="e2e4",
            participating_pieces=[
                PatternPiece(
                    square="e2",
                    piece_type="pawn",
                    color="white",
                    role="attacker",
                    importance=0.8
                )
            ],
            frequency=0.5,
            success_rate=0.7,
            game_phase="opening",
            tags=["test", "opening", "pawn"]
        )
        
        result = self.validator.validate_pattern(pattern)
        
        self.assertTrue(result.is_valid)
        self.assertGreater(result.confidence_score, 0.7)
        self.assertEqual(len(result.validation_errors), 0)
    
    def test_validate_invalid_fen(self):
        """Test validation of pattern with invalid FEN"""
        pattern = ChessPatternEnhanced(
            id="invalid_fen",
            name="Invalid FEN Pattern",
            description="Pattern with invalid FEN",
            category=PatternCategory.TACTICAL,
            fen="invalid_fen_string",
            key_move="e2e4"
        )
        
        result = self.validator.validate_pattern(pattern)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.validation_errors), 0)
        
        # Check for specific error
        fen_errors = [e for e in result.validation_errors if 'FEN' in e]
        self.assertGreater(len(fen_errors), 0)
    
    def test_validate_invalid_move(self):
        """Test validation of pattern with invalid move"""
        pattern = ChessPatternEnhanced(
            id="invalid_move",
            name="Invalid Move Pattern",
            description="Pattern with invalid move",
            category=PatternCategory.TACTICAL,
            fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            key_move="invalid_move"
        )
        
        result = self.validator.validate_pattern(pattern)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.validation_errors), 0)
        
        # Check for specific error
        move_errors = [e for e in result.validation_errors if 'move' in e]
        self.assertGreater(len(move_errors), 0)
    
    def test_validate_missing_required_fields(self):
        """Test validation of pattern with missing required fields"""
        pattern = ChessPatternEnhanced(
            id="",  # Missing ID
            name="",  # Missing name
            description="Pattern with missing fields",
            category=PatternCategory.TACTICAL,
            fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            key_move="e2e4"
        )
        
        result = self.validator.validate_pattern(pattern)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.validation_errors), 2)
    
    def test_comprehensive_validation(self):
        """Test comprehensive validation level"""
        validator = PatternValidator(ValidationLevel.COMPREHENSIVE)
        
        pattern = ChessPatternEnhanced(
            id="comprehensive_test",
            name="Comprehensive Test Pattern",
            description="Pattern for comprehensive validation testing",
            category=PatternCategory.TACTICAL,
            fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            key_move="g1f3",
            participating_pieces=[
                PatternPiece(
                    square="g1",
                    piece_type="knight",
                    color="white",
                    role="attacker",
                    importance=1.0
                )
            ],
            frequency=0.05,  # Very low frequency
            success_rate=0.95,  # Very high success rate
            game_phase="opening",
            tags=["test"]
        )
        
        result = validator.validate_pattern(pattern)
        
        # Should have warnings about unrealistic values
        self.assertGreater(len(result.validation_warnings), 0)
        self.assertGreater(len(result.improvement_suggestions), 0)


class TestTacticalFeatureExtractor(unittest.TestCase):
    """Test cases for TacticalFeatureExtractor"""
    
    def setUp(self):
        self.extractor = TacticalFeatureExtractor()
    
    def test_extract_features_initial_position(self):
        """Test feature extraction from initial position"""
        board = chess.Board()
        
        features = self.extractor.extract_features(board)
        
        # Check required feature categories
        required_features = [
            'material_balance', 'king_safety', 'piece_activity',
            'center_control', 'pawn_structure', 'tactical_motifs',
            'mobility', 'space_advantage', 'tempo', 'threats'
        ]
        
        for feature in required_features:
            self.assertIn(feature, features)
        
        # Check specific feature structures
        self.assertIsInstance(features['material_balance'], (int, float))
        self.assertIsInstance(features['king_safety'], dict)
        self.assertIn('white', features['king_safety'])
        self.assertIn('black', features['king_safety'])
        self.assertIsInstance(features['tactical_motifs'], dict)
    
    def test_material_balance_calculation(self):
        """Test material balance calculation"""
        # Initial position - should be balanced
        board = chess.Board()
        balance = self.extractor._calculate_material_balance(board)
        self.assertEqual(balance, 0)
        
        # Position with extra pawn for white
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        board = chess.Board(fen)
        balance = self.extractor._calculate_material_balance(board)
        self.assertEqual(balance, 0)  # Still balanced in this position
    
    def test_king_safety_evaluation(self):
        """Test king safety evaluation"""
        board = chess.Board()
        
        safety = self.extractor._evaluate_king_safety(board)
        
        self.assertIsInstance(safety, dict)
        self.assertIn('white', safety)
        self.assertIn('black', safety)
        
        # Safety scores should be between 0 and 1
        for color in ['white', 'black']:
            self.assertGreaterEqual(safety[color], 0.0)
            self.assertLessEqual(safety[color], 1.0)
    
    def test_center_control_evaluation(self):
        """Test center control evaluation"""
        board = chess.Board()
        
        control = self.extractor._evaluate_center_control(board)
        
        self.assertIsInstance(control, dict)
        self.assertIn('white', control)
        self.assertIn('black', control)
        
        # Control scores should be between 0 and 1
        for color in ['white', 'black']:
            self.assertGreaterEqual(control[color], 0.0)
            self.assertLessEqual(control[color], 1.0)
    
    def test_passed_pawn_detection(self):
        """Test passed pawn detection"""
        # Position with passed pawn
        fen = "8/1P6/8/8/8/8/8/8 w - - 0 1"
        board = chess.Board(fen)
        
        passed_pawns = self.extractor._find_passed_pawns(board)
        
        self.assertIn(chess.B7, passed_pawns)
    
    def test_isolated_pawn_detection(self):
        """Test isolated pawn detection"""
        # Position with isolated pawn
        fen = "8/8/8/8/8/8/P1P1P1P1/8 w - - 0 1"
        board = chess.Board(fen)
        
        isolated_pawns = self.extractor._find_isolated_pawns(board)
        
        # Should find isolated pawns
        self.assertGreater(len(isolated_pawns), 0)


class TestPatternTestingFramework(unittest.TestCase):
    """Test cases for PatternTestingFramework"""
    
    def setUp(self):
        self.detector = EnhancedPatternDetector()
        self.framework = PatternTestingFramework(self.detector)
    
    def test_evaluate_detection_success(self):
        """Test successful detection evaluation"""
        detected_patterns = [
            PatternMatch(
                pattern=ChessPatternEnhanced(
                    id="pattern1",
                    name="Pattern 1",
                    description="Test pattern 1",
                    category=PatternCategory.TACTICAL,
                    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    key_move="e2e4"
                ),
                confidence=0.8,
                relevant_pieces=[],
                filtered_pieces=[],
                suggested_move="e2e4",
                alternative_moves=[],
                explanation="Test pattern"
            )
        ]
        
        expected_patterns = ["pattern1"]
        
        evaluation = self.framework._evaluate_detection(detected_patterns, expected_patterns)
        
        self.assertTrue(evaluation['success'])
        self.assertEqual(evaluation['max_confidence'], 0.8)
        self.assertIn("pattern1", evaluation['pattern_matches'])
    
    def test_evaluate_detection_failure(self):
        """Test failed detection evaluation"""
        detected_patterns = [
            PatternMatch(
                pattern=ChessPatternEnhanced(
                    id="wrong_pattern",
                    name="Wrong Pattern",
                    description="Wrong pattern",
                    category=PatternCategory.TACTICAL,
                    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    key_move="e2e4"
                ),
                confidence=0.6,
                relevant_pieces=[],
                filtered_pieces=[],
                suggested_move="e2e4",
                alternative_moves=[],
                explanation="Wrong pattern"
            )
        ]
        
        expected_patterns = ["expected_pattern"]
        
        evaluation = self.framework._evaluate_detection(detected_patterns, expected_patterns)
        
        self.assertFalse(evaluation['success'])
        self.assertEqual(len(evaluation['pattern_matches']), 0)
        self.assertIn("expected_pattern", evaluation['missing_patterns'])
    
    def test_generate_test_positions(self):
        """Test test position generation"""
        positions = self.framework._generate_test_positions(10)
        
        self.assertEqual(len(positions), 10)
        
        for pos in positions:
            self.assertIn('fen', pos)
            self.assertIn('expected_patterns', pos)
            
            # Verify FEN is valid
            try:
                chess.Board(pos['fen'])
            except ValueError:
                self.fail(f"Invalid FEN generated: {pos['fen']}")
    
    def test_run_comprehensive_tests(self):
        """Test comprehensive test execution"""
        test_positions = [
            {
                'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                'expected_patterns': []
            },
            {
                'fen': 'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2',
                'expected_patterns': []
            }
        ]
        
        results = self.framework.run_comprehensive_tests(test_positions)
        
        self.assertIn('total_positions', results)
        self.assertIn('successful_detections', results)
        self.assertIn('failed_detections', results)
        self.assertIn('average_confidence', results)
        self.assertIn('performance_metrics', results)
        self.assertIn('detailed_results', results)
        
        self.assertEqual(results['total_positions'], 2)
        self.assertEqual(len(results['detailed_results']), 2)


class IntegrationTest(unittest.TestCase):
    """Integration tests for the complete pattern detection system"""
    
    def test_end_to_end_pattern_detection(self):
        """Test complete pattern detection workflow"""
        # Create detector
        detector = EnhancedPatternDetector()
        
        # Test position with known tactical patterns
        fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4"
        board = chess.Board(fen)
        
        # Detect patterns
        patterns = detector.detect_patterns(board, max_patterns=5)
        
        # Verify results
        self.assertIsInstance(patterns, list)
        self.assertLessEqual(len(patterns), 5)
        
        for pattern in patterns:
            self.assertIsInstance(pattern, PatternMatch)
            self.assertGreaterEqual(pattern.confidence, 0.0)
            self.assertLessEqual(pattern.confidence, 1.0)
            self.assertIsInstance(pattern.pattern, ChessPatternEnhanced)
            self.assertIsInstance(pattern.relevant_pieces, list)
            self.assertIsInstance(pattern.filtered_pieces, list)
            self.assertIsInstance(pattern.suggested_move, str)
            self.assertIsInstance(pattern.alternative_moves, list)
            self.assertIsInstance(pattern.explanation, str)
    
    def test_pattern_validation_integration(self):
        """Test pattern validation integration"""
        validator = PatternValidator(ValidationLevel.COMPREHENSIVE)
        
        # Create a pattern
        pattern = ChessPatternEnhanced(
            id="integration_test",
            name="Integration Test Pattern",
            description="Pattern for integration testing",
            category=PatternCategory.TACTICAL,
            fen="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            key_move="g1f3",
            participating_pieces=[
                PatternPiece(
                    square="g1",
                    piece_type="knight",
                    color="white",
                    role="attacker",
                    importance=1.0
                )
            ],
            frequency=0.5,
            success_rate=0.7,
            game_phase="opening",
            tags=["integration", "test", "knight"]
        )
        
        # Validate pattern
        result = validator.validate_pattern(pattern)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertIsInstance(result.is_valid, bool)
        self.assertIsInstance(result.confidence_score, float)
        self.assertIsInstance(result.validation_errors, list)
        self.assertIsInstance(result.validation_warnings, list)
        self.assertIsInstance(result.improvement_suggestions, list)
    
    def test_performance_benchmark_integration(self):
        """Test performance benchmark integration"""
        detector = EnhancedPatternDetector()
        framework = PatternTestingFramework(detector)
        
        # Run small benchmark
        results = framework.benchmark_performance(num_positions=10)
        
        self.assertIn('num_positions', results)
        self.assertIn('total_time', results)
        self.assertIn('average_time', results)
        self.assertIn('patterns_per_second', results)
        
        self.assertEqual(results['num_positions'], 10)
        self.assertGreater(results['total_time'], 0)
        self.assertGreater(results['patterns_per_second'], 0)


def create_demo_patterns() -> List[ChessPatternEnhanced]:
    """Create demonstration patterns"""
    patterns = []
    
    # Knight fork pattern
    knight_fork = ChessPatternEnhanced(
        id="knight_fork_demo",
        name="Knight Fork Demonstration",
        description="Classic knight fork attacking king and queen",
        category=PatternCategory.TACTICAL,
        fen="r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4",
        key_move="c3d5",
        alternative_moves=["g1f3"],
        participating_pieces=[
            PatternPiece(
                square="c3",
                piece_type="knight",
                color="white",
                role="attacker",
                importance=1.0
            ),
            PatternPiece(
                square="e8",
                piece_type="king",
                color="black",
                role="target",
                importance=0.9
            ),
            PatternPiece(
                square="d8",
                piece_type="queen",
                color="black",
                role="target",
                importance=0.9
            )
        ],
        frequency=0.3,
        success_rate=0.8,
        elo_range=(1200, 2000),
        game_phase="middlegame",
        tags=["fork", "knight", "tactical", "demo"]
    )
    patterns.append(knight_fork)
    
    # Pin pattern
    pin_pattern = ChessPatternEnhanced(
        id="pin_demo",
        name="Pin Demonstration",
        description="Pin knight to queen using bishop",
        category=PatternCategory.TACTICAL,
        fen="r2qkbnr/ppp1pppp/2np4/3p4/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 4",
        key_move="c1g5",
        participating_pieces=[
            PatternPiece(
                square="c1",
                piece_type="bishop",
                color="white",
                role="attacker",
                importance=1.0
            ),
            PatternPiece(
                square="c6",
                piece_type="knight",
                color="black",
                role="target",
                importance=0.8
            ),
            PatternPiece(
                square="d8",
                piece_type="queen",
                color="black",
                role="pinned_to",
                importance=0.9
            )
        ],
        frequency=0.25,
        success_rate=0.7,
        elo_range=(1000, 1800),
        game_phase="middlegame",
        tags=["pin", "bishop", "tactical", "demo"]
    )
    patterns.append(pin_pattern)
    
    # Passed pawn pattern
    passed_pawn = ChessPatternEnhanced(
        id="passed_pawn_demo",
        name="Passed Pawn Demonstration",
        description="Promote passed pawn in endgame",
        category=PatternCategory.ENDGAME,
        fen="8/1P6/8/8/8/8/8/6k1 w - - 0 1",
        key_move="b7b8q",
        participating_pieces=[
            PatternPiece(
                square="b7",
                piece_type="pawn",
                color="white",
                role="attacker",
                importance=1.0
            )
        ],
        frequency=0.4,
        success_rate=0.9,
        elo_range=(800, 1600),
        game_phase="endgame",
        tags=["passed_pawn", "endgame", "promotion", "demo"]
    )
    patterns.append(passed_pawn)
    
    return patterns


def run_pattern_detection_demo():
    """Run a complete pattern detection demonstration"""
    print("=" * 60)
    print("Enhanced Chess Pattern Detector - Demonstration")
    print("=" * 60)
    
    # Create detector
    detector = EnhancedPatternDetector()
    
    # Create demonstration patterns
    demo_patterns = create_demo_patterns()
    
    print(f"\nCreated {len(demo_patterns)} demonstration patterns:")
    for pattern in demo_patterns:
        print(f"  - {pattern.name}: {pattern.description}")
    
    # Test positions
    test_positions = [
        {
            'name': 'Knight Fork Position',
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 4'
        },
        {
            'name': 'Pin Position',
            'fen': 'r2qkbnr/ppp1pppp/2np4/3p4/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 4'
        },
        {
            'name': 'Endgame Position',
            'fen': '8/1P6/8/8/8/8/8/6k1 w - - 0 1'
        },
        {
            'name': 'Complex Middlegame',
            'fen': 'r2qk2r/ppp1ppbp/2np1np1/4p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 6'
        }
    ]
    
    print(f"\nTesting {len(test_positions)} positions:")
    
    for i, test_pos in enumerate(test_positions, 1):
        print(f"\n{i}. {test_pos['name']}")
        print(f"   FEN: {test_pos['fen']}")
        
        try:
            board = chess.Board(test_pos['fen'])
            
            # Detect patterns
            start_time = time.time()
            patterns = detector.detect_patterns(board, max_patterns=5)
            detection_time = time.time() - start_time
            
            print(f"   Detection time: {detection_time:.3f}s")
            print(f"   Patterns found: {len(patterns)}")
            
            for j, pattern in enumerate(patterns, 1):
                print(f"     {j}. {pattern.pattern.name} (confidence: {pattern.confidence:.2f})")
                print(f"        Category: {pattern.pattern.category.value}")
                print(f"        Suggested move: {pattern.suggested_move}")
                print(f"        Explanation: {pattern.explanation}")
                if pattern.tactical_value > 0:
                    print(f"        Tactical value: {pattern.tactical_value:.0f}")
                if pattern.strategic_value > 0:
                    print(f"        Strategic value: {pattern.strategic_value:.0f}")
                print(f"        Risk assessment: {pattern.risk_assessment:.2f}")
            
            # Get statistics
            stats = detector.get_pattern_statistics()
            if stats['total_patterns'] > 0:
                print(f"   Average confidence: {stats['avg_confidence']:.2f}")
                print(f"   Categories found: {list(stats['categories'].keys())}")
        
        except Exception as e:
            print(f"   Error: {e}")
    
    # Performance benchmark
    print(f"\nRunning performance benchmark...")
    framework = PatternTestingFramework(detector)
    benchmark_results = framework.benchmark_performance(num_positions=50)
    
    print(f"   Positions analyzed: {benchmark_results['num_positions']}")
    print(f"   Total time: {benchmark_results['total_time']:.3f}s")
    print(f"   Average time per position: {benchmark_results['average_time']:.6f}s")
    print(f"   Positions per second: {benchmark_results['patterns_per_second']:.1f}")
    
    # Pattern validation demo
    print(f"\nRunning pattern validation demo...")
    validator = PatternValidator(ValidationLevel.COMPREHENSIVE)
    
    for pattern in demo_patterns:
        print(f"\nValidating pattern: {pattern.name}")
        result = validator.validate_pattern(pattern)
        
        print(f"   Valid: {result.is_valid}")
        print(f"   Confidence score: {result.confidence_score:.2f}")
        
        if result.validation_errors:
            print(f"   Errors: {len(result.validation_errors)}")
            for error in result.validation_errors:
                print(f"     - {error}")
        
        if result.validation_warnings:
            print(f"   Warnings: {len(result.validation_warnings)}")
            for warning in result.validation_warnings:
                print(f"     - {warning}")
        
        if result.improvement_suggestions:
            print(f"   Improvement suggestions: {len(result.improvement_suggestions)}")
            for suggestion in result.improvement_suggestions:
                print(f"     - {suggestion}")
    
    print("\n" + "=" * 60)
    print("Demonstration completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    # Run demonstration
    run_pattern_detection_demo()
    
    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(verbosity=2, exit=False)
