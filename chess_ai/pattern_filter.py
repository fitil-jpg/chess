"""
Advanced pattern filtering system that identifies and filters out pieces
not participating in pattern creation.
"""

from __future__ import annotations
import chess
from typing import List, Dict, Any, Set, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PatternFilter:
    """Advanced pattern filtering and piece relevance analysis"""
    
    def __init__(self):
        self.piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 100
        }
    
    def analyze_pattern_relevance(
        self, 
        board: chess.Board, 
        move: chess.Move, 
        pattern_types: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze which pieces are relevant to the pattern and which can be filtered out.
        
        Returns:
            Dict with:
            - relevant_pieces: Set of squares with pieces that matter for the pattern
            - irrelevant_pieces: Set of squares with pieces that can be hidden
            - pattern_analysis: Detailed analysis of the pattern
            - filtered_fen: FEN with irrelevant pieces removed
        """
        relevant_squares = set()
        pattern_analysis = {}
        
        # Analyze each pattern type
        for pattern_type in pattern_types:
            if pattern_type == "fork":
                fork_analysis = self._analyze_fork_relevance(board, move)
                relevant_squares.update(fork_analysis["relevant_squares"])
                pattern_analysis["fork"] = fork_analysis
                
            elif pattern_type == "pin":
                pin_analysis = self._analyze_pin_relevance(board, move)
                relevant_squares.update(pin_analysis["relevant_squares"])
                pattern_analysis["pin"] = pin_analysis
                
            elif pattern_type == "tactical_moment":
                tactical_analysis = self._analyze_tactical_relevance(board, move)
                relevant_squares.update(tactical_analysis["relevant_squares"])
                pattern_analysis["tactical"] = tactical_analysis
                
            elif pattern_type == "hanging_piece":
                hanging_analysis = self._analyze_hanging_relevance(board, move)
                relevant_squares.update(hanging_analysis["relevant_squares"])
                pattern_analysis["hanging"] = hanging_analysis
                
            elif pattern_type == "sacrifice":
                sacrifice_analysis = self._analyze_sacrifice_relevance(board, move)
                relevant_squares.update(sacrifice_analysis["relevant_squares"])
                pattern_analysis["sacrifice"] = sacrifice_analysis
        
        # Add the moving piece and target square
        relevant_squares.add(move.from_square)
        relevant_squares.add(move.to_square)
        
        # Add all pieces that attack or defend the moving piece
        for square in [move.from_square, move.to_square]:
            for color in [chess.WHITE, chess.BLACK]:
                attackers = board.attackers(color, square)
                relevant_squares.update(attackers)
        
        # Find irrelevant pieces
        all_pieces = set(board.piece_map().keys())
        irrelevant_squares = all_pieces - relevant_squares
        
        # Create filtered FEN
        filtered_fen = self._create_filtered_fen(board, irrelevant_squares)
        
        return {
            "relevant_pieces": relevant_squares,
            "irrelevant_pieces": irrelevant_squares,
            "pattern_analysis": pattern_analysis,
            "filtered_fen": filtered_fen,
            "relevance_score": len(relevant_squares) / len(all_pieces) if all_pieces else 0
        }
    
    def _analyze_fork_relevance(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """Analyze which pieces are relevant for a fork pattern"""
        relevant_squares = set()
        fork_info = {}
        
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
            return {"relevant_squares": relevant_squares, "fork_info": fork_info}
        
        # Add the forking piece
        relevant_squares.add(move.to_square)
        
        # Find all attacked pieces
        attacked_squares = []
        for target_sq in board.attacks(move.to_square):
            target_piece = board.piece_at(target_sq)
            if target_piece and target_piece.color != piece.color:
                attacked_squares.append(target_sq)
                relevant_squares.add(target_sq)
                
                # Add pieces that defend the attacked piece
                defenders = board.attackers(not piece.color, target_sq)
                relevant_squares.update(defenders)
        
        fork_info = {
            "forking_piece": move.to_square,
            "attacked_squares": attacked_squares,
            "attack_count": len(attacked_squares)
        }
        
        return {"relevant_squares": relevant_squares, "fork_info": fork_info}
    
    def _analyze_pin_relevance(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """Analyze which pieces are relevant for a pin pattern"""
        relevant_squares = set()
        pin_info = {}
        
        piece = board.piece_at(move.to_square)
        if not piece or piece.piece_type not in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            return {"relevant_squares": relevant_squares, "pin_info": pin_info}
        
        # Add the pinning piece
        relevant_squares.add(move.to_square)
        
        # Find the pinned piece
        enemy_color = not piece.color
        enemy_king_sq = board.king(enemy_color)
        
        if enemy_king_sq is not None:
            try:
                between_squares = chess.SquareSet(chess.between(move.to_square, enemy_king_sq))
                if len(between_squares) == 1:
                    pinned_sq = list(between_squares)[0]
                    pinned_piece = board.piece_at(pinned_sq)
                    if pinned_piece and pinned_piece.color == enemy_color:
                        relevant_squares.add(pinned_sq)
                        relevant_squares.add(enemy_king_sq)
                        
                        # Add pieces that can break the pin
                        for break_sq in board.attacks(pinned_sq):
                            break_piece = board.piece_at(break_sq)
                            if break_piece and break_piece.color == enemy_color:
                                relevant_squares.add(break_sq)
                        
                        pin_info = {
                            "pinning_piece": move.to_square,
                            "pinned_piece": pinned_sq,
                            "pinned_to_king": enemy_king_sq
                        }
            except:
                pass
        
        return {"relevant_squares": relevant_squares, "pin_info": pin_info}
    
    def _analyze_tactical_relevance(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """Analyze which pieces are relevant for a tactical moment"""
        relevant_squares = set()
        tactical_info = {}
        
        # Add the moving piece and target
        relevant_squares.add(move.from_square)
        relevant_squares.add(move.to_square)
        
        # Add all pieces that can immediately respond to this move
        for color in [chess.WHITE, chess.BLACK]:
            for square in [move.from_square, move.to_square]:
                attackers = board.attackers(color, square)
                relevant_squares.update(attackers)
                
                # Add pieces that can counter-attack
                for attacker_sq in attackers:
                    counter_attackers = board.attackers(not color, attacker_sq)
                    relevant_squares.update(counter_attackers)
        
        # Add pieces in the center (more likely to be tactically relevant)
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        for sq in center_squares:
            piece = board.piece_at(sq)
            if piece:
                relevant_squares.add(sq)
        
        tactical_info = {
            "move_squares": [move.from_square, move.to_square],
            "center_control": len([sq for sq in center_squares if sq in relevant_squares])
        }
        
        return {"relevant_squares": relevant_squares, "tactical_info": tactical_info}
    
    def _analyze_hanging_relevance(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """Analyze which pieces are relevant for hanging piece patterns"""
        relevant_squares = set()
        hanging_info = {}
        
        # Check if the moved piece is now hanging
        attackers = board.attackers(not board.turn, move.to_square)
        defenders = board.attackers(board.turn, move.to_square)
        
        if len(attackers) > len(defenders):
            relevant_squares.add(move.to_square)
            relevant_squares.update(attackers)
            relevant_squares.update(defenders)
            
            hanging_info = {
                "hanging_square": move.to_square,
                "attackers": list(attackers),
                "defenders": list(defenders),
                "is_hanging": True
            }
        
        # Check for other hanging pieces
        for sq, piece in board.piece_map().items():
            if piece.color == board.turn:
                sq_attackers = board.attackers(not board.turn, sq)
                sq_defenders = board.attackers(board.turn, sq)
                
                if len(sq_attackers) > len(sq_defenders) and piece.piece_type != chess.PAWN:
                    relevant_squares.add(sq)
                    relevant_squares.update(sq_attackers)
                    relevant_squares.update(sq_defenders)
        
        return {"relevant_squares": relevant_squares, "hanging_info": hanging_info}
    
    def _analyze_sacrifice_relevance(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """Analyze which pieces are relevant for sacrifice patterns"""
        relevant_squares = set()
        sacrifice_info = {}
        
        # Add the sacrificed piece and target
        relevant_squares.add(move.from_square)
        relevant_squares.add(move.to_square)
        
        # Add pieces that can recapture
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                # Add pieces that can recapture the sacrificed piece
                for color in [chess.WHITE, chess.BLACK]:
                    recapturers = board.attackers(color, move.from_square)
                    relevant_squares.update(recapturers)
        
        # Add pieces that can support the sacrifice
        for color in [chess.WHITE, chess.BLACK]:
            supporters = board.attackers(color, move.to_square)
            relevant_squares.update(supporters)
        
        # Add king and pieces around it (sacrifices often target king safety)
        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            if king_sq is not None:
                # Add king and pieces around it
                for offset in [-9, -8, -7, -1, 1, 7, 8, 9]:
                    sq = king_sq + offset
                    if 0 <= sq < 64 and abs(chess.square_file(sq) - chess.square_file(king_sq)) <= 1:
                        piece = board.piece_at(sq)
                        if piece:
                            relevant_squares.add(sq)
        
        sacrifice_info = {
            "sacrifice_square": move.from_square,
            "target_square": move.to_square,
            "is_capture": board.is_capture(move)
        }
        
        return {"relevant_squares": relevant_squares, "sacrifice_info": sacrifice_info}
    
    def _create_filtered_fen(self, board: chess.Board, irrelevant_squares: Set[int]) -> str:
        """Create a FEN string with irrelevant pieces removed"""
        # Create a copy of the board
        filtered_board = board.copy()
        
        # Remove irrelevant pieces
        for square in irrelevant_squares:
            if filtered_board.piece_at(square):
                filtered_board.remove_piece_at(square)
        
        return filtered_board.fen()
    
    def detect_exchange_pattern(self, board: chess.Board, move: chess.Move) -> Optional[Dict[str, Any]]:
        """
        Detect if this move is part of a planned exchange sequence (2-3 moves ahead).
        This is also considered a pattern.
        """
        if not board.is_capture(move):
            return None
        
        # Simulate the move and look for immediate recapture
        board_after = board.copy()
        board_after.push(move)
        
        # Check if opponent can immediately recapture
        for opponent_move in board_after.legal_moves:
            if (opponent_move.to_square == move.to_square and 
                board_after.is_capture(opponent_move)):
                
                # This is a planned exchange
                return {
                    "type": "exchange",
                    "initiating_move": move,
                    "expected_recapture": opponent_move,
                    "exchange_value": self._calculate_exchange_value(board, move, opponent_move),
                    "is_forced": self._is_forced_exchange(board_after, opponent_move)
                }
        
        return None
    
    def _calculate_exchange_value(self, board: chess.Board, move1: chess.Move, move2: chess.Move) -> int:
        """Calculate the value of an exchange"""
        piece1 = board.piece_at(move1.from_square)
        piece2 = board.piece_at(move2.from_square)
        
        if not piece1 or not piece2:
            return 0
        
        value1 = self.piece_values.get(piece1.piece_type, 0)
        value2 = self.piece_values.get(piece2.piece_type, 0)
        
        return value1 - value2
    
    def _is_forced_exchange(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if the recapture is forced (no other good moves)"""
        # Simple heuristic: if there are many legal moves, it's not forced
        legal_moves = list(board.legal_moves)
        return len(legal_moves) <= 3  # Arbitrary threshold
    
    def get_pattern_complexity(self, pattern_analysis: Dict[str, Any]) -> str:
        """Determine the complexity level of a pattern"""
        relevant_count = len(pattern_analysis.get("relevant_pieces", set()))
        
        if relevant_count <= 4:
            return "simple"
        elif relevant_count <= 8:
            return "moderate"
        else:
            return "complex"
    
    def should_show_piece(self, square: int, pattern_analysis: Dict[str, Any]) -> bool:
        """Determine if a piece should be shown in the filtered view"""
        relevant_pieces = pattern_analysis.get("relevant_pieces", set())
        return square in relevant_pieces