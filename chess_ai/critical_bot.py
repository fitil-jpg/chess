from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import chess
from typing import Dict, Any, Optional, Tuple

from core.evaluator import Evaluator
from utils import GameContext
try:
    # Optional: reuse existing depth-2 forcing threat logic
    from .bot_agent import ThreatScout  # type: ignore
except Exception:  # pragma: no cover - available in most environments
    ThreatScout = None  # type: ignore

from .aggressive_bot import AggressiveBot
from .pawn_bot import PawnBot
from .king_value_bot import KingValueBot


class CriticalBot:
    """Agent that targets high-threat opponent pieces with hierarchical delegation.

    The bot uses :class:`Evaluator.criticality` to identify the most critical
    opponent pieces and prefers moves that capture them. When no critical targets
    are found, it delegates to specialized sub-bots:
    - AggressiveBot: for material gain opportunities
    - PawnBot: for pawn structure optimization  
    - KingValueBot: for king safety and pressure
    """

    def __init__(self, color: bool, capture_bonus: float = 100.0, 
                 enable_hierarchy: bool = True) -> None:
        self.color = color
        self.capture_bonus = capture_bonus
        self.enable_hierarchy = enable_hierarchy
        
        # Initialize sub-bots for hierarchical delegation
        if self.enable_hierarchy:
            self.sub_bots = {
                'aggressive': AggressiveBot(color),
                'pawn': PawnBot(color),
                'king': KingValueBot(color)
            }
        else:
            self.sub_bots = {}

    def choose_move(
        self,
        board: chess.Board,
        context=None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        evaluator = evaluator or Evaluator(board)

        # 1) Immediate mate-in-1
        for mv in board.legal_moves:
            piece = board.piece_at(mv.from_square)
            if not piece or piece.color != self.color:
                continue
            tmp = board.copy(stack=False); tmp.push(mv)
            if tmp.is_checkmate():
                if debug:
                    logger.debug("CriticalBot: mate-in-1 via %s", board.san(mv))
                return mv, 10000.0

        # 2) Depth-2 forcing threats (checks, forks, hanging captures), maximin
        if ThreatScout is not None and board.turn == self.color:
            try:
                scout = ThreatScout(self.color)
                m1, info = scout.probe_depth2(board)
                if m1 is not None:
                    score = float(info.get("min_score_after_reply", 0)) + 500.0
                    if debug:
                        logger.debug(
                            "CriticalBot: forcing threat %s | info=%s | score=%.1f",
                            board.san(m1), info, score,
                        )
                    return m1, score
            except Exception as ex:  # pragma: no cover - defensive
                if debug:
                    logger.debug("CriticalBot: ThreatScout failed: %s", ex)

        # 3) Fallback: target critical enemy pieces, plus forks/hanging
        critical = evaluator.criticality(board, self.color)
        critical_squares = {sq for sq, _ in (critical or [])}

        best_move = None
        best_score = float("-inf")
        enemy = not self.color

        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.color != self.color:
                continue

            # Avoid obviously losing destinations
            tmp = board.copy(stack=False); tmp.push(move)
            to_sq = move.to_square
            attackers = len(tmp.attackers(enemy, to_sq))
            defenders = len(tmp.attackers(self.color, to_sq))
            if attackers > defenders:
                continue

            score = 0.0

            # Prefer capturing a critical piece
            if move.to_square in critical_squares and board.piece_at(move.to_square):
                score += self.capture_bonus

            # Capture undefended (hanging) targets
            if board.is_capture(move):
                before_piece = board.piece_at(move.to_square)
                if before_piece and before_piece.color == enemy:
                    defn = len(board.attackers(enemy, move.to_square))
                    if defn == 0:
                        score += self.capture_bonus * 0.8 + 50.0
                    else:
                        score += 20.0

            # Check bonus
            if tmp.is_check():
                score += 35.0

            # Knight fork heuristic: landing knight attacks >=2 valuable targets
            if piece.piece_type == chess.KNIGHT:
                valuable = {chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT}
                val_targets = 0
                for t in tmp.attacks(to_sq):
                    q = tmp.piece_at(t)
                    if q and q.color == enemy and q.piece_type in valuable:
                        val_targets += 1
                if val_targets >= 2:
                    score += 70.0

            if score > best_score:
                best_score = score
                best_move = move

        if best_move is not None and best_score > 0.0:
            if debug:
                logger.debug(
                    "CriticalBot: fallback selects %s with score %.1f",
                    board.san(best_move), best_score,
                )
            return best_move, best_score

        # 4) Hierarchical delegation to sub-bots when no critical targets found
        if self.enable_hierarchy and self.sub_bots:
            return self._delegate_to_sub_bots(board, context, evaluator, debug)

        return None, 0.0
    
    def _delegate_to_sub_bots(self, board: chess.Board, context: GameContext | None, 
                              evaluator: Evaluator, debug: bool = False) -> Tuple[Optional[chess.Move], float]:
        """Delegate move selection to specialized sub-bots."""
        
        # Strategy: Try sub-bots in priority order based on position characteristics
        sub_bot_priority = self._determine_sub_bot_priority(board, evaluator)
        
        best_move = None
        best_score = 0.0
        best_source = ""
        
        for bot_name in sub_bot_priority:
            if bot_name not in self.sub_bots:
                continue
                
            sub_bot = self.sub_bots[bot_name]
            
            try:
                move, confidence = sub_bot.choose_move(board, context, evaluator, debug)
                if move is not None and confidence > best_score:
                    best_move = move
                    best_score = confidence
                    best_source = bot_name
                    
                    if debug:
                        logger.debug(
                            "CriticalBot: sub-bot %s suggests %s with confidence %.1f",
                            bot_name, board.san(move), confidence
                        )
                        
            except Exception as ex:
                if debug:
                    logger.debug(f"CriticalBot: sub-bot {bot_name} failed: {ex}")
                continue
        
        if best_move is not None:
            if debug:
                logger.debug(
                    "CriticalBot: delegated to %s selecting %s with score %.1f",
                    best_source, board.san(best_move), best_score
                )
            return best_move, best_score
        
        return None, 0.0
    
    def _determine_sub_bot_priority(self, board: chess.Board, evaluator: Evaluator) -> list:
        """Determine priority order for sub-bots based on position characteristics."""
        
        # Analyze position to decide which sub-bot to prioritize
        material_diff = evaluator.material_diff(self.color)
        phase = self._detect_game_phase(board)
        has_tactics = self._has_tactical_opportunities(board, evaluator)
        
        priority = []
        
        # Early game: prioritize pawn structure
        if phase == "opening":
            priority.extend(["pawn", "aggressive", "king"])
        # Middlegame with tactics: prioritize aggressive play
        elif phase == "middlegame" and has_tactics:
            priority.extend(["aggressive", "pawn", "king"])
        # Middlegame without tactics: focus on pawn structure and king safety
        elif phase == "middlegame":
            priority.extend(["pawn", "king", "aggressive"])
        # Endgame: prioritize king activity and aggression
        elif phase == "endgame":
            priority.extend(["king", "aggressive", "pawn"])
        
        # Material advantage: be more aggressive
        if material_diff > 200:
            if "aggressive" not in priority[:2]:
                priority.insert(0, "aggressive")
        # Material disadvantage: focus on pawn structure
        elif material_diff < -200:
            if "pawn" not in priority[:2]:
                priority.insert(0, "pawn")
        
        return priority
    
    def _detect_game_phase(self, board: chess.Board) -> str:
        """Simple game phase detection based on move count and material."""
        move_count = board.ply() // 2
        
        if move_count <= 15:
            return "opening"
        elif move_count <= 40:
            return "middlegame"
        else:
            return "endgame"
    
    def _has_tactical_opportunities(self, board: chess.Board, evaluator: Evaluator) -> bool:
        """Check if position has tactical opportunities."""
        
        # Check for captures, checks, or threats
        for move in board.legal_moves:
            if board.is_capture(move):
                return True
            tmp = board.copy(stack=False)
            tmp.push(move)
            if tmp.is_check():
                return True
        
        # Use evaluator to check for hanging pieces
        features = evaluator.compute_features(self.color)
        if features.get("has_hanging_enemy", False) or features.get("valuable_capture", False):
            return True
            
        return False