"""
Bot Filter Module

This module provides filtering capabilities for chess bots based on position
characteristics and pattern matching. It enables dynamic bot selection
according to game state and tactical patterns.
"""

import chess
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FilterType(Enum):
    """Types of bot filters."""
    POSITION = "position"
    PATTERN = "pattern"
    GAME_PHASE = "game_phase"
    MATERIAL = "material"
    TACTICAL = "tactical"


class GamePhase(Enum):
    """Game phases for filtering."""
    OPENING = "opening"
    MIDDLEGAME = "middlegame"
    ENDGAME = "endgame"


@dataclass
class FilterCriteria:
    """Criteria for filtering bots."""
    
    # Position-based filters
    piece_count_range: Optional[Tuple[int, int]] = None
    king_safety_required: bool = False
    center_control_required: bool = False
    pawn_structure_required: bool = False
    
    # Pattern-based filters
    required_patterns: List[str] = None
    excluded_patterns: List[str] = None
    pattern_types: List[str] = None
    
    # Game phase filters
    game_phase: Optional[GamePhase] = None
    move_number_range: Optional[Tuple[int, int]] = None
    
    # Material filters
    material_advantage: Optional[str] = None  # "white", "black", "equal"
    material_imbalance_threshold: float = 0.0
    
    # Tactical filters
    checks_available: bool = False
    captures_available: bool = False
    threats_required: bool = False
    
    def __post_init__(self):
        if self.required_patterns is None:
            self.required_patterns = []
        if self.excluded_patterns is None:
            self.excluded_patterns = []
        if self.pattern_types is None:
            self.pattern_types = []


@dataclass
class BotCapability:
    """Bot capability description."""
    
    bot_name: str
    bot_class: str
    
    # Position capabilities
    preferred_phases: List[GamePhase] = None
    material_situations: List[str] = None  # "advantage", "disadvantage", "equal"
    
    # Pattern capabilities
    supported_patterns: List[str] = None
    pattern_types: List[str] = None
    
    # Tactical capabilities
    tactical_awareness: bool = False
    defensive_strength: float = 0.0  # 0.0 to 1.0
    aggressive_tendency: float = 0.0  # 0.0 to 1.0
    
    # Positional understanding
    king_safety_awareness: bool = False
    center_control_focus: bool = False
    pawn_structure_expertise: bool = False
    
    def __post_init__(self):
        if self.preferred_phases is None:
            self.preferred_phases = []
        if self.material_situations is None:
            self.material_situations = []
        if self.supported_patterns is None:
            self.supported_patterns = []
        if self.pattern_types is None:
            self.pattern_types = []


class PositionAnalyzer:
    """Analyzes chess positions to extract filtering criteria."""
    
    def __init__(self):
        self.center_squares = {
            chess.D4, chess.E4, chess.D5, chess.E5,
            chess.C3, chess.F3, chess.C6, chess.F6
        }
        self.extended_center = {
            chess.C3, chess.D3, chess.E3, chess.F3,
            chess.C4, chess.D4, chess.E4, chess.F4,
            chess.C5, chess.D5, chess.E5, chess.F5,
            chess.C6, chess.D6, chess.E6, chess.F6
        }
    
    def analyze_position(self, board: chess.Board) -> Dict[str, Any]:
        """Analyze current position and return characteristics."""
        
        # Basic position info
        piece_count = len(board.piece_map())
        move_number = board.ply() // 2
        
        # Game phase determination
        game_phase = self._determine_game_phase(board, piece_count, move_number)
        
        # Material analysis
        material_balance = self._calculate_material_balance(board)
        material_advantage = self._determine_material_advantage(material_balance)
        
        # Positional features
        center_control = self._analyze_center_control(board)
        king_safety = self._analyze_king_safety(board)
        pawn_structure = self._analyze_pawn_structure(board)
        
        # Tactical opportunities
        checks_available = any(board.gives_check(move) for move in board.legal_moves)
        captures_available = any(board.is_capture(move) for move in board.legal_moves)
        threats = self._identify_threats(board)
        
        return {
            "piece_count": piece_count,
            "move_number": move_number,
            "game_phase": game_phase,
            "material_balance": material_balance,
            "material_advantage": material_advantage,
            "center_control": center_control,
            "king_safety": king_safety,
            "pawn_structure": pawn_structure,
            "checks_available": checks_available,
            "captures_available": captures_available,
            "threats": threats
        }
    
    def _determine_game_phase(self, board: chess.Board, piece_count: int, move_number: int) -> GamePhase:
        """Determine the current game phase."""
        if piece_count > 28 or move_number < 10:
            return GamePhase.OPENING
        elif piece_count > 20 or move_number < 30:
            return GamePhase.MIDDLEGAME
        else:
            return GamePhase.ENDGAME
    
    def _calculate_material_balance(self, board: chess.Board) -> float:
        """Calculate material balance (positive = white advantage)."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        balance = 0.0
        for square, piece in board.piece_map().items():
            value = piece_values.get(piece.piece_type, 0)
            if piece.color == chess.WHITE:
                balance += value
            else:
                balance -= value
        
        return balance
    
    def _determine_material_advantage(self, balance: float) -> str:
        """Determine who has material advantage."""
        if abs(balance) < 1.0:
            return "equal"
        elif balance > 0:
            return "white"
        else:
            return "black"
    
    def _analyze_center_control(self, board: chess.Board) -> Dict[str, Any]:
        """Analyze center control."""
        white_control = 0
        black_control = 0
        
        for square in self.center_squares:
            if board.is_attacked_by(chess.WHITE, square):
                white_control += 1
            if board.is_attacked_by(chess.BLACK, square):
                black_control += 1
        
        return {
            "white_control": white_control,
            "black_control": black_control,
            "dominance": "white" if white_control > black_control else "black" if black_control > white_control else "equal"
        }
    
    def _analyze_king_safety(self, board: chess.Board) -> Dict[str, Any]:
        """Analyze king safety for both sides."""
        safety = {}
        
        for color in [chess.WHITE, chess.BLACK]:
            king_square = board.king(color)
            if king_square is None:
                continue
            
            # Count attackers near king
            attackers = len([attacker for attacker in board.attackers(not color, king_square)])
            pawn_shield = self._count_pawn_shield(board, king_square, color)
            
            safety[color] = {
                "attackers": attackers,
                "pawn_shield": pawn_shield,
                "safe": attackers <= 1 and pawn_shield >= 2
            }
        
        return safety
    
    def _count_pawn_shield(self, board: chess.Board, king_square: chess.Square, color: chess.Color) -> int:
        """Count pawn shield in front of king."""
        shield_count = 0
        pawn_direction = 1 if color == chess.WHITE else -1
        
        # Check squares in front of king
        for file_offset in [-1, 0, 1]:
            shield_square = king_square + pawn_direction * 8 + file_offset
            if 0 <= shield_square < 64:
                piece = board.piece_at(shield_square)
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    shield_count += 1
        
        return shield_count
    
    def _analyze_pawn_structure(self, board: chess.Board) -> Dict[str, Any]:
        """Analyze pawn structure quality."""
        doubled_pawns = 0
        isolated_pawns = 0
        passed_pawns = 0
        
        pawns_by_file = {chess.WHITE: [[] for _ in range(8)], chess.BLACK: [[] for _ in range(8)]}
        
        for square, piece in board.piece_map().items():
            if piece.piece_type == chess.PAWN:
                file = chess.square_file(square)
                pawns_by_file[piece.color][file].append(square)
        
        # Count structural issues
        for color in [chess.WHITE, chess.BLACK]:
            for file_pawns in pawns_by_file[color]:
                if len(file_pawns) > 1:
                    doubled_pawns += len(file_pawns) - 1
                
                for pawn_square in file_pawns:
                    file = chess.square_file(pawn_square)
                    
                    # Check isolation
                    has_friends = False
                    for check_file in [file - 1, file + 1]:
                        if 0 <= check_file < 8 and pawns_by_file[color][check_file]:
                            has_friends = True
                            break
                    
                    if not has_friends:
                        isolated_pawns += 1
        
        return {
            "doubled_pawns": doubled_pawns,
            "isolated_pawns": isolated_pawns,
            "passed_pawns": passed_pawns,
            "quality": "good" if doubled_pawns + isolated_pawns <= 2 else "fair" if doubled_pawns + isolated_pawns <= 4 else "poor"
        }
    
    def _identify_threats(self, board: chess.Board) -> List[str]:
        """Identify tactical threats in the position."""
        threats = []
        
        for move in board.legal_moves:
            if board.is_capture(move):
                threats.append("capture")
            if board.gives_check(move):
                threats.append("check")
            
            # Check for forks (simplified)
            if board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type == chess.KNIGHT:
                attacked_pieces = 0
                for target in board.attacks(move.to_square):
                    if board.piece_at(target) and board.piece_at(target).piece_type in [chess.QUEEN, chess.ROOK]:
                        attacked_pieces += 1
                if attacked_pieces >= 2:
                    threats.append("fork")
        
        return list(set(threats))


class BotFilter:
    """Main bot filtering system."""
    
    def __init__(self, pattern_responder=None):
        self.position_analyzer = PositionAnalyzer()
        self.pattern_responder = pattern_responder
        self.bot_capabilities: Dict[str, BotCapability] = {}
        self._initialize_default_capabilities()
    
    def _initialize_default_capabilities(self):
        """Initialize default bot capabilities."""
        
        # AggressiveBot - excels in tactical positions
        self.bot_capabilities["AggressiveBot"] = BotCapability(
            bot_name="AggressiveBot",
            bot_class="AggressiveBot",
            preferred_phases=[GamePhase.MIDDLEGAME],
            material_situations=["advantage"],
            pattern_types=["tactical"],
            tactical_awareness=True,
            aggressive_tendency=0.9,
            defensive_strength=0.3,
            center_control_focus=True
        )
        
        # FortifyBot - defensive specialist
        self.bot_capabilities["FortifyBot"] = BotCapability(
            bot_name="FortifyBot",
            bot_class="FortifyBot",
            preferred_phases=[GamePhase.MIDDLEGAME, GamePhase.ENDGAME],
            material_situations=["disadvantage", "equal"],
            tactical_awareness=True,
            aggressive_tendency=0.2,
            defensive_strength=0.9,
            king_safety_awareness=True,
            pawn_structure_expertise=True
        )
        
        # EndgameBot - endgame specialist
        self.bot_capabilities["EndgameBot"] = BotCapability(
            bot_name="EndgameBot",
            bot_class="EndgameBot",
            preferred_phases=[GamePhase.ENDGAME],
            material_situations=["advantage", "equal", "disadvantage"],
            tactical_awareness=True,
            aggressive_tendency=0.5,
            defensive_strength=0.7,
            king_safety_awareness=True
        )
        
        # TrapBot - tactical trap specialist
        self.bot_capabilities["TrapBot"] = BotCapability(
            bot_name="TrapBot",
            bot_class="TrapBot",
            preferred_phases=[GamePhase.MIDDLEGAME],
            material_situations=["equal"],
            pattern_types=["tactical"],
            supported_patterns=["trap_piece", "fork", "pin"],
            tactical_awareness=True,
            aggressive_tendency=0.6,
            defensive_strength=0.5
        )
        
        # CriticalBot - targets critical pieces
        self.bot_capabilities["CriticalBot"] = BotCapability(
            bot_name="CriticalBot",
            bot_class="CriticalBot",
            preferred_phases=[GamePhase.MIDDLEGAME],
            material_situations=["equal", "advantage"],
            pattern_types=["tactical"],
            tactical_awareness=True,
            aggressive_tendency=0.8,
            defensive_strength=0.4
        )
        
        # PieceMateBot - piece trapping specialist
        self.bot_capabilities["PieceMateBot"] = BotCapability(
            bot_name="PieceMateBot",
            bot_class="PieceMateBot",
            preferred_phases=[GamePhase.MIDDLEGAME],
            material_situations=["equal"],
            pattern_types=["tactical"],
            supported_patterns=["trap_piece"],
            tactical_awareness=True,
            aggressive_tendency=0.7,
            defensive_strength=0.6
        )
        
        # KingValueBot - king safety focused
        self.bot_capabilities["KingValueBot"] = BotCapability(
            bot_name="KingValueBot",
            bot_class="KingValueBot",
            preferred_phases=[GamePhase.MIDDLEGAME, GamePhase.ENDGAME],
            material_situations=["disadvantage", "equal"],
            tactical_awareness=True,
            aggressive_tendency=0.3,
            defensive_strength=0.8,
            king_safety_awareness=True
        )
        
        # DynamicBot - adaptive
        self.bot_capabilities["DynamicBot"] = BotCapability(
            bot_name="DynamicBot",
            bot_class="DynamicBot",
            preferred_phases=[GamePhase.OPENING, GamePhase.MIDDLEGAME, GamePhase.ENDGAME],
            material_situations=["advantage", "equal", "disadvantage"],
            pattern_types=["opening", "tactical", "endgame", "positional"],
            tactical_awareness=True,
            aggressive_tendency=0.5,
            defensive_strength=0.5,
            center_control_focus=True,
            pawn_structure_expertise=True
        )
        
        # RandomBot - fallback
        self.bot_capabilities["RandomBot"] = BotCapability(
            bot_name="RandomBot",
            bot_class="RandomBot",
            preferred_phases=[GamePhase.OPENING, GamePhase.MIDDLEGAME, GamePhase.ENDGAME],
            material_situations=["advantage", "equal", "disadvantage"],
            tactical_awareness=False,
            aggressive_tendency=0.5,
            defensive_strength=0.5
        )
    
    def filter_bots(self, board: chess.Board, available_bots: List[str], 
                   criteria: Optional[FilterCriteria] = None) -> List[str]:
        """Filter bots based on position and criteria."""
        
        if criteria is None:
            criteria = FilterCriteria()
        
        position_analysis = self.position_analyzer.analyze_position(board)
        filtered_bots = []
        
        for bot_name in available_bots:
            if bot_name not in self.bot_capabilities:
                continue
            
            capability = self.bot_capabilities[bot_name]
            
            if self._bot_matches_criteria(bot_name, capability, position_analysis, criteria):
                filtered_bots.append(bot_name)
        
        logger.info(f"Filtered {len(filtered_bots)} bots from {len(available_bots)} available")
        return filtered_bots
    
    def _bot_matches_criteria(self, bot_name: str, capability: BotCapability, 
                             position: Dict[str, Any], criteria: FilterCriteria) -> bool:
        """Check if a bot matches the filtering criteria."""
        
        # Game phase filter
        if criteria.game_phase and criteria.game_phase not in capability.preferred_phases:
            return False
        
        # Material filter
        if criteria.material_advantage:
            if criteria.material_advantage not in capability.material_situations:
                return False
        
        # Piece count filter
        if criteria.piece_count_range:
            piece_count = position["piece_count"]
            if not (criteria.piece_count_range[0] <= piece_count <= criteria.piece_count_range[1]):
                return False
        
        # Move number filter
        if criteria.move_number_range:
            move_number = position["move_number"]
            if not (criteria.move_number_range[0] <= move_number <= criteria.move_number_range[1]):
                return False
        
        # King safety requirement
        if criteria.king_safety_required and not capability.king_safety_awareness:
            return False
        
        # Center control requirement
        if criteria.center_control_required and not capability.center_control_focus:
            return False
        
        # Pawn structure requirement
        if criteria.pawn_structure_required and not capability.pawn_structure_expertise:
            return False
        
        # Tactical requirements
        if criteria.checks_available and not capability.tactical_awareness:
            return False
        
        if criteria.captures_available and capability.aggressive_tendency < 0.5:
            return False
        
        if criteria.threats_required and not capability.tactical_awareness:
            return False
        
        # Pattern type filter
        if criteria.pattern_types:
            if not any(pt in capability.pattern_types for pt in criteria.pattern_types):
                return False
        
        # Pattern matching (if pattern_responder available)
        if self.pattern_responder and (criteria.required_patterns or criteria.excluded_patterns):
            board = chess.Board()  # This would need to be passed in properly
            pattern_analysis = self.pattern_responder.analyze_position(board)
            matching_patterns = [match["pattern_type"] for match in pattern_analysis["matches"]]
            
            # Check required patterns
            if criteria.required_patterns:
                if not any(pattern in matching_patterns for pattern in criteria.required_patterns):
                    return False
            
            # Check excluded patterns
            if criteria.excluded_patterns:
                if any(pattern in matching_patterns for pattern in criteria.excluded_patterns):
                    return False
        
        return True
    
    def get_recommended_bots(self, board: chess.Board, available_bots: List[str], 
                           top_n: int = 3) -> List[Tuple[str, float]]:
        """Get top N recommended bots with scores."""
        
        position_analysis = self.position_analyzer.analyze_position(board)
        scored_bots = []
        
        for bot_name in available_bots:
            if bot_name not in self.bot_capabilities:
                continue
            
            capability = self.bot_capabilities[bot_name]
            score = self._calculate_bot_score(bot_name, capability, position_analysis)
            scored_bots.append((bot_name, score))
        
        # Sort by score (descending) and return top N
        scored_bots.sort(key=lambda x: x[1], reverse=True)
        return scored_bots[:top_n]
    
    def _calculate_bot_score(self, bot_name: str, capability: BotCapability, 
                           position: Dict[str, Any]) -> float:
        """Calculate suitability score for a bot in current position."""
        
        score = 0.0
        
        # Game phase suitability
        current_phase = position["game_phase"]
        if current_phase in capability.preferred_phases:
            score += 0.3
        
        # Material situation suitability
        material_advantage = position["material_advantage"]
        material_map = {"white": "advantage", "black": "disadvantage", "equal": "equal"}
        current_material = material_map.get(material_advantage, "equal")
        if current_material in capability.material_situations:
            score += 0.2
        
        # Tactical awareness bonus
        if position["checks_available"] or position["captures_available"] or position["threats"]:
            if capability.tactical_awareness:
                score += 0.2
        
        # Positional feature bonuses
        if position["king_safety"].get(chess.WHITE, {}).get("safe", False) and capability.king_safety_awareness:
            score += 0.1
        
        if position["center_control"]["dominance"] != "equal" and capability.center_control_focus:
            score += 0.1
        
        if position["pawn_structure"]["quality"] == "good" and capability.pawn_structure_expertise:
            score += 0.1
        
        return min(score, 1.0)
    
    def add_bot_capability(self, capability: BotCapability):
        """Add or update a bot capability."""
        self.bot_capabilities[capability.bot_name] = capability
        logger.info(f"Added capability for bot: {capability.bot_name}")
    
    def get_bot_capability(self, bot_name: str) -> Optional[BotCapability]:
        """Get capability for a specific bot."""
        return self.bot_capabilities.get(bot_name)
    
    def list_available_capabilities(self) -> List[str]:
        """List all available bot capabilities."""
        return list(self.bot_capabilities.keys())


# Factory function
def create_bot_filter(pattern_responder=None) -> BotFilter:
    """Create a bot filter with optional pattern responder."""
    return BotFilter(pattern_responder)


# Utility functions
def create_opening_filter() -> FilterCriteria:
    """Create filter criteria for opening positions."""
    return FilterCriteria(
        game_phase=GamePhase.OPENING,
        move_number_range=(0, 15),
        piece_count_range=(28, 32)
    )


def create_middlegame_filter() -> FilterCriteria:
    """Create filter criteria for middlegame positions."""
    return FilterCriteria(
        game_phase=GamePhase.MIDDLEGAME,
        move_number_range=(15, 35),
        piece_count_range=(20, 28),
        tactical_awareness=True
    )


def create_endgame_filter() -> FilterCriteria:
    """Create filter criteria for endgame positions."""
    return FilterCriteria(
        game_phase=GamePhase.ENDGAME,
        move_number_range=(35, 100),
        piece_count_range=(10, 20),
        king_safety_required=True
    )


def create_tactical_filter() -> FilterCriteria:
    """Create filter criteria for tactical positions."""
    return FilterCriteria(
        pattern_types=["tactical"],
        checks_available=True,
        captures_available=True,
        threats_required=True
    )


def create_positional_filter() -> FilterCriteria:
    """Create filter criteria for positional positions."""
    return FilterCriteria(
        pattern_types=["positional"],
        center_control_required=True,
        pawn_structure_required=True,
        king_safety_required=True
    )


if __name__ == "__main__":
    # Example usage
    import chess
    
    # Create bot filter
    filter = create_bot_filter()
    
    # Create test board
    board = chess.Board()
    
    # Filter bots for opening
    opening_filter = create_opening_filter()
    available_bots = ["AggressiveBot", "FortifyBot", "EndgameBot", "DynamicBot", "RandomBot"]
    
    filtered = filter.filter_bots(board, available_bots, opening_filter)
    print(f"Opening bots: {filtered}")
    
    # Get recommendations
    recommendations = filter.get_recommended_bots(board, available_bots)
    print(f"Recommended bots: {recommendations}")
    
    # Analyze position
    analysis = filter.position_analyzer.analyze_position(board)
    print(f"Position analysis: {analysis}")
