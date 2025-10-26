"""
Pattern display widget for PySide viewer.
Shows detected patterns during the game.
"""

from __future__ import annotations
import json
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
    QListWidgetItem, QTextEdit, QGroupBox, QScrollArea,
    QFrame, QSplitter, QPushButton, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector
from chess_ai.pattern_manager import PatternManager


class PatternDisplayWidget(QWidget):
    """Widget for displaying chess patterns during the game"""
    
    pattern_selected = Signal(dict)  # Emitted when a pattern is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_detector = EnhancedPatternDetector()
        self.pattern_manager = PatternManager()
        self.current_patterns: List[Dict[str, Any]] = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Main content area
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Pattern list
        left_panel = self._create_pattern_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Pattern details
        right_panel = self._create_pattern_details_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
    def _create_control_panel(self) -> QWidget:
        """Create control panel with filters and buttons"""
        panel = QGroupBox("Pattern Controls")
        layout = QHBoxLayout(panel)
        
        # Pattern type filter
        layout.addWidget(QLabel("Filter:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "All Patterns",
            "Tactical Moments",
            "Forks",
            "Pins", 
            "Hanging Pieces",
            "Exchanges",
            "Sacrifices",
            "Critical Decisions"
        ])
        self.type_filter.currentTextChanged.connect(self._filter_patterns)
        layout.addWidget(self.type_filter)
        
        # Show only active patterns
        self.active_only_cb = QCheckBox("Active Only")
        self.active_only_cb.setChecked(True)
        self.active_only_cb.toggled.connect(self._filter_patterns)
        layout.addWidget(self.active_only_cb)
        
        # Clear patterns button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_patterns)
        layout.addWidget(self.clear_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_patterns)
        layout.addWidget(self.refresh_btn)
        
        layout.addStretch()
        return panel
        
    def _create_pattern_list_panel(self) -> QWidget:
        """Create pattern list panel"""
        panel = QGroupBox("Detected Patterns")
        layout = QVBoxLayout(panel)
        
        # Pattern count label
        self.pattern_count_label = QLabel("Patterns: 0")
        layout.addWidget(self.pattern_count_label)
        
        # Pattern list
        self.pattern_list = QListWidget()
        self.pattern_list.itemClicked.connect(self._on_pattern_selected)
        layout.addWidget(self.pattern_list)
        
        return panel
        
    def _create_pattern_details_panel(self) -> QWidget:
        """Create pattern details panel"""
        panel = QGroupBox("Pattern Details")
        layout = QVBoxLayout(panel)
        
        # Pattern info
        self.pattern_info = QTextEdit()
        self.pattern_info.setReadOnly(True)
        self.pattern_info.setMaximumHeight(200)
        layout.addWidget(self.pattern_info)
        
        # Participating pieces
        pieces_label = QLabel("Participating Pieces:")
        layout.addWidget(pieces_label)
        
        self.pieces_list = QListWidget()
        self.pieces_list.setMaximumHeight(150)
        layout.addWidget(self.pieces_list)
        
        # Exchange sequence (if applicable)
        self.exchange_label = QLabel("Exchange Sequence:")
        self.exchange_label.hide()
        layout.addWidget(self.exchange_label)
        
        self.exchange_text = QTextEdit()
        self.exchange_text.setReadOnly(True)
        self.exchange_text.setMaximumHeight(100)
        self.exchange_text.hide()
        layout.addWidget(self.exchange_text)
        
        layout.addStretch()
        return panel
        
    def detect_patterns(self, board, move, evaluation_before, evaluation_after, bot_analysis=None):
        """Detect patterns for the current move"""
        try:
            patterns = self.pattern_detector.detect_patterns(
                board, move, evaluation_before, evaluation_after, bot_analysis
            )
            
            for pattern in patterns:
                pattern_dict = pattern.to_dict() if hasattr(pattern, 'to_dict') else pattern
                self.current_patterns.append(pattern_dict)
                
            self._update_pattern_list()
            
        except Exception as e:
            print(f"Pattern detection error: {e}")
            
    def _update_pattern_list(self):
        """Update the pattern list display"""
        self.pattern_list.clear()
        
        filtered_patterns = self._get_filtered_patterns()
        
        for i, pattern in enumerate(filtered_patterns):
            # Create pattern item
            pattern_types = pattern.get('pattern_types', [])
            move = pattern.get('move', 'Unknown')
            description = pattern.get('description', 'No description')
            
            # Format pattern text
            pattern_text = f"{i+1}. {move} - {', '.join(pattern_types)}"
            if description:
                pattern_text += f"\n   {description}"
                
            # Add evaluation change if available
            eval_info = pattern.get('evaluation', {})
            if isinstance(eval_info, dict):
                change = eval_info.get('change', 0)
                if change != 0:
                    pattern_text += f"\n   Eval change: {change:+d}"
            
            item = QListWidgetItem(pattern_text)
            item.setData(Qt.UserRole, pattern)
            
            # Color code by pattern type
            if 'fork' in pattern_types:
                item.setBackground(QColor(255, 200, 200))  # Light red
            elif 'pin' in pattern_types:
                item.setBackground(QColor(200, 255, 200))  # Light green
            elif 'exchange' in pattern_types:
                item.setBackground(QColor(200, 200, 255))  # Light blue
            elif 'sacrifice' in pattern_types:
                item.setBackground(QColor(255, 255, 200))  # Light yellow
                
            self.pattern_list.addItem(item)
            
        # Update count
        self.pattern_count_label.setText(f"Patterns: {len(filtered_patterns)}")
        
    def _get_filtered_patterns(self) -> List[Dict[str, Any]]:
        """Get filtered patterns based on current filters"""
        patterns = self.current_patterns.copy()
        
        # Filter by type
        type_filter = self.type_filter.currentText()
        if type_filter != "All Patterns":
            type_mapping = {
                "Tactical Moments": "tactical_moment",
                "Forks": "fork", 
                "Pins": "pin",
                "Hanging Pieces": "hanging_piece",
                "Exchanges": "exchange",
                "Sacrifices": "sacrifice",
                "Critical Decisions": "critical_decision"
            }
            
            target_type = type_mapping.get(type_filter)
            if target_type:
                patterns = [p for p in patterns if target_type in p.get('pattern_types', [])]
        
        # Filter by active status
        if self.active_only_cb.isChecked():
            active_pattern_ids = self.pattern_manager.get_active_patterns()
            active_ids = {p.metadata.get('pattern_id') for p in active_patterns}
            patterns = [p for p in patterns if p.get('metadata', {}).get('pattern_id') in active_ids]
            
        return patterns
        
    def _filter_patterns(self):
        """Filter patterns based on current settings"""
        self._update_pattern_list()
        
    def _on_pattern_selected(self, item):
        """Handle pattern selection"""
        pattern = item.data(Qt.UserRole)
        if pattern:
            self._display_pattern_details(pattern)
            self.pattern_selected.emit(pattern)
            
    def _display_pattern_details(self, pattern: Dict[str, Any]):
        """Display detailed information about selected pattern"""
        # Pattern info
        info_text = f"<b>Pattern Details</b><br><br>"
        info_text += f"<b>Move:</b> {pattern.get('move', 'Unknown')}<br>"
        info_text += f"<b>Types:</b> {', '.join(pattern.get('pattern_types', []))}<br>"
        info_text += f"<b>Description:</b> {pattern.get('description', 'No description')}<br>"
        
        # Evaluation info
        eval_info = pattern.get('evaluation', {})
        if isinstance(eval_info, dict):
            before = eval_info.get('before', {}).get('total', 0)
            after = eval_info.get('after', {}).get('total', 0)
            change = eval_info.get('change', 0)
            info_text += f"<b>Evaluation:</b> {before} → {after} ({change:+d})<br>"
            
        # Metadata
        metadata = pattern.get('metadata', {})
        if metadata:
            info_text += f"<b>Move Number:</b> {metadata.get('fullmove_number', 'Unknown')}<br>"
            info_text += f"<b>Turn:</b> {metadata.get('turn', 'Unknown')}<br>"
            info_text += f"<b>Pattern Strength:</b> {metadata.get('pattern_strength', 0):.1f}<br>"
            
        self.pattern_info.setHtml(info_text)
        
        # Participating pieces
        self.pieces_list.clear()
        pieces = pattern.get('influencing_pieces', [])
        for piece in pieces:
            square = piece.get('square', 'Unknown')
            piece_name = piece.get('piece', 'Unknown')
            color = piece.get('color', 'Unknown')
            relationship = piece.get('relationship', 'Unknown')
            
            piece_text = f"{square}: {piece_name} ({color}) - {relationship}"
            item = QListWidgetItem(piece_text)
            
            # Color code by relationship
            if relationship in ['attacker', 'mover']:
                item.setBackground(QColor(255, 200, 200))
            elif relationship in ['target', 'pinned', 'hanging']:
                item.setBackground(QColor(200, 255, 200))
            elif relationship in ['exchanger', 'exchanged']:
                item.setBackground(QColor(200, 200, 255))
                
            self.pieces_list.addItem(item)
            
        # Exchange sequence
        exchange_seq = pattern.get('exchange_sequence')
        if exchange_seq and isinstance(exchange_seq, dict):
            self.exchange_label.show()
            self.exchange_text.show()
            
            moves = exchange_seq.get('moves', [])
            if moves:
                exchange_text = " → ".join(moves)
                self.exchange_text.setPlainText(exchange_text)
            else:
                self.exchange_text.setPlainText("No exchange sequence")
        else:
            self.exchange_label.hide()
            self.exchange_text.hide()
            
    def _clear_patterns(self):
        """Clear all patterns"""
        self.current_patterns.clear()
        self._update_pattern_list()
        self.pattern_info.clear()
        self.pieces_list.clear()
        self.exchange_text.clear()
        
    def _refresh_patterns(self):
        """Refresh pattern list"""
        self._update_pattern_list()
        
    def get_patterns_for_move(self, move_number: int) -> List[Dict[str, Any]]:
        """Get patterns for a specific move number"""
        return [p for p in self.current_patterns 
                if p.get('metadata', {}).get('fullmove_number') == move_number]
                
    def get_patterns_by_type(self, pattern_type: str) -> List[Dict[str, Any]]:
        """Get patterns of a specific type"""
        return [p for p in self.current_patterns 
                if pattern_type in p.get('pattern_types', [])]