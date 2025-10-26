"""
Pattern Management Widget
========================

Виджет для управления паттернами в PySide6 интерфейсе.
Позволяет просматривать, создавать, редактировать и удалять паттерны.
"""

from __future__ import annotations
import json
import chess
from pathlib import Path
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QDoubleSpinBox, QGroupBox, QTabWidget, QScrollArea,
    QMessageBox, QFileDialog, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox,
    QFormLayout, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from chess_ai.enhanced_pattern_system import (
    PatternManager, ChessPatternEnhanced, PatternCategory,
    ExchangeType, PatternPiece, ExchangeSequence, create_default_patterns
)
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector, PatternMatch


class PatternListWidget(QListWidget):
    """Список паттернов с дополнительной информацией"""
    
    pattern_selected = Signal(str)  # ID выбранного паттерна
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.patterns: Dict[str, ChessPatternEnhanced] = {}
        self.setAlternatingRowColors(True)
        self.itemClicked.connect(self._on_item_clicked)
    
    def update_patterns(self, patterns: Dict[str, ChessPatternEnhanced]):
        """Обновить список паттернов"""
        self.clear()
        self.patterns = patterns
        
        for pattern_id, pattern in patterns.items():
            item_text = f"{pattern.name} ({pattern.category.value})"
            if not pattern.enabled:
                item_text += " [ОТКЛЮЧЕН]"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, pattern_id)
            
            # Цветовое кодирование по категориям
            if pattern.category == PatternCategory.TACTICAL:
                item.setBackground(QColor(255, 200, 200))
            elif pattern.category == PatternCategory.OPENING:
                item.setBackground(QColor(200, 255, 200))
            elif pattern.category == PatternCategory.ENDGAME:
                item.setBackground(QColor(200, 200, 255))
            elif pattern.category == PatternCategory.EXCHANGE:
                item.setBackground(QColor(255, 255, 200))
            
            if not pattern.enabled:
                item.setForeground(QColor(128, 128, 128))
            
            self.addItem(item)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Обработать клик по элементу"""
        pattern_id = item.data(Qt.UserRole)
        if pattern_id:
            self.pattern_selected.emit(pattern_id)


class PatternDetailsWidget(QWidget):
    """Виджет для отображения деталей паттерна"""
    
    pattern_modified = Signal(str)  # ID измененного паттерна
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_pattern: Optional[ChessPatternEnhanced] = None
        self.pattern_manager: Optional[PatternManager] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        self.title_label = QLabel("Выберите паттерн для просмотра")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.title_label)
        
        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        
        # Основная информация
        self._create_basic_info_group()
        
        # Участвующие фигуры
        self._create_pieces_group()
        
        # Размен (если применимо)
        self._create_exchange_group()
        
        # Условия и метаданные
        self._create_metadata_group()
        
        # Кнопки управления
        self._create_control_buttons()
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
    
    def _create_basic_info_group(self):
        """Создать группу основной информации"""
        group = QGroupBox("Основная информация")
        layout = QFormLayout(group)
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Название:", self.name_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([cat.value for cat in PatternCategory])
        self.category_combo.currentTextChanged.connect(self._on_data_changed)
        layout.addRow("Категория:", self.category_combo)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Описание:", self.description_edit)
        
        self.fen_edit = QLineEdit()
        self.fen_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("FEN позиция:", self.fen_edit)
        
        self.key_move_edit = QLineEdit()
        self.key_move_edit.textChanged.connect(self._on_data_changed)
        layout.addRow("Ключевой ход:", self.key_move_edit)
        
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.stateChanged.connect(self._on_data_changed)
        layout.addRow("Включен:", self.enabled_checkbox)
        
        self.scroll_layout.addWidget(group)
    
    def _create_pieces_group(self):
        """Создать группу участвующих фигур"""
        group = QGroupBox("Участвующие фигуры")
        layout = QVBoxLayout(group)
        
        # Таблица фигур
        self.pieces_table = QTableWidget()
        self.pieces_table.setColumnCount(5)
        self.pieces_table.setHorizontalHeaderLabels([
            "Поле", "Фигура", "Цвет", "Роль", "Важность"
        ])
        self.pieces_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pieces_table)
        
        # Кнопки управления фигурами
        pieces_buttons = QHBoxLayout()
        
        self.add_piece_btn = QPushButton("Добавить фигуру")
        self.add_piece_btn.clicked.connect(self._add_piece)
        pieces_buttons.addWidget(self.add_piece_btn)
        
        self.remove_piece_btn = QPushButton("Удалить фигуру")
        self.remove_piece_btn.clicked.connect(self._remove_piece)
        pieces_buttons.addWidget(self.remove_piece_btn)
        
        pieces_buttons.addStretch()
        layout.addLayout(pieces_buttons)
        
        self.scroll_layout.addWidget(group)
    
    def _create_exchange_group(self):
        """Создать группу размена"""
        self.exchange_group = QGroupBox("Размен")
        layout = QFormLayout(self.exchange_group)
        
        self.exchange_type_combo = QComboBox()
        self.exchange_type_combo.addItems(["Нет"] + [ex.value for ex in ExchangeType])
        self.exchange_type_combo.currentTextChanged.connect(self._on_exchange_type_changed)
        layout.addRow("Тип размена:", self.exchange_type_combo)
        
        self.exchange_moves_edit = QLineEdit()
        self.exchange_moves_edit.setPlaceholderText("e4, exd5, Nxd5 (через запятую)")
        layout.addRow("Ходы размена:", self.exchange_moves_edit)
        
        self.material_balance_spin = QSpinBox()
        self.material_balance_spin.setRange(-10, 10)
        layout.addRow("Материальный баланс:", self.material_balance_spin)
        
        self.positional_gain_spin = QDoubleSpinBox()
        self.positional_gain_spin.setRange(-100.0, 100.0)
        self.positional_gain_spin.setSingleStep(0.1)
        layout.addRow("Позиционная выгода:", self.positional_gain_spin)
        
        self.scroll_layout.addWidget(self.exchange_group)
    
    def _create_metadata_group(self):
        """Создать группу метаданных"""
        group = QGroupBox("Метаданные и условия")
        layout = QFormLayout(group)
        
        self.frequency_spin = QDoubleSpinBox()
        self.frequency_spin.setRange(0.0, 1.0)
        self.frequency_spin.setSingleStep(0.1)
        self.frequency_spin.setValue(0.5)
        layout.addRow("Частота:", self.frequency_spin)
        
        self.success_rate_spin = QDoubleSpinBox()
        self.success_rate_spin.setRange(0.0, 1.0)
        self.success_rate_spin.setSingleStep(0.1)
        self.success_rate_spin.setValue(0.5)
        layout.addRow("Процент успеха:", self.success_rate_spin)
        
        self.game_phase_combo = QComboBox()
        self.game_phase_combo.addItems(["any", "opening", "middlegame", "endgame"])
        layout.addRow("Фаза игры:", self.game_phase_combo)
        
        self.elo_min_spin = QSpinBox()
        self.elo_min_spin.setRange(800, 3000)
        self.elo_min_spin.setValue(800)
        layout.addRow("Мин. ELO:", self.elo_min_spin)
        
        self.elo_max_spin = QSpinBox()
        self.elo_max_spin.setRange(800, 3000)
        self.elo_max_spin.setValue(2800)
        layout.addRow("Макс. ELO:", self.elo_max_spin)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tactical, fork, knight (через запятую)")
        layout.addRow("Теги:", self.tags_edit)
        
        self.scroll_layout.addWidget(group)
    
    def _create_control_buttons(self):
        """Создать кнопки управления"""
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self._save_pattern)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Сбросить")
        self.reset_btn.clicked.connect(self._reset_changes)
        self.reset_btn.setEnabled(False)
        buttons_layout.addWidget(self.reset_btn)
        
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self._delete_pattern)
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)
        
        buttons_layout.addStretch()
        
        self.test_btn = QPushButton("Тестировать")
        self.test_btn.clicked.connect(self._test_pattern)
        self.test_btn.setEnabled(False)
        buttons_layout.addWidget(self.test_btn)
        
        self.scroll_layout.addLayout(buttons_layout)
    
    def set_pattern_manager(self, manager: PatternManager):
        """Установить менеджер паттернов"""
        self.pattern_manager = manager
    
    def display_pattern(self, pattern: ChessPatternEnhanced):
        """Отобразить паттерн"""
        self.current_pattern = pattern
        
        # Основная информация
        self.title_label.setText(f"Паттерн: {pattern.name}")
        self.name_edit.setText(pattern.name)
        self.category_combo.setCurrentText(pattern.category.value)
        self.description_edit.setPlainText(pattern.description)
        self.fen_edit.setText(pattern.fen)
        self.key_move_edit.setText(pattern.key_move)
        self.enabled_checkbox.setChecked(pattern.enabled)
        
        # Участвующие фигуры
        self._update_pieces_table()
        
        # Размен
        if pattern.exchange_sequence:
            self.exchange_type_combo.setCurrentText(pattern.exchange_type.value if pattern.exchange_type else "Нет")
            self.exchange_moves_edit.setText(", ".join(pattern.exchange_sequence.moves))
            self.material_balance_spin.setValue(pattern.exchange_sequence.material_balance)
            self.positional_gain_spin.setValue(pattern.exchange_sequence.positional_gain)
        else:
            self.exchange_type_combo.setCurrentText("Нет")
            self.exchange_moves_edit.clear()
            self.material_balance_spin.setValue(0)
            self.positional_gain_spin.setValue(0.0)
        
        # Метаданные
        self.frequency_spin.setValue(pattern.frequency)
        self.success_rate_spin.setValue(pattern.success_rate)
        self.game_phase_combo.setCurrentText(pattern.game_phase)
        self.elo_min_spin.setValue(pattern.elo_range[0])
        self.elo_max_spin.setValue(pattern.elo_range[1])
        self.tags_edit.setText(", ".join(pattern.tags))
        
        # Активировать кнопки
        self.save_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.delete_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
    
    def _update_pieces_table(self):
        """Обновить таблицу фигур"""
        if not self.current_pattern:
            return
        
        pieces = self.current_pattern.participating_pieces
        self.pieces_table.setRowCount(len(pieces))
        
        for i, piece in enumerate(pieces):
            self.pieces_table.setItem(i, 0, QTableWidgetItem(piece.square))
            self.pieces_table.setItem(i, 1, QTableWidgetItem(piece.piece_type))
            self.pieces_table.setItem(i, 2, QTableWidgetItem(piece.color))
            self.pieces_table.setItem(i, 3, QTableWidgetItem(piece.role))
            self.pieces_table.setItem(i, 4, QTableWidgetItem(str(piece.importance)))
    
    def _on_data_changed(self):
        """Обработать изменение данных"""
        self.save_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
    
    def _on_exchange_type_changed(self, exchange_type: str):
        """Обработать изменение типа размена"""
        is_exchange = exchange_type != "Нет"
        self.exchange_moves_edit.setEnabled(is_exchange)
        self.material_balance_spin.setEnabled(is_exchange)
        self.positional_gain_spin.setEnabled(is_exchange)
        self._on_data_changed()
    
    def _add_piece(self):
        """Добавить фигуру"""
        dialog = PieceEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            piece_data = dialog.get_piece_data()
            if piece_data:
                new_piece = PatternPiece(**piece_data)
                self.current_pattern.participating_pieces.append(new_piece)
                self._update_pieces_table()
                self._on_data_changed()
    
    def _remove_piece(self):
        """Удалить выбранную фигуру"""
        current_row = self.pieces_table.currentRow()
        if current_row >= 0 and self.current_pattern:
            del self.current_pattern.participating_pieces[current_row]
            self._update_pieces_table()
            self._on_data_changed()
    
    def _save_pattern(self):
        """Сохранить изменения паттерна"""
        if not self.current_pattern or not self.pattern_manager:
            return
        
        try:
            # Обновить данные паттерна
            self.current_pattern.name = self.name_edit.text()
            self.current_pattern.category = PatternCategory(self.category_combo.currentText())
            self.current_pattern.description = self.description_edit.toPlainText()
            self.current_pattern.fen = self.fen_edit.text()
            self.current_pattern.key_move = self.key_move_edit.text()
            self.current_pattern.enabled = self.enabled_checkbox.isChecked()
            
            # Обновить размен
            exchange_type = self.exchange_type_combo.currentText()
            if exchange_type != "Нет":
                moves = [m.strip() for m in self.exchange_moves_edit.text().split(",") if m.strip()]
                self.current_pattern.exchange_type = ExchangeType(exchange_type)
                self.current_pattern.exchange_sequence = ExchangeSequence(
                    moves=moves,
                    material_balance=self.material_balance_spin.value(),
                    positional_gain=self.positional_gain_spin.value(),
                    evaluation_change=self.material_balance_spin.value() * 100 + self.positional_gain_spin.value(),
                    probability=0.8
                )
            else:
                self.current_pattern.exchange_type = None
                self.current_pattern.exchange_sequence = None
            
            # Обновить метаданные
            self.current_pattern.frequency = self.frequency_spin.value()
            self.current_pattern.success_rate = self.success_rate_spin.value()
            self.current_pattern.game_phase = self.game_phase_combo.currentText()
            self.current_pattern.elo_range = (self.elo_min_spin.value(), self.elo_max_spin.value())
            self.current_pattern.tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]
            
            # Сохранить в файл
            if self.pattern_manager.save_pattern(self.current_pattern):
                QMessageBox.information(self, "Успех", "Паттерн успешно сохранен!")
                self.save_btn.setEnabled(False)
                self.reset_btn.setEnabled(False)
                self.pattern_modified.emit(self.current_pattern.id)
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить паттерн!")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {e}")
    
    def _reset_changes(self):
        """Сбросить изменения"""
        if self.current_pattern:
            self.display_pattern(self.current_pattern)
    
    def _delete_pattern(self):
        """Удалить паттерн"""
        if not self.current_pattern or not self.pattern_manager:
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить паттерн '{self.current_pattern.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.pattern_manager.delete_pattern(self.current_pattern.id):
                QMessageBox.information(self, "Успех", "Паттерн удален!")
                self.pattern_modified.emit(self.current_pattern.id)
                self.current_pattern = None
                self.title_label.setText("Выберите паттерн для просмотра")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить паттерн!")
    
    def _test_pattern(self):
        """Тестировать паттерн"""
        if not self.current_pattern:
            return
        
        try:
            # Создать доску из FEN
            board = chess.Board(self.current_pattern.fen)
            
            # Создать детектор и протестировать
            detector = EnhancedPatternDetector()
            detector.pattern_manager.patterns[self.current_pattern.id] = self.current_pattern
            
            matches = detector.detect_patterns_in_position(board, max_patterns=1)
            
            if matches:
                match = matches[0]
                message = f"Паттерн обнаружен!\n\n"
                message += f"Уверенность: {match.confidence:.2f}\n"
                message += f"Предлагаемый ход: {match.suggested_move}\n"
                message += f"Объяснение: {match.explanation}"
                QMessageBox.information(self, "Результат теста", message)
            else:
                QMessageBox.information(self, "Результат теста", "Паттерн не обнаружен в данной позиции.")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка теста", f"Ошибка при тестировании: {e}")


class PieceEditDialog(QDialog):
    """Диалог для редактирования фигуры"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить/Редактировать фигуру")
        self.setModal(True)
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.square_edit = QLineEdit()
        self.square_edit.setPlaceholderText("e4")
        form_layout.addRow("Поле:", self.square_edit)
        
        self.piece_type_combo = QComboBox()
        self.piece_type_combo.addItems(["pawn", "knight", "bishop", "rook", "queen", "king"])
        form_layout.addRow("Тип фигуры:", self.piece_type_combo)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(["white", "black"])
        form_layout.addRow("Цвет:", self.color_combo)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["attacker", "defender", "target", "support", "observer"])
        form_layout.addRow("Роль:", self.role_combo)
        
        self.importance_spin = QDoubleSpinBox()
        self.importance_spin.setRange(0.0, 1.0)
        self.importance_spin.setSingleStep(0.1)
        self.importance_spin.setValue(0.5)
        form_layout.addRow("Важность:", self.importance_spin)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_piece_data(self) -> Optional[Dict[str, Any]]:
        """Получить данные фигуры"""
        square = self.square_edit.text().strip()
        if not square:
            return None
        
        return {
            "square": square,
            "piece_type": self.piece_type_combo.currentText(),
            "color": self.color_combo.currentText(),
            "role": self.role_combo.currentText(),
            "importance": self.importance_spin.value()
        }


class PatternManagementWidget(QWidget):
    """Главный виджет управления паттернами"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern_manager = PatternManager()
        self._setup_ui()
        self._connect_signals()
        self._load_patterns()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QHBoxLayout(self)
        
        # Левая панель - список паттернов
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Заголовок и статистика
        left_layout.addWidget(QLabel("Управление паттернами"))
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: gray; font-size: 10px;")
        left_layout.addWidget(self.stats_label)
        
        # Фильтры
        filters_group = QGroupBox("Фильтры")
        filters_layout = QVBoxLayout(filters_group)
        
        self.category_filters = {}
        for category in PatternCategory:
            checkbox = QCheckBox(category.value.title())
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._update_filters)
            self.category_filters[category] = checkbox
            filters_layout.addWidget(checkbox)
        
        left_layout.addWidget(filters_group)
        
        # Список паттернов
        self.pattern_list = PatternListWidget()
        left_layout.addWidget(self.pattern_list)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("Новый")
        self.new_btn.clicked.connect(self._create_new_pattern)
        buttons_layout.addWidget(self.new_btn)
        
        self.import_btn = QPushButton("Импорт")
        self.import_btn.clicked.connect(self._import_patterns)
        buttons_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Экспорт")
        self.export_btn.clicked.connect(self._export_patterns)
        buttons_layout.addWidget(self.export_btn)
        
        left_layout.addLayout(buttons_layout)
        
        # Правая панель - детали паттерна
        self.pattern_details = PatternDetailsWidget()
        self.pattern_details.set_pattern_manager(self.pattern_manager)
        
        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.pattern_details)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
    
    def _connect_signals(self):
        """Подключить сигналы"""
        self.pattern_list.pattern_selected.connect(self._on_pattern_selected)
        self.pattern_details.pattern_modified.connect(self._on_pattern_modified)
    
    def _load_patterns(self):
        """Загрузить паттерны"""
        self.pattern_manager.load_all_patterns()
        
        # Создать паттерны по умолчанию, если их нет
        if not self.pattern_manager.patterns:
            default_patterns = create_default_patterns()
            for pattern in default_patterns:
                self.pattern_manager.create_pattern(pattern)
        
        self._update_pattern_list()
        self._update_statistics()
    
    def _update_pattern_list(self):
        """Обновить список паттернов"""
        # Применить фильтры
        enabled_categories = {
            category for category, checkbox in self.category_filters.items()
            if checkbox.isChecked()
        }
        
        filtered_patterns = {
            pid: pattern for pid, pattern in self.pattern_manager.patterns.items()
            if pattern.category in enabled_categories
        }
        
        self.pattern_list.update_patterns(filtered_patterns)
    
    def _update_statistics(self):
        """Обновить статистику"""
        stats = self.pattern_manager.get_pattern_statistics()
        stats_text = f"Всего: {stats['total_patterns']}, Включено: {stats['enabled_patterns']}"
        self.stats_label.setText(stats_text)
    
    def _update_filters(self):
        """Обновить фильтры"""
        # Обновить включенные категории в менеджере
        enabled_categories = {
            category for category, checkbox in self.category_filters.items()
            if checkbox.isChecked()
        }
        
        self.pattern_manager.enabled_categories = enabled_categories
        self._update_pattern_list()
    
    def _on_pattern_selected(self, pattern_id: str):
        """Обработать выбор паттерна"""
        pattern = self.pattern_manager.patterns.get(pattern_id)
        if pattern:
            self.pattern_details.display_pattern(pattern)
    
    def _on_pattern_modified(self, pattern_id: str):
        """Обработать изменение паттерна"""
        self._load_patterns()  # Перезагрузить все паттерны
    
    def _create_new_pattern(self):
        """Создать новый паттерн"""
        dialog = NewPatternDialog(self)
        if dialog.exec() == QDialog.Accepted:
            pattern_data = dialog.get_pattern_data()
            if pattern_data:
                new_pattern = ChessPatternEnhanced(**pattern_data)
                if self.pattern_manager.create_pattern(new_pattern):
                    self._load_patterns()
                    QMessageBox.information(self, "Успех", "Новый паттерн создан!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось создать паттерн!")
    
    def _import_patterns(self):
        """Импортировать паттерны"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Импорт паттернов", "", "JSON files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # TODO: Реализовать импорт паттернов
                QMessageBox.information(self, "Импорт", "Функция импорта будет реализована позже")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка импорта", f"Не удалось импортировать: {e}")
    
    def _export_patterns(self):
        """Экспортировать паттерны"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт паттернов", "", "JSON files (*.json)"
        )
        
        if file_path:
            try:
                # TODO: Реализовать экспорт паттернов
                QMessageBox.information(self, "Экспорт", "Функция экспорта будет реализована позже")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось экспортировать: {e}")


class NewPatternDialog(QDialog):
    """Диалог создания нового паттерна"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать новый паттерн")
        self.setModal(True)
        self.resize(400, 300)
        self._setup_ui()
    
    def _setup_ui(self):
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("unique_pattern_id")
        form_layout.addRow("ID:", self.id_edit)
        
        self.name_edit = QLineEdit()
        form_layout.addRow("Название:", self.name_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([cat.value for cat in PatternCategory])
        form_layout.addRow("Категория:", self.category_combo)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("Описание:", self.description_edit)
        
        self.fen_edit = QLineEdit()
        self.fen_edit.setText("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        form_layout.addRow("FEN:", self.fen_edit)
        
        self.key_move_edit = QLineEdit()
        self.key_move_edit.setPlaceholderText("e2e4")
        form_layout.addRow("Ключевой ход:", self.key_move_edit)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_pattern_data(self) -> Optional[Dict[str, Any]]:
        """Получить данные нового паттерна"""
        pattern_id = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        
        if not pattern_id or not name:
            QMessageBox.warning(self, "Ошибка", "ID и название обязательны!")
            return None
        
        return {
            "id": pattern_id,
            "name": name,
            "description": self.description_edit.toPlainText(),
            "category": PatternCategory(self.category_combo.currentText()),
            "fen": self.fen_edit.text(),
            "key_move": self.key_move_edit.text(),
            "participating_pieces": [],
            "frequency": 0.5,
            "success_rate": 0.5,
            "game_phase": "any",
            "tags": []
        }