"""

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
Pattern Display Widget

Виджет для отображения применённых паттернов в PySide viewer.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QGroupBox, QTextEdit, QPushButton,
    QScrollArea, QFrame, QSplitter, QTabWidget, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter

import chess
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector, PatternMatch
from chess_ai.enhanced_pattern_system import PatternManager, PatternCategory


class PatternMatchItem(QWidget):
    """Виджет для отображения одного совпадения паттерна"""
    
    def __init__(self, match: PatternMatch, parent=None):
        super().__init__(parent)
        self.match = match
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок с названием и уверенностью
        header_layout = QHBoxLayout()
        
        name_label = QLabel(self.match.pattern.name)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(name_label)
        
        confidence_label = QLabel(f"{self.match.confidence:.1%}")
        confidence_label.setStyleSheet(self._get_confidence_style())
        header_layout.addWidget(confidence_label)
        
        layout.addLayout(header_layout)
        
        # Категория и предлагаемый ход
        info_layout = QHBoxLayout()
        
        category_label = QLabel(f"[{self.match.pattern.category.value}]")
        category_label.setStyleSheet(self._get_category_style())
        info_layout.addWidget(category_label)
        
        if self.match.suggested_move:
            move_label = QLabel(f"→ {self.match.suggested_move}")
            move_label.setFont(QFont("Courier", 9))
            info_layout.addWidget(move_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Объяснение
        if self.match.explanation:
            explanation_label = QLabel(self.match.explanation)
            explanation_label.setWordWrap(True)
            explanation_label.setStyleSheet("color: #666; font-size: 9px;")
            layout.addWidget(explanation_label)
        
        # Участвующие фигуры
        if self.match.relevant_pieces:
            pieces_text = ", ".join([
                f"{p.piece_type}({p.square})" 
                for p in self.match.relevant_pieces[:3]  # Показать первые 3
            ])
            if len(self.match.relevant_pieces) > 3:
                pieces_text += "..."
            
            pieces_label = QLabel(f"Фигуры: {pieces_text}")
            pieces_label.setStyleSheet("color: #888; font-size: 8px;")
            layout.addWidget(pieces_label)
        
        # Рамка
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("QWidget { border: 1px solid #ccc; border-radius: 3px; }")
    
    def _get_confidence_style(self) -> str:
        """Получить стиль для отображения уверенности"""
        confidence = self.match.confidence
        if confidence >= 0.8:
            return "color: green; font-weight: bold;"
        elif confidence >= 0.6:
            return "color: orange; font-weight: bold;"
        else:
            return "color: red; font-weight: bold;"
    
    def _get_category_style(self) -> str:
        """Получить стиль для категории"""
        category = self.match.pattern.category
        if category == PatternCategory.TACTICAL:
            return "color: red; font-weight: bold;"
        elif category == PatternCategory.OPENING:
            return "color: green; font-weight: bold;"
        elif category == PatternCategory.ENDGAME:
            return "color: blue; font-weight: bold;"
        elif category == PatternCategory.EXCHANGE:
            return "color: orange; font-weight: bold;"
        else:
            return "color: gray;"


class PatternHistoryWidget(QWidget):
    """Виджет для отображения истории паттернов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_history: List[PatternMatch] = []
        self.max_history = 50
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        title_label = QLabel("История паттернов")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        header_layout.addWidget(title_label)
        
        self.count_label = QLabel("(0)")
        self.count_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.count_label)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self.clear_history)
        clear_btn.setMaximumWidth(80)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Прокручиваемый список
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarNever)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.addStretch()
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
    
    def add_pattern_match(self, match: PatternMatch):
        """Добавить совпадение паттерна в историю"""
        # Добавить в начало списка
        self.pattern_history.insert(0, match)
        
        # Ограничить размер истории
        if len(self.pattern_history) > self.max_history:
            self.pattern_history = self.pattern_history[:self.max_history]
        
        # Обновить отображение
        self._update_display()
    
    def add_pattern_matches(self, matches: List[PatternMatch]):
        """Добавить несколько совпадений"""
        for match in matches:
            self.add_pattern_match(match)
    
    def clear_history(self):
        """Очистить историю"""
        self.pattern_history.clear()
        self._update_display()
    
    def _update_display(self):
        """Обновить отображение"""
        # Очистить текущие виджеты
        for i in reversed(range(self.content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child and isinstance(child, PatternMatchItem):
                child.setParent(None)
        
        # Добавить новые виджеты
        for match in self.pattern_history:
            item_widget = PatternMatchItem(match)
            self.content_layout.insertWidget(0, item_widget)
        
        # Обновить счетчик
        self.count_label.setText(f"({len(self.pattern_history)})")


class PatternStatsWidget(QWidget):
    """Виджет для отображения статистики паттернов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_stats: Dict[str, int] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Статистика паттернов")
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(title_label)
        
        # Статистика по категориям
        self.stats_layout = QVBoxLayout()
        layout.addLayout(self.stats_layout)
        
        layout.addStretch()
    
    def update_stats(self, matches: List[PatternMatch]):
        """Обновить статистику"""
        # Подсчитать паттерны по категориям
        category_counts = {}
        for match in matches:
            category = match.pattern.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Очистить старые виджеты
        for i in reversed(range(self.stats_layout.count())):
            child = self.stats_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Добавить новую статистику
        total_patterns = sum(category_counts.values())
        
        for category, count in sorted(category_counts.items()):
            percentage = (count / total_patterns * 100) if total_patterns > 0 else 0
            
            stat_widget = QWidget()
            stat_layout = QHBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 0, 0, 0)
            
            label = QLabel(f"{category.title()}:")
            stat_layout.addWidget(label)
            
            count_label = QLabel(f"{count} ({percentage:.1f}%)")
            count_label.setStyleSheet("font-weight: bold;")
            stat_layout.addWidget(count_label)
            
            # Прогресс-бар
            progress = QProgressBar()
            progress.setMaximum(total_patterns)
            progress.setValue(count)
            progress.setMaximumHeight(10)
            stat_layout.addWidget(progress)
            
            self.stats_layout.addWidget(stat_widget)


class PatternDisplayWidget(QWidget):
    """Главный виджет для отображения паттернов"""
    
    pattern_selected = Signal(str)  # Сигнал выбора паттерна для применения
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_detector = EnhancedPatternDetector()
        self.current_matches: List[PatternMatch] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        
        # Вкладки
        tab_widget = QTabWidget()
        
        # Вкладка текущих паттернов
        current_tab = QWidget()
        current_layout = QVBoxLayout(current_tab)
        
        # Заголовок с кнопкой обновления
        current_header = QHBoxLayout()
        
        current_title = QLabel("Текущие паттерны")
        current_title.setFont(QFont("Arial", 11, QFont.Bold))
        current_header.addWidget(current_title)
        
        current_header.addStretch()
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_patterns)
        self.refresh_btn.setMaximumWidth(80)
        current_header.addWidget(self.refresh_btn)
        
        current_layout.addLayout(current_header)
        
        # Список текущих паттернов
        self.current_patterns_area = QScrollArea()
        self.current_patterns_area.setWidgetResizable(True)
        
        self.current_patterns_widget = QWidget()
        self.current_patterns_layout = QVBoxLayout(self.current_patterns_widget)
        self.current_patterns_layout.addStretch()
        
        self.current_patterns_area.setWidget(self.current_patterns_widget)
        current_layout.addWidget(self.current_patterns_area)
        
        tab_widget.addTab(current_tab, "Текущие")
        
        # Вкладка истории
        self.history_widget = PatternHistoryWidget()
        tab_widget.addTab(self.history_widget, "История")
        
        # Вкладка статистики
        self.stats_widget = PatternStatsWidget()
        tab_widget.addTab(self.stats_widget, "Статистика")
        
        layout.addWidget(tab_widget)
    
    def set_board_position(self, board: chess.Board):
        """Установить позицию на доске и обнаружить паттерны"""
        try:
            # Обнаружить паттерны в текущей позиции
            matches = self.pattern_detector.detect_patterns_in_position(
                board, max_patterns=10, include_exchanges=True
            )
            
            self.current_matches = matches
            self._update_current_patterns()
            
            # Добавить в историю, если есть значимые паттерны
            significant_matches = [m for m in matches if m.confidence > 0.6]
            if significant_matches:
                self.history_widget.add_pattern_matches(significant_matches)
                self.stats_widget.update_stats(self.history_widget.pattern_history)
            
        except Exception as e:
            print(f"Error detecting patterns: {e}")
    
    def refresh_patterns(self):
        """Обновить паттерны (перезагрузить менеджер паттернов)"""
        self.pattern_detector.pattern_manager.load_all_patterns()
        # Можно добавить сигнал для обновления позиции
    
    def _update_current_patterns(self):
        """Обновить отображение текущих паттернов"""
        # Очистить текущие виджеты
        for i in reversed(range(self.current_patterns_layout.count())):
            child = self.current_patterns_layout.itemAt(i).widget()
            if child and isinstance(child, PatternMatchItem):
                child.setParent(None)
        
        # Добавить новые виджеты
        for match in self.current_matches:
            item_widget = PatternMatchItem(match)
            
            # Добавить кнопку применения
            apply_layout = QHBoxLayout()
            apply_layout.addStretch()
            
            if match.suggested_move:
                apply_btn = QPushButton("Применить")
                apply_btn.clicked.connect(
                    lambda checked, move=match.suggested_move: self.pattern_selected.emit(move)
                )
                apply_btn.setMaximumWidth(80)
                apply_layout.addWidget(apply_btn)
            
            item_widget.layout().addLayout(apply_layout)
            
            self.current_patterns_layout.insertWidget(
                self.current_patterns_layout.count() - 1, item_widget
            )
    
    def get_pattern_manager(self) -> PatternManager:
        """Получить менеджер паттернов"""
        return self.pattern_detector.pattern_manager
    
    def set_pattern_manager(self, manager: PatternManager):
        """Установить менеджер паттернов"""
        self.pattern_detector.pattern_manager = manager
    
    def get_current_matches(self) -> List[PatternMatch]:
        """Получить текущие совпадения паттернов"""
        return self.current_matches
    
    def clear_all(self):
        """Очистить все данные"""
        self.current_matches.clear()
        self._update_current_patterns()
        self.history_widget.clear_history()
        self.stats_widget.update_stats([])


class GameControlsWidget(QWidget):
    """Виджет с кнопками управления игрой"""
    
    # Сигналы для управления игрой
    start_game = Signal()
    stop_game = Signal()
    reset_game = Signal()
    refresh_game = Signal()
    new_game = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game_running = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QHBoxLayout(self)
        
        # Кнопка Start/Stop
        self.start_stop_btn = QPushButton("Start")
        self.start_stop_btn.clicked.connect(self._toggle_game)
        self.start_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.start_stop_btn)
        
        # Кнопка Reset
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_game)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
        """)
        layout.addWidget(self.reset_btn)
        
        # Кнопка New Game
        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.clicked.connect(self._new_game)
        self.new_game_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a6bc1;
            }
        """)
        layout.addWidget(self.new_game_btn)
        
        # Кнопка Refresh
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_game)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """)
        layout.addWidget(self.refresh_btn)
        
        layout.addStretch()
        
        # Индикатор статуса
        self.status_label = QLabel("Готов к игре")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def _toggle_game(self):
        """Переключить состояние игры"""
        if self.game_running:
            self._stop_game()
        else:
            self._start_game()
    
    def _start_game(self):
        """Запустить игру"""
        self.game_running = True
        self.start_stop_btn.setText("Stop")
        self.start_stop_btn.setStyleSheet(self.start_stop_btn.styleSheet().replace("#4CAF50", "#f44336"))
        self.status_label.setText("Игра запущена")
        self.start_game.emit()
    
    def _stop_game(self):
        """Остановить игру"""
        self.game_running = False
        self.start_stop_btn.setText("Start")
        self.start_stop_btn.setStyleSheet(self.start_stop_btn.styleSheet().replace("#f44336", "#4CAF50"))
        self.status_label.setText("Игра остановлена")
        self.stop_game.emit()
    
    def _reset_game(self):
        """Сбросить игру"""
        if self.game_running:
            self._stop_game()
        self.status_label.setText("Игра сброшена")
        self.reset_game.emit()
    
    def _new_game(self):
        """Начать новую игру"""
        if self.game_running:
            self._stop_game()
        self.status_label.setText("Новая игра")
        self.new_game.emit()
    
    def _refresh_game(self):
        """Обновить игру"""
        self.status_label.setText("Обновление...")
        self.refresh_game.emit()
        
        # Сбросить статус через секунду
        QTimer.singleShot(1000, lambda: self.status_label.setText(
            "Игра запущена" if self.game_running else "Готов к игре"
        ))
    
    def set_game_status(self, running: bool, status_text: str = ""):
        """Установить статус игры"""
        self.game_running = running
        
        if running:
            self.start_stop_btn.setText("Stop")
            self.start_stop_btn.setStyleSheet(self.start_stop_btn.styleSheet().replace("#4CAF50", "#f44336"))
        else:
            self.start_stop_btn.setText("Start")
            self.start_stop_btn.setStyleSheet(self.start_stop_btn.styleSheet().replace("#f44336", "#4CAF50"))
        
        if status_text:
            self.status_label.setText(status_text)
        else:
            self.status_label.setText("Игра запущена" if running else "Готов к игре")
