"""
Wave Function Collapse (WFC) Engine for Chess Pattern Generation.

This module implements a constraint-based procedural generation algorithm
for creating chess patterns, openings, and tactical positions.
"""

import random
import numpy as np
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import chess
from chess import Board, Square, Piece, Move


class PatternType(Enum):
    """Types of chess patterns that can be generated."""
    OPENING = "opening"
    TACTICAL = "tactical"
    ENDGAME = "endgame"
    POSITIONAL = "positional"


@dataclass(frozen=True)
class ChessPattern:
    """Represents a chess pattern with constraints."""
    pattern_type: PatternType
    squares: Tuple[Square, ...]
    pieces: Tuple[Piece, ...]
    constraints: Tuple[Tuple[str, Any], ...]
    frequency: float = 1.0


@dataclass
class WFCCell:
    """Represents a cell in the WFC grid."""
    possible_patterns: Set[ChessPattern]
    collapsed: bool = False
    chosen_pattern: Optional[ChessPattern] = None
    entropy: float = 0.0


class WFCEngine:
    """
    Wave Function Collapse engine for chess pattern generation.
    
    This engine can generate chess patterns by solving constraints
    based on learned patterns from games or tactical positions.
    """
    
    def __init__(self, board_size: int = 8):
        self.board_size = board_size
        self.patterns: List[ChessPattern] = []
        self.grid: List[List[WFCCell]] = []
        self.constraints: Dict[Tuple[ChessPattern, ChessPattern], bool] = {}
        
    def add_pattern(self, pattern: ChessPattern) -> None:
        """Add a pattern to the engine's pattern library."""
        self.patterns.append(pattern)
        
    def learn_constraints_from_patterns(self) -> None:
        """Learn which patterns can be adjacent based on existing patterns."""
        for p1 in self.patterns:
            for p2 in self.patterns:
                if p1 == p2:
                    continue
                    
                # Check if patterns can be adjacent
                compatible = self._are_patterns_compatible(p1, p2)
                self.constraints[(p1, p2)] = compatible
                
    def _are_patterns_compatible(self, p1: ChessPattern, p2: ChessPattern) -> bool:
        """Check if two patterns can be placed adjacent to each other."""
        # Simple compatibility check - can be made more sophisticated
        if p1.pattern_type != p2.pattern_type:
            return False
            
        # Check for conflicting piece positions
        p1_squares = set(p1.squares)
        p2_squares = set(p2.squares)
        
        # Patterns are compatible if they don't overlap in critical squares
        overlap = p1_squares.intersection(p2_squares)
        return len(overlap) == 0 or len(overlap) / max(len(p1_squares), len(p2_squares)) < 0.3
        
    def initialize_grid(self) -> None:
        """Initialize the WFC grid with all possible patterns."""
        self.grid = []
        for row in range(self.board_size):
            grid_row = []
            for col in range(self.board_size):
                cell = WFCCell(possible_patterns=set(self.patterns))
                cell.entropy = len(self.patterns)
                grid_row.append(cell)
            self.grid.append(grid_row)
            
    def calculate_entropy(self, cell: WFCCell) -> float:
        """Calculate the entropy of a cell based on possible patterns."""
        if cell.collapsed or len(cell.possible_patterns) == 0:
            return 0.0
            
        # Entropy based on pattern frequency and constraints
        total_frequency = sum(p.frequency for p in cell.possible_patterns)
        if total_frequency == 0:
            return 0.0
            
        entropy = 0.0
        for pattern in cell.possible_patterns:
            p = pattern.frequency / total_frequency
            if p > 0:
                entropy -= p * np.log2(p)
                
        return entropy
        
    def find_lowest_entropy_cell(self) -> Optional[Tuple[int, int]]:
        """Find the cell with the lowest entropy (most constrained)."""
        min_entropy = float('inf')
        min_cell = None
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                cell = self.grid[row][col]
                if cell.collapsed:
                    continue
                    
                entropy = self.calculate_entropy(cell)
                if entropy < min_entropy and entropy > 0:
                    min_entropy = entropy
                    min_cell = (row, col)
                    
        return min_cell
        
    def collapse_cell(self, row: int, col: int) -> bool:
        """Collapse a cell by choosing one of its possible patterns."""
        cell = self.grid[row][col]
        if cell.collapsed or len(cell.possible_patterns) == 0:
            return False
            
        # Choose pattern based on frequency
        patterns = list(cell.possible_patterns)
        frequencies = [p.frequency for p in patterns]
        total_freq = sum(frequencies)
        
        if total_freq == 0:
            return False
            
        # Weighted random selection
        weights = [f / total_freq for f in frequencies]
        chosen_pattern = np.random.choice(patterns, p=weights)
        
        cell.chosen_pattern = chosen_pattern
        cell.collapsed = True
        cell.possible_patterns = {chosen_pattern}
        
        return True
        
    def propagate_constraints(self, row: int, col: int) -> None:
        """Propagate constraints from a collapsed cell to its neighbors."""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 4-connected neighbors
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row < self.board_size and 
                0 <= new_col < self.board_size):
                
                neighbor_cell = self.grid[new_row][new_col]
                if neighbor_cell.collapsed:
                    continue
                    
                # Filter patterns based on constraints
                compatible_patterns = set()
                for pattern in neighbor_cell.possible_patterns:
                    if self.constraints.get((self.grid[row][col].chosen_pattern, pattern), True):
                        compatible_patterns.add(pattern)
                        
                neighbor_cell.possible_patterns = compatible_patterns
                neighbor_cell.entropy = self.calculate_entropy(neighbor_cell)
                
    def generate_pattern(self, max_iterations: int = 1000) -> Optional[Board]:
        """Generate a chess pattern using WFC algorithm."""
        self.initialize_grid()
        iterations = 0
        
        while iterations < max_iterations:
            # Find the most constrained cell
            cell_pos = self.find_lowest_entropy_cell()
            if cell_pos is None:
                break  # All cells collapsed or no valid moves
                
            row, col = cell_pos
            
            # Collapse the cell
            if not self.collapse_cell(row, col):
                break  # No valid patterns for this cell
                
            # Propagate constraints
            self.propagate_constraints(row, col)
            iterations += 1
            
        # Convert grid to chess board
        return self._grid_to_board()
        
    def _grid_to_board(self) -> Optional[Board]:
        """Convert the WFC grid to a chess board."""
        board = Board()
        board.clear()
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                cell = self.grid[row][col]
                if cell.collapsed and cell.chosen_pattern:
                    pattern = cell.chosen_pattern
                    square = chess.square(col, self.board_size - 1 - row)
                    
                    # Place pieces from the pattern
                    for i, piece in enumerate(pattern.pieces):
                        if i < len(pattern.squares):
                            pattern_square = pattern.squares[i]
                            # Convert pattern square to board square
                            board.set_piece_at(square, piece)
                            
        return board
    
    def analyze_move(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """Analyze a specific move using WFC patterns."""
        analysis = {
            "compatible_patterns": [],
            "constraint_violations": 0,
            "pattern_confidence": 0.0,
            "tactical_value": 0.0,
            "positional_value": 0.0,
            "wfc_zones": []
        }
        
        # Check if move is compatible with existing patterns
        for pattern in self.patterns:
            if self._move_compatible_with_pattern(board, move, pattern):
                analysis["compatible_patterns"].append({
                    "pattern_type": pattern.pattern_type.value,
                    "squares": pattern.squares,
                    "constraints": pattern.constraints,
                    "frequency": pattern.frequency
                })
                
                # Calculate values based on pattern type
                if pattern.pattern_type == PatternType.TACTICAL:
                    analysis["tactical_value"] += pattern.frequency * 0.3
                elif pattern.pattern_type == PatternType.OPENING:
                    analysis["positional_value"] += pattern.frequency * 0.2
                elif pattern.pattern_type == PatternType.ENDGAME:
                    analysis["positional_value"] += pattern.frequency * 0.25
        
        # Calculate overall pattern confidence
        if analysis["compatible_patterns"]:
            analysis["pattern_confidence"] = sum(
                p["frequency"] for p in analysis["compatible_patterns"]
            ) / len(analysis["compatible_patterns"])
        
        # Identify WFC zones (squares that match pattern constraints)
        analysis["wfc_zones"] = self._identify_wfc_zones(board, move)
        
        return analysis
    
    def _move_compatible_with_pattern(self, board: chess.Board, move: chess.Move, pattern: ChessPattern) -> bool:
        """Check if a move is compatible with a specific pattern."""
        # Check if move involves pattern squares
        move_squares = {move.from_square, move.to_square}
        pattern_squares = set(pattern.squares)
        
        # If move doesn't involve pattern squares, it might still be compatible
        if not move_squares.intersection(pattern_squares):
            return False
        
        # Check constraints
        for constraint_name, constraint_value in pattern.constraints:
            if not self._check_constraint(board, move, constraint_name, constraint_value):
                return False
        
        return True
    
    def _check_constraint(self, board: chess.Board, move: chess.Move, constraint_name: str, constraint_value: Any) -> bool:
        """Check if a move satisfies a specific constraint."""
        if constraint_name == "center_control":
            center_squares = {chess.D4, chess.D5, chess.E4, chess.E5}
            return move.to_square in center_squares
        
        elif constraint_name == "development":
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                # Check if moving from starting position
                starting_rank = 0 if piece.color == chess.WHITE else 7
                return chess.square_rank(move.from_square) == starting_rank
        
        elif constraint_name == "tactical":
            # Check if move creates tactical opportunities
            temp_board = board.copy()
            temp_board.push(move)
            return self._has_tactical_opportunities(temp_board)
        
        elif constraint_name == "cow_opening":
            # COW opening specific constraints
            return self._is_cow_opening_move(board, move)
        
        return True
    
    def _has_tactical_opportunities(self, board: chess.Board) -> bool:
        """Check if position has tactical opportunities."""
        # Simple tactical check - can be enhanced
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                attackers = board.attackers(not piece.color, square)
                if len(attackers) > 1:  # Multiple attackers
                    return True
        return False
    
    def _is_cow_opening_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Check if move follows COW opening principles."""
        piece = board.piece_at(move.from_square)
        if not piece:
            return False
        
        # COW opening moves
        cow_moves = {
            chess.PAWN: {chess.E2: chess.E4, chess.D2: chess.D3},
            chess.KNIGHT: {chess.G1: chess.G3, chess.B1: chess.B3},
            chess.BISHOP: {chess.C1: chess.E2, chess.F1: chess.D2}
        }
        
        if piece.piece_type in cow_moves:
            expected_moves = cow_moves[piece.piece_type]
            return move.from_square in expected_moves and move.to_square == expected_moves[move.from_square]
        
        return False
    
    def _identify_wfc_zones(self, board: chess.Board, move: chess.Move) -> List[chess.Square]:
        """Identify squares that are part of WFC zones for visualization."""
        zones = []
        
        # Add move squares
        zones.extend([move.from_square, move.to_square])
        
        # Add squares from compatible patterns
        for pattern in self.patterns:
            if self._move_compatible_with_pattern(board, move, pattern):
                zones.extend(pattern.squares)
        
        return list(set(zones))  # Remove duplicates
        
    def add_opening_patterns(self) -> None:
        """Add common opening patterns to the engine."""
        # COW Opening patterns
        # King's Pawn Opening (e2-e4)
        king_pawn_pattern = ChessPattern(
            pattern_type=PatternType.OPENING,
            squares=(chess.E2, chess.E4),
            pieces=(chess.Piece(chess.PAWN, chess.WHITE), chess.Piece(chess.PAWN, chess.WHITE)),
            constraints=(("center_control", True), ("development", True), ("cow_opening", True)),
            frequency=0.8
        )
        self.add_pattern(king_pawn_pattern)
        
        # Queen's Pawn Opening (d2-d3)
        queen_pawn_pattern = ChessPattern(
            pattern_type=PatternType.OPENING,
            squares=(chess.D2, chess.D3),
            pieces=(chess.Piece(chess.PAWN, chess.WHITE), chess.Piece(chess.PAWN, chess.WHITE)),
            constraints=(("center_control", True), ("development", True), ("cow_opening", True)),
            frequency=0.7
        )
        self.add_pattern(queen_pawn_pattern)
        
        # Knight Development (g1-g3)
        knight_g_pattern = ChessPattern(
            pattern_type=PatternType.OPENING,
            squares=(chess.G1, chess.G3),
            pieces=(chess.Piece(chess.KNIGHT, chess.WHITE), chess.Piece(chess.KNIGHT, chess.WHITE)),
            constraints=(("development", True), ("center_control", True), ("cow_opening", True)),
            frequency=0.6
        )
        self.add_pattern(knight_g_pattern)
        
        # Knight Development (b1-b3)
        knight_b_pattern = ChessPattern(
            pattern_type=PatternType.OPENING,
            squares=(chess.B1, chess.B3),
            pieces=(chess.Piece(chess.KNIGHT, chess.WHITE), chess.Piece(chess.KNIGHT, chess.WHITE)),
            constraints=(("development", True), ("center_control", True), ("cow_opening", True)),
            frequency=0.6
        )
        self.add_pattern(knight_b_pattern)
        
        # Bishop Development (c1-e2)
        bishop_c_pattern = ChessPattern(
            pattern_type=PatternType.OPENING,
            squares=(chess.C1, chess.E2),
            pieces=(chess.Piece(chess.BISHOP, chess.WHITE), chess.Piece(chess.BISHOP, chess.WHITE)),
            constraints=(("development", True), ("center_control", True), ("cow_opening", True)),
            frequency=0.5
        )
        self.add_pattern(bishop_c_pattern)
        
        # Bishop Development (f1-d2)
        bishop_f_pattern = ChessPattern(
            pattern_type=PatternType.OPENING,
            squares=(chess.F1, chess.D2),
            pieces=(chess.Piece(chess.BISHOP, chess.WHITE), chess.Piece(chess.BISHOP, chess.WHITE)),
            constraints=(("development", True), ("center_control", True), ("cow_opening", True)),
            frequency=0.5
        )
        self.add_pattern(bishop_f_pattern)
        
    def add_tactical_patterns(self) -> None:
        """Add common tactical patterns to the engine."""
        # Fork pattern (knight attacking two pieces)
        fork_pattern = ChessPattern(
            pattern_type=PatternType.TACTICAL,
            squares=(chess.C3, chess.D5, chess.F5),
            pieces=(chess.Piece(chess.KNIGHT, chess.WHITE), 
                   chess.Piece(chess.QUEEN, chess.BLACK),
                   chess.Piece(chess.ROOK, chess.BLACK)),
            constraints=(("tactical", True), ("fork", True)),
            frequency=0.4
        )
        self.add_pattern(fork_pattern)
        
        # Pin pattern
        pin_pattern = ChessPattern(
            pattern_type=PatternType.TACTICAL,
            squares=(chess.E1, chess.E4, chess.E7),
            pieces=(chess.Piece(chess.ROOK, chess.WHITE),
                   chess.Piece(chess.KNIGHT, chess.BLACK),
                   chess.Piece(chess.KING, chess.BLACK)),
            constraints=(("tactical", True), ("pin", True)),
            frequency=0.3
        )
        self.add_pattern(pin_pattern)
        
        # Skewer pattern
        skewer_pattern = ChessPattern(
            pattern_type=PatternType.TACTICAL,
            squares=(chess.E1, chess.E7, chess.E8),
            pieces=(chess.Piece(chess.ROOK, chess.WHITE),
                   chess.Piece(chess.QUEEN, chess.BLACK),
                   chess.Piece(chess.KING, chess.BLACK)),
            constraints=(("tactical", True), ("skewer", True)),
            frequency=0.25
        )
        self.add_pattern(skewer_pattern)
        
        # Discovered attack pattern
        discovered_attack_pattern = ChessPattern(
            pattern_type=PatternType.TACTICAL,
            squares=(chess.D1, chess.D4, chess.D7),
            pieces=(chess.Piece(chess.QUEEN, chess.WHITE),
                   chess.Piece(chess.PAWN, chess.WHITE),
                   chess.Piece(chess.QUEEN, chess.BLACK)),
            constraints=(("tactical", True), ("discovered_attack", True)),
            frequency=0.3
        )
        self.add_pattern(discovered_attack_pattern)
        
        # Double attack pattern
        double_attack_pattern = ChessPattern(
            pattern_type=PatternType.TACTICAL,
            squares=(chess.C3, chess.D5, chess.F5, chess.G7),
            pieces=(chess.Piece(chess.KNIGHT, chess.WHITE),
                   chess.Piece(chess.QUEEN, chess.BLACK),
                   chess.Piece(chess.ROOK, chess.BLACK),
                   chess.Piece(chess.KING, chess.BLACK)),
            constraints=(("tactical", True), ("double_attack", True)),
            frequency=0.2
        )
        self.add_pattern(double_attack_pattern)
        
        # Deflection pattern
        deflection_pattern = ChessPattern(
            pattern_type=PatternType.TACTICAL,
            squares=(chess.E4, chess.E5, chess.E6),
            pieces=(chess.Piece(chess.PAWN, chess.WHITE),
                   chess.Piece(chess.PAWN, chess.BLACK),
                   chess.Piece(chess.KING, chess.BLACK)),
            constraints=(("tactical", True), ("deflection", True)),
            frequency=0.15
        )
        self.add_pattern(deflection_pattern)


def create_chess_wfc_engine() -> WFCEngine:
    """Create a WFC engine with common chess patterns."""
    engine = WFCEngine()
    engine.add_opening_patterns()
    engine.add_tactical_patterns()
    engine.learn_constraints_from_patterns()
    return engine


# Example usage
if __name__ == "__main__":
    # Create WFC engine
    wfc_engine = create_chess_wfc_engine()
    
    # Generate a pattern
    generated_board = wfc_engine.generate_pattern()
    
    if generated_board:
        print("Generated chess pattern:")
        print(generated_board)
    else:
        print("Failed to generate pattern")