#!/usr/bin/env python3
"""
Enhanced Pattern Viewer - Комплексный инструмент для просмотра и редактирования шахматных паттернов

Объединяет функциональность:
- Просмотр паттернов с визуализацией доски
- Редактирование паттернов с интерактивной доской
- Фильтрацию, поиск и импорт/экспорт
- Интеграцию с турнирными паттернами
"""

import sys
import json
import logging
import chess
import chess.svg
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea, QTextEdit, QSplitter, QMainWindow, QTabWidget,
    QProgressBar, QSlider, QSpinBox, QComboBox, QGroupBox, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout, QFrame,
    QFileDialog, QMenuBar, QStatusBar, QToolBar, QAction
)
from PySide6.QtCore import QTimer, QRect, Qt, QSettings, Signal, QThread, pyqtSignal
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap, QFont, QBrush, QIcon
from PySide6.QtCore import QStandardPaths

# Импорты системы паттернов
from chess_ai.enhanced_pattern_system import (
    PatternManager, ChessPatternEnhanced, PatternCategory,
    ExchangeType, PatternPiece, ExchangeSequence, create_default_patterns
)
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector, PatternMatch
from chess_ai.pattern_manager import PatternManager as LegacyPatternManager

logger = logging.getLogger(__name__)


class ChessBoardWidget(QWidget):
    """Виджет шахматной доски с интерактивными возможностями"""
    
    square_clicked = Signal(str)  # Координаты нажатой клетки
    move_made = Signal(str)       # Сделанный ход в UCI формате
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.selected_square = None
        self.highlighted_squares = []
        self.arrow_moves = []
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)
        
    def set_position(self, fen: str):
        """Установить позицию по FEN"""
        try:
            self.board = chess.Board(fen)
            self.update()
        except ValueError as e:
            logger.error(f"Invalid FEN: {fen}, error: {e}")
            
    def set_highlighted_squares(self, squares: List[str]):
        """Установить подсвеченные клетки"""
        self.highlighted_squares = squares
        self.update()
        
    def set_arrows(self, moves: List[Tuple[str, str]]):
        """Установить стрелки ходов"""
        self.arrow_moves = moves
        self.update()
        
    def paintEvent(self, event):
        """Отрисовка доски"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Размеры
        board_size = min(self.width(), self.height())
        square_size = board_size // 8
        offset_x = (self.width() - board_size) // 2
        offset_y = (self.height() - board_size) // 2
        
        # Цвета клеток
        light_color = QColor(240, 217, 181)
        dark_color = QColor(181, 136, 99)
        highlight_color = QColor(255, 255, 0, 128)
        selected_color = QColor(0, 255, 0, 128)
        
        # Отрисовка клеток
        for row in range(8):
            for col in range(8):
                x = offset_x + col * square_size
                y = offset_y + (7 - row) * square_size
                
                # Определение цвета клетки
                is_light = (row + col) % 2 == 0
                color = light_color if is_light else dark_color
                
                # Подсветка
                square = chess.square_name(col, 7 - row)
                if square == self.selected_square:
                    painter.fillRect(x, y, square_size, square_size, selected_color)
                elif square in self.highlighted_squares:
                    painter.fillRect(x, y, square_size, square_size, highlight_color)
                else:
                    painter.fillRect(x, y, square_size, square_size, color)
                
                # Координаты по краям
                if col == 0:
                    painter.drawText(x + 2, y + square_size - 2, str(8 - row))
                if row == 7:
                    painter.drawText(x + square_size - 15, y + square_size - 2, chr(ord('a') + col))
        
        # Отрисовка фигур (упрощенно)
        self._draw_pieces(painter, offset_x, offset_y, square_size)
        
        # Отрисовка стрелок
        self._draw_arrows(painter, offset_x, offset_y, square_size)
        
    def _draw_pieces(self, painter, offset_x, offset_y, square_size):
        """Отрисовка фигур"""
        piece_symbols = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
        
        font = QFont("Arial", square_size // 2)
        painter.setFont(font)
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = chess.square_rank(square)
                x = offset_x + col * square_size
                y = offset_y + (7 - row) * square_size
                
                symbol = piece_symbols.get(piece.symbol(), '?')
                color = QColor(0, 0, 0) if piece.color else QColor(255, 255, 255)
                painter.setPen(color)
                painter.drawText(x, y, square_size, square_size, Qt.AlignCenter, symbol)
                
    def _draw_arrows(self, painter, offset_x, offset_y, square_size):
        """Отрисовка стрелок ходов"""
        pen = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen)
        
        for from_sq, to_sq in self.arrow_moves:
            from_file = chess.square_file(from_sq)
            from_rank = chess.square_rank(from_sq)
            to_file = chess.square_file(to_sq)
            to_rank = chess.square_rank(to_sq)
            
            from_x = offset_x + from_file * square_size + square_size // 2
            from_y = offset_y + (7 - from_rank) * square_size + square_size // 2
            to_x = offset_x + to_file * square_size + square_size // 2
            to_y = offset_y + (7 - to_rank) * square_size + square_size // 2
            
            painter.drawLine(from_x, from_y, to_x, to_y)
            
    def mousePressEvent(self, event):
        """Обработка нажатия мыши"""
        if event.button() == Qt.LeftButton:
            board_size = min(self.width(), self.height())
            square_size = board_size // 8
            offset_x = (self.width() - board_size) // 2
            offset_y = (self.height() - board_size) // 2
            
            x = event.x() - offset_x
            y = event.y() - offset_y
            
            if 0 <= x < board_size and 0 <= y < board_size:
                col = x // square_size
                row = 7 - (y // square_size)
                
                if 0 <= col < 8 and 0 <= row < 8:
                    square = chess.square_name(col, row)
                    self._handle_square_click(square)
                    
    def _handle_square_click(self, square: str):
        """Обработка клика по клетке"""
        if self.selected_square is None:
            # Первое нажатие - выбор фигуры
            piece = self.board.piece_at(chess.parse_square(square))
            if piece:
                self.selected_square = square
                self.square_clicked.emit(square)
        else:
            # Второе нажатие - попытка хода
            try:
                move = chess.Move.from_uci(self.selected_square + square)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.move_made.emit(move.uci())
                    self.selected_square = None
                else:
                    # Недопустимый ход, выбираем новую клетку
                    piece = self.board.piece_at(chess.parse_square(square))
                    if piece:
                        self.selected_square = square
                        self.square_clicked.emit(square)
                    else:
                        self.selected_square = None
            except ValueError:
                self.selected_square = None
                
        self.update()


class PatternListWidget(QListWidget):
    """Список паттернов с улучшенной функциональностью"""
    
    pattern_selected = Signal(str)  # ID выбранного паттерна
    pattern_double_clicked = Signal(str)  # ID паттерна при двойном клике
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patterns: Dict[str, ChessPatternEnhanced] = {}
        self.setAlternatingRowColors(True)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
    def update_patterns(self, patterns: Dict[str, ChessPatternEnhanced]):
        """Обновить список паттернов"""
        self.clear()
        self.patterns = patterns
        
        for pattern_id, pattern in patterns.items():
            # Формирование текста элемента
            item_text = f"{pattern.name}"
            
            # Добавление категории
            if hasattr(pattern, 'category') and pattern.category:
                item_text += f" [{pattern.category.value}]"
            
            # Добавление статуса
            if hasattr(pattern, 'enabled') and not pattern.enabled:
                item_text += " [DISABLED]"
                
            # Добавление хода
            if hasattr(pattern, 'key_move') and pattern.key_move:
                item_text += f" - {pattern.key_move}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, pattern_id)
            
            # Цветовое кодирование по категориям
            if hasattr(pattern, 'category') and pattern.category:
                if pattern.category == PatternCategory.TACTICAL:
                    item.setBackground(QColor(255, 200, 200))
                elif pattern.category == PatternCategory.OPENING:
                    item.setBackground(QColor(200, 255, 200))
                elif pattern.category == PatternCategory.ENDGAME:
                    item.setBackground(QColor(200, 200, 255))
                elif pattern.category == PatternCategory.EXCHANGE:
                    item.setBackground(QColor(255, 255, 200))
                elif pattern.category == PatternCategory.ATTACK:
                    item.setBackground(QColor(255, 150, 150))
                elif pattern.category == PatternCategory.DEFENSIVE:
                    item.setBackground(QColor(150, 150, 255))
            
            # Серый цвет для отключенных паттернов
            if hasattr(pattern, 'enabled') and not pattern.enabled:
                item.setForeground(QColor(128, 128, 128))
            
            self.addItem(item)
            
    def _on_item_clicked(self, item: QListWidgetItem):
        """Обработать клик по элементу"""
        pattern_id = item.data(Qt.UserRole)
        if pattern_id:
            self.pattern_selected.emit(pattern_id)
            
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Обработать двойной клик по элементу"""
        pattern_id = item.data(Qt.UserRole)
        if pattern_id:
            self.pattern_double_clicked.emit(pattern_id)


class PatternEditWidget(QWidget):
    """Виджет для редактирования паттерна"""
    
    pattern_modified = Signal(str)  # ID измененного паттерна
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pattern: Optional[ChessPatternEnhanced] = None
        self.pattern_manager: Optional[PatternManager] = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        
        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Основная информация
        basic_group = self._create_basic_info_group()
        content_layout.addWidget(basic_group)
        
        # Позиция и ходы
        position_group = self._create_position_group()
        content_layout.addWidget(position_group)
        
        # Фигуры
        pieces_group = self._create_pieces_group()
        content_layout.addWidget(pieces_group)
        
        # Метаданные
        metadata_group = self._create_metadata_group()
        content_layout.addWidget(metadata_group)
        
        # Кнопки
        buttons_group = self._create_buttons_group()
        content_layout.addWidget(buttons_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
    def _create_basic_info_group(self) -> QGroupBox:
        """Создать группу основной информации"""
        group = QGroupBox("Basic Information")
        layout = QFormLayout(group)
        
        # ID (только для чтения)
        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        layout.addRow("ID:", self.id_edit)
        
        # Название
        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        layout.addRow("Description:", self.description_edit)
        
        # Категория
        self.category_combo = QComboBox()
        for category in PatternCategory:
            self.category_combo.addItem(category.value, category)
        layout.addRow("Category:", self.category_combo)
        
        return group
        
    def _create_position_group(self) -> QGroupBox:
        """Создать группу позиции и ходов"""
        group = QGroupBox("Position & Moves")
        layout = QGridLayout(group)
        
        # FEN
        layout.addWidget(QLabel("FEN:"), 0, 0)
        self.fen_edit = QTextEdit()
        self.fen_edit.setMaximumHeight(60)
        layout.addWidget(self.fen_edit, 0, 1, 1, 2)
        
        # Кнопки для FEN
        self.load_fen_btn = QPushButton("Load Position")
        self.clear_fen_btn = QPushButton("Clear")
        layout.addWidget(self.load_fen_btn, 1, 1)
        layout.addWidget(self.clear_fen_btn, 1, 2)
        
        # Ключевой ход
        layout.addWidget(QLabel("Key Move:"), 2, 0)
        self.key_move_edit = QLineEdit()
        layout.addWidget(self.key_move_edit, 2, 1)
        
        # Альтернативные ходы
        layout.addWidget(QLabel("Alternative Moves:"), 3, 0)
        self.alt_moves_edit = QTextEdit()
        self.alt_moves_edit.setMaximumHeight(60)
        layout.addWidget(self.alt_moves_edit, 3, 1, 1, 2)
        
        return group
        
    def _create_pieces_group(self) -> QGroupBox:
        """Создать группу фигур"""
        group = QGroupBox("Pieces")
        layout = QVBoxLayout(group)
        
        # Участвующие фигуры
        participating_frame = QFrame()
        participating_layout = QVBoxLayout(participating_frame)
        participating_layout.addWidget(QLabel("Participating Pieces:"))
        self.participating_edit = QTextEdit()
        self.participating_edit.setMaximumHeight(80)
        participating_layout.addWidget(self.participating_edit)
        layout.addWidget(participating_frame)
        
        # Исключенные фигуры
        excluded_frame = QFrame()
        excluded_layout = QVBoxLayout(excluded_frame)
        excluded_layout.addWidget(QLabel("Excluded Pieces (squares):"))
        self.excluded_edit = QTextEdit()
        self.excluded_edit.setMaximumHeight(60)
        excluded_layout.addWidget(self.excluded_edit)
        layout.addWidget(excluded_frame)
        
        return group
        
    def _create_metadata_group(self) -> QGroupBox:
        """Создать группу метаданных"""
        group = QGroupBox("Metadata")
        layout = QFormLayout(group)
        
        # Частота
        self.frequency_spin = QDoubleSpinBox()
        self.frequency_spin.setRange(0.0, 10.0)
        self.frequency_spin.setSingleStep(0.1)
        self.frequency_spin.setValue(1.0)
        layout.addRow("Frequency:", self.frequency_spin)
        
        # Успешность
        self.success_rate_spin = QDoubleSpinBox()
        self.success_rate_spin.setRange(0.0, 1.0)
        self.success_rate_spin.setSingleStep(0.01)
        self.success_rate_spin.setValue(0.5)
        layout.addRow("Success Rate:", self.success_rate_spin)
        
        # Диапазон ELO
        elo_layout = QHBoxLayout()
        self.min_elo_spin = QSpinBox()
        self.min_elo_spin.setRange(0, 4000)
        self.min_elo_spin.setValue(800)
        self.max_elo_spin = QSpinBox()
        self.max_elo_spin.setRange(0, 4000)
        self.max_elo_spin.setValue(2800)
        elo_layout.addWidget(self.min_elo_spin)
        elo_layout.addWidget(QLabel("-"))
        elo_layout.addWidget(self.max_elo_spin)
        layout.addRow("ELO Range:", elo_layout)
        
        # Фаза игры
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(["any", "opening", "middlegame", "endgame"])
        layout.addRow("Game Phase:", self.phase_combo)
        
        # Теги
        self.tags_edit = QLineEdit()
        layout.addRow("Tags (comma separated):", self.tags_edit)
        
        return group
        
    def _create_buttons_group(self) -> QGroupBox:
        """Создать группу кнопок"""
        group = QGroupBox()
        layout = QHBoxLayout(group)
        
        self.save_btn = QPushButton("Save Pattern")
        self.save_btn.clicked.connect(self._save_pattern)
        layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset_form)
        layout.addWidget(self.reset_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_pattern)
        layout.addWidget(self.delete_btn)
        
        layout.addStretch()
        return group
        
    def set_pattern(self, pattern: ChessPatternEnhanced):
        """Установить паттерн для редактирования"""
        self.current_pattern = pattern
        
        # Заполнение полей
        self.id_edit.setText(pattern.id)
        self.name_edit.setText(pattern.name)
        self.description_edit.setPlainText(pattern.description)
        
        # Категория
        if pattern.category:
            index = self.category_combo.findData(pattern.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        
        # Позиция
        self.fen_edit.setPlainText(pattern.fen)
        self.key_move_edit.setText(pattern.key_move or "")
        
        if pattern.alternative_moves:
            alt_text = ", ".join(pattern.alternative_moves)
            self.alt_moves_edit.setPlainText(alt_text)
        
        # Фигуры
        if pattern.participating_pieces:
            pieces_text = json.dumps([asdict(p) for p in pattern.participating_pieces], indent=2)
            self.participating_edit.setPlainText(pieces_text)
        
        if pattern.excluded_pieces:
            excluded_text = ", ".join(pattern.excluded_pieces)
            self.excluded_edit.setPlainText(excluded_text)
        
        # Метаданные
        self.frequency_spin.setValue(pattern.frequency)
        self.success_rate_spin.setValue(pattern.success_rate)
        
        if pattern.elo_range:
            self.min_elo_spin.setValue(pattern.elo_range[0])
            self.max_elo_spin.setValue(pattern.elo_range[1])
        
        self.phase_combo.setCurrentText(pattern.game_phase)
        
        if pattern.tags:
            self.tags_edit.setText(", ".join(pattern.tags))
            
    def _save_pattern(self):
        """Сохранить паттерн"""
        if not self.current_pattern or not self.pattern_manager:
            return
            
        try:
            # Обновление полей
            self.current_pattern.name = self.name_edit.text()
            self.current_pattern.description = self.description_edit.toPlainText()
            self.current_pattern.category = self.category_combo.currentData()
            self.current_pattern.fen = self.fen_edit.toPlainText().strip()
            self.current_pattern.key_move = self.key_move_edit.text().strip()
            
            # Альтернативные ходы
            alt_text = self.alt_moves_edit.toPlainText().strip()
            if alt_text:
                self.current_pattern.alternative_moves = [m.strip() for m in alt_text.split(",")]
            else:
                self.current_pattern.alternative_moves = []
            
            # Частота и успешность
            self.current_pattern.frequency = self.frequency_spin.value()
            self.current_pattern.success_rate = self.success_rate_spin.value()
            self.current_pattern.elo_range = (self.min_elo_spin.value(), self.max_elo_spin.value())
            self.current_pattern.game_phase = self.phase_combo.currentText()
            
            # Теги
            tags_text = self.tags_edit.text().strip()
            if tags_text:
                self.current_pattern.tags = [t.strip() for t in tags_text.split(",")]
            else:
                self.current_pattern.tags = []
            
            # Сохранение через менеджер
            self.pattern_manager.save_pattern(self.current_pattern)
            
            # Сигнал об изменении
            self.pattern_modified.emit(self.current_pattern.id)
            
            QMessageBox.information(self, "Success", "Pattern saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save pattern: {str(e)}")
            
    def _reset_form(self):
        """Сбросить форму"""
        if self.current_pattern:
            self.set_pattern(self.current_pattern)
            
    def _delete_pattern(self):
        """Удалить паттерн"""
        if not self.current_pattern or not self.pattern_manager:
            return
            
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete pattern '{self.current_pattern.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.pattern_manager.delete_pattern(self.current_pattern.id)
                self.pattern_modified.emit(self.current_pattern.id)
                self.current_pattern = None
                self._clear_form()
                QMessageBox.information(self, "Success", "Pattern deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete pattern: {str(e)}")
                
    def _clear_form(self):
        """Очистить форму"""
        self.id_edit.clear()
        self.name_edit.clear()
        self.description_edit.clear()
        self.fen_edit.clear()
        self.key_move_edit.clear()
        self.alt_moves_edit.clear()
        self.participating_edit.clear()
        self.excluded_edit.clear()
        self.tags_edit.clear()
        
        # Сброс значений по умолчанию
        self.frequency_spin.setValue(1.0)
        self.success_rate_spin.setValue(0.5)
        self.min_elo_spin.setValue(800)
        self.max_elo_spin.setValue(2800)
        self.phase_combo.setCurrentText("any")


class EnhancedPatternViewer(QMainWindow):
    """Главное окно улучшенного Pattern Viewer"""
    
    def __init__(self):
        super().__init__()
        self.pattern_manager = PatternManager()
        self.legacy_manager = LegacyPatternManager()
        self.current_patterns: Dict[str, ChessPatternEnhanced] = {}
        self.setup_ui()
        self.load_patterns()
        
    def setup_ui(self):
        """Настроить интерфейс"""
        self.setWindowTitle("Enhanced Chess Pattern Viewer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(central_widget)
        
        # Создание сплиттера
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - список паттернов
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель - детали и редактирование
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Установка пропорций
        splitter.setSizes([400, 1000])
        main_layout.addWidget(splitter)
        
        # Создание меню
        self._create_menu_bar()
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def _create_left_panel(self) -> QWidget:
        """Создать левую панель"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Панель управления
        control_group = QGroupBox("Pattern Controls")
        control_layout = QVBoxLayout(control_group)
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._filter_patterns)
        search_layout.addWidget(self.search_edit)
        control_layout.addLayout(search_layout)
        
        # Фильтр по категории
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        for category in PatternCategory:
            self.category_filter.addItem(category.value, category)
        self.category_filter.currentTextChanged.connect(self._filter_patterns)
        filter_layout.addWidget(self.category_filter)
        control_layout.addLayout(filter_layout)
        
        # Чекбоксы
        self.enabled_only_cb = QCheckBox("Enabled Only")
        self.enabled_only_cb.toggled.connect(self._filter_patterns)
        control_layout.addWidget(self.enabled_only_cb)
        
        self.tournament_only_cb = QCheckBox("Tournament Patterns Only")
        self.tournament_only_cb.toggled.connect(self._filter_patterns)
        control_layout.addWidget(self.tournament_only_cb)
        
        layout.addWidget(control_group)
        
        # Список паттернов
        list_group = QGroupBox("Patterns")
        list_layout = QVBoxLayout(list_group)
        
        self.pattern_list = PatternListWidget()
        self.pattern_list.pattern_selected.connect(self._on_pattern_selected)
        self.pattern_list.pattern_double_clicked.connect(self._on_pattern_double_clicked)
        list_layout.addWidget(self.pattern_list)
        
        # Кнопки управления списком
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_patterns)
        btn_layout.addWidget(self.refresh_btn)
        
        self.new_pattern_btn = QPushButton("New Pattern")
        self.new_pattern_btn.clicked.connect(self._create_new_pattern)
        btn_layout.addWidget(self.new_pattern_btn)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self._import_patterns)
        btn_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._export_patterns)
        btn_layout.addWidget(self.export_btn)
        
        list_layout.addLayout(btn_layout)
        layout.addWidget(list_group)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Создать правую панель"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Таб виджет
        self.tab_widget = QTabWidget()
        
        # Таб просмотра
        self.view_tab = self._create_view_tab()
        self.tab_widget.addTab(self.view_tab, "View")
        
        # Таб редактирования
        self.edit_tab = self._create_edit_tab()
        self.tab_widget.addTab(self.edit_tab, "Edit")
        
        # Таб тестирования
        self.test_tab = self._create_test_tab()
        self.tab_widget.addTab(self.test_tab, "Test")
        
        layout.addWidget(self.tab_widget)
        
        return panel
        
    def _create_view_tab(self) -> QWidget:
        """Создать таб просмотра"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Доска
        board_group = QGroupBox("Board")
        board_layout = QVBoxLayout(board_group)
        
        self.board_widget = ChessBoardWidget()
        board_layout.addWidget(self.board_widget)
        
        # Информация о позиции
        self.position_info = QLabel("Select a pattern to view position")
        board_layout.addWidget(self.position_info)
        
        layout.addWidget(board_group)
        
        # Детали паттерна
        details_group = QGroupBox("Pattern Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_group)
        
        return tab
        
    def _create_edit_tab(self) -> QWidget:
        """Создать таб редактирования"""
        self.edit_widget = PatternEditWidget()
        self.edit_widget.pattern_modified.connect(self._on_pattern_modified)
        return self.edit_widget
        
    def _create_test_tab(self) -> QWidget:
        """Создать таб тестирования"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Панель тестирования
        test_group = QGroupBox("Pattern Testing")
        test_layout = QVBoxLayout(test_group)
        
        # Кнопки тестирования
        btn_layout = QHBoxLayout()
        
        self.test_current_btn = QPushButton("Test on Current Position")
        self.test_current_btn.clicked.connect(self._test_current_position)
        btn_layout.addWidget(self.test_current_btn)
        
        self.test_random_btn = QPushButton("Test Random Games")
        self.test_random_btn.clicked.connect(self._test_random_games)
        btn_layout.addWidget(self.test_random_btn)
        
        self.test_load_btn = QPushButton("Load Test Games")
        self.test_load_btn.clicked.connect(self._load_test_games)
        btn_layout.addWidget(self.test_load_btn)
        
        test_layout.addLayout(btn_layout)
        
        # Результаты тестирования
        self.test_results = QTextEdit()
        self.test_results.setReadOnly(True)
        test_layout.addWidget(self.test_results)
        
        layout.addWidget(test_group)
        
        return tab
        
    def _create_menu_bar(self):
        """Создать меню"""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Pattern", self)
        new_action.triggered.connect(self._create_new_pattern)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Pattern File", self)
        open_action.triggered.connect(self._open_pattern_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Pattern File", self)
        save_action.triggered.connect(self._save_pattern_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Редактировать
        edit_menu = menubar.addMenu("Edit")
        
        import_action = QAction("Import Patterns", self)
        import_action.triggered.connect(self._import_patterns)
        edit_menu.addAction(import_action)
        
        export_action = QAction("Export Patterns", self)
        export_action.triggered.connect(self._export_patterns)
        edit_menu.addAction(export_action)
        
        # Инструменты
        tools_menu = menubar.addMenu("Tools")
        
        validate_action = QAction("Validate All Patterns", self)
        validate_action.triggered.connect(self._validate_all_patterns)
        tools_menu.addAction(validate_action)
        
        stats_action = QAction("Pattern Statistics", self)
        stats_action.triggered.connect(self._show_statistics)
        tools_menu.addAction(stats_action)
        
    def load_patterns(self):
        """Загрузить паттерны"""
        try:
            # Загрузка улучшенных паттернов
            self.current_patterns = self.pattern_manager.load_all_patterns()
            
            # Загрузка легаси паттернов
            try:
                legacy_patterns = self.legacy_manager.load_patterns()
                # Конвертация в новый формат (упрощенно)
                for pattern_id, pattern_data in legacy_patterns.items():
                    if pattern_id not in self.current_patterns:
                        # Базовая конвертация
                        enhanced_pattern = ChessPatternEnhanced(
                            id=pattern_id,
                            name=pattern_data.get('name', pattern_id),
                            description=pattern_data.get('description', ''),
                            category=PatternCategory.TACTICAL,  # По умолчанию
                            fen=pattern_data.get('fen', ''),
                            key_move=pattern_data.get('move', ''),
                            created_at=datetime.now().isoformat()
                        )
                        self.current_patterns[pattern_id] = enhanced_pattern
            except Exception as e:
                logger.warning(f"Failed to load legacy patterns: {e}")
            
            # Обновление списка
            self.pattern_list.update_patterns(self.current_patterns)
            
            # Обновление статуса
            count = len(self.current_patterns)
            self.status_bar.showMessage(f"Loaded {count} patterns")
            
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load patterns: {str(e)}")
            
    def _filter_patterns(self):
        """Отфильтровать паттерны"""
        search_text = self.search_edit.text().lower()
        category_filter = self.category_filter.currentData()
        enabled_only = self.enabled_only_cb.isChecked()
        tournament_only = self.tournament_only_cb.isChecked()
        
        filtered_patterns = {}
        
        for pattern_id, pattern in self.current_patterns.items():
            # Поиск по тексту
            if search_text:
                if (search_text not in pattern.name.lower() and 
                    search_text not in pattern.description.lower()):
                    continue
            
            # Фильтр по категории
            if category_filter and pattern.category != category_filter:
                continue
                
            # Только включенные
            if enabled_only and hasattr(pattern, 'enabled') and not pattern.enabled:
                continue
                
            # Только турнирные (упрощенная проверка)
            if tournament_only and 'tournament' not in pattern.tags:
                continue
                
            filtered_patterns[pattern_id] = pattern
            
        self.pattern_list.update_patterns(filtered_patterns)
        
    def _on_pattern_selected(self, pattern_id: str):
        """Обработать выбор паттерна"""
        if pattern_id in self.current_patterns:
            pattern = self.current_patterns[pattern_id]
            
            # Обновление доски
            self.board_widget.set_position(pattern.fen)
            
            # Подсветка ключевых полей
            highlighted = []
            if pattern.key_move:
                try:
                    move = chess.Move.from_uci(pattern.key_move)
                    highlighted.append(chess.square_name(move.from_square))
                    highlighted.append(chess.square_name(move.to_square))
                    
                    # Добавление стрелки
                    self.board_widget.set_arrows([(move.from_square, move.to_square)])
                except ValueError:
                    pass
                    
            self.board_widget.set_highlighted_squares(highlighted)
            
            # Обновление деталей
            details = self._format_pattern_details(pattern)
            self.details_text.setPlainText(details)
            
            # Обновление редактора
            self.edit_widget.set_pattern(pattern)
            self.edit_widget.pattern_manager = self.pattern_manager
            
            # Информация о позиции
            self.position_info.setText(f"FEN: {pattern.fen}")
            
    def _on_pattern_double_clicked(self, pattern_id: str):
        """Обработать двойной клик по паттерну"""
        # Переключение на таб редактирования
        self.tab_widget.setCurrentIndex(1)
        
    def _on_pattern_modified(self, pattern_id: str):
        """Обработать изменение паттерна"""
        # Перезагрузка паттернов
        self.load_patterns()
        self.status_bar.showMessage(f"Pattern {pattern_id} updated")
        
    def _format_pattern_details(self, pattern: ChessPatternEnhanced) -> str:
        """Отформатировать детали паттерна"""
        details = f"ID: {pattern.id}\n"
        details += f"Name: {pattern.name}\n"
        details += f"Description: {pattern.description}\n"
        details += f"Category: {pattern.category.value if pattern.category else 'None'}\n"
        details += f"FEN: {pattern.fen}\n"
        details += f"Key Move: {pattern.key_move or 'None'}\n"
        
        if pattern.alternative_moves:
            details += f"Alternative Moves: {', '.join(pattern.alternative_moves)}\n"
            
        details += f"\nMetadata:\n"
        details += f"Frequency: {pattern.frequency}\n"
        details += f"Success Rate: {pattern.success_rate}\n"
        details += f"ELO Range: {pattern.elo_range}\n"
        details += f"Game Phase: {pattern.game_phase}\n"
        
        if pattern.tags:
            details += f"Tags: {', '.join(pattern.tags)}\n"
            
        if pattern.created_at:
            details += f"Created: {pattern.created_at}\n"
            
        return details
        
    def _create_new_pattern(self):
        """Создать новый паттерн"""
        # Создание базового паттерна
        new_pattern = ChessPatternEnhanced(
            id=f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="New Pattern",
            description="Enter pattern description",
            category=PatternCategory.TACTICAL,
            fen=chess.Board().fen(),
            key_move="",
            created_at=datetime.now().isoformat()
        )
        
        # Добавление в менеджер
        self.pattern_manager.save_pattern(new_pattern)
        
        # Перезагрузка и выбор
        self.load_patterns()
        self._on_pattern_selected(new_pattern.id)
        
        # Переключение на таб редактирования
        self.tab_widget.setCurrentIndex(1)
        
    def _import_patterns(self):
        """Импортировать паттерны"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Patterns", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Импорт паттернов
                imported_count = 0
                for pattern_data in data.get('patterns', []):
                    try:
                        pattern = ChessPatternEnhanced(**pattern_data)
                        self.pattern_manager.save_pattern(pattern)
                        imported_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to import pattern: {e}")
                        
                self.load_patterns()
                QMessageBox.information(self, "Import Complete", f"Imported {imported_count} patterns")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import patterns: {str(e)}")
                
    def _export_patterns(self):
        """Экспортировать паттерны"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Patterns", "patterns.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                patterns_data = []
                for pattern in self.current_patterns.values():
                    pattern_dict = asdict(pattern)
                    patterns_data.append(pattern_dict)
                    
                export_data = {
                    'version': '1.0',
                    'exported_at': datetime.now().isoformat(),
                    'count': len(patterns_data),
                    'patterns': patterns_data
                }
                
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2)
                    
                QMessageBox.information(self, "Export Complete", f"Exported {len(patterns_data)} patterns")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export patterns: {str(e)}")
                
    def _open_pattern_file(self):
        """Открыть файл паттернов"""
        self._import_patterns()
        
    def _save_pattern_file(self):
        """Сохранить файл паттернов"""
        self._export_patterns()
        
    def _validate_all_patterns(self):
        """Валидировать все паттерны"""
        errors = []
        
        for pattern_id, pattern in self.current_patterns.items():
            try:
                # Проверка FEN
                chess.Board(pattern.fen)
                
                # Проверка хода
                if pattern.key_move:
                    board = chess.Board(pattern.fen)
                    move = chess.Move.from_uci(pattern.key_move)
                    if move not in board.legal_moves:
                        errors.append(f"{pattern_id}: Invalid key move {pattern.key_move}")
                        
            except ValueError as e:
                errors.append(f"{pattern_id}: Invalid FEN - {str(e)}")
                
        if errors:
            error_text = "Validation Errors:\n" + "\n".join(errors[:20])  # Ограничение вывода
            QMessageBox.warning(self, "Validation Results", error_text)
        else:
            QMessageBox.information(self, "Validation Results", "All patterns are valid!")
            
    def _show_statistics(self):
        """Показать статистику"""
        stats = {
            'total_patterns': len(self.current_patterns),
            'categories': {},
            'phases': {},
            'enabled': 0
        }
        
        for pattern in self.current_patterns.values():
            # Категории
            if pattern.category:
                cat_name = pattern.category.value
                stats['categories'][cat_name] = stats['categories'].get(cat_name, 0) + 1
                
            # Фазы игры
            phase = pattern.game_phase
            stats['phases'][phase] = stats['phases'].get(phase, 0) + 1
            
            # Включенные
            if hasattr(pattern, 'enabled') and pattern.enabled:
                stats['enabled'] += 1
                
        # Формирование текста статистики
        stats_text = "Pattern Statistics:\n\n"
        stats_text += f"Total Patterns: {stats['total_patterns']}\n"
        stats_text += f"Enabled: {stats['enabled']}\n\n"
        
        stats_text += "By Category:\n"
        for cat, count in stats['categories'].items():
            stats_text += f"  {cat}: {count}\n"
            
        stats_text += "\nBy Game Phase:\n"
        for phase, count in stats['phases'].items():
            stats_text += f"  {phase}: {count}\n"
            
        QMessageBox.information(self, "Pattern Statistics", stats_text)
        
    def _test_current_position(self):
        """Тестировать на текущей позиции"""
        # Заглушка для тестирования
        self.test_results.append("Testing current position...")
        
    def _test_random_games(self):
        """Тестировать на случайных играх"""
        # Заглушка для тестирования
        self.test_results.append("Testing on random games...")
        
    def _load_test_games(self):
        """Загрузить тестовые игры"""
        # Заглушка для загрузки тестовых игр
        self.test_results.append("Loading test games...")


def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создание и показ главного окна
    viewer = EnhancedPatternViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
