"""
Pattern Matching Engine and Validation System for Enhanced Chess Pattern Detector

This module provides:
1. Advanced pattern matching algorithms
2. Pattern validation and verification
3. Performance optimization for real-time detection
4. Machine learning integration for pattern improvement
5. Comprehensive testing framework
"""

from __future__ import annotations
import chess
import chess.syzygy
import logging
from typing import List, Dict, Any, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import time
import numpy as np
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle
import sqlite3
from pathlib import Path

from chess_ai.enhanced_chess_pattern_detector import (
    EnhancedPatternDetector, PatternMatch, ChessPatternEnhanced, 
    PatternCategory, PatternPiece, ExchangeSequence
)

logger = logging.getLogger(__name__)


class MatchingStrategy(Enum):
    """Pattern matching strategies"""
    EXACT_FEN = "exact_fen"
    POSITIONAL_SIMILARITY = "positional_similarity"
    TACTICAL_FEATURES = "tactical_features"
    STRUCTURAL_PATTERNS = "structural_patterns"
    SEMANTIC_MATCHING = "semantic_matching"
    HYBRID_APPROACH = "hybrid_approach"


class ValidationLevel(Enum):
    """Pattern validation levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    COMPREHENSIVE = "comprehensive"


@dataclass
class MatchingConfig:
    """Configuration for pattern matching"""
    strategies: List[MatchingStrategy] = field(default_factory=lambda: [MatchingStrategy.HYBRID_APPROACH])
    min_confidence_threshold: float = 0.3
    max_patterns_per_category: int = 5
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    enable_caching: bool = True
    cache_size_limit: int = 1000
    enable_ml_scoring: bool = False
    tactical_weight: float = 0.4
    strategic_weight: float = 0.3
    positional_weight: float = 0.2
    material_weight: float = 0.1


@dataclass
class ValidationResult:
    """Result of pattern validation"""
    is_valid: bool
    confidence_score: float
    validation_errors: List[str]
    validation_warnings: List[str]
    corrected_pattern: Optional[ChessPatternEnhanced] = None
    improvement_suggestions: List[str] = field(default_factory=list)


class PatternCache:
    """Efficient caching system for pattern matching results"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.access_order = deque()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                # Update access time
                self.access_times[key] = time.time()
                # Move to end of access order
                try:
                    self.access_order.remove(key)
                except ValueError:
                    pass
                self.access_order.append(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: Any):
        """Put value in cache"""
        with self.lock:
            if key in self.cache:
                # Update existing
                self.cache[key] = value
                self.access_times[key] = time.time()
                try:
                    self.access_order.remove(key)
                except ValueError:
                    pass
                self.access_order.append(key)
            else:
                # Add new
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    oldest = self.access_order.popleft()
                    del self.cache[oldest]
                    del self.access_times[oldest]
                
                self.cache[key] = value
                self.access_times[key] = time.time()
                self.access_order.append(key)
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.access_order.clear()
    
    def size(self) -> int:
        """Get cache size"""
        with self.lock:
            return len(self.cache)


class TacticalFeatureExtractor:
    """Extracts tactical features from chess positions"""
    
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
    
    def extract_features(self, board: chess.Board) -> Dict[str, Any]:
        """Extract comprehensive tactical features"""
        features = {
            'material_balance': self._calculate_material_balance(board),
            'king_safety': self._evaluate_king_safety(board),
            'piece_activity': self._evaluate_piece_activity(board),
            'center_control': self._evaluate_center_control(board),
            'pawn_structure': self._evaluate_pawn_structure(board),
            'tactical_motifs': self._detect_tactical_motifs(board),
            'mobility': self._calculate_mobility(board),
            'space_advantage': self._calculate_space_advantage(board),
            'tempo': self._evaluate_tempo(board),
            'threats': self._count_threats(board)
        }
        
        return features
    
    def _calculate_material_balance(self, board: chess.Board) -> float:
        """Calculate material balance"""
        balance = 0
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            white_count = len(board.pieces(piece_type, chess.WHITE))
            black_count = len(board.pieces(piece_type, chess.BLACK))
            balance += (white_count - black_count) * self.piece_values[piece_type]
        return balance
    
    def _evaluate_king_safety(self, board: chess.Board) -> Dict[str, float]:
        """Evaluate king safety for both sides"""
        safety = {'white': 0.0, 'black': 0.0}
        
        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            if king_sq is None:
                continue
            
            # Pawn shield
            pawn_shield = self._evaluate_pawn_shield(board, king_sq, color)
            
            # Piece exposure
            exposure = self._evaluate_king_exposure(board, king_sq, color)
            
            # Castle readiness
            castle_ready = self._evaluate_castle_readiness(board, color)
            
            safety['white' if color == chess.WHITE else 'black'] = (
                pawn_shield * 0.4 + exposure * 0.4 + castle_ready * 0.2
            )
        
        return safety
    
    def _evaluate_pawn_shield(self, board: chess.Board, king_sq: int, color: chess.Color) -> float:
        """Evaluate pawn shield around king"""
        shield_score = 0.0
        king_rank = chess.square_rank(king_sq)
        king_file = chess.square_file(king_sq)
        
        # Define shield squares
        if color == chess.WHITE:
            shield_ranks = [king_rank - 1, king_rank - 2] if king_rank > 0 else [king_rank - 1]
        else:
            shield_ranks = [king_rank + 1, king_rank + 2] if king_rank < 7 else [king_rank + 1]
        
        shield_files = [max(0, king_file - 1), king_file, min(7, king_file + 1)]
        
        for rank in shield_ranks:
            for file in shield_files:
                if 0 <= rank <= 7 and 0 <= file <= 7:
                    sq = chess.square(file, rank)
                    piece = board.piece_at(sq)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        shield_score += 1.0
        
        return min(1.0, shield_score / 6.0)
    
    def _evaluate_king_exposure(self, board: chess.Board, king_sq: int, color: chess.Color) -> float:
        """Evaluate king exposure to attacks"""
        enemy_color = not color
        attackers = board.attackers(enemy_color, king_sq)
        
        # Count attackers and their values
        attack_value = 0
        for attacker_sq in attackers:
            attacker = board.piece_at(attacker_sq)
            if attacker:
                attack_value += self.piece_values[attacker.piece_type]
        
        # Normalize to 0-1 scale (lower is better)
        exposure = min(1.0, attack_value / 2000.0)
        return 1.0 - exposure  # Convert to safety score
    
    def _evaluate_castle_readiness(self, board: chess.Board, color: chess.Color) -> float:
        """Evaluate castling readiness"""
        if board.has_castling_rights(color):
            return 1.0
        elif board.has_kingside_castling_rights(color) or board.has_queenside_castling_rights(color):
            return 0.5
        else:
            return 0.0
    
    def _evaluate_piece_activity(self, board: chess.Board) -> Dict[str, float]:
        """Evaluate piece activity for both sides"""
        activity = {'white': 0.0, 'black': 0.0}
        
        for color in [chess.WHITE, chess.BLACK]:
            total_activity = 0.0
            piece_count = 0
            
            for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                pieces = board.pieces(piece_type, color)
                for sq in pieces:
                    # Activity based on mobility and centralization
                    mobility = len(board.attacks(sq))
                    centrality = self._calculate_centrality(sq)
                    activity_score = mobility * 0.7 + centrality * 0.3
                    total_activity += activity_score
                    piece_count += 1
            
            activity['white' if color == chess.WHITE else 'black'] = (
                total_activity / max(1, piece_count) / 14.0  # Normalize
            )
        
        return activity
    
    def _calculate_centrality(self, square: int) -> float:
        """Calculate centrality score for a square"""
        file, rank = chess.square_file(square), chess.square_rank(square)
        
        # Distance from center (d4, e4, d5, e5)
        center_files = [3, 4]
        center_ranks = [3, 4]
        
        min_distance = min(
            abs(file - cf) + abs(rank - cr)
            for cf in center_files for cr in center_ranks
        )
        
        # Convert to 0-1 scale (center is 1.0)
        return max(0.0, 1.0 - min_distance / 7.0)
    
    def _evaluate_center_control(self, board: chess.Board) -> Dict[str, float]:
        """Evaluate center control"""
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        extended_center = [chess.C3, chess.D3, chess.E3, chess.F3, 
                          chess.C4, chess.F4, chess.C5, chess.F5,
                          chess.C6, chess.D6, chess.E6, chess.F6]
        
        control = {'white': 0.0, 'black': 0.0}
        
        for color in [chess.WHITE, chess.BLACK]:
            score = 0.0
            
            # Center squares
            for sq in center_squares:
                if board.piece_at(sq) and board.piece_at(sq).color == color:
                    score += 2.0
                elif sq in board.attackers(color, sq):
                    score += 1.0
            
            # Extended center
            for sq in extended_center:
                if board.piece_at(sq) and board.piece_at(sq).color == color:
                    score += 1.0
                elif sq in board.attackers(color, sq):
                    score += 0.5
            
            control['white' if color == chess.WHITE else 'black'] = min(1.0, score / 20.0)
        
        return control
    
    def _evaluate_pawn_structure(self, board: chess.Board) -> Dict[str, float]:
        """Evaluate pawn structure"""
        structure = {
            'passed_pawns': 0.0,
            'isolated_pawns': 0.0,
            'doubled_pawns': 0.0,
            'pawn_chains': 0.0
        }
        
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            
            # Passed pawns
            passed_count = 0
            for pawn_sq in pawns:
                if self._is_passed_pawn(board, pawn_sq, color):
                    passed_count += 1
            
            # Isolated pawns
            isolated_count = 0
            for pawn_sq in pawns:
                if self._is_isolated_pawn(board, pawn_sq, color):
                    isolated_count += 1
            
            # Doubled pawns
            file_counts = defaultdict(int)
            for pawn_sq in pawns:
                file_counts[chess.square_file(pawn_sq)] += 1
            
            doubled_count = sum(count - 1 for count in file_counts.values() if count > 1)
            
            # Normalize scores
            total_pawns = len(pawns)
            if total_pawns > 0:
                structure['passed_pawns'] += passed_count / total_pawns
                structure['isolated_pawns'] += isolated_count / total_pawns
                structure['doubled_pawns'] += doubled_count / total_pawns
        
        return structure
    
    def _is_passed_pawn(self, board: chess.Board, pawn_sq: int, color: chess.Color) -> bool:
        """Check if pawn is passed"""
        pawn_file = chess.square_file(pawn_sq)
        pawn_rank = chess.square_rank(pawn_sq)
        enemy_pawns = board.pieces(chess.PAWN, not color)
        
        for enemy_pawn in enemy_pawns:
            enemy_file = chess.square_file(enemy_pawn)
            enemy_rank = chess.square_rank(enemy_pawn)
            
            # Check if enemy pawn is in front and on same or adjacent file
            if color == chess.WHITE:
                if enemy_rank > pawn_rank and abs(enemy_file - pawn_file) <= 1:
                    return False
            else:
                if enemy_rank < pawn_rank and abs(enemy_file - pawn_file) <= 1:
                    return False
        
        return True
    
    def _is_isolated_pawn(self, board: chess.Board, pawn_sq: int, color: chess.Color) -> bool:
        """Check if pawn is isolated"""
        pawn_file = chess.square_file(pawn_sq)
        pawns = board.pieces(chess.PAWN, color)
        
        # Check adjacent files for friendly pawns
        for check_file in [pawn_file - 1, pawn_file + 1]:
            if 0 <= check_file <= 7:
                for pawn in pawns:
                    if chess.square_file(pawn) == check_file:
                        return False
        
        return True
    
    def _detect_tactical_motifs(self, board: chess.Board) -> Dict[str, List[str]]:
        """Detect various tactical motifs"""
        motifs = {
            'forks': [],
            'pins': [],
            'skewers': [],
            'discovered_attacks': [],
            'x_rays': []
        }
        
        # Detect forks
        for move in board.legal_moves:
            if self._creates_fork(board, move):
                motifs['forks'].append(move.uci())
        
        # Detect pins
        for move in board.legal_moves:
            if self._creates_pin(board, move):
                motifs['pins'].append(move.uci())
        
        # Detect skewers
        for move in board.legal_moves:
            if self._creates_skewer(board, move):
                motifs['skewers'].append(move.uci())
        
        # Detect discovered attacks
        for move in board.legal_moves:
            if self._creates_discovered_attack(board, move):
                motifs['discovered_attacks'].append(move.uci())
        
        return motifs
    
    def _creates_fork(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a fork"""
        piece = board.piece_at(move.from_square)
        if not piece or piece.piece_type not in [chess.KNIGHT, chess.BISHOP]:
            return False
        
        test_board = board.copy()
        test_board.push(move)
        
        attacks = test_board.attacks(move.to_square)
        valuable_targets = 0
        
        for target_sq in attacks:
            target = test_board.piece_at(target_sq)
            if target and target.color != piece.color:
                if target.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]:
                    valuable_targets += 1
        
        return valuable_targets >= 2
    
    def _creates_pin(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a pin"""
        piece = board.piece_at(move.from_square)
        if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            return False
        
        test_board = board.copy()
        test_board.push(move)
        
        enemy_king_sq = test_board.king(not piece.color)
        if enemy_king_sq is None:
            return False
        
        # Check if piece can pin along line to king
        direction = self._get_line_direction(move.to_square, enemy_king_sq)
        if direction is None:
            return False
        
        # Look for enemy piece between attacker and king
        current_sq = move.to_square + direction
        while 0 <= current_sq < 64:
            target = test_board.piece_at(current_sq)
            if target:
                if target.color == piece.color:
                    break
                else:
                    return True  # Found enemy piece to pin
            current_sq += direction
        
        return False
    
    def _creates_skewer(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a skewer"""
        # Similar to pin but with more valuable piece in front
        return False  # Simplified for now
    
    def _creates_discovered_attack(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a discovered attack"""
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
        
        # Check if moving piece reveals attack
        attacks_before = set()
        for sq in chess.SQUARES:
            if sq != move.from_square:
                p = board.piece_at(sq)
                if p and p.color == board.turn:
                    attacks_before.update(board.attacks(sq))
        
        test_board = board.copy()
        test_board.push(move)
        
        attacks_after = set()
        for sq in chess.SQUARES:
            if sq != move.to_square:
                p = test_board.piece_at(sq)
                if p and p.color == board.turn:
                    attacks_after.update(test_board.attacks(sq))
        
        # Check if new attacks on enemy pieces
        new_attacks = attacks_after - attacks_before
        for attack_sq in new_attacks:
            target = test_board.piece_at(attack_sq)
            if target and target.color != board.turn and target.piece_type != chess.PAWN:
                return True
        
        return False
    
    def _get_line_direction(self, from_sq: int, to_sq: int) -> Optional[int]:
        """Get direction vector between two squares on same line"""
        from_file, from_rank = chess.square_file(from_sq), chess.square_rank(from_sq)
        to_file, to_rank = chess.square_file(to_sq), chess.square_rank(to_sq)
        
        file_diff = to_file - from_file
        rank_diff = to_rank - from_rank
        
        if file_diff == 0:  # Same file
            return 8 if rank_diff > 0 else -8
        elif rank_diff == 0:  # Same rank
            return 1 if file_diff > 0 else -1
        elif abs(file_diff) == abs(rank_diff):  # Same diagonal
            if file_diff > 0 and rank_diff > 0:
                return 9
            elif file_diff > 0 and rank_diff < 0:
                return -7
            elif file_diff < 0 and rank_diff > 0:
                return 7
            else:
                return -9
        
        return None
    
    def _calculate_mobility(self, board: chess.Board) -> Dict[str, float]:
        """Calculate mobility scores"""
        mobility = {'white': 0.0, 'black': 0.0}
        
        for color in [chess.WHITE, chess.BLACK]:
            total_moves = 0
            for move in board.legal_moves:
                piece = board.piece_at(move.from_square)
                if piece and piece.color == color:
                    total_moves += 1
            
            # Normalize by piece count
            piece_count = sum(len(board.pieces(pt, color)) for pt in 
                            [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
            
            mobility['white' if color == chess.WHITE else 'black'] = (
                total_moves / max(1, piece_count * 8)  # Rough normalization
            )
        
        return mobility
    
    def _calculate_space_advantage(self, board: chess.Board) -> Dict[str, float]:
        """Calculate space advantage"""
        space = {'white': 0.0, 'black': 0.0}
        
        for color in [chess.WHITE, chess.BLACK]:
            controlled_squares = set()
            
            # Add squares attacked by pieces
            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.color == color:
                    controlled_squares.update(board.attacks(sq))
            
            # Add squares occupied by pieces
            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.color == color:
                    controlled_squares.add(sq)
            
            space['white' if color == chess.WHITE else 'black'] = len(controlled_squares) / 64.0
        
        return space
    
    def _evaluate_tempo(self, board: chess.Board) -> float:
        """Evaluate tempo advantage"""
        # Simple tempo evaluation based on move count and development
        white_development = len([sq for sq in board.pieces(chess.KNIGHT, chess.WHITE)]) + \
                           len([sq for sq in board.pieces(chess.BISHOP, chess.WHITE)])
        black_development = len([sq for sq in board.pieces(chess.KNIGHT, chess.BLACK)]) + \
                           len([sq for sq in board.pieces(chess.BISHOP, chess.BLACK)])
        
        return (white_development - black_development) / 4.0  # Normalize
    
    def _count_threats(self, board: chess.Board) -> Dict[str, int]:
        """Count threats for both sides"""
        threats = {'white': 0, 'black': 0}
        
        for color in [chess.WHITE, chess.BLACK]:
            enemy_color = not color
            threat_count = 0
            
            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.color == enemy_color:
                    attackers = board.attackers(color, sq)
                    if attackers:
                        threat_count += len(attackers)
            
            threats['white' if color == chess.WHITE else 'black'] = threat_count
        
        return threats


class AdvancedPatternMatcher:
    """Advanced pattern matching engine with multiple strategies"""
    
    def __init__(self, config: MatchingConfig = None):
        self.config = config or MatchingConfig()
        self.feature_extractor = TacticalFeatureExtractor()
        self.cache = PatternCache(self.config.cache_size_limit) if self.config.enable_caching else None
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_worker_threads)
        
        # Strategy-specific matchers
        self.strategies = {
            MatchingStrategy.EXACT_FEN: self._exact_fen_match,
            MatchingStrategy.POSITIONAL_SIMILARITY: self._positional_similarity_match,
            MatchingStrategy.TACTICAL_FEATURES: self._tactical_features_match,
            MatchingStrategy.STRUCTURAL_PATTERNS: self._structural_patterns_match,
            MatchingStrategy.HYBRID_APPROACH: self._hybrid_match
        }
    
    def match_patterns(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Match board position against patterns using configured strategies"""
        
        # Generate cache key
        cache_key = self._generate_cache_key(board, patterns)
        
        # Check cache
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # Perform matching
        if self.config.enable_parallel_processing and len(patterns) > 10:
            matches = self._parallel_match(board, patterns)
        else:
            matches = self._sequential_match(board, patterns)
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Cache result
        if self.cache:
            self.cache.put(cache_key, matches)
        
        return matches
    
    def _sequential_match(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Sequential pattern matching"""
        matches = []
        
        for strategy in self.config.strategies:
            if strategy in self.strategies:
                strategy_matches = self.strategies[strategy](board, patterns)
                matches.extend(strategy_matches)
        
        # Remove duplicates and keep best score
        unique_matches = {}
        for pattern, score in matches:
            if pattern.id not in unique_matches or score > unique_matches[pattern.id][1]:
                unique_matches[pattern.id] = (pattern, score)
        
        return list(unique_matches.values())
    
    def _parallel_match(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Parallel pattern matching"""
        matches = []
        
        # Split patterns by strategy
        strategy_patterns = defaultdict(list)
        for pattern in patterns:
            strategy_patterns[pattern.category].append(pattern)
        
        # Execute matching in parallel
        futures = []
        for strategy in self.config.strategies:
            if strategy in self.strategies and strategy_patterns.get(strategy):
                future = self.executor.submit(self.strategies[strategy], board, strategy_patterns[strategy])
                futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            try:
                strategy_matches = future.result(timeout=5.0)
                matches.extend(strategy_matches)
            except Exception as e:
                logger.error(f"Parallel matching error: {e}")
        
        # Remove duplicates and keep best score
        unique_matches = {}
        for pattern, score in matches:
            if pattern.id not in unique_matches or score > unique_matches[pattern.id][1]:
                unique_matches[pattern.id] = (pattern, score)
        
        return list(unique_matches.values())
    
    def _exact_fen_match(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Exact FEN matching strategy"""
        matches = []
        board_fen = board.fen()
        
        for pattern in patterns:
            if pattern.fen == board_fen:
                matches.append((pattern, 1.0))
        
        return matches
    
    def _positional_similarity_match(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Positional similarity matching strategy"""
        matches = []
        board_features = self.feature_extractor.extract_features(board)
        
        for pattern in patterns:
            try:
                pattern_board = chess.Board(pattern.fen)
                pattern_features = self.feature_extractor.extract_features(pattern_board)
                
                similarity = self._calculate_feature_similarity(board_features, pattern_features)
                
                if similarity >= self.config.min_confidence_threshold:
                    matches.append((pattern, similarity))
            
            except Exception as e:
                logger.debug(f"Error in positional similarity matching for pattern {pattern.id}: {e}")
                continue
        
        return matches
    
    def _tactical_features_match(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Tactical features matching strategy"""
        matches = []
        board_tactical = self.feature_extractor.extract_features(board)
        
        for pattern in patterns:
            if pattern.category == PatternCategory.TACTICAL:
                # Extract tactical features from pattern position
                try:
                    pattern_board = chess.Board(pattern.fen)
                    pattern_tactical = self.feature_extractor.extract_features(pattern_board)
                    
                    # Focus on tactical features
                    tactical_similarity = self._calculate_tactical_similarity(board_tactical, pattern_tactical)
                    
                    if tactical_similarity >= self.config.min_confidence_threshold:
                        matches.append((pattern, tactical_similarity))
                
                except Exception as e:
                    logger.debug(f"Error in tactical features matching for pattern {pattern.id}: {e}")
                    continue
        
        return matches
    
    def _structural_patterns_match(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Structural patterns matching strategy"""
        matches = []
        
        for pattern in patterns:
            # Check pawn structure, piece placement, etc.
            structural_similarity = self._calculate_structural_similarity(board, pattern)
            
            if structural_similarity >= self.config.min_confidence_threshold:
                matches.append((pattern, structural_similarity))
        
        return matches
    
    def _hybrid_match(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Hybrid matching combining multiple strategies"""
        matches = []
        
        for pattern in patterns:
            # Calculate weighted combination of different similarities
            exact_score = 1.0 if pattern.fen == board.fen() else 0.0
            
            positional_score = self._calculate_positional_similarity(board, pattern)
            tactical_score = self._calculate_tactical_similarity_score(board, pattern)
            structural_score = self._calculate_structural_similarity(board, pattern)
            
            # Weighted combination
            combined_score = (
                exact_score * 0.3 +
                positional_score * self.config.positional_weight +
                tactical_score * self.config.tactical_weight +
                structural_score * 0.1
            )
            
            if combined_score >= self.config.min_confidence_threshold:
                matches.append((pattern, combined_score))
        
        return matches
    
    def _calculate_feature_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate similarity between feature dictionaries"""
        similarity_scores = []
        
        # Material balance similarity
        mat_diff = abs(features1['material_balance'] - features2['material_balance'])
        mat_similarity = max(0.0, 1.0 - mat_diff / 1000.0)
        similarity_scores.append(mat_similarity)
        
        # King safety similarity
        for color in ['white', 'black']:
            king_diff = abs(features1['king_safety'][color] - features2['king_safety'][color])
            king_similarity = max(0.0, 1.0 - king_diff)
            similarity_scores.append(king_similarity)
        
        # Piece activity similarity
        for color in ['white', 'black']:
            activity_diff = abs(features1['piece_activity'][color] - features2['piece_activity'][color])
            activity_similarity = max(0.0, 1.0 - activity_diff)
            similarity_scores.append(activity_similarity)
        
        # Center control similarity
        for color in ['white', 'black']:
            center_diff = abs(features1['center_control'][color] - features2['center_control'][color])
            center_similarity = max(0.0, 1.0 - center_diff)
            similarity_scores.append(center_similarity)
        
        return sum(similarity_scores) / len(similarity_scores)
    
    def _calculate_tactical_similarity(self, tactical1: Dict[str, Any], tactical2: Dict[str, Any]) -> float:
        """Calculate tactical similarity"""
        similarity_scores = []
        
        # Compare tactical motifs
        for motif in ['forks', 'pins', 'skewers', 'discovered_attacks']:
            count1 = len(tactical1['tactical_motifs'].get(motif, []))
            count2 = len(tactical2['tactical_motifs'].get(motif, []))
            
            if count1 == 0 and count2 == 0:
                motif_similarity = 1.0
            else:
                motif_similarity = 1.0 - abs(count1 - count2) / max(1, max(count1, count2))
            
            similarity_scores.append(motif_similarity)
        
        # Compare threats
        for color in ['white', 'black']:
            threat_diff = abs(tactical1['threats'][color] - tactical2['threats'][color])
            threat_similarity = max(0.0, 1.0 - threat_diff / 10.0)
            similarity_scores.append(threat_similarity)
        
        return sum(similarity_scores) / len(similarity_scores)
    
    def _calculate_positional_similarity(self, board: chess.Board, pattern: ChessPatternEnhanced) -> float:
        """Calculate positional similarity"""
        try:
            pattern_board = chess.Board(pattern.fen)
            
            # Compare piece placement
            piece_similarity = self._compare_piece_placement(board, pattern_board)
            
            # Compare pawn structure
            pawn_similarity = self._compare_pawn_structure(board, pattern_board)
            
            # Compare space control
            space_similarity = self._compare_space_control(board, pattern_board)
            
            return (piece_similarity * 0.4 + pawn_similarity * 0.3 + space_similarity * 0.3)
        
        except Exception:
            return 0.0
    
    def _calculate_tactical_similarity_score(self, board: chess.Board, pattern: ChessPatternEnhanced) -> float:
        """Calculate tactical similarity score"""
        if pattern.category != PatternCategory.TACTICAL:
            return 0.3  # Default for non-tactical patterns
        
        try:
            pattern_board = chess.Board(pattern.fen)
            board_features = self.feature_extractor.extract_features(board)
            pattern_features = self.feature_extractor.extract_features(pattern_board)
            
            return self._calculate_tactical_similarity(board_features, pattern_features)
        
        except Exception:
            return 0.0
    
    def _calculate_structural_similarity(self, board: chess.Board, pattern: ChessPatternEnhanced) -> float:
        """Calculate structural similarity"""
        try:
            pattern_board = chess.Board(pattern.fen)
            
            # Compare overall structure
            structure_similarity = 0.0
            
            # Piece count similarity
            board_pieces = len(board.piece_map())
            pattern_pieces = len(pattern_board.piece_map())
            piece_count_similarity = 1.0 - abs(board_pieces - pattern_pieces) / max(1, max(board_pieces, pattern_pieces))
            structure_similarity += piece_count_similarity * 0.3
            
            # Material distribution similarity
            board_material = self._calculate_material_distribution(board)
            pattern_material = self._calculate_material_distribution(pattern_board)
            
            material_similarity = 0.0
            for piece_type in board_material:
                diff = abs(board_material[piece_type] - pattern_material.get(piece_type, 0))
                piece_similarity = 1.0 - diff / max(1, max(board_material[piece_type], pattern_material.get(piece_type, 0)))
                material_similarity += piece_similarity
            
            material_similarity /= len(board_material)
            structure_similarity += material_similarity * 0.7
            
            return structure_similarity
        
        except Exception:
            return 0.0
    
    def _compare_piece_placement(self, board1: chess.Board, board2: chess.Board) -> float:
        """Compare piece placement between two boards"""
        matching_pieces = 0
        total_pieces = 0
        
        for sq in chess.SQUARES:
            piece1 = board1.piece_at(sq)
            piece2 = board2.piece_at(sq)
            
            if piece1 or piece2:
                total_pieces += 1
                if piece1 and piece2 and piece1.piece_type == piece2.piece_type and piece1.color == piece2.color:
                    matching_pieces += 1
        
        return matching_pieces / max(1, total_pieces)
    
    def _compare_pawn_structure(self, board1: chess.Board, board2: chess.Board) -> float:
        """Compare pawn structure between two boards"""
        pawns1 = board1.pieces(chess.PAWN, chess.WHITE).union(board1.pieces(chess.PAWN, chess.BLACK))
        pawns2 = board2.pieces(chess.PAWN, chess.WHITE).union(board2.pieces(chess.PAWN, chess.BLACK))
        
        common_pawns = len(pawns1.intersection(pawns2))
        total_pawns = len(pawns1.union(pawns2))
        
        return common_pawns / max(1, total_pawns)
    
    def _compare_space_control(self, board1: chess.Board, board2: chess.Board) -> float:
        """Compare space control between two boards"""
        control1 = self._calculate_space_control(board1)
        control2 = self._calculate_space_control(board2)
        
        similarity = 0.0
        for color in ['white', 'black']:
            diff = abs(control1[color] - control2[color])
            color_similarity = max(0.0, 1.0 - diff)
            similarity += color_similarity
        
        return similarity / 2.0
    
    def _calculate_space_control(self, board: chess.Board) -> Dict[str, float]:
        """Calculate space control for both sides"""
        control = {'white': 0.0, 'black': 0.0}
        
        for color in [chess.WHITE, chess.BLACK]:
            controlled_squares = set()
            
            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.color == color:
                    controlled_squares.update(board.attacks(sq))
            
            control['white' if color == chess.WHITE else 'black'] = len(controlled_squares) / 64.0
        
        return control
    
    def _calculate_material_distribution(self, board: chess.Board) -> Dict[str, int]:
        """Calculate material distribution"""
        distribution = {}
        
        for color in [chess.WHITE, chess.BLACK]:
            for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                key = f"{chess.piece_name(piece_type)}_{'white' if color == chess.WHITE else 'black'}"
                distribution[key] = len(board.pieces(piece_type, color))
        
        return distribution
    
    def _generate_cache_key(self, board: chess.Board, patterns: List[ChessPatternEnhanced]) -> str:
        """Generate cache key for board and patterns"""
        board_hash = hashlib.md5(board.fen().encode()).hexdigest()[:8]
        pattern_ids = sorted(p.id for p in patterns)
        patterns_hash = hashlib.md5(','.join(pattern_ids).encode()).hexdigest()[:8]
        return f"{board_hash}_{patterns_hash}"
    
    def clear_cache(self):
        """Clear pattern matching cache"""
        if self.cache:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache:
            return {
                'size': self.cache.size(),
                'max_size': self.cache.max_size,
                'enabled': True
            }
        return {'enabled': False}
    
    def shutdown(self):
        """Shutdown the pattern matcher"""
        self.executor.shutdown(wait=True)


class PatternValidator:
    """Comprehensive pattern validation system"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.INTERMEDIATE):
        self.validation_level = validation_level
        self.feature_extractor = TacticalFeatureExtractor()
    
    def validate_pattern(self, pattern: ChessPatternEnhanced) -> ValidationResult:
        """Validate a chess pattern"""
        errors = []
        warnings = []
        corrections = []
        improvements = []
        
        # Basic validation
        basic_result = self._validate_basic_properties(pattern)
        errors.extend(basic_result['errors'])
        warnings.extend(basic_result['warnings'])
        
        # Position validation
        position_result = self._validate_position(pattern)
        errors.extend(position_result['errors'])
        warnings.extend(position_result['warnings'])
        
        # Tactical validation
        if self.validation_level in [ValidationLevel.ADVANCED, ValidationLevel.COMPREHENSIVE]:
            tactical_result = self._validate_tactical_elements(pattern)
            errors.extend(tactical_result['errors'])
            warnings.extend(tactical_result['warnings'])
            improvements.extend(tactical_result['improvements'])
        
        # Comprehensive validation
        if self.validation_level == ValidationLevel.COMPREHENSIVE:
            comprehensive_result = self._validate_comprehensive(pattern)
            errors.extend(comprehensive_result['errors'])
            warnings.extend(comprehensive_result['warnings'])
            improvements.extend(comprehensive_result['improvements'])
        
        # Calculate confidence score
        confidence_score = self._calculate_validation_confidence(errors, warnings, pattern)
        
        # Create corrected pattern if needed
        corrected_pattern = None
        if corrections:
            corrected_pattern = self._apply_corrections(pattern, corrections)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            confidence_score=confidence_score,
            validation_errors=errors,
            validation_warnings=warnings,
            corrected_pattern=corrected_pattern,
            improvement_suggestions=improvements
        )
    
    def _validate_basic_properties(self, pattern: ChessPatternEnhanced) -> Dict[str, List[str]]:
        """Validate basic pattern properties"""
        errors = []
        warnings = []
        
        # Check required fields
        if not pattern.id or not pattern.id.strip():
            errors.append("Pattern ID is required")
        
        if not pattern.name or not pattern.name.strip():
            errors.append("Pattern name is required")
        
        if not pattern.description or not pattern.description.strip():
            warnings.append("Pattern description is missing")
        
        # Check FEN validity
        try:
            chess.Board(pattern.fen)
        except ValueError as e:
            errors.append(f"Invalid FEN: {e}")
        
        # Check move validity
        try:
            if pattern.key_move:
                chess.Move.from_uci(pattern.key_move)
        except ValueError as e:
            errors.append(f"Invalid key move: {e}")
        
        # Check ranges
        if not 0.0 <= pattern.frequency <= 1.0:
            errors.append("Pattern frequency must be between 0.0 and 1.0")
        
        if not 0.0 <= pattern.success_rate <= 1.0:
            errors.append("Pattern success rate must be between 0.0 and 1.0")
        
        if len(pattern.elo_range) != 2 or pattern.elo_range[0] >= pattern.elo_range[1]:
            errors.append("Invalid ELO range")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_position(self, pattern: ChessPatternEnhanced) -> Dict[str, List[str]]:
        """Validate pattern position"""
        errors = []
        warnings = []
        
        try:
            board = chess.Board(pattern.fen)
            
            # Check if position is legal
            if not board.is_valid():
                errors.append("Position is not legal")
            
            # Check if position is reachable
            if board.fullmove_number < 1:
                warnings.append("Position has no move history")
            
            # Check participating pieces
            for piece in pattern.participating_pieces:
                try:
                    sq = chess.parse_square(piece.square)
                    board_piece = board.piece_at(sq)
                    
                    if not board_piece:
                        warnings.append(f"Participating piece {piece.piece_type} not found at {piece.square}")
                    elif board_piece.piece_type.name.lower() != piece.piece_type:
                        warnings.append(f"Piece type mismatch at {piece.square}")
                    elif (board_piece.color == chess.WHITE) != (piece.color == "white"):
                        warnings.append(f"Piece color mismatch at {piece.square}")
                
                except ValueError:
                    errors.append(f"Invalid square notation: {piece.square}")
            
            # Check excluded pieces
            for square in pattern.excluded_pieces:
                try:
                    chess.parse_square(square)
                except ValueError:
                    errors.append(f"Invalid excluded square: {square}")
        
        except Exception as e:
            errors.append(f"Error validating position: {e}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _validate_tactical_elements(self, pattern: ChessPatternEnhanced) -> Dict[str, List[str]]:
        """Validate tactical elements"""
        errors = []
        warnings = []
        improvements = []
        
        if pattern.category == PatternCategory.TACTICAL:
            try:
                board = chess.Board(pattern.fen)
                
                # Check if tactical elements are present
                if pattern.key_move:
                    move = chess.Move.from_uci(pattern.key_move)
                    if move in board.legal_moves:
                        # Analyze tactical value
                        board_copy = board.copy()
                        board_copy.push(move)
                        
                        # Check for actual tactical motifs
                        if 'fork' in pattern.tags.lower():
                            if not self._check_for_fork(board_copy, move.to_square):
                                warnings.append("Pattern claims to be a fork but no fork detected")
                                improvements.append("Verify fork condition or update pattern tags")
                        
                        if 'pin' in pattern.tags.lower():
                            if not self._check_for_pin(board_copy, move.to_square):
                                warnings.append("Pattern claims to be a pin but no pin detected")
                                improvements.append("Verify pin condition or update pattern tags")
                    else:
                        warnings.append("Key move is not legal in the pattern position")
                
                # Validate exchange sequence
                if pattern.exchange_sequence:
                    if not pattern.exchange_sequence.moves:
                        errors.append("Exchange sequence has no moves")
                    else:
                        for move_str in pattern.exchange_sequence.moves:
                            try:
                                chess.Move.from_uci(move_str)
                            except ValueError:
                                errors.append(f"Invalid move in exchange sequence: {move_str}")
            
            except Exception as e:
                errors.append(f"Error validating tactical elements: {e}")
        
        return {'errors': errors, 'warnings': warnings, 'improvements': improvements}
    
    def _validate_comprehensive(self, pattern: ChessPatternEnhanced) -> Dict[str, List[str]]:
        """Comprehensive pattern validation"""
        errors = []
        warnings = []
        improvements = []
        
        try:
            board = chess.Board(pattern.fen)
            
            # Analyze position characteristics
            features = self.feature_extractor.extract_features(board)
            
            # Check game phase consistency
            detected_phase = self._detect_game_phase(board)
            if pattern.game_phase != "any" and pattern.game_phase != detected_phase:
                warnings.append(f"Game phase mismatch: pattern says {pattern.game_phase}, position looks like {detected_phase}")
            
            # Check material balance consistency
            material_balance = features['material_balance']
            if abs(material_balance) > 1000 and pattern.category != PatternCategory.TACTICAL:
                warnings.append("Large material imbalance in non-tactical pattern")
            
            # Check pattern uniqueness (simplified)
            if pattern.frequency < 0.1:
                improvements.append("Consider increasing pattern frequency if it's more common")
            
            # Check success rate realism
            if pattern.success_rate > 0.9 and pattern.category == PatternCategory.TACTICAL:
                warnings.append("Very high success rate for tactical pattern may be unrealistic")
            
            # Suggest improvements based on analysis
            if not pattern.participating_pieces:
                improvements.append("Add participating pieces for better pattern matching")
            
            if len(pattern.tags) < 2:
                improvements.append("Add more descriptive tags for better categorization")
        
        except Exception as e:
            errors.append(f"Error in comprehensive validation: {e}")
        
        return {'errors': errors, 'warnings': warnings, 'improvements': improvements}
    
    def _check_for_fork(self, board: chess.Board, square: int) -> bool:
        """Check if position contains a fork"""
        piece = board.piece_at(square)
        if not piece or piece.piece_type not in [chess.KNIGHT, chess.BISHOP]:
            return False
        
        attacks = board.attacks(square)
        valuable_targets = 0
        
        for target_sq in attacks:
            target = board.piece_at(target_sq)
            if target and target.color != piece.color:
                if target.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]:
                    valuable_targets += 1
        
        return valuable_targets >= 2
    
    def _check_for_pin(self, board: chess.Board, square: int) -> bool:
        """Check if position contains a pin"""
        piece = board.piece_at(square)
        if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
            return False
        
        enemy_king_sq = board.king(not piece.color)
        if enemy_king_sq is None:
            return False
        
        # Check if piece can pin along line to king
        direction = self._get_line_direction(square, enemy_king_sq)
        if direction is None:
            return False
        
        # Look for enemy piece between attacker and king
        current_sq = square + direction
        while 0 <= current_sq < 64:
            target = board.piece_at(current_sq)
            if target:
                if target.color == piece.color:
                    break
                else:
                    return True  # Found enemy piece to pin
            current_sq += direction
        
        return False
    
    def _get_line_direction(self, from_sq: int, to_sq: int) -> Optional[int]:
        """Get direction vector between two squares on same line"""
        from_file, from_rank = chess.square_file(from_sq), chess.square_rank(from_sq)
        to_file, to_rank = chess.square_file(to_sq), chess.square_rank(to_sq)
        
        file_diff = to_file - from_file
        rank_diff = to_rank - from_rank
        
        if file_diff == 0:  # Same file
            return 8 if rank_diff > 0 else -8
        elif rank_diff == 0:  # Same rank
            return 1 if file_diff > 0 else -1
        elif abs(file_diff) == abs(rank_diff):  # Same diagonal
            if file_diff > 0 and rank_diff > 0:
                return 9
            elif file_diff > 0 and rank_diff < 0:
                return -7
            elif file_diff < 0 and rank_diff > 0:
                return 7
            else:
                return -9
        
        return None
    
    def _detect_game_phase(self, board: chess.Board) -> str:
        """Detect game phase from position"""
        piece_count = sum(len(board.pieces(pt, chess.WHITE)) + len(board.pieces(pt, chess.BLACK)) 
                         for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
        
        if piece_count >= 20:
            return "opening"
        elif piece_count >= 10:
            return "middlegame"
        else:
            return "endgame"
    
    def _calculate_validation_confidence(self, errors: List[str], warnings: List[str], pattern: ChessPatternEnhanced) -> float:
        """Calculate overall validation confidence score"""
        base_confidence = 1.0
        
        # Penalize errors heavily
        error_penalty = len(errors) * 0.3
        base_confidence -= error_penalty
        
        # Penalize warnings moderately
        warning_penalty = len(warnings) * 0.1
        base_confidence -= warning_penalty
        
        # Bonus for complete patterns
        completeness_bonus = 0.0
        if pattern.participating_pieces:
            completeness_bonus += 0.1
        if len(pattern.tags) >= 3:
            completeness_bonus += 0.05
        if pattern.exchange_sequence:
            completeness_bonus += 0.05
        
        base_confidence += completeness_bonus
        
        return max(0.0, min(1.0, base_confidence))
    
    def _apply_corrections(self, pattern: ChessPatternEnhanced, corrections: List[str]) -> ChessPatternEnhanced:
        """Apply corrections to create a corrected pattern"""
        # This would implement specific corrections based on identified issues
        # For now, return a copy of the original pattern
        return ChessPatternEnhanced(
            id=pattern.id,
            name=pattern.name,
            description=pattern.description,
            category=pattern.category,
            fen=pattern.fen,
            key_move=pattern.key_move,
            alternative_moves=pattern.alternative_moves.copy(),
            participating_pieces=pattern.participating_pieces.copy(),
            excluded_pieces=pattern.excluded_pieces.copy(),
            exchange_sequence=pattern.exchange_sequence,
            exchange_type=pattern.exchange_type,
            frequency=pattern.frequency,
            success_rate=pattern.success_rate,
            elo_range=pattern.elo_range,
            game_phase=pattern.game_phase,
            conditions=pattern.conditions.copy(),
            tags=pattern.tags.copy(),
            created_at=pattern.created_at,
            updated_at=pattern.updated_at,
            author=pattern.author,
            enabled=pattern.enabled,
            confidence_threshold=pattern.confidence_threshold
        )


class PatternTestingFramework:
    """Comprehensive testing framework for pattern detection"""
    
    def __init__(self, pattern_detector: EnhancedPatternDetector):
        self.detector = pattern_detector
        self.test_results = []
    
    def run_comprehensive_tests(self, test_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive tests on pattern detection"""
        results = {
            'total_positions': len(test_positions),
            'successful_detections': 0,
            'failed_detections': 0,
            'average_confidence': 0.0,
            'performance_metrics': {},
            'category_performance': {},
            'detailed_results': []
        }
        
        total_confidence = 0.0
        category_stats = defaultdict(lambda: {'count': 0, 'confidence': 0.0})
        
        start_time = time.time()
        
        for i, test_case in enumerate(test_positions):
            try:
                board = chess.Board(test_case['fen'])
                expected_patterns = test_case.get('expected_patterns', [])
                
                # Run pattern detection
                detection_start = time.time()
                detected_patterns = self.detector.detect_patterns(board)
                detection_time = time.time() - detection_start
                
                # Evaluate results
                evaluation = self._evaluate_detection(detected_patterns, expected_patterns)
                
                # Update statistics
                if evaluation['success']:
                    results['successful_detections'] += 1
                else:
                    results['failed_detections'] += 1
                
                total_confidence += evaluation['max_confidence']
                
                # Category performance
                for pattern in detected_patterns:
                    category = pattern.pattern.category.value
                    category_stats[category]['count'] += 1
                    category_stats[category]['confidence'] += pattern.confidence
                
                # Store detailed result
                detailed_result = {
                    'test_index': i,
                    'fen': test_case['fen'],
                    'detection_time': detection_time,
                    'detected_count': len(detected_patterns),
                    'expected_count': len(expected_patterns),
                    'evaluation': evaluation
                }
                results['detailed_results'].append(detailed_result)
                
            except Exception as e:
                logger.error(f"Error testing position {i}: {e}")
                results['failed_detections'] += 1
        
        total_time = time.time() - start_time
        
        # Calculate final statistics
        results['average_confidence'] = total_confidence / max(1, len(test_positions))
        results['performance_metrics'] = {
            'total_time': total_time,
            'average_time_per_position': total_time / len(test_positions),
            'positions_per_second': len(test_positions) / total_time
        }
        
        # Category performance
        for category, stats in category_stats.items():
            if stats['count'] > 0:
                results['category_performance'][category] = {
                    'count': stats['count'],
                    'average_confidence': stats['confidence'] / stats['count']
                }
        
        return results
    
    def _evaluate_detection(self, detected_patterns: List[PatternMatch], expected_patterns: List[str]) -> Dict[str, Any]:
        """Evaluate pattern detection results"""
        evaluation = {
            'success': False,
            'max_confidence': 0.0,
            'pattern_matches': [],
            'missing_patterns': [],
            'unexpected_patterns': []
        }
        
        if detected_patterns:
            evaluation['max_confidence'] = max(p.confidence for p in detected_patterns)
        
        # Check for expected patterns
        detected_ids = {p.pattern.id for p in detected_patterns}
        expected_ids = set(expected_patterns)
        
        evaluation['pattern_matches'] = list(detected_ids.intersection(expected_ids))
        evaluation['missing_patterns'] = list(expected_ids - detected_ids)
        evaluation['unexpected_patterns'] = list(detected_ids - expected_ids)
        
        # Consider success if at least one expected pattern was detected
        evaluation['success'] = len(evaluation['pattern_matches']) > 0
        
        return evaluation
    
    def benchmark_performance(self, num_positions: int = 1000) -> Dict[str, Any]:
        """Benchmark pattern detection performance"""
        # Generate random test positions
        test_positions = self._generate_test_positions(num_positions)
        
        results = {
            'num_positions': num_positions,
            'total_time': 0.0,
            'average_time': 0.0,
            'patterns_per_second': 0.0,
            'memory_usage': 0.0
        }
        
        start_time = time.time()
        
        for test_case in test_positions:
            try:
                board = chess.Board(test_case['fen'])
                self.detector.detect_patterns(board)
            except Exception as e:
                logger.error(f"Error in benchmark: {e}")
        
        total_time = time.time() - start_time
        
        results['total_time'] = total_time
        results['average_time'] = total_time / num_positions
        results['patterns_per_second'] = num_positions / total_time
        
        return results
    
    def _generate_test_positions(self, num_positions: int) -> List[Dict[str, Any]]:
        """Generate test positions for benchmarking"""
        positions = []
        
        # Start from initial position and make random moves
        for i in range(num_positions):
            board = chess.Board()
            
            # Make random moves
            for _ in range(np.random.randint(10, 40)):
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    move = np.random.choice(legal_moves)
                    board.push(move)
                else:
                    break
            
            positions.append({
                'fen': board.fen(),
                'expected_patterns': []  # No expectations for benchmarking
            })
        
        return positions
