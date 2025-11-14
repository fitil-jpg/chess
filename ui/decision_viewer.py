"""
Decision Viewer UI Component

Real-time visualization of chess AI decision-making process.
Shows agent contributions, weights, timing, and tactical analysis.
"""

from __future__ import annotations

import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import threading

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
        QProgressBar, QPushButton, QGroupBox, QGridLayout,
        QSplitter, QScrollArea, QFrame, QTabWidget
    )
    from PySide6.QtCore import QTimer, Qt, Signal, QObject
    from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

from ui.decision_roadmap import decision_roadmap


@dataclass
class ViewerConfig:
    """Configuration for the decision viewer."""
    update_interval_ms: int = 500
    max_history_items: int = 50
    show_real_time: bool = True
    show_timing: bool = True
    show_weights: bool = True
    show_tactical: bool = True
    auto_scroll: bool = True


class DecisionSignals(QObject):
    """Signals for decision viewer updates."""
    update_received = Signal(dict)
    new_move_completed = Signal(dict)


class DecisionViewer(QWidget):
    """
    Real-time UI viewer for chess AI decision-making process.
    
    Features:
    - Live updates during move evaluation
    - Agent contribution visualization
    - Weight and timing analysis
    - Tactical motif display
    - Historical move review
    - Export functionality
    """
    
    def __init__(self, config: Optional[ViewerConfig] = None):
        super().__init__()
        
        if not GUI_AVAILABLE:
            raise ImportError("PySide6 is required for DecisionViewer GUI")
        
        self.config = config or ViewerConfig()
        self.signals = DecisionSignals()
        self.current_roadmap: Dict[str, Any] = {}
        self.move_history: List[Dict[str, Any]] = []
        
        self._setup_ui()
        self._setup_timer()
        self._connect_signals()
        
        # Update initial state
        self._update_display()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        self.setWindowTitle("Chess AI Decision Roadmap Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.real_time_tab = self._create_real_time_tab()
        self.agents_tab = self._create_agents_tab()
        self.timing_tab = self._create_timing_tab()
        self.tactical_tab = self._create_tactical_tab()
        self.history_tab = self._create_history_tab()
        
        self.tab_widget.addTab(self.real_time_tab, "Real-time")
        self.tab_widget.addTab(self.agents_tab, "Agents")
        self.tab_widget.addTab(self.timing_tab, "Timing")
        self.tab_widget.addTab(self.tactical_tab, "Tactical")
        self.tab_widget.addTab(self.history_tab, "History")
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with buttons and status."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        layout = QHBoxLayout(panel)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        layout.addWidget(self.status_label)
        
        # Control buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._update_display)
        layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self._export_data)
        layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self._clear_history)
        layout.addWidget(self.clear_btn)
        
        # Update interval control
        layout.addWidget(QLabel("Update (ms):"))
        self.interval_spin = QPushButton(str(self.config.update_interval_ms))
        self.interval_spin.clicked.connect(self._change_update_interval)
        layout.addWidget(self.interval_spin)
        
        layout.addStretch()
        
        return panel
    
    def _create_real_time_tab(self) -> QWidget:
        """Create the real-time monitoring tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current move info
        move_group = QGroupBox("Current Move")
        move_layout = QGridLayout(move_group)
        
        self.move_label = QLabel("No active move")
        self.move_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        move_layout.addWidget(self.move_label, 0, 0, 1, 2)
        
        self.phase_label = QLabel("Phase: -")
        move_layout.addWidget(self.phase_label, 1, 0)
        
        self.status_label_rt = QLabel("Status: -")
        move_layout.addWidget(self.status_label_rt, 1, 1)
        
        self.score_label = QLabel("Score: -")
        move_layout.addWidget(self.score_label, 2, 0)
        
        self.confidence_label = QLabel("Confidence: -")
        move_layout.addWidget(self.confidence_label, 2, 1)
        
        layout.addWidget(move_group)
        
        # Progress bar for evaluation
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Real-time log
        log_group = QGroupBox("Evaluation Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setFont(QFont("Courier", 9))
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        return widget
    
    def _create_agents_tab(self) -> QWidget:
        """Create the agents analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Agent contributions
        self.agents_text = QTextEdit()
        self.agents_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.agents_text)
        
        return widget
    
    def _create_timing_tab(self) -> QWidget:
        """Create the timing analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.timing_text = QTextEdit()
        self.timing_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.timing_text)
        
        return widget
    
    def _create_tactical_tab(self) -> QWidget:
        """Create the tactical analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.tactical_text = QTextEdit()
        self.tactical_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.tactical_text)
        
        return widget
    
    def _create_history_tab(self) -> QWidget:
        """Create the move history tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # History controls
        history_controls = QHBoxLayout()
        self.history_prev_btn = QPushButton("← Previous")
        self.history_prev_btn.clicked.connect(self._show_previous_move)
        history_controls.addWidget(self.history_prev_btn)
        
        self.history_next_btn = QPushButton("Next →")
        self.history_next_btn.clicked.connect(self._show_next_move)
        history_controls.addWidget(self.history_next_btn)
        
        self.history_pos_label = QLabel("Move: 0/0")
        history_controls.addWidget(self.history_pos_label)
        
        history_controls.addStretch()
        layout.addLayout(history_controls)
        
        # History display
        self.history_text = QTextEdit()
        self.history_text.setFont(QFont("Courier", 9))
        layout.addWidget(self.history_text)
        
        self.current_history_index = -1
        
        return widget
    
    def _setup_timer(self):
        """Setup the update timer."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(self.config.update_interval_ms)
    
    def _connect_signals(self):
        """Connect signals to slots."""
        self.signals.update_received.connect(self._on_update_received)
        self.signals.new_move_completed.connect(self._on_new_move_completed)
    
    def _update_display(self):
        """Update the display with current data."""
        try:
            # Get current roadmap
            self.current_roadmap = decision_roadmap.get_current_roadmap()
            
            # Get real-time updates
            realtime_data = decision_roadmap.get_real_time_updates()
            
            # Emit signals
            self.signals.update_received.emit(realtime_data)
            
            # Check if move is completed
            if realtime_data.get("status") == "completed":
                self.signals.new_move_completed.emit(self.current_roadmap)
                
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
    
    def _on_update_received(self, data: Dict[str, Any]):
        """Handle real-time update data."""
        if data.get("status") == "no_active_move":
            self.move_label.setText("No active move")
            self.phase_label.setText("Phase: -")
            self.status_label_rt.setText("Status: -")
            self.progress_bar.setValue(0)
            return
        
        # Update move info
        move = data.get("move", "Unknown")
        self.move_label.setText(f"Move: {move}")
        
        phase = data.get("current_phase", "unknown")
        self.phase_label.setText(f"Phase: {phase}")
        
        status = data.get("status", "unknown")
        self.status_label_rt.setText(f"Status: {status}")
        
        # Update progress
        agents_evaluated = data.get("agents_evaluated", 0)
        total_agents = data.get("total_agents", 1)
        progress = int((agents_evaluated / total_agents) * 100) if total_agents > 0 else 0
        self.progress_bar.setValue(progress)
        
        # Update confidence
        confidence = data.get("confidence", 0)
        self.confidence_label.setText(f"Confidence: {confidence:.3f}")
        
        # Add to log
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Phase: {phase}, Agents: {agents_evaluated}/{total_agents}, Progress: {progress}%\n"
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertPlainText(log_entry)
        
        # Auto-scroll if enabled
        if self.config.auto_scroll:
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Update other tabs
        self._update_agents_tab()
        self._update_timing_tab()
        self._update_tactical_tab()
    
    def _on_new_move_completed(self, roadmap: Dict[str, Any]):
        """Handle completion of a new move."""
        if "move_info" in roadmap:
            self.move_history.append(roadmap)
            
            # Limit history size
            if len(self.move_history) > self.config.max_history_items:
                self.move_history = self.move_history[-self.config.max_history_items:]
            
            # Update history display
            self._update_history_display()
    
    def _update_agents_tab(self):
        """Update the agents analysis tab."""
        if not self.current_roadmap:
            return
        
        text = []
        text.append("=" * 60)
        text.append("AGENT CONTRIBUTIONS ANALYSIS")
        text.append("=" * 60)
        
        if "agent_contributions" in self.current_roadmap:
            for agent, contrib in self.current_roadmap["agent_contributions"].items():
                text.append(f"\n{agent.upper()}:")
                text.append(f"  Method: {contrib.get('method', 'N/A')}")
                text.append(f"  Confidence: {contrib.get('confidence', 0):.3f}")
                text.append(f"  Duration: {contrib.get('duration_ms', 0):.1f}ms")
                text.append(f"  Status: {contrib.get('status', 'N/A')}")
                
                if contrib.get('output_data'):
                    output = contrib['output_data']
                    if output.get('move'):
                        text.append(f"  Suggested: {output['move']}")
                    if output.get('engine'):
                        text.append(f"  Engine: {output['engine']}")
        
        self.agents_text.setText("\n".join(text))
    
    def _update_timing_tab(self):
        """Update the timing analysis tab."""
        if not self.current_roadmap:
            return
        
        text = []
        text.append("=" * 60)
        text.append("TIMING ANALYSIS")
        text.append("=" * 60)
        
        if "decision_process" in self.current_roadmap:
            decision = self.current_roadmap["decision_process"]
            text.append(f"Total Duration: {decision.get('total_duration_ms', 0):.1f}ms")
            text.append(f"Current Phase: {decision.get('current_phase', 'N/A')}")
        
        if "timing_breakdown" in self.current_roadmap:
            text.append("\nPhase Breakdown:")
            for phase, duration in self.current_roadmap["timing_breakdown"].items():
                text.append(f"  {phase}: {duration:.1f}ms")
        
        self.timing_text.setText("\n".join(text))
    
    def _update_tactical_tab(self):
        """Update the tactical analysis tab."""
        if not self.current_roadmap:
            return
        
        text = []
        text.append("=" * 60)
        text.append("TACTICAL ANALYSIS")
        text.append("=" * 60)
        
        if "tactical_analysis" in self.current_roadmap:
            tactical = self.current_roadmap["tactical_analysis"]
            
            motifs = tactical.get("motifs", [])
            if motifs:
                text.append(f"Tactical Motifs: {', '.join(motifs)}")
            
            threats = tactical.get("threats", [])
            if threats:
                text.append(f"Threats: {', '.join(threats)}")
            
            guardrails = tactical.get("guardrails", {})
            if guardrails:
                text.append(f"\nGuardrails:")
                text.append(f"  Passed: {guardrails.get('passed', False)}")
                violations = guardrails.get("violations", [])
                if violations:
                    text.append(f"  Violations: {', '.join(violations)}")
                warnings = guardrails.get("warnings", [])
                if warnings:
                    text.append(f"  Warnings: {', '.join(warnings)}")
            
            minimax = tactical.get("minimax", {})
            if minimax.get("value") is not None:
                text.append(f"\nMinimax Analysis:")
                text.append(f"  Depth: {minimax.get('depth', 0)}")
                text.append(f"  Value: {minimax.get('value', 0):.2f}")
                text.append(f"  Meets Threshold: {minimax.get('meets_threshold', False)}")
        
        self.tactical_text.setText("\n".join(text))
    
    def _update_history_display(self):
        """Update the history tab display."""
        if not self.move_history:
            self.history_text.setText("No move history available")
            self.history_pos_label.setText("Move: 0/0")
            return
        
        # Update position label
        total_moves = len(self.move_history)
        current_pos = self.current_history_index + 1 if self.current_history_index >= 0 else total_moves
        self.history_pos_label.setText(f"Move: {current_pos}/{total_moves}")
        
        # Show current or last move
        if self.current_history_index < 0:
            roadmap = self.move_history[-1]
        else:
            roadmap = self.move_history[self.current_history_index]
        
        text = []
        text.append("=" * 60)
        text.append("MOVE HISTORY")
        text.append("=" * 60)
        
        if "move_info" in roadmap:
            move_info = roadmap["move_info"]
            text.append(f"Move: {move_info.get('move', 'N/A')}")
            text.append(f"Number: {move_info.get('move_number', 'N/A')}")
            text.append(f"Color: {move_info.get('color', 'N/A')}")
        
        if "decision_process" in roadmap:
            decision = roadmap["decision_process"]
            text.append(f"\nDecision Process:")
            text.append(f"  Phase: {decision.get('current_phase', 'N/A')}")
            text.append(f"  Status: {decision.get('status', 'N/A')}")
            text.append(f"  Score: {decision.get('final_score', 0):.3f}")
            text.append(f"  Confidence: {decision.get('confidence', 0):.3f}")
            text.append(f"  Duration: {decision.get('total_duration_ms', 0):.1f}ms")
            text.append(f"  Reason: {decision.get('primary_reason', 'N/A')}")
        
        self.history_text.setText("\n".join(text))
    
    def _show_previous_move(self):
        """Show previous move in history."""
        if self.move_history and self.current_history_index > 0:
            self.current_history_index -= 1
            self._update_history_display()
    
    def _show_next_move(self):
        """Show next move in history."""
        if self.move_history and self.current_history_index < len(self.move_history) - 1:
            self.current_history_index += 1
            self._update_history_display()
        elif self.current_history_index == len(self.move_history) - 1:
            self.current_history_index = -1  # Show latest
            self._update_history_display()
    
    def _export_data(self):
        """Export decision data to file."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"decision_roadmap_{timestamp}.json"
            decision_roadmap.export_roadmap_json(filename, include_history=True)
            self.status_label.setText(f"Exported to {filename}")
        except Exception as e:
            self.status_label.setText(f"Export failed: {str(e)}")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
    
    def _clear_history(self):
        """Clear move history."""
        self.move_history.clear()
        self.current_history_index = -1
        self._update_history_display()
        self.status_label.setText("History cleared")
    
    def _change_update_interval(self):
        """Change the update interval."""
        # Simple implementation - cycles through common intervals
        intervals = [200, 500, 1000, 2000]
        current_idx = intervals.index(self.config.update_interval_ms)
        next_idx = (current_idx + 1) % len(intervals)
        
        self.config.update_interval_ms = intervals[next_idx]
        self.update_timer.setInterval(self.config.update_interval_ms)
        self.interval_spin.setText(str(self.config.update_interval_ms))
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.update_timer.stop()
        super().closeEvent(event)


def create_decision_viewer(config: Optional[ViewerConfig] = None) -> Optional[DecisionViewer]:
    """Create and return a decision viewer instance."""
    if not GUI_AVAILABLE:
        print("Warning: PySide6 not available. Decision viewer cannot be created.")
        print("Install with: pip install PySide6")
        return None
    
    return DecisionViewer(config)


def main():
    """Main function for standalone decision viewer."""
    import sys
    
    if not GUI_AVAILABLE:
        print("Error: PySide6 is required for the decision viewer.")
        print("Install with: pip install PySide6")
        sys.exit(1)
    
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create and show viewer
    config = ViewerConfig(update_interval_ms=500)
    viewer = DecisionViewer(config)
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
