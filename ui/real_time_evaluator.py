"""
Real-time Move Evaluation Visualizer.

This module provides real-time visualization of move evaluation processes,
showing step-by-step analysis with colored cells and timing delays.
"""

from __future__ import annotations

import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from PySide6.QtCore import QObject, QTimer, pyqtSignal
from PySide6.QtWidgets import QWidget
import chess
from chess import Board, Move

from core.move_object import MoveEvaluation, MovePhase, EvaluationStep
from core.timing_config import timing_manager
from core.move_evaluator import enhanced_move_evaluator


class RealTimeEvaluationVisualizer(QObject):
    """
    Real-time visualizer for move evaluation processes.
    
    This class coordinates the visualization of move evaluation steps,
    showing progress through different phases with appropriate delays
    and visual feedback.
    """
    
    # Signals
    evaluation_started = pyqtSignal(dict)  # move_info
    phase_started = pyqtSignal(str, dict)  # phase_name, phase_info
    step_completed = pyqtSignal(str, dict)  # step_name, step_result
    evaluation_completed = pyqtSignal(dict)  # final_result
    cell_highlighted = pyqtSignal(int, str)  # square, color
    visualization_updated = pyqtSignal(dict)  # visualization_state
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Visualization state
        self.current_evaluation: Optional[MoveEvaluation] = None
        self.visualization_active = False
        self.current_phase_index = 0
        self.current_step_index = 0
        
        # Timing control
        self.phase_timer = QTimer()
        self.step_timer = QTimer()
        self.cell_timer = QTimer()
        
        # Connect timers
        self.phase_timer.timeout.connect(self._advance_phase)
        self.step_timer.timeout.connect(self._advance_step)
        self.cell_timer.timeout.connect(self._update_cell_visualization)
        
        # Visualization settings
        self.show_phase_delays = True
        self.show_step_delays = True
        self.show_cell_animations = True
        
        # Phase sequence for visualization
        self.phase_sequence = [
            MovePhase.INITIALIZATION,
            MovePhase.PATTERN_MATCHING,
            MovePhase.WFC_ANALYSIS,
            MovePhase.BSP_ANALYSIS,
            MovePhase.BOT_EVALUATION,
            MovePhase.GUARDRAILS_CHECK,
            MovePhase.FINAL_SELECTION,
            MovePhase.VISUALIZATION
        ]
        
        # Colors for different phases
        self.phase_colors = {
            MovePhase.INITIALIZATION: 'lightgray',
            MovePhase.PATTERN_MATCHING: 'yellow',
            MovePhase.WFC_ANALYSIS: 'orange',
            MovePhase.BSP_ANALYSIS: 'blue',
            MovePhase.BOT_EVALUATION: 'purple',
            MovePhase.GUARDRAILS_CHECK: 'red',
            MovePhase.FINAL_SELECTION: 'green',
            MovePhase.VISUALIZATION: 'cyan'
        }
    
    def start_real_time_evaluation(self, board: Board, move: Move, 
                                  bot_name: str = "RealTimeBot") -> None:
        """Start real-time evaluation visualization."""
        if self.visualization_active:
            self.stop_visualization()
        
        # Create move evaluation
        self.current_evaluation = enhanced_move_evaluator.evaluate_move(board, move, bot_name)
        
        # Reset visualization state
        self.current_phase_index = 0
        self.current_step_index = 0
        self.visualization_active = True
        
        # Emit start signal
        move_info = {
            'move': move.uci(),
            'san': board.san(move) if board.is_legal(move) else str(move),
            'board_fen': board.fen(),
            'bot_name': bot_name
        }
        self.evaluation_started.emit(move_info)
        
        # Start phase visualization
        self._start_phase_visualization()
    
    def _start_phase_visualization(self) -> None:
        """Start visualization of the current phase."""
        if (not self.visualization_active or 
            self.current_phase_index >= len(self.phase_sequence)):
            self._complete_visualization()
            return
        
        current_phase = self.phase_sequence[self.current_phase_index]
        
        # Emit phase start signal
        phase_info = {
            'phase': current_phase.value,
            'index': self.current_phase_index,
            'total_phases': len(self.phase_sequence),
            'color': self.phase_colors.get(current_phase, 'gray')
        }
        self.phase_started.emit(current_phase.value, phase_info)
        
        # Start step visualization for this phase
        self._start_step_visualization()
    
    def _start_step_visualization(self) -> None:
        """Start visualization of steps within the current phase."""
        if not self.visualization_active or not self.current_evaluation:
            return
        
        current_phase = self.phase_sequence[self.current_phase_index]
        
        # Find steps for current phase
        phase_steps = [step for step in self.current_evaluation.evaluation_steps 
                      if self._step_belongs_to_phase(step, current_phase)]
        
        if not phase_steps:
            # No steps for this phase, move to next phase
            self._advance_phase()
            return
        
        # Start step timer
        step_delay = timing_manager.get_visualization_delay_ms()
        self.step_timer.start(step_delay)
    
    def _step_belongs_to_phase(self, step: EvaluationStep, phase: MovePhase) -> bool:
        """Check if a step belongs to a specific phase."""
        phase_method_mapping = {
            MovePhase.PATTERN_MATCHING: ['pattern_matching'],
            MovePhase.WFC_ANALYSIS: ['wfc_analysis'],
            MovePhase.BSP_ANALYSIS: ['bsp_analysis'],
            MovePhase.BOT_EVALUATION: ['bot_evaluation'],
            MovePhase.GUARDRAILS_CHECK: ['guardrails_check'],
        }
        
        methods = phase_method_mapping.get(phase, [])
        return step.method_name in methods
    
    def _advance_step(self) -> None:
        """Advance to the next step in the current phase."""
        if not self.visualization_active or not self.current_evaluation:
            return
        
        current_phase = self.phase_sequence[self.current_phase_index]
        phase_steps = [step for step in self.current_evaluation.evaluation_steps 
                      if self._step_belongs_to_phase(step, current_phase)]
        
        if self.current_step_index >= len(phase_steps):
            # All steps in this phase completed
            self.step_timer.stop()
            self._advance_phase()
            return
        
        # Process current step
        current_step = phase_steps[self.current_step_index]
        self._visualize_step(current_step)
        
        self.current_step_index += 1
    
    def _visualize_step(self, step: EvaluationStep) -> None:
        """Visualize a single evaluation step."""
        # Emit step completion signal
        step_result = {
            'method': step.method_name,
            'bot_name': step.bot_name,
            'duration_ms': step.duration_ms,
            'status': step.status.value,
            'confidence': step.confidence,
            'reason': step.reason,
            'output_data': step.output_data
        }
        self.step_completed.emit(step.method_name, step_result)
        
        # Start cell animation if enabled
        if self.show_cell_animations:
            self._start_cell_animation(step)
    
    def _start_cell_animation(self, step: EvaluationStep) -> None:
        """Start cell animation for a step."""
        if not self.current_evaluation:
            return
        
        # Determine squares to highlight based on step type
        squares_to_highlight = self._get_squares_for_step(step)
        
        # Get color for current phase
        current_phase = self.phase_sequence[self.current_phase_index]
        color = self.phase_colors.get(current_phase, 'gray')
        
        # Highlight squares
        for square in squares_to_highlight:
            self.cell_highlighted.emit(square, color)
        
        # Start cell timer for animation duration
        animation_duration = timing_manager.get_visualization_delay_ms() // 2
        self.cell_timer.start(animation_duration)
    
    def _get_squares_for_step(self, step: EvaluationStep) -> List[int]:
        """Get squares to highlight for a specific step."""
        if not self.current_evaluation:
            return []
        
        squares = []
        
        # Add move squares
        if hasattr(self.current_evaluation, 'move'):
            move = self.current_evaluation.move
            squares.extend([move.from_square, move.to_square])
        
        # Add method-specific squares
        if step.method_name == 'pattern_matching':
            # Highlight pattern-related squares
            for pattern_match in self.current_evaluation.pattern_matches:
                pattern_data = pattern_match.get('data', {})
                if 'squares' in pattern_data:
                    squares.extend(pattern_data['squares'])
        
        elif step.method_name == 'bsp_analysis':
            # Highlight BSP zone squares (simplified)
            # In a real implementation, this would use actual BSP results
            pass
        
        elif step.method_name == 'wfc_analysis':
            # Highlight WFC pattern squares (simplified)
            pass
        
        return squares
    
    def _update_cell_visualization(self) -> None:
        """Update cell visualization animation."""
        self.cell_timer.stop()
        
        # Clear cell highlights (emit with empty color)
        if self.current_evaluation and hasattr(self.current_evaluation, 'move'):
            move = self.current_evaluation.move
            self.cell_highlighted.emit(move.from_square, '')
            self.cell_highlighted.emit(move.to_square, '')
    
    def _advance_phase(self) -> None:
        """Advance to the next phase."""
        self.current_phase_index += 1
        self.current_step_index = 0
        
        # Add delay between phases if enabled
        if self.show_phase_delays:
            phase_delay = timing_manager.get_visualization_delay_ms() * 2
            QTimer.singleShot(phase_delay, self._start_phase_visualization)
        else:
            self._start_phase_visualization()
    
    def _complete_visualization(self) -> None:
        """Complete the visualization process."""
        self.visualization_active = False
        self.phase_timer.stop()
        self.step_timer.stop()
        self.cell_timer.stop()
        
        if self.current_evaluation:
            # Emit completion signal
            final_result = {
                'move': self.current_evaluation.san_notation,
                'final_score': self.current_evaluation.final_score,
                'confidence': self.current_evaluation.confidence,
                'primary_reason': self.current_evaluation.primary_reason,
                'total_duration_ms': self.current_evaluation.total_duration_ms,
                'evaluation_summary': self.current_evaluation.get_evaluation_summary()
            }
            self.evaluation_completed.emit(final_result)
    
    def stop_visualization(self) -> None:
        """Stop the current visualization."""
        self.visualization_active = False
        self.phase_timer.stop()
        self.step_timer.stop()
        self.cell_timer.stop()
        self.current_evaluation = None
    
    def set_visualization_settings(self, show_phase_delays: bool = True,
                                 show_step_delays: bool = True,
                                 show_cell_animations: bool = True) -> None:
        """Configure visualization settings."""
        self.show_phase_delays = show_phase_delays
        self.show_step_delays = show_step_delays
        self.show_cell_animations = show_cell_animations
    
    def get_visualization_state(self) -> Dict[str, Any]:
        """Get current visualization state."""
        return {
            'active': self.visualization_active,
            'current_phase': (self.phase_sequence[self.current_phase_index].value 
                            if self.current_phase_index < len(self.phase_sequence) else None),
            'phase_progress': f"{self.current_phase_index}/{len(self.phase_sequence)}",
            'current_evaluation': (self.current_evaluation.get_evaluation_summary() 
                                 if self.current_evaluation else None),
            'settings': {
                'show_phase_delays': self.show_phase_delays,
                'show_step_delays': self.show_step_delays,
                'show_cell_animations': self.show_cell_animations
            }
        }


class RealTimeVisualizationIntegrator:
    """
    Integrates real-time visualization with the PySide viewer.
    
    This class manages the connection between the real-time evaluator
    and the chess board visualization components.
    """
    
    def __init__(self, chess_viewer):
        self.chess_viewer = chess_viewer
        self.visualizer = RealTimeEvaluationVisualizer()
        
        # Connect signals
        self.visualizer.evaluation_started.connect(self._on_evaluation_started)
        self.visualizer.phase_started.connect(self._on_phase_started)
        self.visualizer.step_completed.connect(self._on_step_completed)
        self.visualizer.evaluation_completed.connect(self._on_evaluation_completed)
        self.visualizer.cell_highlighted.connect(self._on_cell_highlighted)
    
    def start_real_time_evaluation(self, board: Board, move: Move, bot_name: str) -> None:
        """Start real-time evaluation for a move."""
        self.visualizer.start_real_time_evaluation(board, move, bot_name)
    
    def _on_evaluation_started(self, move_info: Dict[str, Any]) -> None:
        """Handle evaluation start."""
        if hasattr(self.chess_viewer, '_append_to_console'):
            self.chess_viewer._append_to_console(
                f"🔍 Starting real-time evaluation: {move_info['san']}"
            )
    
    def _on_phase_started(self, phase_name: str, phase_info: Dict[str, Any]) -> None:
        """Handle phase start."""
        if hasattr(self.chess_viewer, '_append_to_console'):
            progress = f"{phase_info['index'] + 1}/{phase_info['total_phases']}"
            self.chess_viewer._append_to_console(
                f"📊 Phase {progress}: {phase_name}"
            )
    
    def _on_step_completed(self, step_name: str, step_result: Dict[str, Any]) -> None:
        """Handle step completion."""
        if hasattr(self.chess_viewer, '_append_to_console'):
            duration = step_result['duration_ms']
            status = step_result['status']
            self.chess_viewer._append_to_console(
                f"  ✓ {step_name}: {status} ({duration:.1f}ms)"
            )
    
    def _on_evaluation_completed(self, final_result: Dict[str, Any]) -> None:
        """Handle evaluation completion."""
        if hasattr(self.chess_viewer, '_append_to_console'):
            score = final_result['final_score']
            reason = final_result['primary_reason']
            duration = final_result['total_duration_ms']
            self.chess_viewer._append_to_console(
                f"🎯 Evaluation complete: {score:.1f} ({reason}) [{duration:.1f}ms]"
            )
    
    def _on_cell_highlighted(self, square: int, color: str) -> None:
        """Handle cell highlighting."""
        # Update the chess board visualization
        if hasattr(self.chess_viewer, 'cell_grid'):
            row = 7 - chess.square_rank(square)
            col = chess.square_file(square)
            
            if 0 <= row < 8 and 0 <= col < 8:
                cell = self.chess_viewer.cell_grid[row][col]
                if color:
                    cell.set_highlight(True)
                    # You could set different highlight colors here
                else:
                    cell.set_highlight(False)
                cell.update()
    
    def stop_visualization(self) -> None:
        """Stop the current visualization."""
        self.visualizer.stop_visualization()
    
    def set_visualization_settings(self, **settings) -> None:
        """Set visualization settings."""
        self.visualizer.set_visualization_settings(**settings)