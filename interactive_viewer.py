# interactive_viewer.py
# Интерактивный PySide viewer с кликабельными графиками и автоматическим воспроизведением игр

from utils.usage_logger import record_usage
record_usage(__file__)

import sys
import re
import chess
import logging
import subprocess
import json
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea, QFileDialog, QTabWidget, QProgressBar,
    QSpinBox, QComboBox, QGroupBox, QSplitter, QTextEdit, QMainWindow
)
from PySide6.QtCore import QTimer, QRect, Qt, QSettings, Signal, QThread
from PySide6.QtGui import QClipboard, QPainter, QColor, QPen, QPixmap, QFont, QPalette
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QValueAxis, 
    QBarCategoryAxis, QLineSeries, QScatterSeries, QPieSeries, QPieSlice
)
from ui.interactive_charts import (
    InteractiveBarChart, InteractivePieChart, InteractiveLineChart, ChartContainer
)

from utils.error_handler import ErrorHandler
from core.pst_trainer import update_from_board, update_from_history
from core.piece import piece_class_factory
from ui.cell import Cell
from ui.drawer_manager import DrawerManager
from chess_ai.bot_agent import make_agent
from chess_ai.threat_map import ThreatMap
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage
from utils.module_colors import MODULE_COLORS, REASON_PRIORITY
from ui.usage_timeline import UsageTimeline
from ui.panels import create_heatmap_panel
from utils.integration import generate_heatmaps
from utils.metrics_sidebar import build_sidebar_metrics
from chess_ai.elo_sync_manager import ELOSyncManager
from ui.mini_board import MiniBoard

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set Stockfish path if available
import os
if not os.environ.get("STOCKFISH_PATH"):
    stockfish_path = "/workspace/bin/stockfish-bin"
    if os.path.exists(stockfish_path):
        os.environ["STOCKFISH_PATH"] = stockfish_path

# Конфигурация ботов
WHITE_AGENT = "StockfishBot"
BLACK_AGENT = "DynamicBot"

class GameResult:
    """Класс для хранения результатов игры"""
    def __init__(self, game_id: int, result: str, moves: List[str], 
                 modules_w: List[str], modules_b: List[str], 
                 fens: List[str], duration_ms: int):
        self.game_id = game_id
        self.result = result
        self.moves = moves
        self.modules_w = modules_w
        self.modules_b = modules_b
        self.fens = fens
        self.duration_ms = duration_ms
        self.move_count = len(moves)

class InteractiveChart(QChartView):
    """Базовый класс для интерактивных графиков"""
    dataClicked = Signal(str, dict)  # signal when data point is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(200)
        self._selected_data = None
        
    def set_selected(self, data_key: str = None):
        """Выделить определенный элемент данных"""
        self._selected_data = data_key
        self.update()

class ModuleUsageChart(InteractiveBarChart):
    """Интерактивная диаграмма использования модулей"""

    # Унифицированный сигнал клика по данным
    dataClicked = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__("Module Usage Statistics", parent)
        # Пробрасываем клики с бар-чарта в унифицированный сигнал
        self.barClicked.connect(self._relay_click)

    def _relay_click(self, module: str, data: dict):
        """Проброс клика по бару как dataClicked"""
        self.dataClicked.emit(module, data)

class GameResultsChart(InteractivePieChart):
    """Интерактивная диаграмма результатов игр"""

    # Унифицированный сигнал клика по данным
    dataClicked = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__("Game Results", parent)
        # Пробрасываем клики с pie-чарта в унифицированный сигнал
        self.sliceClicked.connect(self._relay_click)

    def set_data(self, results: List[GameResult]):
        """Установить данные результатов игр"""
        results_dict = {}
        for result in results:
            if result.result not in results_dict:
                results_dict[result.result] = 0
            results_dict[result.result] += 1
            
        # Цвета для результатов
        colors = {
            "1-0": QColor(0, 150, 0),      # Белые выиграли - зеленый
            "0-1": QColor(150, 0, 0),      # Черные выиграли - красный
            "1/2-1/2": QColor(100, 100, 100),  # Ничья - серый
            "*": QColor(200, 200, 0)       # Незавершенная - желтый
        }
        
        super().set_data(results_dict, colors)

    def _relay_click(self, result: str, data: dict):
        """Проброс клика по сегменту как dataClicked"""
        self.dataClicked.emit(result, data)

class MoveTimelineChart(InteractiveLineChart):
    """Интерактивная временная шкала ходов"""

    # Унифицированный сигнал клика по данным (индекс точки)
    dataClicked = Signal(int, dict)

    def __init__(self, parent=None):
        super().__init__("Move Timeline", parent)
        # Пробрасываем клики с line-чарта в унифицированный сигнал
        self.pointClicked.connect(self._relay_click)

    def set_data(self, moves: List[str], modules: List[str]):
        """Установить данные ходов"""
        # Создаем данные для линейного графика
        data_points = []
        for i, (move, module) in enumerate(zip(moves, modules)):
            data_points.append((i, 1))  # Простая визуализация
            
        super().set_data(data_points)

    def _relay_click(self, index: int, data: dict):
        """Проброс клика по точке как dataClicked"""
        self.dataClicked.emit(index, data)

class GameWorker(QThread):
    """Worker thread для выполнения игр в фоне"""
    gameCompleted = Signal(object)  # GameResult
    progressUpdated = Signal(int)   # progress percentage
    statusUpdated = Signal(str)     # status message
    patternDetected = Signal(object)  # streamed pattern objects during play
    
    def __init__(self, white_agent, black_agent, num_games=10):
        super().__init__()
        self.white_agent = white_agent
        self.black_agent = black_agent
        self.num_games = num_games
        self._stop_requested = False
        
    def run(self):
        """Выполнить серию игр"""
        for game_id in range(self.num_games):
            if self._stop_requested:
                break
                
            self.statusUpdated.emit(f"Playing game {game_id + 1}/{self.num_games}")
            
            # Играем одну игру
            result = self._play_single_game(game_id)
            self.gameCompleted.emit(result)
            
            # Обновляем прогресс
            progress = int((game_id + 1) / self.num_games * 100)
            self.progressUpdated.emit(progress)
            
        self.statusUpdated.emit("All games completed!")
        
    def _play_single_game(self, game_id: int) -> GameResult:
        """Сыграть одну игру"""
        import time
        start_time = time.time()
        
        board = chess.Board()
        moves = []
        modules_w = []
        modules_b = []
        fens = [board.fen()]
        
        while not board.is_game_over():
            mover_color = board.turn
            agent = self.white_agent if mover_color == chess.WHITE else self.black_agent
            
            try:
                # Count legal moves for branching metric
                try:
                    legal_count = sum(1 for _ in board.legal_moves)
                except Exception:
                    legal_count = 0

                move = agent.choose_move(board)
                if move is None or not board.is_legal(move):
                    break
                    
                san = board.san(move)
                moves.append(san)
                
                # Получаем информацию о модуле
                reason = agent.get_last_reason() if hasattr(agent, "get_last_reason") else "UNKNOWN"
                key = self._extract_reason_key(reason)
                
                if mover_color == chess.WHITE:
                    modules_w.append(key)
                else:
                    modules_b.append(key)

                # Try to build and emit an interesting pattern before applying move
                try:
                    pattern_obj = self._build_pattern_if_interesting(board, move, san, mover_color, legal_count, game_id, len(moves))
                    if pattern_obj is not None:
                        self.patternDetected.emit(pattern_obj)
                except Exception:
                    pass
                
                board.push(move)
                fens.append(board.fen())
                
            except Exception as e:
                logger.error(f"Error in game {game_id}: {e}")
                break
        
        duration_ms = int((time.time() - start_time) * 1000)
        result = board.result()
        
        return GameResult(
            game_id=game_id,
            result=result,
            moves=moves,
            modules_w=modules_w,
            modules_b=modules_b,
            fens=fens,
            duration_ms=duration_ms
        )

    # ---------------- Pattern collection helpers -----------------
    def _piece_type_to_name(self, piece_type: int) -> Optional[str]:
        mapping = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king",
        }
        return mapping.get(piece_type)

    def _build_pattern_if_interesting(
        self,
        board: chess.Board,
        move: chess.Move,
        san: str,
        mover_color: chess.Color,
        legal_count: int,
        game_id: int,
        move_index: int,
    ) -> Optional[dict]:
        """Create a compact 'pattern' dict when a move looks interesting.

        Heuristics:
        - High branching factor before the move
        - Captures high-value piece, gives check, or promotes
        """
        # Evaluate tactical flags on a copy
        temp = board.copy()
        is_capture = temp.is_capture(move)
        captured_value = 0
        captured_piece_symbol = None
        if is_capture:
            target = temp.piece_at(move.to_square)
            if target:
                captured_piece_symbol = target.symbol()
                values = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9, 6: 0}
                captured_value = values.get(target.piece_type, 0)

        temp.push(move)
        gives_check = temp.is_check()
        is_promotion = move.promotion is not None

        # Basic importance score
        importance = 0.0
        if legal_count >= 30:
            importance += 0.15
        elif legal_count >= 20:
            importance += 0.08
        importance += min(0.3, captured_value * 0.03)
        if gives_check:
            importance += 0.2
        if is_promotion:
            importance += 0.25

        # Lightweight fork hint for knights
        fork_hint = False
        src_piece = board.piece_at(move.from_square)
        if src_piece and src_piece.piece_type == chess.KNIGHT:
            attacks = board.attacks(move.from_square)
            hits = 0
            for sq in attacks:
                pc = board.piece_at(sq)
                if pc and pc.color != mover_color and pc.piece_type in (chess.QUEEN, chess.ROOK, chess.KING):
                    hits += 1
            if hits >= 2:
                fork_hint = True
                importance += 0.15

        # Threshold for interesting pattern
        if importance < 0.25 and not fork_hint and legal_count < 25:
            return None

        piece_name = self._piece_type_to_name(src_piece.piece_type) if src_piece else None

        # Influencer squares around destination (defenders/attackers)
        influencers = {
            "friendly_defenders": list(board.attackers(mover_color, move.to_square)),
            "enemy_attackers": list(board.attackers(not mover_color, move.to_square)),
        }

        highlight_squares = set(influencers["friendly_defenders"]) | set(influencers["enemy_attackers"]) | {move.from_square, move.to_square}

        tags = []
        if legal_count >= 25:
            tags.append("high_branching")
        if is_capture:
            tags.append("capture")
            if captured_value >= 5:
                tags.append("big_capture")
        if gives_check:
            tags.append("check")
        if is_promotion:
            tags.append("promotion")
        if fork_hint:
            tags.append("fork")

        pattern = {
            "game_id": game_id,
            "move_index": move_index,
            "color": "white" if mover_color == chess.WHITE else "black",
            "san": san,
            "uci": move.uci(),
            "fen": board.fen(),
            "board_fen": board.board_fen(),
            "legal_moves": legal_count,
            "importance": round(importance, 3),
            "tags": tags,
            "moving_piece": piece_name,
            "captured_piece": captured_piece_symbol,
            "influencers": {
                "friendly_defenders": [int(sq) for sq in influencers["friendly_defenders"]],
                "enemy_attackers": [int(sq) for sq in influencers["enemy_attackers"]],
            },
            "highlight_squares": [int(sq) for sq in highlight_squares],
            "heatmap_piece": piece_name,
        }
        return pattern
    
    def _extract_reason_key(self, reason: str) -> str:
        """Извлечь ключ модуля из reason"""
        if not reason or reason == "-":
            return "OTHER"
        up = reason.upper()
        
        for tok in REASON_PRIORITY:
            if tok in up:
                return tok
                
        m = re.search(r"\b[A-Z][A-Z_]{1,}\b", up)
        if m:
            return m.group(0)
            
        return "OTHER"
    
    def stop(self):
        """Остановить выполнение"""
        self._stop_requested = True

class InteractiveChessViewer(QMainWindow):
    """Главный класс интерактивного viewer'а"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Chess Viewer - Auto Play Mode")
        self.resize(1400, 800)
        
        # Create scroll area (single central widget)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Style the scroll area
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #6c757d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #495057;
            }
            QScrollBar:horizontal {
                background-color: #e9ecef;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #6c757d;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #495057;
            }
        """)
        
        # Set scroll area as central widget
        self.setCentralWidget(self.scroll_area)
        
        # Инициализация данных
        self.board = chess.Board()
        self.piece_objects = {}
        self.settings = QSettings("InteractiveChessViewer", "Preferences")
        
        # Результаты игр
        self.game_results: List[GameResult] = []
        self.current_game_index = 0
        
        # Инициализация агентов
        self._init_agents()
        
        # Инициализация UI
        self._init_ui()
        
        # Инициализация таймеров
        self._init_timers()
        
        # Не запускаем авто-плей автоматически, чтобы кнопка Start не была серой
        
        # Ensure scrollbars are properly configured
        self._configure_scrollbars()
        
    def _configure_scrollbars(self):
        """Configure scrollbars to ensure proper content display"""
        # Ensure the content widget has a minimum size
        if hasattr(self, "content_widget") and self.content_widget is not None:
            self.content_widget.setMinimumSize(1200, 700)
        
        # Update scroll area size policy
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Ensure scrollbars appear when content exceeds viewport
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _init_agents(self):
        """Инициализация шахматных агентов"""
        try:
            self.white_agent = make_agent(WHITE_AGENT, chess.WHITE)
            self.black_agent = make_agent(BLACK_AGENT, chess.BLACK)
        except Exception as exc:
            ErrorHandler.handle_agent_error(exc, f"{WHITE_AGENT}/{BLACK_AGENT}")
            self._show_critical_error("AI Agent Initialization Failed", str(exc))
            
    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        # Главный контент, который помещается в центральный scroll area
        self.content_widget = QWidget()
        main_layout = QVBoxLayout(self.content_widget)

        # Создаем сплиттер для разделения панелей
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - шахматная доска
        left_panel = self._create_board_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель - интерактивные графики и управление
        right_panel = self._create_control_panel()
        splitter.addWidget(right_panel)
        
        # Устанавливаем пропорции
        splitter.setSizes([600, 800])
        
        # Добавить сплиттер в основной layout и установить в scroll area
        main_layout.addWidget(splitter)
        self.scroll_area.setWidget(self.content_widget)
        
    def _create_board_panel(self) -> QWidget:
        """Создать панель с шахматной доской"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title = QLabel("Chess Board")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Шахматная доска
        self.board_frame = QFrame()
        self.board_frame.setFixedSize(560, 560)
        self.board_frame.setStyleSheet("border: 2px solid #333;")
        
        self.grid = QGridLayout(self.board_frame)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.cell_grid = [[None for _ in range(8)] for _ in range(8)]
        
        # Инициализация ячеек доски
        self._init_board_cells()
        
        layout.addWidget(self.board_frame, alignment=Qt.AlignCenter)
        
        # Информация о текущей игре
        self.game_info = QLabel("Game: 0/10 | Status: Ready")
        self.game_info.setStyleSheet("font-size: 12px; margin: 10px;")
        layout.addWidget(self.game_info)
        
        return panel
        
    def _create_control_panel(self) -> QWidget:
        """Создать панель управления с интерактивными графиками"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Создаем табы для разных типов графиков
        tab_widget = QTabWidget()
        
        # Таб 1: Управление играми
        control_tab = self._create_control_tab()
        tab_widget.addTab(control_tab, "Game Control")
        
        # Таб 2: Статистика модулей
        modules_tab = self._create_modules_tab()
        tab_widget.addTab(modules_tab, "Module Statistics")
        
        # Таб 3: Результаты игр
        results_tab = self._create_results_tab()
        tab_widget.addTab(results_tab, "Game Results")
        
        # Таб 4: Временная шкала
        timeline_tab = self._create_timeline_tab()
        tab_widget.addTab(timeline_tab, "Move Timeline")

        # Таб 5: Редактор паттернов
        patterns_tab = self._create_patterns_tab()
        tab_widget.addTab(patterns_tab, "Pattern Editor")
        
        layout.addWidget(tab_widget)
        
        return panel
        
    def _create_control_tab(self) -> QWidget:
        """Создать таб управления играми"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Группа управления
        control_group = QGroupBox("Game Control")
        control_layout = QVBoxLayout(control_group)
        
        # Кнопки управления
        self.btn_start = QPushButton("▶ Start Auto Play")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_reset = QPushButton("🔄 Reset")
        
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        
        # Подключение сигналов
        self.btn_start.clicked.connect(self._start_auto_play)
        self.btn_pause.clicked.connect(self._pause_auto_play)
        self.btn_stop.clicked.connect(self._stop_auto_play)
        self.btn_reset.clicked.connect(self._reset_games)
        
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_reset)
        
        # Настройки
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Количество игр
        games_layout = QHBoxLayout()
        games_layout.addWidget(QLabel("Number of games:"))
        self.games_spinbox = QSpinBox()
        self.games_spinbox.setRange(1, 100)
        self.games_spinbox.setValue(10)
        games_layout.addWidget(self.games_spinbox)
        games_layout.addStretch()
        settings_layout.addLayout(games_layout)
        
        # Выбор ботов
        bots_layout = QHBoxLayout()
        bots_layout.addWidget(QLabel("White:"))
        self.white_combo = QComboBox()
        self.white_combo.addItems(["StockfishBot", "DynamicBot", "RandomBot", "AggressiveBot"])
        self.white_combo.setCurrentText(WHITE_AGENT)
        bots_layout.addWidget(self.white_combo)
        
        bots_layout.addWidget(QLabel("Black:"))
        self.black_combo = QComboBox()
        self.black_combo.addItems(["StockfishBot", "DynamicBot", "RandomBot", "AggressiveBot"])
        self.black_combo.setCurrentText(BLACK_AGENT)
        bots_layout.addWidget(self.black_combo)
        settings_layout.addLayout(bots_layout)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        settings_layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("Ready to start")
        settings_layout.addWidget(self.status_label)
        
        layout.addWidget(control_group)
        layout.addWidget(settings_group)
        layout.addStretch()
        
        return widget

    def _create_patterns_tab(self) -> QWidget:
        """Создать вкладку редактора паттернов с предпросмотром и тегами."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Список найденных паттернов
        self.patterns_list = QListWidget()
        self.patterns_list.itemClicked.connect(self._on_pattern_item_clicked)
        layout.addWidget(QLabel("Discovered patterns (auto-updating during games):"))
        layout.addWidget(self.patterns_list)

        # Мини-доска предпросмотра
        self.pattern_preview = MiniBoard(scale=0.35)
        layout.addWidget(self.pattern_preview)

        # Категории/теги
        tags_row1 = QHBoxLayout()
        tags_row2 = QHBoxLayout()
        self.combo_category = QComboBox()
        self.combo_category.addItems(["tactical", "opening", "positional", "endgame"])
        tags_row1.addWidget(QLabel("Category:"))
        tags_row1.addWidget(self.combo_category)

        def mk(tag: str) -> QCheckBox:
            cb = QCheckBox(tag)
            cb.setChecked(False)
            return cb

        self.cb_fork = mk("fork")
        self.cb_pin = mk("pin")
        self.cb_skewer = mk("skewer")
        self.cb_discovered = mk("discovered")
        self.cb_check = mk("check")
        self.cb_capture = mk("capture")
        self.cb_promotion = mk("promotion")
        self.cb_high_branching = mk("high_branching")
        self.cb_trick = mk("trick")

        for w in [self.cb_fork, self.cb_pin, self.cb_skewer, self.cb_discovered, self.cb_check]:
            tags_row1.addWidget(w)
        for w in [self.cb_capture, self.cb_promotion, self.cb_high_branching, self.cb_trick]:
            tags_row2.addWidget(w)

        layout.addLayout(tags_row1)
        layout.addLayout(tags_row2)

        # Кнопки управления
        btns = QHBoxLayout()
        self.btn_prev_pattern = QPushButton("◀ Prev")
        self.btn_next_pattern = QPushButton("Next ▶")
        self.btn_save_pattern = QPushButton("💾 Save pattern")
        self.btn_prev_pattern.clicked.connect(lambda: self._navigate_pattern(-1))
        self.btn_next_pattern.clicked.connect(lambda: self._navigate_pattern(1))
        self.btn_save_pattern.clicked.connect(self._save_selected_pattern)
        btns.addWidget(self.btn_prev_pattern)
        btns.addWidget(self.btn_next_pattern)
        btns.addStretch()
        btns.addWidget(self.btn_save_pattern)
        layout.addLayout(btns)

        return widget
        
    def _create_modules_tab(self) -> QWidget:
        """Создать таб статистики модулей"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Интерактивная диаграмма модулей в контейнере
        self.module_chart = ModuleUsageChart()
        self.module_chart.dataClicked.connect(self._on_module_clicked)
        module_container = ChartContainer(self.module_chart, "Module Usage Statistics")
        layout.addWidget(module_container)
        
        # Детали выбранного модуля
        self.module_details = QTextEdit()
        self.module_details.setMaximumHeight(150)
        self.module_details.setPlainText("Click on a module bar to see details...")
        layout.addWidget(self.module_details)
        
        return widget
        
    def _create_results_tab(self) -> QWidget:
        """Создать таб результатов игр"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Интерактивная диаграмма результатов в контейнере
        self.results_chart = GameResultsChart()
        self.results_chart.dataClicked.connect(self._on_result_clicked)
        results_container = ChartContainer(self.results_chart, "Game Results")
        layout.addWidget(results_container)
        
        # Список игр
        self.games_list = QListWidget()
        self.games_list.itemClicked.connect(self._on_game_selected)
        layout.addWidget(self.games_list)
        
        return widget
        
    def _create_timeline_tab(self) -> QWidget:
        """Создать таб временной шкалы"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Интерактивная временная шкала в контейнере
        self.timeline_chart = MoveTimelineChart()
        self.timeline_chart.dataClicked.connect(self._on_timeline_clicked)
        timeline_container = ChartContainer(self.timeline_chart, "Move Timeline")
        layout.addWidget(timeline_container)
        
        # Детали хода
        self.move_details = QTextEdit()
        self.move_details.setMaximumHeight(100)
        self.move_details.setPlainText("Select a game to see move timeline...")
        layout.addWidget(self.move_details)
        
        return widget
        
    def _init_board_cells(self):
        """Инициализация ячеек шахматной доски"""
        for row in range(8):
            for col in range(8):
                cell = Cell(row, col, DrawerManager())
                self.grid.addWidget(cell, row, col)
                self.cell_grid[row][col] = cell
                
    def _init_timers(self):
        """Инициализация таймеров"""
        self.auto_timer = QTimer()
        self.auto_timer.setInterval(1000)  # 1 секунда между ходами
        self.auto_timer.timeout.connect(self._auto_step)
        self.auto_running = False
        
    def _start_auto_play(self):
        """Начать автоматическое воспроизведение игр"""
        if self.auto_running:
            return
            
        self.auto_running = True
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        
        # Создаем worker thread для игр
        self.game_worker = GameWorker(
            self.white_agent, 
            self.black_agent, 
            self.games_spinbox.value()
        )
        self.game_worker.gameCompleted.connect(self._on_game_completed)
        self.game_worker.progressUpdated.connect(self._on_progress_updated)
        self.game_worker.statusUpdated.connect(self._on_status_updated)
        self.game_worker.patternDetected.connect(self._on_pattern_detected)
        self.game_worker.start()
        
        self.status_label.setText("Starting auto play...")
        self.progress_bar.setVisible(True)
        
    def _pause_auto_play(self):
        """Приостановить автоматическое воспроизведение"""
        if hasattr(self, 'game_worker') and self.game_worker.isRunning():
            self.game_worker.stop()
            
        self.auto_running = False
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.status_label.setText("Paused")
        
    def _stop_auto_play(self):
        """Остановить автоматическое воспроизведение"""
        if hasattr(self, 'game_worker') and self.game_worker.isRunning():
            self.game_worker.stop()
            self.game_worker.wait()
            
        self.auto_running = False
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Stopped")
        
    def _reset_games(self):
        """Сбросить все игры"""
        self._stop_auto_play()
        self.game_results.clear()
        self.current_game_index = 0
        self.board = chess.Board()
        self._update_board()
        self._update_ui()
        self.status_label.setText("Reset completed")
        
    def _on_game_completed(self, result: GameResult):
        """Обработка завершения игры"""
        self.game_results.append(result)
        self._update_ui()
        self._update_game_info()
        
    def _on_progress_updated(self, progress: int):
        """Обновление прогресса"""
        self.progress_bar.setValue(progress)
        
    def _on_status_updated(self, status: str):
        """Обновление статуса"""
        self.status_label.setText(status)

    # ---------------- Pattern editor logic -----------------
    def _on_pattern_detected(self, pattern: dict):
        """Получен новый паттерн во время автоигры."""
        self.discovered_patterns.append(pattern)
        label = f"G{pattern.get('game_id', '?')} M{pattern.get('move_index', '?')}: {pattern.get('san', '')} [{', '.join(pattern.get('tags', []))}]"
        self.patterns_list.addItem(label)
        self.patterns_list.setCurrentRow(self.patterns_list.count() - 1)
        self._load_pattern_preview(pattern)

    def _on_pattern_item_clicked(self, item):
        idx = self.patterns_list.row(item)
        if 0 <= idx < len(self.discovered_patterns):
            self._load_pattern_preview(self.discovered_patterns[idx])

    def _load_pattern_preview(self, pattern: dict):
        try:
            fen = pattern.get("fen") or pattern.get("board_fen")
            if fen:
                self.pattern_preview.set_fen(fen)
            highlights = pattern.get("highlight_squares", [])
            self.pattern_preview.set_border_highlights(highlights)
            try:
                piece = pattern.get("heatmap_piece")
                if piece:
                    self.pattern_preview.drawer_manager.active_heatmap_piece = piece
                    # Rebuild overlays by reapplying the same FEN
                    self.pattern_preview.set_fen(self.pattern_preview.board.fen())
            except Exception:
                pass

            tags = set(pattern.get("tags", []))
            self.cb_fork.setChecked("fork" in tags)
            self.cb_pin.setChecked("pin" in tags)
            self.cb_skewer.setChecked("skewer" in tags)
            self.cb_discovered.setChecked("discovered" in tags)
            self.cb_check.setChecked("check" in tags)
            self.cb_capture.setChecked("capture" in tags or "big_capture" in tags)
            self.cb_promotion.setChecked("promotion" in tags)
            self.cb_high_branching.setChecked("high_branching" in tags)
        except Exception as exc:
            logger.warning(f"Failed to load pattern preview: {exc}")

    def _navigate_pattern(self, delta: int):
        cur = self.patterns_list.currentRow()
        if cur < 0 and self.patterns_list.count() > 0:
            cur = 0
        nxt = max(0, min(self.patterns_list.count() - 1, cur + delta))
        if nxt != cur:
            self.patterns_list.setCurrentRow(nxt)
            item = self.patterns_list.item(nxt)
            if item:
                self._on_pattern_item_clicked(item)

    def _save_selected_pattern(self):
        """Сохранить выбранный паттерн в configs/patterns.json и журнал JSONL."""
        idx = self.patterns_list.currentRow()
        if idx < 0 or idx >= len(self.discovered_patterns):
            QMessageBox.information(self, "No pattern", "Select a pattern to save")
            return
        pattern = dict(self.discovered_patterns[idx])

        # Merge UI tag selections
        extra_tags = []
        for cb, name in (
            (self.cb_fork, "fork"),
            (self.cb_pin, "pin"),
            (self.cb_skewer, "skewer"),
            (self.cb_discovered, "discovered"),
            (self.cb_check, "check"),
            (self.cb_capture, "capture"),
            (self.cb_promotion, "promotion"),
            (self.cb_high_branching, "high_branching"),
            (self.cb_trick, "trick"),
        ):
            if cb.isChecked():
                extra_tags.append(name)
        tags = sorted(set(pattern.get("tags", [])) | set(extra_tags))
        pattern["tags"] = tags
        pattern["category"] = self.combo_category.currentText()

        # Append to configs/patterns.json
        try:
            import json, os
            path = os.path.join("configs", "patterns.json")
            data = {"patterns": []}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as fh:
                    try:
                        existing = json.load(fh)
                        if isinstance(existing, dict) and "patterns" in existing:
                            data = existing
                        elif isinstance(existing, list):
                            data = {"patterns": existing}
                    except Exception:
                        pass
            entry = {
                "situation": pattern.get("board_fen") or (pattern.get("fen") or "").split(" ")[0],
                "action": pattern.get("uci", ""),
                "name": f"auto_{pattern.get('moving_piece','?')}_{pattern.get('san','')}",
                "description": f"tags={','.join(tags)}; importance={pattern.get('importance',0)}",
                "confidence": max(0.5, min(0.99, float(pattern.get("importance", 0.4) + 0.4))),
                "game_phase": "opening" if pattern.get("move_index", 0) <= 10 else "any",
            }
            data.setdefault("patterns", []).append(entry)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"Failed to save to configs/patterns.json: {exc}")
            QMessageBox.warning(self, "Save failed", f"Could not update configs/patterns.json: {exc}")
            return

        # Append verbose record to runs/patterns_captured.jsonl
        try:
            import json, os
            os.makedirs("runs", exist_ok=True)
            with open(os.path.join("runs", "patterns_captured.jsonl"), "a", encoding="utf-8") as fh:
                fh.write(json.dumps(pattern, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning(f"Failed to append JSONL record: {exc}")

        self.status_label.setText("Pattern saved ✔")
        
    def _on_module_clicked(self, module: str, data: dict):
        """Обработка клика по модулю"""
        details = f"Module: {module}\n"
        details += f"Usage count: {data.get(module, 0)}\n"
        details += f"Percentage: {data.get(module, 0) / sum(data.values()) * 100:.1f}%\n"
        details += f"Color: {MODULE_COLORS.get(module, 'Unknown')}"
        
        self.module_details.setPlainText(details)
        
    def _on_result_clicked(self, result: str, data: dict):
        """Обработка клика по результату"""
        # Фильтруем игры по результату
        filtered_games = [g for g in self.game_results if g.result == result]
        
        self.games_list.clear()
        for game in filtered_games:
            item_text = f"Game {game.game_id + 1}: {result} ({game.move_count} moves, {game.duration_ms}ms)"
            self.games_list.addItem(item_text)
            
    def _on_game_selected(self, item):
        """Обработка выбора игры"""
        # Найти игру по тексту элемента
        for i, game in enumerate(self.game_results):
            if f"Game {game.game_id + 1}:" in item.text():
                self.current_game_index = i
                self._load_game_to_board(game)
                break
                
    def _on_timeline_clicked(self, index: int, data: dict):
        """Обработка клика по временной шкале"""
        if self.current_game_index < len(self.game_results):
            game = self.game_results[self.current_game_index]
            if 0 <= index < len(game.moves):
                move = game.moves[index]
                module = game.modules_w[index] if index < len(game.modules_w) else "Unknown"
                self.move_details.setPlainText(f"Move {index + 1}: {move} (Module: {module})")
                
    def _load_game_to_board(self, game: GameResult):
        """Загрузить игру на доску"""
        if game.fens:
            self.board = chess.Board(game.fens[0])
            for move in game.moves:
                try:
                    self.board.push_san(move)
                except:
                    break
            self._update_board()
            
    def _update_board(self):
        """Обновить отображение доски"""
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                cell = self.cell_grid[row][col]
                cell.set_piece(piece.symbol() if piece else None)
                cell.update()
                
    def _update_ui(self):
        """Обновить все UI элементы"""
        if not self.game_results:
            return
            
        # Обновляем диаграмму модулей
        all_modules = defaultdict(int)
        for game in self.game_results:
            for module in game.modules_w + game.modules_b:
                all_modules[module] += 1
        self.module_chart.set_data(dict(all_modules))
        
        # Обновляем диаграмму результатов
        self.results_chart.set_data(self.game_results)
        
        # Обновляем список игр
        self.games_list.clear()
        for game in self.game_results:
            item_text = f"Game {game.game_id + 1}: {game.result} ({game.move_count} moves, {game.duration_ms}ms)"
            self.games_list.addItem(item_text)
            
    def _update_game_info(self):
        """Обновить информацию о текущей игре"""
        total_games = len(self.game_results)
        if total_games > 0:
            current_game = self.game_results[-1]
            self.game_info.setText(f"Game: {current_game.game_id + 1}/{self.games_spinbox.value()} | "
                                 f"Result: {current_game.result} | "
                                 f"Moves: {current_game.move_count}")
        else:
            self.game_info.setText("Game: 0/10 | Status: Ready")
            
    def _auto_step(self):
        """Автоматический шаг (не используется в новом режиме)"""
        pass
        
    def _show_critical_error(self, title: str, message: str):
        """Показать критическую ошибку"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
        self.close()

def main():
    """Главная функция"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Interactive Chess Viewer")
        app.setApplicationVersion("2.0")
        
        # Стилизация приложения
        app.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        viewer = InteractiveChessViewer()
        viewer.show()
        
        sys.exit(app.exec())
        
    except Exception as exc:
        print(f"Application failed to start: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()