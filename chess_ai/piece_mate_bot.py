from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict

import chess
import numpy as np

from core.evaluator import Evaluator, escape_squares, is_piece_mated
from metrics.attack_map import attack_count_per_square
from .see import static_exchange_eval
from .threat_map import ThreatMap
from utils import GameContext
try:
    from utils.heatmap_analyzer import HeatmapAnalyzer
    HEATMAP_AVAILABLE = True
except ImportError:
    HEATMAP_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class PieceAgent:
    """Represents a piece as an agent with coverage capabilities"""
    square: int
    piece_type: str  # 'P', 'N', 'B', 'R', 'Q', 'K'
    color: bool
    coverage_cells: Set[int]  # Cells this piece controls/attacks
    support_cells: Set[int]   # Cells that support/defend this piece
    influence_radius: int     # How far this piece projects power
    vulnerability_score: float # How exposed this piece is


class HeatmapManipulator:
    """
    Advanced heatmap manipulation system.
    
    Focuses on:
    1. Weakening enemy's surrounding heatmap through strategic targeting
    2. Creating safer surrounding heatmaps for your pieces through coordination
    """
    
    def __init__(self, color: bool = chess.WHITE):
        self.color = color
        self.enemy_color = not color
        
        # Agent coverage patterns for each piece type
        self.agent_patterns = {
            'P': self._pawn_agent_pattern,
            'N': self._knight_agent_pattern,
            'B': self._bishop_agent_pattern,
            'R': self._rook_agent_pattern,
            'Q': self._queen_agent_pattern,
            'K': self._king_agent_pattern
        }
        
        # Strategic cell values (how important cells are for coverage)
        self.strategic_values = self._initialize_strategic_values()
    
    def analyze_piece_agents(self, board: chess.Board) -> Dict[str, PieceAgent]:
        """Analyze all pieces as agents with coverage networks."""
        agents = {}
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == self.color:
                piece_key = f"{piece.symbol()}_{chess.square_name(square)}"
                
                # Calculate coverage and support networks
                coverage_cells = self._get_coverage_cells(board, square, piece.symbol())
                support_cells = self._get_support_cells(board, square)
                influence_radius = self._get_influence_radius(piece.symbol())
                vulnerability = self._calculate_vulnerability(board, square, piece.symbol())
                
                agents[piece_key] = PieceAgent(
                    square=square,
                    piece_type=piece.symbol().upper(),
                    color=piece.color,
                    coverage_cells=coverage_cells,
                    support_cells=support_cells,
                    influence_radius=influence_radius,
                    vulnerability_score=vulnerability
                )
        
        return agents
    
    def find_enemy_heatmap_weakening_moves(self, board: chess.Board) -> List[Tuple[chess.Move, float]]:
        """
        Find moves that weaken enemy's surrounding heatmap.
        
        Strategy:
        - Target enemy piece support networks
        - Attack cells that defend multiple enemy pieces
        - Create threats that force enemy pieces to vulnerable positions
        - Disrupt enemy piece coordination
        """
        weakening_moves = []
        enemy_agents = self._analyze_enemy_agents(board)
        
        for move in board.legal_moves:
            score = 0.0
            
            # Simulate move
            board.push(move)
            
            # 1. Check if move attacks enemy support cells
            attacked_supports = self._find_attacked_enemy_supports(board, enemy_agents)
            score += attacked_supports * 2.0
            
            # 2. Check if move creates multiple threats
            threats = self._count_created_threats(board, enemy_agents)
            score += threats * 1.5
            
            # 3. Check if move disrupts enemy coordination
            coordination_disruption = self._measure_coordination_disruption(board, enemy_agents)
            score += coordination_disruption * 1.8
            
            # 4. Check if move forces enemy pieces to open squares
            forced_vulnerability = self._measure_forced_vulnerability(board, enemy_agents)
            score += forced_vulnerability * 2.5
            
            board.pop()
            
            if score > 0:
                weakening_moves.append((move, score))
        
        return sorted(weakening_moves, key=lambda x: x[1], reverse=True)
    
    def find_safety_enhancement_moves(self, board: chess.Board) -> List[Tuple[chess.Move, float]]:
        """
        Find moves that create safer surrounding heatmaps for your pieces.
        
        Strategy:
        - Strengthen piece support networks
        - Create defensive coverage overlaps
        - Move pieces to cells with better defensive support
        - Coordinate pieces to protect each other
        """
        safety_moves = []
        friendly_agents = self.analyze_piece_agents(board)
        
        for move in board.legal_moves:
            score = 0.0
            
            # Simulate move
            board.push(move)
            
            # 1. Calculate new support network strength
            support_improvement = self._calculate_support_improvement(board, friendly_agents, move)
            score += support_improvement * 2.0
            
            # 2. Check for defensive coverage overlaps
            coverage_overlaps = self._count_defensive_overlaps(board)
            score += coverage_overlaps * 1.5
            
            # 3. Measure piece coordination improvement
            coordination_bonus = self._measure_coordination_improvement(board, friendly_agents)
            score += coordination_bonus * 1.8
            
            # 4. Check if move protects vulnerable pieces
            protection_value = self._calculate_protection_value(board, friendly_agents)
            score += protection_value * 2.2
            
            board.pop()
            
            if score > 0:
                safety_moves.append((move, score))
        
        return sorted(safety_moves, key=lambda x: x[1], reverse=True)
    
    def _get_coverage_cells(self, board: chess.Board, square: int, piece_symbol: str) -> Set[int]:
        """Get cells that this piece controls/attacks."""
        piece_type = piece_symbol.upper()
        if piece_type in self.agent_patterns:
            return self.agent_patterns[piece_type](board, square)
        return set()
    
    def _get_support_cells(self, board: chess.Board, square: int) -> Set[int]:
        """Get cells that support/defend this piece."""
        support_cells = set()
        color = board.piece_at(square).color if board.piece_at(square) else self.color
        
        for attacker_square in chess.SQUARES:
            if board.piece_at(attacker_square) and board.piece_at(attacker_square).color == color:
                if square in board.attacks(attacker_square):
                    support_cells.add(attacker_square)
        
        return support_cells
    
    def _get_influence_radius(self, piece_symbol: str) -> int:
        """Get how far this piece projects power."""
        influence_radii = {
            'P': 2,  # Pawns control immediate diagonals
            'N': 3,  # Knights have L-shaped reach
            'B': 7,  # Bishops control entire diagonals
            'R': 7,  # Rooks control entire files/ranks
            'Q': 7,  # Queens control multiple directions
            'K': 1   # Kings control adjacent squares
        }
        return influence_radii.get(piece_symbol.upper(), 1)
    
    def _calculate_vulnerability(self, board: chess.Board, square: int, piece_symbol: str) -> float:
        """Calculate how exposed this piece is."""
        enemy_attackers = len(board.attackers(self.enemy_color, square))
        friendly_defenders = len(board.attackers(self.color, square))
        
        # Base vulnerability
        vulnerability = max(0, enemy_attackers - friendly_defenders)
        
        # Piece value modifier
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
        piece_value = piece_values.get(piece_symbol.upper(), 1)
        
        return vulnerability * (piece_value / 3.0)  # Normalize by knight value
    
    def _analyze_enemy_agents(self, board: chess.Board) -> Dict[str, PieceAgent]:
        """Analyze enemy pieces as agents."""
        # Temporarily switch color to analyze enemy
        original_color = self.color
        self.color = self.enemy_color
        self.enemy_color = original_color
        
        enemy_agents = self.analyze_piece_agents(board)
        
        # Switch back
        self.color = original_color
        self.enemy_color = not original_color
        
        return enemy_agents
    
    def _find_attacked_enemy_supports(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> int:
        """Count how many enemy support cells are now under attack."""
        attacked_supports = 0
        
        for agent in enemy_agents.values():
            for support_cell in agent.support_cells:
                if len(board.attackers(self.color, support_cell)) > 0:
                    attacked_supports += 1
        
        return attacked_supports
    
    def _count_created_threats(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> int:
        """Count how many new threats are created against enemy pieces."""
        threats = 0
        
        for agent in enemy_agents.values():
            if len(board.attackers(self.color, agent.square)) > 0:
                threats += 1
        
        return threats
    
    def _measure_coordination_disruption(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> float:
        """Measure how much enemy coordination is disrupted."""
        disruption = 0.0
        
        # Check if key coordination cells are attacked
        coordination_cells = set()
        for agent in enemy_agents.values():
            coordination_cells.update(agent.support_cells)
            coordination_cells.update(agent.coverage_cells)
        
        for cell in coordination_cells:
            if len(board.attackers(self.color, cell)) > 0:
                disruption += 0.5
        
        return disruption
    
    def _measure_forced_vulnerability(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> float:
        """Measure if enemy pieces are forced into vulnerable positions."""
        forced_vulnerability = 0.0
        
        # Check if enemy pieces have limited escape squares
        for agent in enemy_agents.values():
            escape_squares = 0
            for move in board.legal_moves:
                if board.piece_at(move.from_square) and board.piece_at(move.from_square).color == self.enemy_color:
                    escape_squares += 1
            
            if escape_squares <= 2:  # Very limited mobility
                forced_vulnerability += 1.0
        
        return forced_vulnerability
    
    def _calculate_support_improvement(self, board: chess.Board, friendly_agents: Dict[str, PieceAgent], move: chess.Move) -> float:
        """Calculate how much the support network improves."""
        improvement = 0.0
        
        # Get new agents after move
        new_agents = self.analyze_piece_agents(board)
        
        # Compare support networks
        for agent_key, new_agent in new_agents.items():
            if agent_key in friendly_agents:
                old_support_count = len(friendly_agents[agent_key].support_cells)
                new_support_count = len(new_agent.support_cells)
                improvement += max(0, new_support_count - old_support_count) * 0.5
        
        return improvement
    
    def _count_defensive_overlaps(self, board: chess.Board) -> int:
        """Count defensive coverage overlaps for better safety."""
        overlaps = 0
        all_coverage = defaultdict(int)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == self.color:
                coverage = self._get_coverage_cells(board, square, piece.symbol())
                for cell in coverage:
                    all_coverage[cell] += 1
        
        # Count cells with multiple defenders
        for cell, count in all_coverage.items():
            if count >= 2:
                overlaps += count - 1
        
        return overlaps
    
    def _measure_coordination_improvement(self, board: chess.Board, friendly_agents: Dict[str, PieceAgent]) -> float:
        """Measure improvement in piece coordination."""
        coordination = 0.0
        new_agents = self.analyze_piece_agents(board)
        
        # Check for mutual support patterns
        for agent_key, new_agent in new_agents.items():
            mutual_support = 0
            for other_key, other_agent in new_agents.items():
                if agent_key != other_key:
                    if new_agent.square in other_agent.support_cells and other_agent.square in new_agent.support_cells:
                        mutual_support += 1
            coordination += mutual_support * 0.3
        
        return coordination
    
    def _calculate_protection_value(self, board: chess.Board, friendly_agents: Dict[str, PieceAgent]) -> float:
        """Calculate value of protecting vulnerable pieces."""
        protection_value = 0.0
        new_agents = self.analyze_piece_agents(board)
        
        for agent_key, new_agent in new_agents.items():
            if agent_key in friendly_agents:
                old_vulnerability = friendly_agents[agent_key].vulnerability_score
                new_vulnerability = new_agent.vulnerability_score
                
                if new_vulnerability < old_vulnerability:
                    protection_value += (old_vulnerability - new_vulnerability) * 2.0
        
        return protection_value
    
    # Piece agent pattern methods
    def _pawn_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Pawn coverage pattern."""
        coverage = set()
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        piece = board.piece_at(square)
        
        if piece:  # White or black pawn
            if piece.color == chess.WHITE and rank < 7:
                if file > 0:
                    coverage.add(chess.square(file - 1, rank + 1))
                if file < 7:
                    coverage.add(chess.square(file + 1, rank + 1))
            elif piece.color == chess.BLACK and rank > 0:
                if file > 0:
                    coverage.add(chess.square(file - 1, rank - 1))
                if file < 7:
                    coverage.add(chess.square(file + 1, rank - 1))
        
        return coverage
    
    def _knight_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Knight coverage pattern."""
        return set(board.attacks(square))
    
    def _bishop_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Bishop coverage pattern."""
        return set(board.attacks(square))
    
    def _rook_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Rook coverage pattern."""
        return set(board.attacks(square))
    
    def _queen_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Queen coverage pattern."""
        bishop = self._bishop_agent_pattern(board, square)
        rook = self._rook_agent_pattern(board, square)
        return bishop.union(rook)
    
    def _king_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """King coverage pattern."""
        return set(board.attacks(square))
    
    def _initialize_strategic_values(self) -> Dict[int, float]:
        """Initialize strategic values for each square."""
        values = {}
        
        for square in chess.SQUARES:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            
            # Center squares are most valuable
            if 3 <= file <= 4 and 3 <= rank <= 4:
                values[square] = 3.0
            # Extended center
            elif 2 <= file <= 5 and 2 <= rank <= 5:
                values[square] = 2.0
            # Key flank squares
            elif (file in [2, 5] and 2 <= rank <= 5) or (rank in [2, 5] and 2 <= file <= 5):
                values[square] = 1.5
            # Perimeter
            else:
                values[square] = 0.5
        
        return values
    
    def select_optimal_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Select optimal move based on heatmap manipulation principles.
        
        Balances enemy weakening with safety enhancement.
        """
        weakening_moves = self.find_enemy_heatmap_weakening_moves(board)
        safety_moves = self.find_safety_enhancement_moves(board)
        
        # Combine and score based on current position needs
        all_moves = []
        
        # Add weakening moves
        for move, score in weakening_moves:
            all_moves.append((move, score * 1.2, 'weakening'))  # Slight priority to weakening
        
        # Add safety moves
        for move, score in safety_moves:
            all_moves.append((move, score, 'safety'))
        
        if not all_moves:
            return None
        
        # Select best move
        best_move_tuple = max(all_moves, key=lambda x: x[1])
        best_move = best_move_tuple[0]
        move_type = best_move_tuple[2]
        best_score = best_move_tuple[1]
        
        logger.info(f"HeatmapManipulator selected {best_move} ({move_type}) with score {best_score:.2f}")
        return best_move


class PieceMateBot:
    """Bot that prioritises trapping ("mating") a chosen enemy piece.

    A non-king piece is considered "mated" if its current square is attacked
    and it has no safe legal move (including captures) that lands on a square
    not attacked by our side. This uses :func:`is_piece_mated` semantics.

    Strategy:
    - Focus a target class of enemy pieces (e.g. all knights) or auto-pick
      the thinnest enemy pieces from :class:`ThreatMap`.
    - Score moves by how much they increase the count of mated target pieces
      and reduce those targets' safe escape moves.
    - Use a small positional tiebreak and SEE to avoid outright blunders.
    """

    def __init__(
        self,
        color: bool,
        *,
        target_piece_type: Optional[int] = None,
        max_targets: int = 3,
        safe_only: bool = False,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.color = color
        self.target_piece_type = target_piece_type
        self.max_targets = max(1, int(max_targets))
        self.safe_only = safe_only
        self.W: Dict[str, float] = {
            # Primary objectives
            "mate": 800.0,            # increase in mated target pieces
            "reduce_escape": 15.0,    # reduction of total escape moves across targets
            # Pressure heuristics
            "pressure": 2.5,          # increase in (our_attackers - their_defenders) on targets
            # Tactical prudence / tie-breakers
            "see": 1.0,               # static exchange eval for captures
            "check": 20.0,            # giving check often reduces enemy freedom globally
            "pos": 0.1,               # light positional nudge
        }
        if weights:
            self.W.update(weights)

        self._shared_evaluator: Optional[Evaluator] = None
        self._heatmap_analyzer: Optional[HeatmapAnalyzer] = None
        if HEATMAP_AVAILABLE:
            try:
                self._heatmap_analyzer = HeatmapAnalyzer()
            except Exception:
                self._heatmap_analyzer = None

    # ------------------ Public API ------------------
    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
        heatmap_widget=None,
    ) -> Tuple[Optional[chess.Move], float]:
        if board.turn != self.color:
            return None, 0.0

        evalr = evaluator or self._shared_evaluator or Evaluator(board)
        if self._shared_evaluator is None:
            self._shared_evaluator = evalr

        enemy = not self.color
        target_squares = self._select_targets(board, enemy)
        if not target_squares:
            # Fall back to general positional choice if nothing to trap
            return self._fallback_choice(board, evalr)

        baseline = self._targets_stats(board, target_squares)

        best_move: Optional[chess.Move] = None
        best_score: float = float("-inf")
        best_info: Dict[str, float] = {}

        for mv in board.legal_moves:
            tmp = board.copy(stack=False)
            tmp.push(mv)

            # Safety gate when requested: skip moves that obviously worsen
            # SEE on their destination or step into heavy fire.
            if self.safe_only and self._is_obviously_unsafe(board, mv):
                continue

            # Re-evaluate targets on the new position (capture may remove some)
            new_targets = [
                sq for sq in target_squares
                if (pc := tmp.piece_at(sq)) is not None and pc.color == enemy
            ]
            stats_after = self._targets_stats(tmp, new_targets)

            mate_delta = stats_after["mated_count"] - baseline["mated_count"]
            escape_delta = baseline["total_escapes"] - stats_after["total_escapes"]
            pressure_delta = stats_after["pressure"] - baseline["pressure"]
            heatmap_delta = stats_after.get("heatmap_bonus", 0.0) - baseline.get("heatmap_bonus", 0.0)

            score = (
                self.W["mate"] * mate_delta
                + self.W["reduce_escape"] * max(0, escape_delta)
                + self.W["pressure"] * max(0, pressure_delta)
                + self.W.get("heatmap", 1.0) * max(0, heatmap_delta)
            )

            if board.is_capture(mv):
                see_gain = static_exchange_eval(board, mv)
                score += self.W["see"] * see_gain
            else:
                see_gain = 0.0

            if tmp.is_check():
                score += self.W["check"]

            # Light positional tiebreak
            score += self.W["pos"] * evalr.position_score(tmp, self.color)

            if score > best_score or (
                score == best_score and mv.uci() < (best_move.uci() if best_move else "zzzz")
            ):
                best_move = mv
                best_score = float(score)
                best_info = {
                    "mateΔ": float(mate_delta),
                    "escΔ": float(escape_delta),
                    "pressΔ": float(pressure_delta),
                    "see": float(see_gain),
                    "heatΔ": float(heatmap_delta),
                }

        if debug and best_move is not None:
            # Detailed move analysis output
            move_uci = best_move.uci()
            analysis_parts = []
            
            # Mate analysis
            if mate_delta > 0:
                analysis_parts.append(f"заматував {int(mate_delta)} фігур(и)")
            elif mate_delta < 0:
                analysis_parts.append(f"втратив заматованих фігур: {abs(int(mate_delta))}")
            
            # Escape analysis  
            if escape_delta > 0:
                analysis_parts.append(f"зменшив втечі на {int(escape_delta)}")
            elif escape_delta < 0:
                analysis_parts.append(f"збільшив втечі на {abs(int(escape_delta))}")
            
            # Pressure analysis
            if pressure_delta > 0:
                analysis_parts.append(f"збільшив тиск на {pressure_delta:.1f}")
            elif pressure_delta < 0:
                analysis_parts.append(f"зменшив тиск на {abs(pressure_delta):.1f}")
            
            # SEE analysis
            if see_gain != 0:
                analysis_parts.append(f"SEE: {see_gain:+.1f}")
            
            # Heatmap analysis
            heatmap_delta = stats_after.get("heatmap_bonus", 0.0) - baseline.get("heatmap_bonus", 0.0)
            if heatmap_delta > 0:
                analysis_parts.append(f"зональний бонус: {heatmap_delta:.2f}")
            
            # Build comprehensive message
            if analysis_parts:
                result_text = ", ".join(analysis_parts)
                logger.debug("PieceMateBot: хід %s, дельта [mateΔ:%.1f, escΔ:%.1f, pressΔ:%.1f, see:%.1f, heatΔ:%.2f] - %s", 
                            move_uci, mate_delta, escape_delta, pressure_delta, see_gain, heatmap_delta, result_text)
                print(f"PieceMateBot: хід {move_uci}, дельта [{mate_delta:.1f}, {escape_delta:.1f}, {pressure_delta:.1f}, {see_gain:.1f}, {heatmap_delta:.2f}] - {result_text}")
            else:
                logger.debug("PieceMateBot: хід %s, дельта [mateΔ:%.1f, escΔ:%.1f, pressΔ:%.1f, see:%.1f, heatΔ:%.2f] - позиційний хід", 
                            move_uci, mate_delta, escape_delta, pressure_delta, see_gain, heatmap_delta)
                print(f"PieceMateBot: хід {move_uci}, дельта [{mate_delta:.1f}, {escape_delta:.1f}, {pressure_delta:.1f}, {see_gain:.1f}, {heatmap_delta:.2f}] - позиційний хід")

        return best_move, float(best_score if best_move is not None else 0.0)

    # ------------------ Internals ------------------
    def _fallback_choice(self, board: chess.Board, evaluator: Evaluator) -> Tuple[Optional[chess.Move], float]:
        best: Optional[chess.Move] = None
        best_score = float("-inf")
        for mv in board.legal_moves:
            tmp = board.copy(stack=False)
            tmp.push(mv)
            s = evaluator.position_score(tmp, self.color)
            if tmp.is_check():
                s += 25.0
            if board.is_capture(mv):
                s += 0.5 * static_exchange_eval(board, mv)
            if s > best_score or (s == best_score and (best is None or mv.uci() < best.uci())):
                best, best_score = mv, float(s)
        return best, float(best_score if best is not None else 0.0)

    def _select_targets(self, board: chess.Board, enemy: bool) -> List[int]:
        # If explicit type requested, gather all enemy squares of that type
        if self.target_piece_type is not None:
            return [
                sq for sq, pc in board.piece_map().items()
                if pc.color == enemy and pc.piece_type == self.target_piece_type
            ]

        # Otherwise pick up to N thinnest enemy pieces (def - att <= 0 first)
        try:
            thin = ThreatMap(enemy).summary(board)["thin_pieces"]
            squares = [sq for (sq, _d, _a) in thin[: self.max_targets]]
            if squares:
                return squares
        except Exception:
            pass

        # Fallback: any enemy pieces, prefer non-pawns and not the king
        candidates: List[Tuple[int, int]] = []
        for sq, pc in board.piece_map().items():
            if pc.color != enemy:
                continue
            # Skip king only if other pieces available
            if pc.piece_type == chess.KING and len([s for s, p in board.piece_map().items() if p.color == enemy and p.piece_type != chess.KING]) > 0:
                continue
            # Prefer more valuable targets
            val = {
                chess.QUEEN: 9,
                chess.ROOK: 5,
                chess.BISHOP: 3,
                chess.KNIGHT: 3,
                chess.PAWN: 1,
                chess.KING: 2,  # Low value but included as last resort
            }.get(pc.piece_type, 0)
            candidates.append((val, sq))
        candidates.sort(reverse=True)
        
        # Ensure we always have at least one target if enemy has pieces
        if not candidates and any(pc.color == enemy for pc in board.piece_map().values()):
            # Last resort: target any enemy piece including king
            for sq, pc in board.piece_map().items():
                if pc.color == enemy:
                    candidates.append((1, sq))
                    break
        
        return [sq for _v, sq in candidates[: self.max_targets]]

    def _is_obviously_unsafe(self, board: chess.Board, move: chess.Move) -> bool:
        if not board.is_capture(move):
            # moving onto a square heavily attacked without defenders is risky
            tmp = board.copy(stack=False)
            tmp.push(move)
            attackers = len(tmp.attackers(not self.color, move.to_square))
            defenders = len(tmp.attackers(self.color, move.to_square))
            return attackers > defenders + 1
        # For captures, rely on SEE
        return static_exchange_eval(board, move) < 0

    def _targets_stats(self, board: chess.Board, target_squares: Sequence[int]) -> Dict[str, float]:
        # Count how many targets are already mated and sum their safe escapes
        mated_count = 0
        total_escapes = 0
        enemy = not self.color
        for sq in target_squares:
            pc = board.piece_at(sq)
            if pc is None or pc.color != enemy:
                continue
            if is_piece_mated(board, sq):
                mated_count += 1
            else:
                total_escapes += len(escape_squares(board, sq))

        # Aggregate pressure (our attackers - their defenders) on targets
        counts = attack_count_per_square(board)
        pressure = 0
        heatmap_bonus = 0.0
        
        for sq in target_squares:
            pc = board.piece_at(sq)
            if pc is None or pc.color != enemy:
                continue
            our = counts[self.color][sq]
            theirs = counts[enemy][sq]
            pressure += max(0, our - theirs)
            
            # Add heatmap-based zone analysis if available
            if self._heatmap_analyzer is not None:
                try:
                    # Convert square to row,col for heatmap analysis
                    row = 7 - (sq // 8)  # Flip row for chess coordinate system
                    col = sq % 8
                    
                    # Check if this square is in a high-activity zone
                    heatmap_data = self._heatmap_analyzer.load_heatmap_data('PieceMateBot')
                    if heatmap_data and 'intensity_map' in heatmap_data:
                        intensity_map = np.array(heatmap_data['intensity_map'])
                        if 0 <= row < 8 and 0 <= col < 8:
                            zone_intensity = intensity_map[row][col]
                            heatmap_bonus += zone_intensity * 0.5  # Weight for zone importance
                except Exception:
                    pass  # Silently fail if heatmap analysis fails

        return {
            "mated_count": float(mated_count),
            "total_escapes": float(total_escapes),
            "pressure": float(pressure),
            "heatmap_bonus": float(heatmap_bonus),
        }


    # Helper methods for HeatmapManipulator
    def _get_coverage_cells(self, board: chess.Board, square: int, piece_symbol: str) -> Set[int]:
        """Get cells that this piece controls/attacks."""
        piece_type = piece_symbol.upper()
        if piece_type in self.agent_patterns:
            return self.agent_patterns[piece_type](board, square)
        return set()
    
    def _get_support_cells(self, board: chess.Board, square: int) -> Set[int]:
        """Get cells that support/defend this piece."""
        support_cells = set()
        color = board.piece_at(square).color if board.piece_at(square) else self.color
        
        for attacker_square in chess.SQUARES:
            if board.piece_at(attacker_square) and board.piece_at(attacker_square).color == color:
                if square in board.attacks(attacker_square):
                    support_cells.add(attacker_square)
        
        return support_cells
    
    def _get_influence_radius(self, piece_symbol: str) -> int:
        """Get how far this piece projects power."""
        influence_radii = {
            'P': 2,  # Pawns control immediate diagonals
            'N': 3,  # Knights have L-shaped reach
            'B': 7,  # Bishops control entire diagonals
            'R': 7,  # Rooks control entire files/ranks
            'Q': 7,  # Queens control multiple directions
            'K': 1   # Kings control adjacent squares
        }
        return influence_radii.get(piece_symbol.upper(), 1)
    
    def _calculate_vulnerability(self, board: chess.Board, square: int, piece_symbol: str) -> float:
        """Calculate how exposed this piece is."""
        enemy_attackers = len(board.attackers(self.enemy_color, square))
        friendly_defenders = len(board.attackers(self.color, square))
        
        # Base vulnerability
        vulnerability = max(0, enemy_attackers - friendly_defenders)
        
        # Piece value modifier
        piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
        piece_value = piece_values.get(piece_symbol.upper(), 1)
        
        return vulnerability * (piece_value / 3.0)  # Normalize by knight value
    
    def _analyze_enemy_agents(self, board: chess.Board) -> Dict[str, PieceAgent]:
        """Analyze enemy pieces as agents."""
        # Temporarily switch color to analyze enemy
        original_color = self.color
        self.color = self.enemy_color
        self.enemy_color = original_color
        
        enemy_agents = self.analyze_piece_agents(board)
        
        # Switch back
        self.color = original_color
        self.enemy_color = not original_color
        
        return enemy_agents
    
    def _find_attacked_enemy_supports(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> int:
        """Count how many enemy support cells are now under attack."""
        attacked_supports = 0
        
        for agent in enemy_agents.values():
            for support_cell in agent.support_cells:
                if len(board.attackers(self.color, support_cell)) > 0:
                    attacked_supports += 1
        
        return attacked_supports
    
    def _count_created_threats(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> int:
        """Count how many new threats are created against enemy pieces."""
        threats = 0
        
        for agent in enemy_agents.values():
            if len(board.attackers(self.color, agent.square)) > 0:
                threats += 1
        
        return threats
    
    def _measure_coordination_disruption(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> float:
        """Measure how much enemy coordination is disrupted."""
        disruption = 0.0
        
        # Check if key coordination cells are attacked
        coordination_cells = set()
        for agent in enemy_agents.values():
            coordination_cells.update(agent.support_cells)
            coordination_cells.update(agent.coverage_cells)
        
        for cell in coordination_cells:
            if len(board.attackers(self.color, cell)) > 0:
                disruption += 0.5
        
        return disruption
    
    def _measure_forced_vulnerability(self, board: chess.Board, enemy_agents: Dict[str, PieceAgent]) -> float:
        """Measure if enemy pieces are forced into vulnerable positions."""
        forced_vulnerability = 0.0
        
        # Check if enemy pieces have limited escape squares
        for agent in enemy_agents.values():
            escape_squares = 0
            for move in board.legal_moves:
                if board.piece_at(move.from_square) and board.piece_at(move.from_square).color == self.enemy_color:
                    escape_squares += 1
            
            if escape_squares <= 2:  # Very limited mobility
                forced_vulnerability += 1.0
        
        return forced_vulnerability
    
    def _calculate_support_improvement(self, board: chess.Board, friendly_agents: Dict[str, PieceAgent], move: chess.Move) -> float:
        """Calculate how much the support network improves."""
        improvement = 0.0
        
        # Get new agents after move
        new_agents = self.analyze_piece_agents(board)
        
        # Compare support networks
        for agent_key, new_agent in new_agents.items():
            if agent_key in friendly_agents:
                old_support_count = len(friendly_agents[agent_key].support_cells)
                new_support_count = len(new_agent.support_cells)
                improvement += max(0, new_support_count - old_support_count) * 0.5
        
        return improvement
    
    def _count_defensive_overlaps(self, board: chess.Board) -> int:
        """Count defensive coverage overlaps for better safety."""
        overlaps = 0
        all_coverage = defaultdict(int)
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == self.color:
                coverage = self._get_coverage_cells(board, square, piece.symbol())
                for cell in coverage:
                    all_coverage[cell] += 1
        
        # Count cells with multiple defenders
        for cell, count in all_coverage.items():
            if count >= 2:
                overlaps += count - 1
        
        return overlaps
    
    def _measure_coordination_improvement(self, board: chess.Board, friendly_agents: Dict[str, PieceAgent]) -> float:
        """Measure improvement in piece coordination."""
        coordination = 0.0
        new_agents = self.analyze_piece_agents(board)
        
        # Check for mutual support patterns
        for agent_key, new_agent in new_agents.items():
            mutual_support = 0
            for other_key, other_agent in new_agents.items():
                if agent_key != other_key:
                    if new_agent.square in other_agent.support_cells and other_agent.square in new_agent.support_cells:
                        mutual_support += 1
            coordination += mutual_support * 0.3
        
        return coordination
    
    def _calculate_protection_value(self, board: chess.Board, friendly_agents: Dict[str, PieceAgent]) -> float:
        """Calculate value of protecting vulnerable pieces."""
        protection_value = 0.0
        new_agents = self.analyze_piece_agents(board)
        
        for agent_key, new_agent in new_agents.items():
            if agent_key in friendly_agents:
                old_vulnerability = friendly_agents[agent_key].vulnerability_score
                new_vulnerability = new_agent.vulnerability_score
                
                if new_vulnerability < old_vulnerability:
                    protection_value += (old_vulnerability - new_vulnerability) * 2.0
        
        return protection_value
    
    # Piece agent pattern methods
    def _pawn_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Pawn coverage pattern."""
        coverage = set()
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        piece = board.piece_at(square)
        
        if piece:  # White or black pawn
            if piece.color == chess.WHITE and rank < 7:
                if file > 0:
                    coverage.add(chess.square(file - 1, rank + 1))
                if file < 7:
                    coverage.add(chess.square(file + 1, rank + 1))
            elif piece.color == chess.BLACK and rank > 0:
                if file > 0:
                    coverage.add(chess.square(file - 1, rank - 1))
                if file < 7:
                    coverage.add(chess.square(file + 1, rank - 1))
        
        return coverage
    
    def _knight_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Knight coverage pattern."""
        return set(board.attacks(square))
    
    def _bishop_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Bishop coverage pattern."""
        return set(board.attacks(square))
    
    def _rook_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Rook coverage pattern."""
        return set(board.attacks(square))
    
    def _queen_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """Queen coverage pattern."""
        bishop = self._bishop_agent_pattern(board, square)
        rook = self._rook_agent_pattern(board, square)
        return bishop.union(rook)
    
    def _king_agent_pattern(self, board: chess.Board, square: int) -> Set[int]:
        """King coverage pattern."""
        return set(board.attacks(square))
    
    def _initialize_strategic_values(self) -> Dict[int, float]:
        """Initialize strategic values for each square."""
        values = {}
        
        for square in chess.SQUARES:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            
            # Center squares are most valuable
            if 3 <= file <= 4 and 3 <= rank <= 4:
                values[square] = 3.0
            # Extended center
            elif 2 <= file <= 5 and 2 <= rank <= 5:
                values[square] = 2.0
            # Key flank squares
            elif (file in [2, 5] and 2 <= rank <= 5) or (rank in [2, 5] and 2 <= file <= 5):
                values[square] = 1.5
            # Perimeter
            else:
                values[square] = 0.5
        
        return values
    
    def get_heatmap_analysis(self, board: chess.Board) -> Dict[str, Any]:
        """Get comprehensive heatmap manipulation analysis."""
        friendly_agents = self.analyze_piece_agents(board)
        enemy_agents = self._analyze_enemy_agents(board)
        
        weakening_moves = self.find_enemy_heatmap_weakening_moves(board)
        safety_moves = self.find_safety_enhancement_moves(board)
        
        return {
            'friendly_agents': len(friendly_agents),
            'enemy_agents': len(enemy_agents),
            'weakening_opportunities': len(weakening_moves),
            'safety_opportunities': len(safety_moves),
            'top_weakening_moves': [(str(move), score) for move, score in weakening_moves[:3]],
            'top_safety_moves': [(str(move), score) for move, score in safety_moves[:3]],
            'avg_friendly_vulnerability': np.mean([agent.vulnerability_score for agent in friendly_agents.values()]) if friendly_agents else 0,
            'avg_enemy_vulnerability': np.mean([agent.vulnerability_score for agent in enemy_agents.values()]) if enemy_agents else 0
        }


def create_heatmap_manipulator(color: bool = chess.WHITE) -> HeatmapManipulator:
    """Factory function to create HeatmapManipulator."""
    return HeatmapManipulator(color)


__all__ = ["PieceMateBot", "HeatmapManipulator"]


if __name__ == "__main__":
    # Test the heatmap manipulator
    print("=== Testing Heatmap Manipulator ===")
    
    manipulator = HeatmapManipulator(chess.WHITE)
    board = chess.Board()
    
    print("\nInitial board analysis:")
    analysis = manipulator.get_heatmap_analysis(board)
    
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    # Test move selection
    print("\nTesting move selection:")
    move = manipulator.select_optimal_move(board)
    print(f"Selected optimal move: {move}")
    
    # Test weakening moves
    print("\nTesting enemy weakening moves:")
    weakening_moves = manipulator.find_enemy_heatmap_weakening_moves(board)
    for i, (move, score) in enumerate(weakening_moves[:3]):
        print(f"{i+1}. {move}: {score:.2f}")
    
    # Test safety enhancement moves
    print("\nTesting safety enhancement moves:")
    safety_moves = manipulator.find_safety_enhancement_moves(board)
    for i, (move, score) in enumerate(safety_moves[:3]):
        print(f"{i+1}. {move}: {score:.2f}")
    
    print("\n=== Heatmap Manipulator Test Complete ===")
