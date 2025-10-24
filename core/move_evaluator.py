"""
Enhanced Move Evaluator with WFC/BSP Integration.

This module provides a comprehensive move evaluation system that integrates
Wave Function Collapse (WFC) and Binary Space Partitioning (BSP) engines
with traditional chess AI evaluation methods.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
import chess
from chess import Board, Move

from core.move_object import (
    MoveEvaluation, MovePhase, MoveStatus, EvaluationStep,
    move_evaluation_manager
)
from core.pattern_loader import PatternResponder, PatternType
from chess_ai.wfc_engine import WFCEngine, create_chess_wfc_engine
from chess_ai.bsp_engine import BSPEngine, create_chess_bsp_engine
from chess_ai.guardrails import Guardrails

logger = logging.getLogger(__name__)


class EnhancedMoveEvaluator:
    """
    Enhanced move evaluator that integrates multiple evaluation methods:
    - Pattern matching (including COW openings and tactical patterns)
    - WFC (Wave Function Collapse) analysis
    - BSP (Binary Space Partitioning) spatial analysis
    - Traditional bot evaluation
    - Guardrails safety checks
    """
    
    def __init__(self, move_time_ms: int = 700):
        self.move_time_ms = move_time_ms
        self.pattern_responder = PatternResponder()
        self.wfc_engine = create_chess_wfc_engine()
        self.bsp_engine = create_chess_bsp_engine()
        self.guardrails = Guardrails(blunder_depth=2, high_value_threshold=500)
        
        # Evaluation weights
        self.weights = {
            'pattern_match': 0.3,
            'wfc_analysis': 0.2,
            'bsp_analysis': 0.2,
            'bot_evaluation': 0.2,
            'guardrails': 0.1
        }
        
        # Performance tracking
        self.evaluation_stats = {
            'total_evaluations': 0,
            'avg_duration_ms': 0.0,
            'method_usage': {},
            'success_rate': 0.0
        }
    
    def evaluate_move(self, board: Board, move: Move, bot_name: str = "EnhancedEvaluator") -> MoveEvaluation:
        """
        Comprehensive move evaluation using all available methods.
        
        Args:
            board: Current chess board position
            move: Move to evaluate
            bot_name: Name of the bot requesting evaluation
            
        Returns:
            MoveEvaluation object with complete analysis
        """
        # Create move evaluation object
        move_eval = move_evaluation_manager.create_move_evaluation(move, board)
        move_eval.start_phase(MovePhase.INITIALIZATION)
        
        try:
            # Phase 1: Pattern Matching
            self._evaluate_patterns(board, move, move_eval)
            
            # Phase 2: WFC Analysis
            self._evaluate_wfc(board, move, move_eval)
            
            # Phase 3: BSP Analysis
            self._evaluate_bsp(board, move, move_eval)
            
            # Phase 4: Bot Evaluation (placeholder for integration with existing bots)
            self._evaluate_with_bot(board, move, move_eval, bot_name)
            
            # Phase 5: Guardrails Check
            self._evaluate_guardrails(board, move, move_eval)
            
            # Phase 6: Final Scoring
            self._calculate_final_score(move_eval)
            
            # Update visualization state
            self._update_visualization_state(board, move, move_eval)
            
            move_eval.status = MoveStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Error evaluating move {move}: {e}")
            move_eval.set_error(str(e))
        
        finally:
            move_eval.end_phase(move_eval.phase)
            move_evaluation_manager.finalize_current_move()
            self._update_stats(move_eval)
        
        return move_eval
    
    def _evaluate_patterns(self, board: Board, move: Move, move_eval: MoveEvaluation) -> None:
        """Evaluate move using pattern matching."""
        move_eval.start_phase(MovePhase.PATTERN_MATCHING)
        start_time = time.time()
        
        try:
            # Create a temporary board to test the move
            temp_board = board.copy()
            temp_board.push(move)
            
            # Try to match patterns
            pattern_action = self.pattern_responder.match(temp_board)
            
            step = EvaluationStep(
                method_name="pattern_matching",
                bot_name="PatternResponder",
                input_data={"board_fen": temp_board.fen()},
                status=MoveStatus.COMPLETED
            )
            
            if pattern_action:
                # Pattern matched
                step.output_data = {"matched_action": pattern_action, "match_found": True}
                step.confidence = 0.8
                step.reason = "Pattern match found"
                
                # Add pattern match to move evaluation
                move_eval.add_pattern_match(
                    pattern_type="general",
                    pattern_data={"action": pattern_action},
                    confidence=0.8
                )
                
                # Check if it's a COW opening pattern
                if "COW" in pattern_action:
                    move_eval.add_pattern_match(
                        pattern_type="cow_opening",
                        pattern_data={"action": pattern_action},
                        confidence=0.95
                    )
            else:
                step.output_data = {"match_found": False}
                step.confidence = 0.0
                step.reason = "No pattern match"
            
            step.duration_ms = (time.time() - start_time) * 1000
            move_eval.add_evaluation_step(step)
            
        except Exception as e:
            logger.error(f"Pattern evaluation error: {e}")
            step = EvaluationStep(
                method_name="pattern_matching",
                bot_name="PatternResponder",
                status=MoveStatus.ERROR,
                reason=str(e)
            )
            move_eval.add_evaluation_step(step)
        
        move_eval.end_phase(MovePhase.PATTERN_MATCHING)
    
    def _evaluate_wfc(self, board: Board, move: Move, move_eval: MoveEvaluation) -> None:
        """Evaluate move using WFC (Wave Function Collapse) analysis."""
        move_eval.start_phase(MovePhase.WFC_ANALYSIS)
        start_time = time.time()
        
        try:
            # Create a temporary board to test the move
            temp_board = board.copy()
            temp_board.push(move)
            
            # Analyze position with WFC
            # For now, we'll do a simplified analysis
            wfc_score = self._calculate_wfc_score(temp_board, move)
            
            step = EvaluationStep(
                method_name="wfc_analysis",
                bot_name="WFCEngine",
                input_data={"board_fen": temp_board.fen(), "move": move.uci()},
                output_data={"wfc_score": wfc_score},
                confidence=min(wfc_score / 100.0, 1.0),
                reason=f"WFC analysis score: {wfc_score:.2f}",
                status=MoveStatus.COMPLETED
            )
            
            step.duration_ms = (time.time() - start_time) * 1000
            move_eval.add_evaluation_step(step)
            
            # Set WFC analysis results
            move_eval.set_wfc_analysis({
                'score': wfc_score,
                'pattern_compatibility': wfc_score > 50,
                'generated_patterns': [],  # Could be populated with actual WFC results
                'constraints_satisfied': wfc_score > 30
            })
            
        except Exception as e:
            logger.error(f"WFC evaluation error: {e}")
            step = EvaluationStep(
                method_name="wfc_analysis",
                bot_name="WFCEngine",
                status=MoveStatus.ERROR,
                reason=str(e)
            )
            move_eval.add_evaluation_step(step)
        
        move_eval.end_phase(MovePhase.WFC_ANALYSIS)
    
    def _calculate_wfc_score(self, board: Board, move: Move) -> float:
        """Calculate WFC-based score for a move."""
        score = 50.0  # Base score
        
        # Analyze piece placement patterns
        piece_map = board.piece_map()
        
        # Bonus for center control
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        center_pieces = sum(1 for sq in center_squares if sq in piece_map)
        score += center_pieces * 10
        
        # Bonus for piece development
        if move.from_square in [chess.B1, chess.G1, chess.B8, chess.G8]:  # Knight development
            score += 15
        
        # Bonus for piece coordination
        moving_piece = board.piece_at(move.from_square)
        if moving_piece:
            attacks = board.attacks(move.to_square)
            friendly_pieces = sum(1 for sq in attacks 
                                if board.piece_at(sq) and board.piece_at(sq).color == moving_piece.color)
            score += friendly_pieces * 5
        
        return min(score, 100.0)
    
    def _evaluate_bsp(self, board: Board, move: Move, move_eval: MoveEvaluation) -> None:
        """Evaluate move using BSP (Binary Space Partitioning) analysis."""
        move_eval.start_phase(MovePhase.BSP_ANALYSIS)
        start_time = time.time()
        
        try:
            # Create a temporary board to test the move
            temp_board = board.copy()
            temp_board.push(move)
            
            # Analyze with BSP engine
            zone_stats = self.bsp_engine.analyze_board(temp_board)
            zone_control = self.bsp_engine.calculate_zone_control(temp_board, temp_board.turn)
            
            # Calculate BSP score
            bsp_score = self._calculate_bsp_score(zone_stats, zone_control, move)
            
            step = EvaluationStep(
                method_name="bsp_analysis",
                bot_name="BSPEngine",
                input_data={"board_fen": temp_board.fen(), "move": move.uci()},
                output_data={
                    "bsp_score": bsp_score,
                    "zone_stats": zone_stats,
                    "zone_control": zone_control
                },
                confidence=min(bsp_score / 100.0, 1.0),
                reason=f"BSP spatial analysis score: {bsp_score:.2f}",
                status=MoveStatus.COMPLETED
            )
            
            step.duration_ms = (time.time() - start_time) * 1000
            move_eval.add_evaluation_step(step)
            
            # Set BSP analysis results
            move_eval.set_bsp_analysis({
                'score': bsp_score,
                'zone_stats': zone_stats,
                'zone_control': zone_control,
                'spatial_advantage': bsp_score > 60,
                'zones_controlled': len([z for z in zone_control.values() if z > 0])
            })
            
            # Update visualization with zone information
            move_eval.update_visualization(
                zone_colors=self._get_zone_colors(zone_control),
                bsp_zones=[{
                    'type': zone_type,
                    'control': control_value,
                    'color': 'blue' if control_value > 0 else 'red'
                } for zone_type, control_value in zone_control.items()]
            )
            
        except Exception as e:
            logger.error(f"BSP evaluation error: {e}")
            step = EvaluationStep(
                method_name="bsp_analysis",
                bot_name="BSPEngine",
                status=MoveStatus.ERROR,
                reason=str(e)
            )
            move_eval.add_evaluation_step(step)
        
        move_eval.end_phase(MovePhase.BSP_ANALYSIS)
    
    def _calculate_bsp_score(self, zone_stats: Dict[str, Any], 
                           zone_control: Dict[str, float], move: Move) -> float:
        """Calculate BSP-based score for a move."""
        score = 50.0  # Base score
        
        # Bonus for center control
        center_control = zone_control.get('center', 0)
        score += center_control * 20
        
        # Bonus for balanced piece distribution
        total_zones_with_pieces = sum(1 for stats in zone_stats.values() 
                                    if stats.get('total_pieces', 0) > 0)
        if total_zones_with_pieces >= 3:
            score += 15
        
        # Penalty for over-concentration in one zone
        max_pieces_in_zone = max(stats.get('total_pieces', 0) for stats in zone_stats.values())
        if max_pieces_in_zone > 6:
            score -= 10
        
        return min(max(score, 0.0), 100.0)
    
    def _get_zone_colors(self, zone_control: Dict[str, float]) -> Dict[str, str]:
        """Get color mapping for zones based on control values."""
        colors = {}
        for zone_type, control in zone_control.items():
            if control > 2.0:
                colors[zone_type] = 'blue'  # Strong control
            elif control > 0:
                colors[zone_type] = 'lightblue'  # Weak control
            elif control < -2.0:
                colors[zone_type] = 'red'  # Opponent strong control
            elif control < 0:
                colors[zone_type] = 'lightred'  # Opponent weak control
            else:
                colors[zone_type] = 'gray'  # Neutral
        return colors
    
    def _evaluate_with_bot(self, board: Board, move: Move, move_eval: MoveEvaluation, bot_name: str) -> None:
        """Evaluate move using traditional bot evaluation (placeholder)."""
        move_eval.start_phase(MovePhase.BOT_EVALUATION)
        start_time = time.time()
        
        try:
            # This is a placeholder for integration with existing bots
            # In a real implementation, this would call the actual bot evaluation
            bot_score = self._calculate_simple_bot_score(board, move)
            
            step = EvaluationStep(
                method_name="bot_evaluation",
                bot_name=bot_name,
                input_data={"board_fen": board.fen(), "move": move.uci()},
                output_data={"bot_score": bot_score},
                confidence=0.7,
                reason=f"Bot evaluation score: {bot_score:.2f}",
                status=MoveStatus.COMPLETED
            )
            
            step.duration_ms = (time.time() - start_time) * 1000
            move_eval.add_evaluation_step(step)
            
        except Exception as e:
            logger.error(f"Bot evaluation error: {e}")
            step = EvaluationStep(
                method_name="bot_evaluation",
                bot_name=bot_name,
                status=MoveStatus.ERROR,
                reason=str(e)
            )
            move_eval.add_evaluation_step(step)
        
        move_eval.end_phase(MovePhase.BOT_EVALUATION)
    
    def _calculate_simple_bot_score(self, board: Board, move: Move) -> float:
        """Simple bot evaluation score calculation."""
        score = 50.0
        
        # Basic material evaluation
        temp_board = board.copy()
        temp_board.push(move)
        
        # Check for captures
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            if captured_piece:
                piece_values = {
                    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
                }
                score += piece_values.get(captured_piece.piece_type, 0) * 10
        
        # Check for checks
        if temp_board.is_check():
            score += 20
        
        # Check for checkmate
        if temp_board.is_checkmate():
            score += 1000
        
        return min(score, 100.0)
    
    def _evaluate_guardrails(self, board: Board, move: Move, move_eval: MoveEvaluation) -> None:
        """Evaluate move using guardrails safety checks."""
        move_eval.start_phase(MovePhase.GUARDRAILS_CHECK)
        start_time = time.time()
        
        try:
            # Check guardrails
            is_legal = self.guardrails.is_legal_and_sane(board, move)
            is_high_value_hang = self.guardrails.is_high_value_hang(board, move)
            is_blunder = self.guardrails.is_blunder(board, move)
            allow_move = self.guardrails.allow_move(board, move)
            
            violations = []
            if not is_legal:
                violations.append("Illegal or insane move")
            if is_high_value_hang:
                violations.append("High value piece hang")
            if is_blunder:
                violations.append("Tactical blunder")
            
            step = EvaluationStep(
                method_name="guardrails_check",
                bot_name="Guardrails",
                input_data={"board_fen": board.fen(), "move": move.uci()},
                output_data={
                    "is_legal": is_legal,
                    "is_high_value_hang": is_high_value_hang,
                    "is_blunder": is_blunder,
                    "allow_move": allow_move,
                    "violations": violations
                },
                confidence=1.0 if allow_move else 0.0,
                reason=f"Guardrails: {'PASS' if allow_move else 'FAIL'} - {', '.join(violations) if violations else 'All checks passed'}",
                status=MoveStatus.COMPLETED
            )
            
            step.duration_ms = (time.time() - start_time) * 1000
            move_eval.add_evaluation_step(step)
            
            # Update move evaluation with guardrails results
            if not allow_move:
                move_eval.guardrails_passed = False
                for violation in violations:
                    move_eval.add_guardrails_violation(violation)
            
        except Exception as e:
            logger.error(f"Guardrails evaluation error: {e}")
            step = EvaluationStep(
                method_name="guardrails_check",
                bot_name="Guardrails",
                status=MoveStatus.ERROR,
                reason=str(e)
            )
            move_eval.add_evaluation_step(step)
        
        move_eval.end_phase(MovePhase.GUARDRAILS_CHECK)
    
    def _calculate_final_score(self, move_eval: MoveEvaluation) -> None:
        """Calculate final weighted score for the move."""
        move_eval.start_phase(MovePhase.FINAL_SELECTION)
        
        scores = {}
        total_weight = 0.0
        
        # Collect scores from each evaluation method
        for step in move_eval.evaluation_steps:
            method = step.method_name
            if method in self.weights and step.status == MoveStatus.COMPLETED:
                if method == "pattern_matching":
                    scores[method] = 80.0 if len(move_eval.pattern_matches) > 0 else 20.0
                elif method == "wfc_analysis":
                    scores[method] = step.output_data.get("wfc_score", 50.0)
                elif method == "bsp_analysis":
                    scores[method] = step.output_data.get("bsp_score", 50.0)
                elif method == "bot_evaluation":
                    scores[method] = step.output_data.get("bot_score", 50.0)
                elif method == "guardrails_check":
                    scores[method] = 100.0 if step.output_data.get("allow_move", False) else 0.0
                
                total_weight += self.weights[method]
        
        # Calculate weighted average
        if total_weight > 0:
            weighted_score = sum(scores[method] * self.weights[method] 
                               for method in scores) / total_weight
        else:
            weighted_score = 50.0  # Default score
        
        # Apply guardrails penalty
        if not move_eval.guardrails_passed:
            weighted_score *= 0.1  # Severe penalty for guardrails violations
        
        # Determine primary reason
        primary_reason = "Unknown"
        max_contribution = 0.0
        
        for method, score in scores.items():
            contribution = score * self.weights.get(method, 0)
            if contribution > max_contribution:
                max_contribution = contribution
                primary_reason = method.replace("_", " ").title()
        
        # Finalize evaluation
        confidence = min(len(scores) / len(self.weights), 1.0)  # Based on how many methods contributed
        move_eval.finalize_evaluation(weighted_score, primary_reason, confidence)
        move_eval.contributing_factors = scores
        
        move_eval.end_phase(MovePhase.FINAL_SELECTION)
    
    def _update_visualization_state(self, board: Board, move: Move, move_eval: MoveEvaluation) -> None:
        """Update visualization state for the move."""
        move_eval.start_phase(MovePhase.VISUALIZATION)
        
        # Determine heatmap piece based on moving piece
        moving_piece = board.piece_at(move.from_square)
        if moving_piece:
            piece_names = {
                chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
                chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"
            }
            heatmap_piece = piece_names.get(moving_piece.piece_type)
            move_eval.update_visualization(heatmap_piece=heatmap_piece)
        
        # Highlight relevant squares
        highlighted_squares = {move.from_square, move.to_square}
        
        # Add squares from pattern matches
        for pattern_match in move_eval.pattern_matches:
            if "squares" in pattern_match.get("data", {}):
                highlighted_squares.update(pattern_match["data"]["squares"])
        
        move_eval.update_visualization(
            highlighted_squares=highlighted_squares,
            current_cell=move.to_square
        )
        
        move_eval.end_phase(MovePhase.VISUALIZATION)
    
    def _update_stats(self, move_eval: MoveEvaluation) -> None:
        """Update evaluation statistics."""
        self.evaluation_stats['total_evaluations'] += 1
        
        # Update average duration
        total_duration = (self.evaluation_stats['avg_duration_ms'] * 
                         (self.evaluation_stats['total_evaluations'] - 1) + 
                         move_eval.total_duration_ms)
        self.evaluation_stats['avg_duration_ms'] = total_duration / self.evaluation_stats['total_evaluations']
        
        # Update method usage
        for step in move_eval.evaluation_steps:
            method = step.method_name
            self.evaluation_stats['method_usage'][method] = (
                self.evaluation_stats['method_usage'].get(method, 0) + 1
            )
        
        # Update success rate
        successes = sum(1 for me in move_evaluation_manager.move_history 
                       if me.status == MoveStatus.COMPLETED)
        self.evaluation_stats['success_rate'] = successes / self.evaluation_stats['total_evaluations']
    
    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        return self.evaluation_stats.copy()
    
    def set_move_time(self, time_ms: int) -> None:
        """Set the move time limit."""
        self.move_time_ms = max(100, time_ms)  # Minimum 100ms
    
    def get_move_time(self) -> int:
        """Get the current move time limit."""
        return self.move_time_ms


# Global enhanced move evaluator instance
enhanced_move_evaluator = EnhancedMoveEvaluator()