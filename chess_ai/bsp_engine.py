"""
Binary Space Partitioning (BSP) Engine for Chess Board Analysis.

This module implements BSP for spatial organization and analysis
of chess board positions, zones, and strategic areas.
"""

import random
import math
from typing import List, Dict, Set, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import chess
from chess import Board, Square, Piece, Move


class SplitDirection(Enum):
    """Direction for BSP splits."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass
class BSPNode:
    """Represents a node in the BSP tree."""
    x: int
    y: int
    width: int
    height: int
    left_child: Optional['BSPNode'] = None
    right_child: Optional['BSPNode'] = None
    parent: Optional['BSPNode'] = None
    is_leaf: bool = True
    split_direction: Optional[SplitDirection] = None
    split_position: Optional[int] = None
    zone_type: Optional[str] = None
    pieces: List[Square] = None
    
    def __post_init__(self):
        if self.pieces is None:
            self.pieces = []
    
    @property
    def area(self) -> int:
        """Calculate the area of this node."""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get the center point of this node."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def contains_square(self, square: Square) -> bool:
        """Check if this node contains a given square."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        return (self.x <= file < self.x + self.width and 
                self.y <= rank < self.y + self.height)
    
    def get_squares_in_zone(self) -> List[Square]:
        """Get all squares that belong to this zone."""
        squares = []
        for file in range(self.x, self.x + self.width):
            for rank in range(self.y, self.y + self.height):
                square = chess.square(file, rank)
                squares.append(square)
        return squares


class BSPEngine:
    """
    Binary Space Partitioning engine for chess board analysis.
    
    This engine can partition the chess board into strategic zones
    and analyze spatial relationships between pieces.
    """
    
    def __init__(self, board_size: int = 8):
        self.board_size = board_size
        self.root: Optional[BSPNode] = None
        self.leaf_nodes: List[BSPNode] = []
        
    def create_root(self) -> BSPNode:
        """Create the root node covering the entire board."""
        self.root = BSPNode(0, 0, self.board_size, self.board_size)
        return self.root
    
    def split_node(self, node: BSPNode, min_size: int = 2) -> bool:
        """Split a node into two children if possible."""
        if not node.is_leaf:
            return False
            
        # Determine split direction and position
        split_direction, split_pos = self._choose_split(node, min_size)
        if split_direction is None:
            return False
            
        # Create children
        if split_direction == SplitDirection.HORIZONTAL:
            # Split horizontally (by rank)
            left_child = BSPNode(
                node.x, node.y, 
                node.width, split_pos - node.y,
                parent=node
            )
            right_child = BSPNode(
                node.x, split_pos,
                node.width, node.height - (split_pos - node.y),
                parent=node
            )
        else:
            # Split vertically (by file)
            left_child = BSPNode(
                node.x, node.y,
                split_pos - node.x, node.height,
                parent=node
            )
            right_child = BSPNode(
                split_pos, node.y,
                node.width - (split_pos - node.x), node.height,
                parent=node
            )
        
        node.left_child = left_child
        node.right_child = right_child
        node.is_leaf = False
        node.split_direction = split_direction
        node.split_position = split_pos
        
        return True
    
    def _choose_split(self, node: BSPNode, min_size: int) -> Tuple[Optional[SplitDirection], Optional[int]]:
        """Choose the best split direction and position for a node."""
        # Check if we can split horizontally
        can_split_h = node.height > min_size * 2
        can_split_v = node.width > min_size * 2
        
        if not can_split_h and not can_split_v:
            return None, None
            
        # Prefer splitting the longer dimension
        if can_split_h and can_split_v:
            if node.height > node.width:
                direction = SplitDirection.HORIZONTAL
            else:
                direction = SplitDirection.VERTICAL
        elif can_split_h:
            direction = SplitDirection.HORIZONTAL
        else:
            direction = SplitDirection.VERTICAL
            
        # Choose split position
        if direction == SplitDirection.HORIZONTAL:
            min_split = node.y + min_size
            max_split = node.y + node.height - min_size
        else:
            min_split = node.x + min_size
            max_split = node.x + node.width - min_size
            
        if min_split >= max_split:
            return None, None
            
        # Random split position within valid range
        split_pos = random.randint(min_split, max_split)
        return direction, split_pos
    
    def build_tree(self, max_depth: int = 3, min_zone_size: int = 2) -> None:
        """Build the BSP tree by recursively splitting nodes."""
        if self.root is None:
            self.create_root()
            
        self._build_tree_recursive(self.root, max_depth, min_zone_size)
        self._collect_leaf_nodes()
        self._classify_zones()
    
    def _build_tree_recursive(self, node: BSPNode, max_depth: int, min_zone_size: int) -> None:
        """Recursively build the BSP tree."""
        if max_depth <= 0:
            return
            
        if self.split_node(node, min_zone_size):
            self._build_tree_recursive(node.left_child, max_depth - 1, min_zone_size)
            self._build_tree_recursive(node.right_child, max_depth - 1, min_zone_size)
    
    def _collect_leaf_nodes(self) -> None:
        """Collect all leaf nodes in the tree."""
        self.leaf_nodes = []
        if self.root:
            self._collect_leaf_nodes_recursive(self.root)
    
    def _collect_leaf_nodes_recursive(self, node: BSPNode) -> None:
        """Recursively collect leaf nodes."""
        if node.is_leaf:
            self.leaf_nodes.append(node)
        else:
            if node.left_child:
                self._collect_leaf_nodes_recursive(node.left_child)
            if node.right_child:
                self._collect_leaf_nodes_recursive(node.right_child)
    
    def _classify_zones(self) -> None:
        """Classify zones based on their position and characteristics."""
        for node in self.leaf_nodes:
            center_x, center_y = node.center
            zone_type = self._determine_zone_type(center_x, center_y, node)
            node.zone_type = zone_type
    
    def _determine_zone_type(self, x: int, y: int, node: BSPNode) -> str:
        """Determine the type of zone based on position."""
        # Center zones
        if 2 <= x <= 5 and 2 <= y <= 5:
            return "center"
        
        # Corner zones
        if (x <= 1 and y <= 1) or (x >= 6 and y <= 1) or (x <= 1 and y >= 6) or (x >= 6 and y >= 6):
            return "corner"
        
        # Edge zones
        if x <= 1 or x >= 6 or y <= 1 or y >= 6:
            return "edge"
        
        # Flank zones
        if x <= 2 or x >= 5:
            return "flank"
        
        return "general"
    
    def analyze_board(self, board: Board) -> Dict[str, Any]:
        """Analyze a chess board using BSP zones."""
        if not self.leaf_nodes:
            self.build_tree()
            
        # Assign pieces to zones
        for node in self.leaf_nodes:
            node.pieces = []
            for square in node.get_squares_in_zone():
                piece = board.piece_at(square)
                if piece:
                    node.pieces.append(square)
        
        # Calculate zone statistics
        zone_stats = {}
        for node in self.leaf_nodes:
            zone_type = node.zone_type
            if zone_type not in zone_stats:
                zone_stats[zone_type] = {
                    'zones': 0,
                    'total_pieces': 0,
                    'white_pieces': 0,
                    'black_pieces': 0,
                    'squares': []
                }
            
            zone_stats[zone_type]['zones'] += 1
            zone_stats[zone_type]['total_pieces'] += len(node.pieces)
            zone_stats[zone_type]['squares'].extend(node.get_squares_in_zone())
            
            for square in node.pieces:
                piece = board.piece_at(square)
                if piece.color == chess.WHITE:
                    zone_stats[zone_type]['white_pieces'] += 1
                else:
                    zone_stats[zone_type]['black_pieces'] += 1
        
        return zone_stats
    
    def get_zone_for_square(self, square: Square) -> Optional[BSPNode]:
        """Get the zone that contains a specific square."""
        if not self.leaf_nodes:
            return None
            
        for node in self.leaf_nodes:
            if node.contains_square(square):
                return node
        return None
    
    def get_adjacent_zones(self, zone: BSPNode) -> List[BSPNode]:
        """Get zones adjacent to a given zone."""
        adjacent = []
        zone_squares = set(zone.get_squares_in_zone())
        
        for other_zone in self.leaf_nodes:
            if other_zone == zone:
                continue
                
            other_squares = set(other_zone.get_squares_in_zone())
            
            # Check if zones are adjacent (share an edge)
            if self._zones_are_adjacent(zone_squares, other_squares):
                adjacent.append(other_zone)
        
        return adjacent
    
    def _zones_are_adjacent(self, squares1: Set[Square], squares2: Set[Square]) -> bool:
        """Check if two zones are adjacent."""
        for square1 in squares1:
            for square2 in squares2:
                if self._squares_are_adjacent(square1, square2):
                    return True
        return False
    
    def _squares_are_adjacent(self, square1: Square, square2: Square) -> bool:
        """Check if two squares are adjacent."""
        file1, rank1 = chess.square_file(square1), chess.square_rank(square1)
        file2, rank2 = chess.square_file(square2), chess.square_rank(square2)
        
        return abs(file1 - file2) <= 1 and abs(rank1 - rank2) <= 1
    
    def calculate_zone_control(self, board: Board, color: chess.Color) -> Dict[str, float]:
        """Calculate zone control for a given color."""
        if not self.leaf_nodes:
            self.build_tree()
            
        zone_control = {}
        
        for node in self.leaf_nodes:
            zone_type = node.zone_type
            if zone_type not in zone_control:
                zone_control[zone_type] = 0.0
            
            # Count pieces of the given color in this zone
            color_pieces = 0
            for square in node.pieces:
                piece = board.piece_at(square)
                if piece and piece.color == color:
                    color_pieces += 1
            
            # Calculate control based on piece count and zone importance
            zone_importance = self._get_zone_importance(zone_type)
            control_value = color_pieces * zone_importance
            zone_control[zone_type] += control_value
        
        return zone_control
    
    def _get_zone_importance(self, zone_type: str) -> float:
        """Get the importance multiplier for a zone type."""
        importance_map = {
            "center": 2.0,
            "flank": 1.5,
            "edge": 1.0,
            "corner": 0.5,
            "general": 1.0
        }
        return importance_map.get(zone_type, 1.0)
    
    def analyze_move(self, board: chess.Board, move: chess.Move) -> Dict[str, Any]:
        """Analyze a specific move using BSP zones."""
        if not self.leaf_nodes:
            self.build_tree()
        
        analysis = {
            "move_zone": None,
            "zone_control": {},
            "zone_importance": 0.0,
            "adjacent_zones": [],
            "bsp_zones": []
        }
        
        # Get zone for move destination
        move_zone = self.get_zone_for_square(move.to_square)
        analysis["move_zone"] = move_zone
        
        if move_zone:
            analysis["zone_importance"] = self._get_zone_importance(move_zone.zone_type)
            analysis["adjacent_zones"] = self.get_adjacent_zones(move_zone)
            
            # Add all squares in the move zone for visualization
            analysis["bsp_zones"] = move_zone.get_squares_in_zone()
        
        # Calculate zone control for the moving color
        analysis["zone_control"] = self.calculate_zone_control(board, board.turn)
        
        return analysis
    
    def get_zones_for_visualization(self) -> Dict[str, List[chess.Square]]:
        """Get zones organized by type for visualization."""
        zones_by_type = {}
        
        for node in self.leaf_nodes:
            zone_type = node.zone_type or "unknown"
            if zone_type not in zones_by_type:
                zones_by_type[zone_type] = []
            zones_by_type[zone_type].extend(node.get_squares_in_zone())
        
        return zones_by_type
    
    def visualize_zones(self) -> str:
        """Create a visual representation of the BSP zones."""
        if not self.leaf_nodes:
            return "No zones available. Call build_tree() first."
        
        # Create a grid representation
        grid = [[' ' for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # Fill grid with zone types
        for node in self.leaf_nodes:
            zone_type = node.zone_type or "unknown"
            zone_char = zone_type[0].upper() if zone_type else "?"
            
            for square in node.get_squares_in_zone():
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                grid[rank][file] = zone_char
        
        # Create string representation
        result = "BSP Zone Map:\n"
        result += "  " + " ".join([chr(ord('a') + i) for i in range(self.board_size)]) + "\n"
        
        for rank in range(self.board_size - 1, -1, -1):
            result += f"{rank + 1} " + " ".join(grid[rank]) + f" {rank + 1}\n"
        
        result += "  " + " ".join([chr(ord('a') + i) for i in range(self.board_size)]) + "\n"
        result += "\nZone Types: C=Center, F=Flank, E=Edge, G=General\n"
        
        return result


def create_chess_bsp_engine() -> BSPEngine:
    """Create a BSP engine for chess board analysis."""
    engine = BSPEngine()
    engine.build_tree(max_depth=3, min_zone_size=2)
    return engine


# Example usage
if __name__ == "__main__":
    # Create BSP engine
    bsp_engine = create_chess_bsp_engine()
    
    # Create a sample board
    board = Board()
    
    # Analyze the board
    zone_stats = bsp_engine.analyze_board(board)
    print("Zone Statistics:")
    for zone_type, stats in zone_stats.items():
        print(f"{zone_type}: {stats['zones']} zones, {stats['total_pieces']} pieces")
    
    # Visualize zones
    print("\n" + bsp_engine.visualize_zones())
    
    # Calculate zone control
    white_control = bsp_engine.calculate_zone_control(board, chess.WHITE)
    black_control = bsp_engine.calculate_zone_control(board, chess.BLACK)
    
    print(f"\nWhite zone control: {white_control}")
    print(f"Black zone control: {black_control}")