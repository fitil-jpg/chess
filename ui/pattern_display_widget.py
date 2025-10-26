"""
Pattern Display Widget for PySide Viewer
=========================================

Отображает применённые паттерны во время игры:
- Список применённых паттернов
- Детали каждого паттерна
- Участвующие фигуры
- Последовательности обменов
- Статистика использования паттернов
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QGroupBox, QTextEdit, QListWidgetItem, QScrollArea,
    QFrame, QCheckBox, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette, QFont

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PatternDisplayWidget(QWidget):
    """
    Виджет для отображения паттернов во время игры.
    
    Показывает:
    - Применённые паттерны для обоих ботов
    - Детали паттерна (фигуры, размены)
    - Статистику
    """
    
    pattern_selected = Signal(str)  # Emitted when pattern is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.applied_patterns: List[Dict[str, Any]] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("📋 <b>Применённые паттерны</b>")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 8px;
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
            }
        """)
        layout.addWidget(header_label)
        
        # Filter controls
        filter_group = QGroupBox("Фильтры")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Бот:"))
        self.bot_filter = QComboBox()
        self.bot_filter.addItems(["Все", "DynamicBot", "StockfishBot"])
        self.bot_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.bot_filter)
        
        filter_layout.addWidget(QLabel("Тип:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "Все", "fork", "pin", "exchange", "capture", "check", "tactical"
        ])
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addStretch()
        layout.addWidget(filter_group)
        
        # Pattern list
        list_label = QLabel("Список паттернов:")
        layout.addWidget(list_label)
        
        self.pattern_list = QListWidget()
        self.pattern_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #bbdefb;
                color: #000;
            }
        """)
        self.pattern_list.itemClicked.connect(self.on_pattern_clicked)
        layout.addWidget(self.pattern_list)
        
        # Pattern details
        details_label = QLabel("Детали паттерна:")
        layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.details_text)
        
        # Statistics
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Очистить")
        self.clear_btn.clicked.connect(self.clear_patterns)
        button_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("💾 Экспорт")
        self.export_btn.clicked.connect(self.export_patterns)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Initial update
        self.update_statistics()
    
    def add_pattern(
        self,
        pattern_id: str,
        pattern_type: str,
        bot_name: str,
        move_number: int,
        fen: str,
        move: str,
        participating_pieces: List[Dict[str, Any]],
        exchange: Optional[Dict[str, Any]] = None
    ):
        """
        Add a pattern to the display.
        
        Args:
            pattern_id: Unique pattern identifier
            pattern_type: Type of pattern (fork, pin, etc.)
            bot_name: Name of bot that used this pattern
            move_number: Move number when pattern was applied
            fen: Position FEN
            move: Move in UCI/SAN format
            participating_pieces: List of participating pieces
            exchange: Optional exchange sequence data
        """
        pattern_data = {
            "pattern_id": pattern_id,
            "pattern_type": pattern_type,
            "bot_name": bot_name,
            "move_number": move_number,
            "fen": fen,
            "move": move,
            "participating_pieces": participating_pieces,
            "exchange": exchange
        }
        
        self.applied_patterns.append(pattern_data)
        self.refresh_list()
        self.update_statistics()
    
    def refresh_list(self):
        """Refresh the pattern list display."""
        self.pattern_list.clear()
        
        # Apply filters
        filtered_patterns = self.get_filtered_patterns()
        
        for pattern in filtered_patterns:
            # Format: "Move 12 | DynamicBot | fork | Nf3"
            move_num = pattern["move_number"]
            bot = pattern["bot_name"]
            ptype = pattern["pattern_type"]
            move = pattern["move"]
            
            item_text = f"Ход {move_num:3d} | {bot:15s} | {ptype:12s} | {move}"
            
            item = QListWidgetItem(item_text)
            
            # Color code by pattern type
            if ptype == "fork":
                item.setBackground(QColor("#ffecb3"))  # Light orange
            elif ptype == "pin":
                item.setBackground(QColor("#c5cae9"))  # Light blue
            elif ptype == "exchange":
                item.setBackground(QColor("#c8e6c9"))  # Light green
            elif ptype == "check":
                item.setBackground(QColor("#ffcdd2"))  # Light red
            
            # Store pattern data
            item.setData(Qt.UserRole, pattern)
            
            self.pattern_list.addItem(item)
    
    def get_filtered_patterns(self) -> List[Dict[str, Any]]:
        """Get filtered patterns based on current filter settings."""
        filtered = self.applied_patterns
        
        # Filter by bot
        bot_filter = self.bot_filter.currentText()
        if bot_filter != "Все":
            filtered = [p for p in filtered if p["bot_name"] == bot_filter]
        
        # Filter by type
        type_filter = self.type_filter.currentText()
        if type_filter != "Все":
            filtered = [p for p in filtered if p["pattern_type"] == type_filter]
        
        return filtered
    
    def apply_filters(self):
        """Apply current filters and refresh the list."""
        self.refresh_list()
        self.update_statistics()
    
    def on_pattern_clicked(self, item: QListWidgetItem):
        """Handle pattern selection."""
        pattern = item.data(Qt.UserRole)
        if pattern:
            self.show_pattern_details(pattern)
            self.pattern_selected.emit(pattern["pattern_id"])
    
    def show_pattern_details(self, pattern: Dict[str, Any]):
        """Show detailed information about a pattern."""
        details = []
        
        details.append(f"═══════════════════════════════════════")
        details.append(f"Паттерн: {pattern['pattern_type'].upper()}")
        details.append(f"═══════════════════════════════════════")
        details.append(f"")
        details.append(f"Ход:    {pattern['move_number']}")
        details.append(f"Бот:    {pattern['bot_name']}")
        details.append(f"Ход:    {pattern['move']}")
        details.append(f"FEN:    {pattern['fen'][:50]}...")
        details.append(f"")
        
        # Participating pieces
        details.append(f"Участвующие фигуры ({len(pattern['participating_pieces'])}):")
        details.append(f"───────────────────────────────────────")
        
        for piece in pattern['participating_pieces']:
            square = piece['square']
            ptype = piece['piece_type']
            color = piece['color']
            role = piece['role']
            moved = "✓" if piece.get('moved_in_pattern', False) else " "
            
            details.append(f"  [{moved}] {square:4s} | {color:5s} {ptype:7s} | {role}")
        
        # Exchange sequence
        if pattern.get('exchange'):
            exchange = pattern['exchange']
            details.append(f"")
            details.append(f"Размен:")
            details.append(f"───────────────────────────────────────")
            details.append(f"  Ходы:     {' → '.join(exchange['moves'])}")
            details.append(f"  Баланс:   {exchange['material_balance']:+d}")
            details.append(f"  Форсир.:  {'Да' if exchange['forced'] else 'Нет'}")
            details.append(f"  Оценка:   {exchange['evaluation_change']:+.1f}")
        
        details.append(f"═══════════════════════════════════════")
        
        self.details_text.setText("\n".join(details))
    
    def update_statistics(self):
        """Update the statistics display."""
        total = len(self.applied_patterns)
        filtered = len(self.get_filtered_patterns())
        
        if total == 0:
            self.stats_label.setText("Паттернов пока нет")
            return
        
        # Count by type
        type_counts = {}
        bot_counts = {}
        exchange_count = 0
        
        for pattern in self.applied_patterns:
            ptype = pattern["pattern_type"]
            bot = pattern["bot_name"]
            
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
            bot_counts[bot] = bot_counts.get(bot, 0) + 1
            
            if pattern.get("exchange"):
                exchange_count += 1
        
        stats_lines = [
            f"<b>Всего паттернов:</b> {total}",
            f"<b>Отображено:</b> {filtered}",
            f"<b>С обменами:</b> {exchange_count}",
            "",
            "<b>По типу:</b>",
        ]
        
        for ptype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            stats_lines.append(f"  • {ptype}: {count}")
        
        stats_lines.append("")
        stats_lines.append("<b>По ботам:</b>")
        
        for bot, count in sorted(bot_counts.items(), key=lambda x: -x[1]):
            stats_lines.append(f"  • {bot}: {count}")
        
        self.stats_label.setText("<br>".join(stats_lines))
    
    def clear_patterns(self):
        """Clear all patterns."""
        self.applied_patterns.clear()
        self.pattern_list.clear()
        self.details_text.clear()
        self.update_statistics()
        logger.info("Cleared all patterns from display")
    
    def export_patterns(self):
        """Export patterns to file."""
        # This would open a file dialog and save patterns
        logger.info("Pattern export requested")
        # TODO: Implement export functionality
    
    def get_pattern_count(self, bot_name: Optional[str] = None) -> int:
        """Get count of patterns, optionally filtered by bot."""
        if bot_name:
            return len([p for p in self.applied_patterns if p["bot_name"] == bot_name])
        return len(self.applied_patterns)
