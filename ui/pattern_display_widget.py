"""
Pattern Display Widget
=====================

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