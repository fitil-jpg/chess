"""
Enhanced Chess Pattern Detector - 3.1 Розробка детектора шахових патернів

A comprehensive pattern detection system that combines multiple detection strategies:
1. Position-based pattern matching using FEN
2. Tactical pattern detection (forks, pins, skewers, etc.)
3. Exchange sequence analysis
4. Strategic pattern recognition
5. Dynamic pattern learning from games
"""

from __future__ import annotations
import chess
import chess.syzygy
import logging
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from pathlib import Path
import numpy as np
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class PatternCategory(Enum):
    """Pattern categories for classification"""
    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    OPENING = "opening"
    ENDGAME = "endgame"
    POSITIONAL = "positional"
    EXCHANGE = "exchange"
    DEFENSIVE = "defensive"
    ATTACKING = "attacking"


class PatternConfidence(Enum):
    """Confidence levels for pattern detection"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class PatternPiece:
    """Represents a piece involved in a pattern"""
    square: str
    piece_type: str
    color: str
    role: str  # attacker, defender, target, supporter, observer
    importance: float = 0.5
    move_sequence: Optional[List[str]] = None


@dataclass
class ExchangeSequence:
    """Represents an exchange sequence"""
    moves: List[str]
    material_balance: float
    probability: float
    depth: int
    estimated_gain: float = 0.0


@dataclass
class ChessPatternEnhanced:
    """Enhanced chess pattern with comprehensive metadata"""
    id: str
    name: str
    description: str
    category: PatternCategory
    fen: str
    key_move: str
    alternative_moves: List[str] = field(default_factory=list)
    participating_pieces: List[PatternPiece] = field(default_factory=list)
    excluded_pieces: List[str] = field(default_factory=list)
    exchange_sequence: Optional[ExchangeSequence] = None
    exchange_type: Optional[str] = None
    frequency: float = 0.5
    success_rate: float = 0.5
    elo_range: Tuple[int, int] = (800, 2800)
    game_phase: str = "any"
    conditions: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    author: str = "system"
    enabled: bool = True
    confidence_threshold: float = 0.5


@dataclass
class PatternMatch:
    """Result of pattern matching"""
    pattern: ChessPatternEnhanced
    confidence: float
    relevant_pieces: List[PatternPiece]
    filtered_pieces: List[str]
    suggested_move: str
    alternative_moves: List[str]
    explanation: str
    tactical_value: float = 0.0
    strategic_value: float = 0.0
    risk_assessment: float = 0.0


class TacticalAnalyzer:
    """Analyzes tactical patterns in chess positions"""
    
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
    
    def detect_forks(self, board: chess.Board) -> List[Dict[str, Any]]:
        """Detect fork opportunities"""
        forks = []
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece:
                continue
                
            # Test the move
            test_board = board.copy()
            test_board.push(move)
            
            # Check for knight forks
            if piece.piece_type == chess.KNIGHT:
                targets = self._find_knight_fork_targets(test_board, move.to_square, piece.color)
                if len(targets) >= 2:
                    forks.append({
                        'move': move.uci(),
                        'type': 'knight_fork',
                        'targets': targets,
                        'value': self._evaluate_fork_value(targets)
                    })
            
            # Check for bishop forks
            elif piece.piece_type == chess.BISHOP:
                targets = self._find_bishop_fork_targets(test_board, move.to_square, piece.color)
                if len(targets) >= 2:
                    forks.append({
                        'move': move.uci(),
                        'type': 'bishop_fork',
                        'targets': targets,
                        'value': self._evaluate_fork_value(targets)
                    })
        
        return sorted(forks, key=lambda x: x['value'], reverse=True)
    
    def detect_pins(self, board: chess.Board) -> List[Dict[str, Any]]:
        """Detect pin opportunities"""
        pins = []
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                continue
            
            test_board = board.copy()
            test_board.push(move)
            
            pin_info = self._analyze_pin(test_board, move.to_square, piece.color)
            if pin_info:
                pins.append({
                    'move': move.uci(),
                    'type': 'pin',
                    'pinned_piece': pin_info['pinned_piece'],
                    'pinned_to': pin_info['pinned_to'],
                    'value': pin_info['value']
                })
        
        return sorted(pins, key=lambda x: x['value'], reverse=True)
    
    def detect_skewers(self, board: chess.Board) -> List[Dict[str, Any]]:
        """Detect skewer opportunities"""
        skewers = []
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.piece_type not in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                continue
            
            test_board = board.copy()
            test_board.push(move)
            
            skewer_info = self._analyze_skewer(test_board, move.to_square, piece.color)
            if skewer_info:
                skewers.append({
                    'move': move.uci(),
                    'type': 'skewer',
                    'skewered_piece': skewer_info['skewered_piece'],
                    'target_piece': skewer_info['target_piece'],
                    'value': skewer_info['value']
                })
        
        return sorted(skewers, key=lambda x: x['value'], reverse=True)
    
    def detect_discovered_attacks(self, board: chess.Board) -> List[Dict[str, Any]]:
        """Detect discovered attack opportunities"""
        discoveries = []
        
        for move in board.legal_moves:
            # Check if moving piece reveals attack
            if self._creates_discovered_attack(board, move):
                value = self._evaluate_discovered_attack(board, move)
                discoveries.append({
                    'move': move.uci(),
                    'type': 'discovered_attack',
                    'value': value
                })
        
        return sorted(discoveries, key=lambda x: x['value'], reverse=True)
    
    def detect_hanging_pieces(self, board: chess.Board) -> List[Dict[str, Any]]:
        """Detect hanging pieces"""
        hanging = []
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece or piece.color == board.turn:
                continue
            
            attackers = board.attackers(board.turn, square)
            defenders = board.attackers(not board.turn, square)
            
            if len(attackers) > len(defenders) and piece.piece_type != chess.PAWN:
                capture_moves = [m for m in board.legal_moves if m.to_square == square]
                if capture_moves:
                    best_capture = min(capture_moves, 
                                     key=lambda m: self.piece_values[board.piece_at(m.from_square).piece_type])
                    
                    hanging.append({
                        'square': chess.square_name(square),
                        'piece': chess.piece_name(piece.piece_type),
                        'capture_move': best_capture.uci(),
                        'value': self.piece_values[piece.piece_type],
                        'attackers': len(attackers),
                        'defenders': len(defenders)
                    })
        
        return sorted(hanging, key=lambda x: x['value'], reverse=True)
    
    def _find_knight_fork_targets(self, board: chess.Board, knight_sq: int, color: chess.Color) -> List[str]:
        """Find targets for knight fork"""
        targets = []
        attacks = board.attacks(knight_sq)
        
        for target_sq in attacks:
            target_piece = board.piece_at(target_sq)
            if target_piece and target_piece.color != color:
                if target_piece.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]:
                    targets.append(f"{chess.piece_name(target_piece.piece_type)}@{chess.square_name(target_sq)}")
        
        return targets
    
    def _find_bishop_fork_targets(self, board: chess.Board, bishop_sq: int, color: chess.Color) -> List[str]:
        """Find targets for bishop fork"""
        targets = []
        attacks = board.attacks(bishop_sq)
        
        for target_sq in attacks:
            target_piece = board.piece_at(target_sq)
            if target_piece and target_piece.color != color:
                if target_piece.piece_type in [chess.KING, chess.QUEEN, chess.ROOK]:
                    targets.append(f"{chess.piece_name(target_piece.piece_type)}@{chess.square_name(target_sq)}")
        
        return targets
    
    def _evaluate_fork_value(self, targets: List[str]) -> float:
        """Evaluate the value of a fork"""
        value = 0.0
        for target in targets:
            piece_name = target.split('@')[0]
            if 'king' in piece_name:
                value += 1000  # Check/checkmate potential
            elif 'queen' in piece_name:
                value += 900
            elif 'rook' in piece_name:
                value += 500
            elif 'bishop' in piece_name or 'knight' in piece_name:
                value += 300
        return value
    
    def _analyze_pin(self, board: chess.Board, attacker_sq: int, attacker_color: chess.Color) -> Optional[Dict[str, Any]]:
        """Analyze if a piece creates a pin"""
        enemy_king_sq = board.king(not attacker_color)
        if enemy_king_sq is None:
            return None
        
        # Check if attacker can pin along line to king
        direction = self._get_line_direction(attacker_sq, enemy_king_sq)
        if direction is None:
            return None
        
        # Look for piece between attacker and king
        current_sq = attacker_sq + direction
        pinned_piece_sq = None
        
        while 0 <= current_sq < 64:
            piece = board.piece_at(current_sq)
            if piece:
                if piece.color == attacker_color:
                    break  # Friendly piece blocks
                else:
                    if pinned_piece_sq is None:
                        pinned_piece_sq = current_sq
                    else:
                        break  # Second enemy piece blocks
            current_sq += direction
        
        if pinned_piece_sq:
            pinned_piece = board.piece_at(pinned_piece_sq)
            if pinned_piece:
                return {
                    'pinned_piece': f"{chess.piece_name(pinned_piece.piece_type)}@{chess.square_name(pinned_piece_sq)}",
                    'pinned_to': f"king@{chess.square_name(enemy_king_sq)}",
                    'value': self.piece_values[pinned_piece.piece_type] * 0.8
                }
        
        return None
    
    def _analyze_skewer(self, board: chess.Board, attacker_sq: int, attacker_color: chess.Color) -> Optional[Dict[str, Any]]:
        """Analyze if a piece creates a skewer"""
        enemy_king_sq = board.king(not attacker_color)
        if enemy_king_sq is None:
            return None
        
        direction = self._get_line_direction(attacker_sq, enemy_king_sq)
        if direction is None:
            return None
        
        # Look for valuable piece that can be skewered
        current_sq = attacker_sq + direction
        valuable_piece_sq = None
        
        while 0 <= current_sq < 64:
            piece = board.piece_at(current_sq)
            if piece:
                if piece.color == attacker_color:
                    break
                else:
                    if current_sq == enemy_king_sq:
                        break  # Reached king
                    elif piece.piece_type in [chess.QUEEN, chess.ROOK]:
                        valuable_piece_sq = current_sq
                    else:
                        break  # Lesser value piece blocks
            current_sq += direction
        
        if valuable_piece_sq:
            valuable_piece = board.piece_at(valuable_piece_sq)
            if valuable_piece:
                return {
                    'skewered_piece': f"{chess.piece_name(valuable_piece.piece_type)}@{chess.square_name(valuable_piece_sq)}",
                    'target_piece': f"king@{chess.square_name(enemy_king_sq)}",
                    'value': self.piece_values[valuable_piece.piece_type] * 0.9
                }
        
        return None
    
    def _creates_discovered_attack(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move creates a discovered attack"""
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
        
        # Get attacks before move
        attacks_before = set()
        for sq in chess.SQUARES:
            if sq != move.from_square:
                p = board.piece_at(sq)
                if p and p.color == board.turn:
                    attacks_before.update(board.attacks(sq))
        
        # Test move
        test_board = board.copy()
        test_board.push(move)
        
        # Get attacks after move
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
    
    def _evaluate_discovered_attack(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate the value of a discovered attack"""
        test_board = board.copy()
        test_board.push(move)
        
        value = 0.0
        for sq in chess.SQUARES:
            target = test_board.piece_at(sq)
            if target and target.color != board.turn:
                attackers = test_board.attackers(board.turn, sq)
                if attackers:
                    value += self.piece_values[target.piece_type] * 0.6
        
        return value
    
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


class ExchangeAnalyzer:
    """Analyzes exchange sequences and material balance"""
    
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
    
    def analyze_exchange(self, board: chess.Board, move: chess.Move, depth: int = 3) -> Optional[ExchangeSequence]:
        """Analyze exchange sequence for a given move"""
        if not board.is_capture(move) and not board.is_en_passant(move):
            return None
        
        sequence = []
        current_board = board.copy()
        current_board.push(move)
        sequence.append(move.uci())
        
        material_balance = self._calculate_capture_value(board, move)
        current_color = not board.turn
        
        # Continue recaptures on same square
        for _ in range(depth - 1):
            recaptures = [m for m in current_board.legal_moves if m.to_square == move.to_square]
            if not recaptures:
                break
            
            # Choose least valuable attacker
            best_recapture = min(recaptures, 
                               key=lambda m: self.piece_values[current_board.piece_at(m.from_square).piece_type])
            
            capture_value = self._calculate_capture_value(current_board, best_recapture)
            if current_color == board.turn:
                material_balance += capture_value
            else:
                material_balance -= capture_value
            
            sequence.append(best_recapture.uci())
            current_board.push(best_recapture)
            current_color = not current_color
        
        return ExchangeSequence(
            moves=sequence,
            material_balance=material_balance,
            probability=self._calculate_exchange_probability(material_balance),
            depth=len(sequence),
            estimated_gain=material_balance * 0.8
        )
    
    def _calculate_capture_value(self, board: chess.Board, move: chess.Move) -> float:
        """Calculate material value of a capture"""
        captured_piece = board.piece_at(move.to_square)
        if captured_piece:
            return self.piece_values[captured_piece.piece_type]
        
        # Check for en passant
        if board.is_en_passant(move):
            ep_sq = move.to_square + (-8 if board.turn == chess.WHITE else 8)
            ep_piece = board.piece_at(ep_sq)
            if ep_piece and ep_piece.piece_type == chess.PAWN:
                return self.piece_values[chess.PAWN]
        
        return 0.0
    
    def _calculate_exchange_probability(self, material_balance: float) -> float:
        """Calculate probability of exchange being favorable"""
        if material_balance > 200:
            return min(0.95, 0.5 + material_balance / 2000)
        elif material_balance < -200:
            return max(0.05, 0.5 + material_balance / 2000)
        else:
            return 0.5


class PatternMatcher:
    """Matches positions against stored patterns"""
    
    def __init__(self, pattern_storage_path: Optional[str] = None):
        self.patterns: List[ChessPatternEnhanced] = []
        self.pattern_storage_path = pattern_storage_path or "patterns"
        self.load_patterns()
    
    def load_patterns(self):
        """Load patterns from storage"""
        patterns_dir = Path(self.pattern_storage_path)
        if not patterns_dir.exists():
            return
        
        for pattern_file in patterns_dir.glob("*.json"):
            try:
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    pattern_data = json.load(f)
                    pattern = self._deserialize_pattern(pattern_data)
                    if pattern.enabled:
                        self.patterns.append(pattern)
            except Exception as e:
                logger.warning(f"Failed to load pattern from {pattern_file}: {e}")
    
    def find_matching_patterns(self, board: chess.Board, max_patterns: int = 10) -> List[Tuple[ChessPatternEnhanced, float]]:
        """Find patterns matching the current position"""
        matches = []
        board_fen = board.fen()
        board_fen_partial = board.board_fen()  # Without move counters
        
        for pattern in self.patterns:
            similarity = self._calculate_pattern_similarity(board, pattern, board_fen, board_fen_partial)
            if similarity >= pattern.confidence_threshold:
                matches.append((pattern, similarity))
        
        # Sort by similarity and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_patterns]
    
    def _calculate_pattern_similarity(self, board: chess.Board, pattern: ChessPatternEnhanced, 
                                    full_fen: str, partial_fen: str) -> float:
        """Calculate similarity between board position and pattern"""
        # Exact FEN match
        if pattern.fen == full_fen:
            return 1.0
        
        # Partial FEN match (piece placement only)
        if pattern.fen == partial_fen:
            return 0.9
        
        # Piece-based similarity
        piece_similarity = self._calculate_piece_similarity(board, pattern)
        
        # Tactical similarity
        tactical_similarity = self._calculate_tactical_similarity(board, pattern)
        
        # Positional similarity
        positional_similarity = self._calculate_positional_similarity(board, pattern)
        
        # Weighted combination
        total_similarity = (
            piece_similarity * 0.4 +
            tactical_similarity * 0.4 +
            positional_similarity * 0.2
        )
        
        return min(1.0, total_similarity)
    
    def _calculate_piece_similarity(self, board: chess.Board, pattern: ChessPatternEnhanced) -> float:
        """Calculate similarity based on piece placement"""
        pattern_board = chess.Board(pattern.fen)
        
        matching_pieces = 0
        total_pattern_pieces = 0
        
        for square in chess.SQUARES:
            pattern_piece = pattern_board.piece_at(square)
            if pattern_piece:
                total_pattern_pieces += 1
                board_piece = board.piece_at(square)
                if board_piece and board_piece.piece_type == pattern_piece.piece_type and \
                   board_piece.color == pattern_piece.color:
                    matching_pieces += 1
        
        return matching_pieces / max(1, total_pattern_pieces)
    
    def _calculate_tactical_similarity(self, board: chess.Board, pattern: ChessPatternEnhanced) -> float:
        """Calculate similarity based on tactical elements"""
        # Simplified tactical similarity based on pattern category
        if pattern.category == PatternCategory.TACTICAL:
            # Check for similar tactical opportunities
            return 0.5  # Placeholder - would need actual tactical analysis
        
        return 0.3  # Default tactical similarity
    
    def _calculate_positional_similarity(self, board: chess.Board, pattern: ChessPatternEnhanced) -> float:
        """Calculate similarity based on positional elements"""
        # Simplified positional similarity
        pattern_board = chess.Board(pattern.fen)
        
        # Compare pawn structures
        board_pawns = board.pieces(chess.PAWN, chess.WHITE).union(board.pieces(chess.PAWN, chess.BLACK))
        pattern_pawns = pattern_board.pieces(chess.PAWN, chess.WHITE).union(pattern_board.pieces(chess.PAWN, chess.BLACK))
        
        common_pawns = len(board_pawns.intersection(pattern_pawns))
        total_pawns = max(1, len(board_pawns.union(pattern_pawns)))
        
        return common_pawns / total_pawns
    
    def _deserialize_pattern(self, data: Dict[str, Any]) -> ChessPatternEnhanced:
        """Deserialize pattern from dictionary"""
        participating_pieces = []
        for piece_data in data.get('participating_pieces', []):
            participating_pieces.append(PatternPiece(**piece_data))
        
        exchange_sequence = None
        if data.get('exchange_sequence'):
            seq_data = data['exchange_sequence']
            exchange_sequence = ExchangeSequence(**seq_data)
        
        return ChessPatternEnhanced(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            category=PatternCategory(data['category']),
            fen=data['fen'],
            key_move=data['key_move'],
            alternative_moves=data.get('alternative_moves', []),
            participating_pieces=participating_pieces,
            excluded_pieces=data.get('excluded_pieces', []),
            exchange_sequence=exchange_sequence,
            exchange_type=data.get('exchange_type'),
            frequency=data.get('frequency', 0.5),
            success_rate=data.get('success_rate', 0.5),
            elo_range=tuple(data.get('elo_range', [800, 2800])),
            game_phase=data.get('game_phase', 'any'),
            conditions=data.get('conditions', {}),
            tags=data.get('tags', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            author=data.get('author', 'system'),
            enabled=data.get('enabled', True),
            confidence_threshold=data.get('confidence_threshold', 0.5)
        )


class EnhancedPatternDetector:
    """Main enhanced pattern detector combining all analysis components"""
    
    def __init__(self, pattern_storage_path: Optional[str] = None):
        self.tactical_analyzer = TacticalAnalyzer()
        self.exchange_analyzer = ExchangeAnalyzer()
        self.pattern_matcher = PatternMatcher(pattern_storage_path)
        self.detected_patterns: List[PatternMatch] = []
        
        # Configuration
        self.max_patterns_per_analysis = 10
        self.min_confidence_threshold = 0.3
        self.enable_dynamic_patterns = True
        self.enable_exchange_analysis = True
        
    def detect_patterns(self, board: chess.Board, max_patterns: int = None) -> List[PatternMatch]:
        """Main pattern detection method"""
        if max_patterns is None:
            max_patterns = self.max_patterns_per_analysis
        
        all_matches = []
        
        # 1. Pattern matching against stored patterns
        stored_matches = self._detect_stored_patterns(board)
        all_matches.extend(stored_matches)
        
        # 2. Tactical pattern detection
        if self.enable_dynamic_patterns:
            tactical_matches = self._detect_tactical_patterns(board)
            all_matches.extend(tactical_matches)
        
        # 3. Exchange pattern analysis
        if self.enable_exchange_analysis:
            exchange_matches = self._detect_exchange_patterns(board)
            all_matches.extend(exchange_matches)
        
        # 4. Strategic pattern detection
        strategic_matches = self._detect_strategic_patterns(board)
        all_matches.extend(strategic_matches)
        
        # Sort by confidence and filter
        all_matches.sort(key=lambda m: m.confidence, reverse=True)
        filtered_matches = [m for m in all_matches if m.confidence >= self.min_confidence_threshold]
        
        self.detected_patterns = filtered_matches[:max_patterns]
        return self.detected_patterns
    
    def _detect_stored_patterns(self, board: chess.Board) -> List[PatternMatch]:
        """Detect patterns from stored pattern database"""
        matches = []
        stored_patterns = self.pattern_matcher.find_matching_patterns(board)
        
        for pattern, similarity in stored_patterns:
            # Create pattern match
            match = PatternMatch(
                pattern=pattern,
                confidence=similarity,
                relevant_pieces=pattern.participating_pieces,
                filtered_pieces=pattern.excluded_pieces,
                suggested_move=pattern.key_move,
                alternative_moves=pattern.alternative_moves,
                explanation=f"Matched stored pattern: {pattern.name}",
                tactical_value=self._evaluate_tactical_value(pattern),
                strategic_value=self._evaluate_strategic_value(pattern),
                risk_assessment=self._assess_risk(pattern)
            )
            matches.append(match)
        
        return matches
    
    def _detect_tactical_patterns(self, board: chess.Board) -> List[PatternMatch]:
        """Detect tactical patterns dynamically"""
        matches = []
        
        # Detect forks
        forks = self.tactical_analyzer.detect_forks(board)
        for fork in forks[:3]:  # Limit top forks
            pattern = self._create_dynamic_fork_pattern(board, fork)
            match = PatternMatch(
                pattern=pattern,
                confidence=0.8,
                relevant_pieces=pattern.participating_pieces,
                filtered_pieces=[],
                suggested_move=fork['move'],
                alternative_moves=[],
                explanation=f"Dynamic fork opportunity: {fork['type']}",
                tactical_value=fork['value'],
                strategic_value=0.0,
                risk_assessment=0.2
            )
            matches.append(match)
        
        # Detect pins
        pins = self.tactical_analyzer.detect_pins(board)
        for pin in pins[:2]:  # Limit top pins
            pattern = self._create_dynamic_pin_pattern(board, pin)
            match = PatternMatch(
                pattern=pattern,
                confidence=0.7,
                relevant_pieces=pattern.participating_pieces,
                filtered_pieces=[],
                suggested_move=pin['move'],
                alternative_moves=[],
                explanation=f"Dynamic pin opportunity: {pin['type']}",
                tactical_value=pin['value'],
                strategic_value=0.0,
                risk_assessment=0.15
            )
            matches.append(match)
        
        # Detect hanging pieces
        hanging = self.tactical_analyzer.detect_hanging_pieces(board)
        for hang in hanging[:2]:  # Limit top hanging pieces
            pattern = self._create_dynamic_hanging_pattern(board, hang)
            match = PatternMatch(
                pattern=pattern,
                confidence=0.9,
                relevant_pieces=pattern.participating_pieces,
                filtered_pieces=[],
                suggested_move=hang['capture_move'],
                alternative_moves=[],
                explanation=f"Hanging piece: {hang['piece']} at {hang['square']}",
                tactical_value=hang['value'],
                strategic_value=0.0,
                risk_assessment=0.1
            )
            matches.append(match)
        
        return matches
    
    def _detect_exchange_patterns(self, board: chess.Board) -> List[PatternMatch]:
        """Detect exchange patterns"""
        matches = []
        
        for move in board.legal_moves:
            if board.is_capture(move):
                exchange = self.exchange_analyzer.analyze_exchange(board, move)
                if exchange and abs(exchange.material_balance) > 100:
                    pattern = self._create_exchange_pattern(board, move, exchange)
                    confidence = min(0.9, 0.5 + abs(exchange.material_balance) / 1000)
                    
                    match = PatternMatch(
                        pattern=pattern,
                        confidence=confidence,
                        relevant_pieces=pattern.participating_pieces,
                        filtered_pieces=[],
                        suggested_move=move.uci(),
                        alternative_moves=[],
                        explanation=f"Exchange sequence: {exchange.material_balance:+.0f} material",
                        tactical_value=abs(exchange.material_balance),
                        strategic_value=exchange.estimated_gain * 0.5,
                        risk_assessment=max(0.0, abs(exchange.material_balance) / 1000 - 0.3)
                    )
                    matches.append(match)
        
        return matches[:3]  # Limit top exchanges
    
    def _detect_strategic_patterns(self, board: chess.Board) -> List[PatternMatch]:
        """Detect strategic patterns"""
        matches = []
        
        # Detect pawn structure patterns
        pawn_patterns = self._analyze_pawn_structure(board)
        for pattern_info in pawn_patterns:
            pattern = self._create_strategic_pattern(board, pattern_info)
            match = PatternMatch(
                pattern=pattern,
                confidence=0.6,
                relevant_pieces=pattern.participating_pieces,
                filtered_pieces=[],
                suggested_move=pattern_info.get('suggested_move', ''),
                alternative_moves=[],
                explanation=f"Strategic pattern: {pattern_info['name']}",
                tactical_value=0.0,
                strategic_value=pattern_info.get('value', 0.0),
                risk_assessment=0.2
            )
            matches.append(match)
        
        return matches
    
    def _create_dynamic_fork_pattern(self, board: chess.Board, fork_info: Dict[str, Any]) -> ChessPatternEnhanced:
        """Create a dynamic fork pattern"""
        move = chess.Move.from_uci(fork_info['move'])
        
        participating_pieces = [
            PatternPiece(
                square=chess.square_name(move.to_square),
                piece_type="knight" if "knight" in fork_info['type'] else "bishop",
                color="white" if board.turn == chess.WHITE else "black",
                role="attacker",
                importance=1.0
            )
        ]
        
        # Add target pieces
        for target in fork_info['targets']:
            target_square = target.split('@')[1]
            target_piece = target.split('@')[0]
            participating_pieces.append(PatternPiece(
                square=target_square,
                piece_type=target_piece,
                color="black" if board.turn == chess.WHITE else "white",
                role="target",
                importance=0.8
            ))
        
        return ChessPatternEnhanced(
            id=f"dynamic_fork_{hash(board.fen()) % 10000}",
            name=f"Dynamic {fork_info['type'].replace('_', ' ').title()}",
            description=f"Dynamic {fork_info['type']} opportunity detected",
            category=PatternCategory.TACTICAL,
            fen=board.fen(),
            key_move=fork_info['move'],
            participating_pieces=participating_pieces,
            frequency=0.3,
            success_rate=0.8,
            game_phase=self._determine_game_phase(board),
            tags=["fork", "dynamic", "tactical"]
        )
    
    def _create_dynamic_pin_pattern(self, board: chess.Board, pin_info: Dict[str, Any]) -> ChessPatternEnhanced:
        """Create a dynamic pin pattern"""
        move = chess.Move.from_uci(pin_info['move'])
        piece = board.piece_at(move.from_square)
        
        participating_pieces = [
            PatternPiece(
                square=chess.square_name(move.to_square),
                piece_type=chess.piece_name(piece.piece_type),
                color="white" if piece.color == chess.WHITE else "black",
                role="attacker",
                importance=1.0
            ),
            PatternPiece(
                square=pin_info['pinned_piece'].split('@')[1],
                piece_type=pin_info['pinned_piece'].split('@')[0],
                color="black" if piece.color == chess.WHITE else "white",
                role="target",
                importance=0.8
            )
        ]
        
        return ChessPatternEnhanced(
            id=f"dynamic_pin_{hash(board.fen()) % 10000}",
            name="Dynamic Pin",
            description="Dynamic pin opportunity detected",
            category=PatternCategory.TACTICAL,
            fen=board.fen(),
            key_move=pin_info['move'],
            participating_pieces=participating_pieces,
            frequency=0.25,
            success_rate=0.7,
            game_phase=self._determine_game_phase(board),
            tags=["pin", "dynamic", "tactical"]
        )
    
    def _create_dynamic_hanging_pattern(self, board: chess.Board, hang_info: Dict[str, Any]) -> ChessPatternEnhanced:
        """Create a dynamic hanging piece pattern"""
        participating_pieces = [
            PatternPiece(
                square=hang_info['square'],
                piece_type=hang_info['piece'],
                color="black" if board.turn == chess.WHITE else "white",
                role="target",
                importance=1.0
            )
        ]
        
        return ChessPatternEnhanced(
            id=f"dynamic_hanging_{hash(board.fen()) % 10000}",
            name="Hanging Piece",
            description="Hanging piece detected",
            category=PatternCategory.TACTICAL,
            fen=board.fen(),
            key_move=hang_info['capture_move'],
            participating_pieces=participating_pieces,
            frequency=0.4,
            success_rate=0.9,
            game_phase=self._determine_game_phase(board),
            tags=["hanging", "dynamic", "tactical"]
        )
    
    def _create_exchange_pattern(self, board: chess.Board, move: chess.Move, 
                               exchange: ExchangeSequence) -> ChessPatternEnhanced:
        """Create an exchange pattern"""
        participating_pieces = [
            PatternPiece(
                square=chess.square_name(move.from_square),
                piece_type=chess.piece_name(board.piece_at(move.from_square).piece_type),
                color="white" if board.turn == chess.WHITE else "black",
                role="attacker",
                importance=1.0
            ),
            PatternPiece(
                square=chess.square_name(move.to_square),
                piece_type=chess.piece_name(board.piece_at(move.to_square).piece_type),
                color="black" if board.turn == chess.WHITE else "white",
                role="target",
                importance=0.9
            )
        ]
        
        exchange_type = "favorable" if exchange.material_balance > 0 else "unfavorable" if exchange.material_balance < 0 else "equal"
        
        return ChessPatternEnhanced(
            id=f"exchange_{hash(board.fen()) % 10000}",
            name=f"Exchange Sequence ({exchange_type})",
            description=f"Exchange with material balance: {exchange.material_balance:+.0f}",
            category=PatternCategory.EXCHANGE,
            fen=board.fen(),
            key_move=move.uci(),
            participating_pieces=participating_pieces,
            exchange_sequence=exchange,
            exchange_type=exchange_type,
            frequency=0.3,
            success_rate=exchange.probability,
            game_phase=self._determine_game_phase(board),
            tags=["exchange", "dynamic"]
        )
    
    def _analyze_pawn_structure(self, board: chess.Board) -> List[Dict[str, Any]]:
        """Analyze pawn structure patterns"""
        patterns = []
        
        # Check for passed pawns
        passed_pawns = self._find_passed_pawns(board)
        for pawn_sq in passed_pawns:
            patterns.append({
                'name': 'Passed Pawn',
                'value': 200,
                'suggested_move': self._suggest_passed_pawn_move(board, pawn_sq),
                'square': chess.square_name(pawn_sq)
            })
        
        # Check for isolated pawns
        isolated_pawns = self._find_isolated_pawns(board)
        for pawn_sq in isolated_pawns:
            patterns.append({
                'name': 'Isolated Pawn',
                'value': -50,
                'suggested_move': '',
                'square': chess.square_name(pawn_sq)
            })
        
        # Check for doubled pawns
        doubled_pawns = self._find_doubled_pawns(board)
        for file_sq in doubled_pawns:
            patterns.append({
                'name': 'Doubled Pawns',
                'value': -30,
                'suggested_move': '',
                'square': chess.file_name(file_sq)
            })
        
        return patterns
    
    def _create_strategic_pattern(self, board: chess.Board, pattern_info: Dict[str, Any]) -> ChessPatternEnhanced:
        """Create a strategic pattern"""
        participating_pieces = []
        
        if 'square' in pattern_info:
            participating_pieces.append(PatternPiece(
                square=pattern_info['square'],
                piece_type="pawn",
                color="white" if board.turn == chess.WHITE else "black",
                role="target",
                importance=0.7
            ))
        
        return ChessPatternEnhanced(
            id=f"strategic_{pattern_info['name'].lower().replace(' ', '_')}_{hash(board.fen()) % 10000}",
            name=pattern_info['name'],
            description=f"Strategic pattern: {pattern_info['name']}",
            category=PatternCategory.STRATEGIC,
            fen=board.fen(),
            key_move=pattern_info.get('suggested_move', ''),
            participating_pieces=participating_pieces,
            frequency=0.5,
            success_rate=0.6,
            game_phase=self._determine_game_phase(board),
            tags=["strategic", "positional"]
        )
    
    def _find_passed_pawns(self, board: chess.Board) -> List[chess.Square]:
        """Find passed pawns"""
        passed_pawns = []
        
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            enemy_pawns = board.pieces(chess.PAWN, not color)
            
            for pawn_sq in pawns:
                is_passed = True
                pawn_file = chess.square_file(pawn_sq)
                pawn_rank = chess.square_rank(pawn_sq)
                
                # Check if enemy pawns block or can capture
                for enemy_pawn in enemy_pawns:
                    enemy_file = chess.square_file(enemy_pawn)
                    enemy_rank = chess.square_rank(enemy_pawn)
                    
                    # Check if enemy pawn is in front and on same or adjacent file
                    if color == chess.WHITE:
                        if enemy_rank > pawn_rank and abs(enemy_file - pawn_file) <= 1:
                            is_passed = False
                            break
                    else:
                        if enemy_rank < pawn_rank and abs(enemy_file - pawn_file) <= 1:
                            is_passed = False
                            break
                
                if is_passed:
                    passed_pawns.append(pawn_sq)
        
        return passed_pawns
    
    def _find_isolated_pawns(self, board: chess.Board) -> List[chess.Square]:
        """Find isolated pawns"""
        isolated_pawns = []
        
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            
            for pawn_sq in pawns:
                pawn_file = chess.square_file(pawn_sq)
                has_friendly_pawn_adjacent = False
                
                # Check adjacent files for friendly pawns
                for check_file in [pawn_file - 1, pawn_file + 1]:
                    if 0 <= check_file <= 7:
                        file_pawns = [sq for sq in pawns if chess.square_file(sq) == check_file]
                        if file_pawns:
                            has_friendly_pawn_adjacent = True
                            break
                
                if not has_friendly_pawn_adjacent:
                    isolated_pawns.append(pawn_sq)
        
        return isolated_pawns
    
    def _find_doubled_pawns(self, board: chess.Board) -> List[int]:
        """Find files with doubled pawns"""
        doubled_files = []
        
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            file_counts = defaultdict(int)
            
            for pawn_sq in pawns:
                file_counts[chess.square_file(pawn_sq)] += 1
            
            for file_num, count in file_counts.items():
                if count > 1:
                    doubled_files.append(file_num)
        
        return list(set(doubled_files))
    
    def _suggest_passed_pawn_move(self, board: chess.Board, pawn_sq: chess.Square) -> str:
        """Suggest a move for a passed pawn"""
        pawn = board.piece_at(pawn_sq)
        if not pawn or pawn.piece_type != chess.PAWN:
            return ""
        
        # Try to advance the pawn
        direction = 8 if pawn.color == chess.WHITE else -8
        advance_sq = pawn_sq + direction
        
        if 0 <= advance_sq < 64:
            advance_move = chess.Move(pawn_sq, advance_sq)
            if advance_move in board.legal_moves:
                return advance_move.uci()
            
            # Try double advance
            if ((pawn.color == chess.WHITE and chess.square_rank(pawn_sq) == 1) or
                (pawn.color == chess.BLACK and chess.square_rank(pawn_sq) == 6)):
                double_advance_sq = advance_sq + direction
                double_advance_move = chess.Move(pawn_sq, double_advance_sq)
                if double_advance_move in board.legal_moves:
                    return double_advance_move.uci()
        
        return ""
    
    def _determine_game_phase(self, board: chess.Board) -> str:
        """Determine the current game phase"""
        piece_count = sum(len(board.pieces(pt, chess.WHITE)) + len(board.pieces(pt, chess.BLACK)) 
                         for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT])
        
        if piece_count >= 20:
            return "opening"
        elif piece_count >= 10:
            return "middlegame"
        else:
            return "endgame"
    
    def _evaluate_tactical_value(self, pattern: ChessPatternEnhanced) -> float:
        """Evaluate tactical value of a pattern"""
        if pattern.category == PatternCategory.TACTICAL:
            return pattern.success_rate * pattern.frequency * 100
        elif pattern.category == PatternCategory.EXCHANGE:
            if pattern.exchange_sequence:
                return abs(pattern.exchange_sequence.material_balance)
        return 0.0
    
    def _evaluate_strategic_value(self, pattern: ChessPatternEnhanced) -> float:
        """Evaluate strategic value of a pattern"""
        if pattern.category == PatternCategory.STRATEGIC:
            return pattern.success_rate * pattern.frequency * 80
        elif pattern.category == PatternCategory.POSITIONAL:
            return pattern.success_rate * pattern.frequency * 60
        return 0.0
    
    def _assess_risk(self, pattern: ChessPatternEnhanced) -> float:
        """Assess risk level of a pattern"""
        base_risk = 0.2
        
        if pattern.category == PatternCategory.TACTICAL:
            base_risk = 0.3
        elif pattern.category == PatternCategory.EXCHANGE:
            if pattern.exchange_sequence and pattern.exchange_sequence.material_balance < 0:
                base_risk = 0.6
            else:
                base_risk = 0.4
        
        # Adjust based on success rate
        risk = base_risk * (1.0 - pattern.success_rate)
        return min(1.0, max(0.0, risk))
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected patterns"""
        if not self.detected_patterns:
            return {'total_patterns': 0}
        
        stats = {
            'total_patterns': len(self.detected_patterns),
            'categories': Counter(p.pattern.category.value for p in self.detected_patterns),
            'avg_confidence': sum(p.confidence for p in self.detected_patterns) / len(self.detected_patterns),
            'avg_tactical_value': sum(p.tactical_value for p in self.detected_patterns) / len(self.detected_patterns),
            'avg_strategic_value': sum(p.strategic_value for p in self.detected_patterns) / len(self.detected_patterns),
            'avg_risk': sum(p.risk_assessment for p in self.detected_patterns) / len(self.detected_patterns)
        }
        
        return stats
