"""
Enhanced pattern detection system with piece filtering and exchange prediction.
Filters out pieces that don't participate in pattern creation.
"""

from __future__ import annotations
import chess
from typing import List, Dict, Any, Optional, Tuple, Set
import logging

from chess_ai.pattern_detector import ChessPattern, PatternType

logger = logging.getLogger(__name__)


class EnhancedPatternDetector:
    """Enhanced pattern detector with piece filtering and exchange prediction"""
    
    def __init__(self):
        self.patterns: List[ChessPattern] = []
        self.exchange_patterns: List[Dict[str, Any]] = []
        
    def detect_patterns(
        self,
        board: chess.Board,
        move: chess.Move,
        evaluation_before: Dict[str, Any],
        evaluation_after: Dict[str, Any],
        bot_analysis: Dict[str, Any] = None
    ) -> List[ChessPattern]:
        """
        Detect patterns with enhanced piece filtering.
        Only shows pieces that actively participate in the pattern.
        """
        detected_patterns = []
        
        # Create board state before move
        board_before = board.copy()
        if board_before.move_stack:
            board_before.pop()
        
        # Get move in SAN notation
        try:
            move_san = board_before.san(move)
        except:
            move_san = move.uci()
        
        # Detect different pattern types with piece filtering
        pattern_detections = []
        
        # 1. Tactical moments
        if self._is_tactical_moment(evaluation_before, evaluation_after):
            pattern_detections.append({
                "type": PatternType.TACTICAL_MOMENT,
                "description": f"Tactical moment (eval change: {abs(evaluation_after.get('total', 0) - evaluation_before.get('total', 0))})",
                "participating_pieces": self._get_tactical_pieces(board, move)
            })
        
        # 2. Fork detection
        fork_info = self._detect_fork_enhanced(board, move)
        if fork_info:
            pattern_detections.append({
                "type": PatternType.FORK,
                "description": f"Fork: {fork_info['description']}",
                "participating_pieces": fork_info['pieces']
            })
        
        # 3. Pin detection
        pin_info = self._detect_pin_enhanced(board, move)
        if pin_info:
            pattern_detections.append({
                "type": PatternType.PIN,
                "description": f"Pin: {pin_info['description']}",
                "participating_pieces": pin_info['pieces']
            })
        
        # 4. Exchange prediction (2-3 moves ahead)
        exchange_info = self._predict_exchange(board, move, 3)
        if exchange_info:
            pattern_detections.append({
                "type": "exchange",
                "description": f"Exchange sequence: {exchange_info['description']}",
                "participating_pieces": exchange_info['pieces']
            })
            # Store exchange pattern separately
            self.exchange_patterns.append(exchange_info)
        
        # 5. Hanging pieces
        hanging_info = self._detect_hanging_pieces_enhanced(board)
        if hanging_info:
            pattern_detections.append({
                "type": PatternType.HANGING_PIECE,
                "description": f"Hanging piece: {hanging_info['description']}",
                "participating_pieces": hanging_info['pieces']
            })
        
        # 6. Critical decision
        if bot_analysis and self._is_critical_decision(bot_analysis):
            pattern_detections.append({
                "type": PatternType.CRITICAL_DECISION,
                "description": "Critical position with multiple alternatives",
                "participating_pieces": self._get_critical_pieces(board, move)
            })
        
        # 7. Opening trick
        if board.fullmove_number <= 10 and self._is_unusual_move(board_before, move):
            pattern_detections.append({
                "type": PatternType.OPENING_TRICK,
                "description": "Unusual opening move",
                "participating_pieces": self._get_opening_pieces(board, move)
            })
        
        # 8. Endgame technique
        if self._is_endgame(board) and abs(evaluation_after.get("total", 0)) > 200:
            pattern_detections.append({
                "type": PatternType.ENDGAME_TECHNIQUE,
                "description": "Endgame technique",
                "participating_pieces": self._get_endgame_pieces(board, move)
            })
        
        # 9. Sacrifice
        if self._is_sacrifice_enhanced(board_before, move, evaluation_before, evaluation_after):
            pattern_detections.append({
                "type": PatternType.SACRIFICE,
                "description": "Piece sacrifice",
                "participating_pieces": self._get_sacrifice_pieces(board, move)
            })
        
        # Create patterns with filtered pieces
        for detection in pattern_detections:
            pattern = ChessPattern(
                fen=board_before.fen(),
                move=move_san,
                pattern_types=[detection["type"]],
                description=detection["description"],
                influencing_pieces=detection["participating_pieces"],
                evaluation={
                    "before": evaluation_before,
                    "after": evaluation_after,
                    "change": evaluation_after.get("total", 0) - evaluation_before.get("total", 0)
                },
                metadata={
                    "fullmove_number": board.fullmove_number,
                    "turn": "white" if board_before.turn == chess.WHITE else "black",
                    "is_capture": board_before.is_capture(move),
                    "is_check": board.is_check(),
                    "participating_pieces_count": len(detection["participating_pieces"]),
                    "pattern_strength": self._calculate_pattern_strength(detection, evaluation_before, evaluation_after)
                }
            )
            
            detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _is_tactical_moment(self, eval_before: Dict, eval_after: Dict) -> bool:
        """Check if this is a tactical moment"""
        change = abs(eval_after.get("total", 0) - eval_before.get("total", 0))
        return change > 150
    
    def _get_tactical_pieces(self, board: chess.Board, move: chess.Move) -> List[Dict[str, Any]]:
        """Get pieces involved in tactical moment"""
        pieces = []
        
        # Moving piece
        moving_piece = board.piece_at(move.to_square)
        if moving_piece:
            pieces.append({
                "square": chess.square_name(move.to_square),
                "piece": self._piece_name(moving_piece),
                "color": "white" if moving_piece.color == chess.WHITE else "black",
                "relationship": "mover"
            })
        
        # Pieces that attack or defend the target square
        for color in [chess.WHITE, chess.BLACK]:
            attackers = board.attackers(color, move.to_square)
            for attacker_sq in attackers:
                if attacker_sq != move.from_square:  # Don't include the moving piece twice
                    piece = board.piece_at(attacker_sq)
                    if piece:
                        pieces.append({
                            "square": chess.square_name(attacker_sq),
                            "piece": self._piece_name(piece),
                            "color": "white" if piece.color == chess.WHITE else "black",
                            "relationship": "attacker" if color == board.turn else "defender"
                        })
        
        return pieces
    
    def _detect_fork_enhanced(self, board: chess.Board, move: chess.Move) -> Optional[Dict[str, Any]]:
        """Enhanced fork detection with piece filtering"""
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
            return None
        
        # Get attacked pieces
        attacked_pieces = []
        for target_sq in board.attacks(move.to_square):
            target_piece = board.piece_at(target_sq)
            if target_piece and target_piece.color != piece.color:
                if target_piece.piece_type in (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
                    attacked_pieces.append({
                        "square": chess.square_name(target_sq),
                        "piece": self._piece_name(target_piece),
                        "color": "white" if target_piece.color == chess.WHITE else "black",
                        "relationship": "target"
                    })
        
        if len(attacked_pieces) >= 2:
            piece_name = "Knight" if piece.piece_type == chess.KNIGHT else "Bishop"
            return {
                "description": f"{piece_name} attacks {len(attacked_pieces)} pieces",
                "pieces": [
                    {
                        "square": chess.square_name(move.to_square),
                        "piece": piece_name,
                        "color": "white" if piece.color == chess.WHITE else "black",
                        "relationship": "attacker"
                    }
                ] + attacked_pieces[:3]  # Limit to 3 targets for clarity
            }
        
        return None
    
    def _detect_pin_enhanced(self, board: chess.Board, move: chess.Move) -> Optional[Dict[str, Any]]:
        """Enhanced pin detection with piece filtering"""
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            return None
        
        enemy_color = not piece.color
        enemy_king_sq = board.king(enemy_color)
        
        if enemy_king_sq is None:
            return None
        
        # Check for pin
        try:
            between_squares = chess.SquareSet(chess.between(move.to_square, enemy_king_sq))
            if len(between_squares) == 1:
                pinned_sq = list(between_squares)[0]
                pinned_piece = board.piece_at(pinned_sq)
                if pinned_piece and pinned_piece.color == enemy_color:
                    return {
                        "description": f"{self._piece_name(pinned_piece)} pinned to King",
                        "pieces": [
                            {
                                "square": chess.square_name(move.to_square),
                                "piece": self._piece_name(piece),
                                "color": "white" if piece.color == chess.WHITE else "black",
                                "relationship": "attacker"
                            },
                            {
                                "square": chess.square_name(pinned_sq),
                                "piece": self._piece_name(pinned_piece),
                                "color": "white" if pinned_piece.color == chess.WHITE else "black",
                                "relationship": "pinned"
                            },
                            {
                                "square": chess.square_name(enemy_king_sq),
                                "piece": "King",
                                "color": "white" if enemy_color == chess.WHITE else "black",
                                "relationship": "target"
                            }
                        ]
                    }
        except:
            pass
        
        return None
    
    def _predict_exchange(self, board: chess.Board, move: chess.Move, depth: int = 3) -> Optional[Dict[str, Any]]:
        """Predict exchange sequences 2-3 moves ahead"""
        try:
            # Simulate the move
            board_copy = board.copy()
            board_copy.push(move)
            
            # Look for immediate captures and counter-captures
            exchange_sequence = []
            participating_pieces = []
            
            # Get pieces involved in potential exchanges
            current_board = board_copy
            for i in range(min(depth, 3)):
                if current_board.is_game_over():
                    break
                
                # Find captures
                captures = []
                for move_candidate in current_board.legal_moves:
                    if current_board.is_capture(move_candidate):
                        captures.append(move_candidate)
                
                if captures:
                    # Take the most valuable capture
                    best_capture = max(captures, key=lambda m: self._get_capture_value(current_board, m))
                    exchange_sequence.append(current_board.san(best_capture))
                    
                    # Add participating pieces
                    moving_piece = current_board.piece_at(best_capture.from_square)
                    captured_piece = current_board.piece_at(best_capture.to_square)
                    
                    if moving_piece:
                        participating_pieces.append({
                            "square": chess.square_name(best_capture.from_square),
                            "piece": self._piece_name(moving_piece),
                            "color": "white" if moving_piece.color == chess.WHITE else "black",
                            "relationship": "exchanger"
                        })
                    
                    if captured_piece:
                        participating_pieces.append({
                            "square": chess.square_name(best_capture.to_square),
                            "piece": self._piece_name(captured_piece),
                            "color": "white" if captured_piece.color == chess.WHITE else "black",
                            "relationship": "exchanged"
                        })
                    
                    # Apply the move
                    current_board.push(best_capture)
                else:
                    break
            
            if len(exchange_sequence) >= 2:
                return {
                    "description": f"Exchange: {' -> '.join(exchange_sequence)}",
                    "pieces": participating_pieces,
                    "sequence": exchange_sequence
                }
        
        except Exception as e:
            logger.warning(f"Exchange prediction failed: {e}")
        
        return None
    
    def _detect_hanging_pieces_enhanced(self, board: chess.Board) -> Optional[Dict[str, Any]]:
        """Enhanced hanging piece detection with piece filtering"""
        hanging_pieces = []
        
        for sq, piece in board.piece_map().items():
            if piece.color == board.turn:
                continue
            
            attackers = len(board.attackers(board.turn, sq))
            defenders = len(board.attackers(not board.turn, sq))
            
            if attackers > 0 and defenders == 0 and piece.piece_type != chess.PAWN:
                hanging_pieces.append({
                    "square": chess.square_name(sq),
                    "piece": self._piece_name(piece),
                    "color": "white" if piece.color == chess.WHITE else "black",
                    "relationship": "hanging"
                })
        
        if hanging_pieces:
            return {
                "description": f"{len(hanging_pieces)} hanging pieces",
                "pieces": hanging_pieces[:3]  # Limit for clarity
            }
        
        return None
    
    def _is_critical_decision(self, bot_analysis: Dict[str, Any]) -> bool:
        """Check if this is a critical decision"""
        return bot_analysis.get("alternatives_count", 0) > 5
    
    def _get_critical_pieces(self, board: chess.Board, move: chess.Move) -> List[Dict[str, Any]]:
        """Get pieces involved in critical decision"""
        pieces = []
        
        # Moving piece
        moving_piece = board.piece_at(move.to_square)
        if moving_piece:
            pieces.append({
                "square": chess.square_name(move.to_square),
                "piece": self._piece_name(moving_piece),
                "color": "white" if moving_piece.color == chess.WHITE else "black",
                "relationship": "mover"
            })
        
        # Pieces in the center or key squares
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        for sq in center_squares:
            piece = board.piece_at(sq)
            if piece:
                pieces.append({
                    "square": chess.square_name(sq),
                    "piece": self._piece_name(piece),
                    "color": "white" if piece.color == chess.WHITE else "black",
                    "relationship": "center_control"
                })
        
        return pieces[:5]  # Limit for clarity
    
    def _is_unusual_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if this is an unusual opening move"""
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
        
        # Unusual if moving same piece twice in opening
        move_history = [m.from_square for m in board.move_stack[-3:] if board.move_stack]
        return move.from_square in move_history
    
    def _get_opening_pieces(self, board: chess.Board, move: chess.Move) -> List[Dict[str, Any]]:
        """Get pieces involved in opening trick"""
        pieces = []
        
        # Moving piece
        moving_piece = board.piece_at(move.to_square)
        if moving_piece:
            pieces.append({
                "square": chess.square_name(move.to_square),
                "piece": self._piece_name(moving_piece),
                "color": "white" if moving_piece.color == chess.WHITE else "black",
                "relationship": "mover"
            })
        
        # Pieces that could be affected by this unusual move
        for sq in board.attacks(move.to_square):
            piece = board.piece_at(sq)
            if piece and piece.color != moving_piece.color:
                pieces.append({
                    "square": chess.square_name(sq),
                    "piece": self._piece_name(piece),
                    "color": "white" if piece.color == chess.WHITE else "black",
                    "relationship": "threatened"
                })
        
        return pieces
    
    def _is_endgame(self, board: chess.Board) -> bool:
        """Check if position is in endgame"""
        piece_count = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            piece_count += len(board.pieces(piece_type, chess.WHITE))
            piece_count += len(board.pieces(piece_type, chess.BLACK))
        return piece_count <= 6
    
    def _get_endgame_pieces(self, board: chess.Board, move: chess.Move) -> List[Dict[str, Any]]:
        """Get pieces involved in endgame technique"""
        pieces = []
        
        # All pieces in endgame are important
        for sq, piece in board.piece_map().items():
            if piece.piece_type != chess.PAWN:  # Focus on major pieces
                pieces.append({
                    "square": chess.square_name(sq),
                    "piece": self._piece_name(piece),
                    "color": "white" if piece.color == chess.WHITE else "black",
                    "relationship": "endgame_piece"
                })
        
        return pieces[:8]  # Limit for clarity
    
    def _is_sacrifice_enhanced(
        self,
        board_before: chess.Board,
        move: chess.Move,
        eval_before: Dict,
        eval_after: Dict
    ) -> bool:
        """Enhanced sacrifice detection"""
        if not board_before.is_capture(move):
            board_after = board_before.copy()
            board_after.push(move)
            
            attackers = len(board_after.attackers(not board_before.turn, move.to_square))
            defenders = len(board_after.attackers(board_before.turn, move.to_square))
            
            if attackers > defenders:
                eval_change = eval_after.get("total", 0) - eval_before.get("total", 0)
                if board_before.turn == chess.WHITE:
                    return eval_change > 0
                else:
                    return eval_change < 0
        
        return False
    
    def _get_sacrifice_pieces(self, board: chess.Board, move: chess.Move) -> List[Dict[str, Any]]:
        """Get pieces involved in sacrifice"""
        pieces = []
        
        # Sacrificed piece
        moving_piece = board.piece_at(move.to_square)
        if moving_piece:
            pieces.append({
                "square": chess.square_name(move.to_square),
                "piece": self._piece_name(moving_piece),
                "color": "white" if moving_piece.color == chess.WHITE else "black",
                "relationship": "sacrificed"
            })
        
        # Pieces that benefit from the sacrifice
        for sq in board.attacks(move.to_square):
            piece = board.piece_at(sq)
            if piece and piece.color != moving_piece.color:
                pieces.append({
                    "square": chess.square_name(sq),
                    "piece": self._piece_name(piece),
                    "color": "white" if piece.color == chess.WHITE else "black",
                    "relationship": "beneficiary"
                })
        
        return pieces
    
    def _piece_name(self, piece: chess.Piece) -> str:
        """Get piece name"""
        piece_names = {
            chess.KING: "King",
            chess.QUEEN: "Queen",
            chess.ROOK: "Rook",
            chess.BISHOP: "Bishop",
            chess.KNIGHT: "Knight",
            chess.PAWN: "Pawn"
        }
        return piece_names.get(piece.piece_type, "Unknown")
    
    def _get_capture_value(self, board: chess.Board, move: chess.Move) -> int:
        """Get value of capture move"""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 100
        }
        
        captured_piece = board.piece_at(move.to_square)
        if captured_piece:
            return piece_values.get(captured_piece.piece_type, 0)
        return 0
    
    def _calculate_pattern_strength(self, detection: Dict, eval_before: Dict, eval_after: Dict) -> float:
        """Calculate pattern strength based on evaluation change and piece involvement"""
        eval_change = abs(eval_after.get("total", 0) - eval_before.get("total", 0))
        piece_count = len(detection["participating_pieces"])
        
        # Higher evaluation change and more pieces involved = stronger pattern
        strength = (eval_change / 100.0) + (piece_count * 0.1)
        return min(strength, 10.0)  # Cap at 10.0