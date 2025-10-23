# pyside_viewer.py
# Ліворуч: дошка (припіднята). Праворуч: кнопки + статуси + лічильник використання модулів.
# Додано: Usage таймлайн (два ряди кольорових прямокутників для W/B).
# Боти задаються тут у коді.

from utils.usage_logger import record_usage
record_usage(__file__)

import sys
import re
import chess
import logging
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea, QFileDialog, QTextEdit, QSplitter,
    QScrollBar, QMainWindow, QTabWidget
)
from PySide6.QtCore import QTimer, QRect, Qt, QSettings
from PySide6.QtGui import QClipboard, QPainter, QColor, QPen, QPixmap, QFont

from utils.error_handler import ErrorHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Set Stockfish path if available
import os
if not os.environ.get("STOCKFISH_PATH"):
    stockfish_path = "/workspace/bin/stockfish-bin"
    if os.path.exists(stockfish_path):
        os.environ["STOCKFISH_PATH"] = stockfish_path

# Фіксована пара ботів у в’ювері:
WHITE_AGENT = "StockfishBot"
BLACK_AGENT = "DynamicBot"

class OverallUsageChart(QWidget):
    """Simple bar chart summarising module usage across multiple runs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counts = {}
        self.pad = 8
        self.bar_h = 14
        self.legend_h = 20
        self.setMinimumWidth(280)
        self._update_height()

    def _update_height(self) -> None:
        total = len(self.counts)
        height = self.pad + total * (self.bar_h + self.pad) + self.legend_h
        self.setMinimumHeight(height)
        self.updateGeometry()

    def set_data(self, counts):
        self.counts = dict(counts)
        self._update_height()
        self.update()

    def paintEvent(self, ev):  # pragma: no cover - GUI drawing
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        if not self.counts:
            return

        w = self.width()
        max_count = max(self.counts.values())
        items = sorted(self.counts.items(), key=lambda kv: (-kv[1], kv[0]))

        y = self.pad
        for name, count in items:
            bar_w = (
                int((w - self.pad * 2) * (count / max_count)) if max_count else 0
            )
            color = MODULE_COLORS.get(name, MODULE_COLORS["OTHER"])
            painter.fillRect(QRect(self.pad, y, bar_w, self.bar_h), color)
            painter.setPen(QPen(QColor(60, 60, 60)))
            painter.drawRect(QRect(self.pad, y, bar_w, self.bar_h))
            painter.drawText(
                self.pad + bar_w + 4, y + self.bar_h - 2, f"{name} ({count})"
            )
            y += self.bar_h + self.pad

        # Legend mapping colours to modules
        y_leg = y
        x_leg = self.pad
        painter.setPen(QPen(QColor(80, 80, 80)))
        for name, _ in items:
            color = MODULE_COLORS.get(name, MODULE_COLORS["OTHER"])
            rect = QRect(x_leg, y_leg, 10, 10)
            painter.fillRect(rect, color)
            painter.drawRect(rect)
            painter.drawText(x_leg + 14, y_leg + 10, name)
            x_leg += 14 + painter.fontMetrics().horizontalAdvance(name) + 10
            if x_leg > w - self.pad:
                break

class ChessViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Viewer — ThreatMap & Metrics")
        self.resize(980, 620)  # більше місця праворуч
        
        # Мінімальна затримка між застосуванням ходів (мс)
        self.min_move_delay_ms = 400
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        try:
            # Логіка позиції
            self.board = chess.Board()
            self.piece_objects = {}
            self.settings = QSettings("ChessViewer", "Preferences")
        except Exception as exc:
            ErrorHandler.handle_chess_error(exc, "board initialization")
            self._show_critical_error(
                "Chess Board Initialization Failed",
                f"🚨 <b>Failed to initialize chess board:</b> {exc}\n\n"
                f"<b>This usually indicates:</b>\n"
                f"• Corrupted chess library installation\n"
                f"• Missing required dependencies\n"
                f"• System resource issues\n\n"
                f"<b>Try:</b>\n"
                f"• Reinstall chess library: pip install --upgrade chess\n"
                f"• Restart the application\n"
                f"• Check system memory availability"
            )
            return
        saved_set_raw = self.settings.value("heatmap/set")
        saved_set = str(saved_set_raw) if saved_set_raw is not None else None
        saved_piece_raw = self.settings.value("heatmap/piece")
        saved_piece_missing = saved_piece_raw is None
        if not saved_piece_missing:
            saved_piece_str = str(saved_piece_raw)
            saved_piece = None if saved_piece_str == "none" else saved_piece_str
        else:
            saved_piece = None

        self.drawer_manager = DrawerManager()
        self.heatmap_set_combo = None
        self.heatmap_piece_combo = None

        if saved_set:
            self.drawer_manager.set_heatmap_set(saved_set)

        default_heatmap_set = self.drawer_manager.active_heatmap_set
        default_heatmap_piece = self.drawer_manager.active_heatmap_piece

        if not saved_piece_missing:
            if saved_piece is None:
                self.drawer_manager.active_heatmap_piece = None
                default_heatmap_piece = None
            elif saved_piece in self.drawer_manager.heatmaps:
                self.drawer_manager.active_heatmap_piece = saved_piece
                default_heatmap_piece = saved_piece
            else:
                default_heatmap_piece = self.drawer_manager.active_heatmap_piece

        # ELO ratings manager
        self.elo_manager = ELOSyncManager()
        
        # Register bots with initial ELO if not already registered
        self._ensure_bots_registered()
        
        # Агенти
        try:
            self.white_agent = make_agent(WHITE_AGENT, chess.WHITE)
            self.black_agent = make_agent(BLACK_AGENT, chess.BLACK)
        except Exception as exc:
            ErrorHandler.handle_agent_error(exc, f"{WHITE_AGENT}/{BLACK_AGENT}")
            self._show_critical_error(
                "AI Agent Initialization Failed",
                f"🤖 <b>Failed to create AI agents:</b> {exc}\n\n"
                f"<b>Agent configuration:</b>\n"
                f"• White: {WHITE_AGENT}\n"
                f"• Black: {BLACK_AGENT}\n\n"
                f"<b>Possible causes:</b>\n"
                f"• Missing agent implementation files\n"
                f"• Corrupted agent modules\n"
                f"• Import path issues\n\n"
                f"<b>Try:</b>\n"
                f"• Check if chess_ai module is properly installed\n"
                f"• Verify agent names are correct\n"
                f"• Restart the application"
            )
            return

        # ThreatMap’и
        self.tmap_white = ThreatMap(chess.WHITE)
        self.tmap_black = ThreatMap(chess.BLACK)

        # Лічильники використання модулів (вьювер-локальні)
        self.usage_w = defaultdict(int)
        self.usage_b = defaultdict(int)
        self.timeline_w = []  # послідовність ключів для W (по кожному ході білих)
        self.timeline_b = []  # для B
        self.fen_history = []

        # ---- ЛЕВА КОЛОНКА: ДОШКА + КОНСОЛЬ ----
        self.board_frame = QFrame()
        self.board_frame.setFixedSize(560, 560)
        self.grid = QGridLayout(self.board_frame)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.cell_grid = [[None for _ in range(8)] for _ in range(8)]
        self._draw_board_widgets()

        # Console output area
        self.console_output = QTextEdit()
        self.console_output.setMaximumHeight(140)  # Зменшено на 60 пікселів (4 рядки)
        self.console_output.setMinimumHeight(90)   # Зменшено на 60 пікселів
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)
        self.console_output.setPlainText("Console output will appear here during auto-play...")
        # Make console 4 lines shorter than previous ~200px cap and stick to bottom
        try:
            line_h = self.console_output.fontMetrics().lineSpacing()
            new_h = max(80, 200 - 4 * line_h)
            self.console_output.setFixedHeight(new_h)
        except Exception:
            # Fallback height if metrics unavailable
            self.console_output.setFixedHeight(140)
        
        # Ensure console is visible and properly sized
        self.console_output.setVisible(True)

        left_col = QVBoxLayout()
        left_col.addWidget(self.board_frame)
        left_col.addStretch(1)  # консоль притискаємо до нижнього краю
        left_col.addWidget(QLabel("Console Output:"))
        left_col.addWidget(self.console_output)

        # ---- ПРАВА КОЛОНКА: КНОПКИ + ТАБИ ----
        right_col = QVBoxLayout()

        # Create title with ELO ratings
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self._update_title_with_elo()
        right_col.addWidget(self.title_label)

        # Кнопки
        btn_row = QHBoxLayout()
        self.btn_auto  = QPushButton("▶ Авто")
        self.btn_pause = QPushButton("⏸ Пауза")
        self.btn_auto_play = QPushButton("🎮 10 Игр")
        self.btn_auto_play.setToolTip("Автоматически сыграть 10 игр подряд")
        self.btn_copy_san = QPushButton("⧉ SAN")
        self.btn_copy_pgn = QPushButton("⧉ PGN")
        self.btn_save_png = QPushButton("📷 PNG")
        self.btn_refresh_elo = QPushButton("🔄 ELO")
        self.btn_refresh_elo.setToolTip("Refresh ELO ratings from ratings.json file")
        self.debug_verbose = QCheckBox("Debug")
        for b in (self.btn_auto, self.btn_pause, self.btn_auto_play, self.btn_copy_san, self.btn_copy_pgn, self.btn_save_png, self.btn_refresh_elo, self.debug_verbose):
            btn_row.addWidget(b)
        right_col.addLayout(btn_row)

        # Зв’язки
        self.btn_auto.clicked.connect(self.start_auto)
        self.btn_pause.clicked.connect(self.pause_auto)
        self.btn_auto_play.clicked.connect(self.start_auto_play)
        self.btn_copy_san.clicked.connect(self.copy_san)
        self.btn_copy_pgn.clicked.connect(self.copy_pgn)
        self.btn_save_png.clicked.connect(self.save_png)
        self.btn_refresh_elo.clicked.connect(self._refresh_elo_ratings)

        # Створюємо таби
        self.tab_widget = QTabWidget()
        right_col.addWidget(self.tab_widget)

        # Таб 1: Статуси та метрики
        self.status_tab = QWidget()
        status_layout = QVBoxLayout(self.status_tab)

        # Статуси
        self.lbl_module   = QLabel("Модуль: —")
        self.lbl_features = QLabel("Фічі: —")
        self.lbl_threat   = QLabel("ThreatMap: —")
        self.lbl_attacks  = QLabel("Attacks: —")
        self.lbl_leaders  = QLabel("Attack leaders: —")
        self.lbl_king     = QLabel("King coeff: —")

        for lab in (
            self.lbl_module,
            self.lbl_features,
            self.lbl_threat,
            self.lbl_attacks,
            self.lbl_leaders,
            self.lbl_king,
        ):
            lab.setWordWrap(True)
            status_layout.addWidget(lab)
        
        status_layout.addStretch()
        self.tab_widget.addTab(self.status_tab, "📊 Статуси")

        # Підготовка віджетів для вкладок (табів)
        self.chart_usage_w = OverallUsageChart()
        self.chart_usage_b = OverallUsageChart()

        # Список ходів SAN
        self.moves_list = QListWidget()

        # Таймлайн застосованих модулів
        self.timeline = UsageTimeline()
        self.timeline.moveClicked.connect(self._on_timeline_click)
        # Таб 2: Usage та Timeline
        self.usage_tab = QWidget()
        usage_layout = QVBoxLayout(self.usage_tab)
        
        usage_layout.addWidget(QLabel("Dynamic usage (W):"))
        self.chart_usage_w = OverallUsageChart()
        usage_layout.addWidget(self.chart_usage_w)

        usage_layout.addWidget(QLabel("Dynamic usage (B):"))
        self.chart_usage_b = OverallUsageChart()
        usage_layout.addWidget(self.chart_usage_b)

        # Таймлайн застосованих модулів
        usage_layout.addWidget(QLabel("Usage timeline:"))
        self.timeline = UsageTimeline()
        self.timeline.moveClicked.connect(self._on_timeline_click)
        usage_layout.addWidget(self.timeline)
        
        usage_layout.addStretch()
        self.tab_widget.addTab(self.usage_tab, "📈 Usage")

        # Таб 3: Ходи
        self.moves_tab = QWidget()
        moves_layout = QVBoxLayout(self.moves_tab)
        
        moves_layout.addWidget(QLabel("Moves:"))
        self.moves_list = QListWidget()
        moves_layout.addWidget(self.moves_list)
        
        moves_layout.addStretch()
        self.tab_widget.addTab(self.moves_tab, "♟️ Ходи")

        # Таб 4: Heatmaps
        self.heatmap_tab = QWidget()
        heatmap_layout = QVBoxLayout(self.heatmap_tab)
        
        # Heatmap statistics
        self.heatmap_stats_label = QLabel()
        self.heatmap_stats_label.setWordWrap(True)
        self.heatmap_stats_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        heatmap_layout.addWidget(self.heatmap_stats_label)
        
        # Heatmap selection panel
        # Побудова вкладки Heatmaps (контент відрізняється залежно від наявності карт)
        heatmaps_tab = QWidget()
        heatmaps_tab_layout = QVBoxLayout(heatmaps_tab)
        if self.drawer_manager.heatmaps:
            heatmap_panel_layout, self.heatmap_set_combo, self.heatmap_piece_combo = create_heatmap_panel(
                self._on_heatmap_piece,
                set_callback=self._on_heatmap_set,
                sets=self.drawer_manager.list_heatmap_sets(),
                pieces=list(self.drawer_manager.heatmaps),
                current_set=default_heatmap_set,
                current_piece=default_heatmap_piece,
            )
            heatmap_layout.addLayout(heatmap_panel_layout)
            self._populate_heatmap_pieces(default_heatmap_piece)
            self._sync_heatmap_set_selection()
            self._save_heatmap_preferences(
                set_name=self.drawer_manager.active_heatmap_set,
                piece_name=self.drawer_manager.active_heatmap_piece,
            )
            heatmaps_tab_layout.addStretch(1)
        else:
            msg = QLabel(
                "🔍 <b>Heatmap Visualization Unavailable</b><br><br>"
                "<b>What are heatmaps?</b><br>"
                "Heatmaps show piece movement patterns and strategic hotspots on the chess board. "
                "They help visualize where pieces are most likely to move or be most effective.<br><br>"
                "<b>How to enable heatmaps:</b><br>"
                "1. <b>Python method:</b> Run <code>utils.integration.generate_heatmaps</code><br>"
                "2. <b>R script:</b> Execute <code>analysis/heatmaps/generate_heatmaps.R</code><br>"
                "3. <b>Quick fix:</b> Click 'Generate heatmaps' button below<br><br>"
                "<b>Requirements:</b> R or Wolfram Engine must be installed for heatmap generation."
            )
            msg.setWordWrap(True)
            msg.setStyleSheet("QLabel { background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 10px; }")
            heatmap_layout.addWidget(msg)
            btn_gen_heatmaps = QPushButton("🔧 Generate heatmaps now")
            btn_gen_heatmaps.setStyleSheet("QPushButton { background-color: #007bff; color: white; border: none; padding: 8px; border-radius: 4px; }")
            btn_gen_heatmaps.clicked.connect(self._generate_heatmaps)
            heatmap_layout.addWidget(btn_gen_heatmaps)
        
        heatmap_layout.addStretch()
        self.tab_widget.addTab(self.heatmap_tab, "🔥 Heatmaps")

        # Таб 5: Загальна статистика
        self.overall_tab = QWidget()
        overall_layout = QVBoxLayout(self.overall_tab)
        
        # Загальна діаграма використання модулів
        overall_layout.addWidget(QLabel("Overall module usage:"))
        self.overall_chart = OverallUsageChart()
        runs = load_runs("runs")
        self.overall_chart.set_data(aggregate_module_usage(runs))
        chart_scroll = QScrollArea()
        chart_scroll.setWidgetResizable(True)
        chart_scroll.setWidget(self.overall_chart)
        overall_layout.addWidget(chart_scroll)
        
        overall_layout.addStretch()
        self.tab_widget.addTab(self.overall_tab, "📊 Загальна статистика")

        # Додаємо таби до основного лейауту (вже створені вище)

        # ---- ГОЛОВНИЙ ЛЕЙАУТ ----
        main = QHBoxLayout(self.central_widget)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(12)
        main.addLayout(left_col, stretch=0)
        main.addLayout(right_col, stretch=1)

        self.board_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Таймер автогри
        self.auto_timer = QTimer()
        self.auto_timer.setInterval(1000)  # Збільшено інтервал для стабільності
        self.auto_timer.timeout.connect(self.auto_step)
        self.auto_running = False
        self.move_in_progress = False
        
        # Настройки автоматического воспроизведения
        self.auto_play_games = 10  # Количество игр для автоматического воспроизведения
        self.current_auto_game = 0
        self.auto_play_results = []  # Результаты автоматических игр
        self.auto_play_mode = False  # Режим автоматического воспроизведения

        # Початкова ініціалізація
        self._init_pieces()
        if default_heatmap_piece:
            self.drawer_manager.collect_overlays(self.piece_objects, self.board)
        self._refresh_board()
        self._update_status("-", None)
        
        # Оновлюємо статистику хітмапів
        self._update_heatmap_stats()
        
        # Refresh ELO ratings display
        self._refresh_elo_ratings()
        
        # Ensure proper window sizing and scrolling
        self._configure_window()

    # ---------- UI helpers ----------

    def _configure_window(self):
        """Configure window sizing and ensure proper content display"""
        # Set minimum window size to ensure all content is visible
        self.setMinimumSize(1000, 700)
        
        # Ensure the central widget can expand properly
        self.central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set window properties for better display on different platforms
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        # Ensure proper resizing behavior
        self.resize(1200, 800)

    def _piece_type_to_name(self, piece_type: int) -> str | None:
        mapping = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king",
        }
        return mapping.get(piece_type)

    def _update_heatmap_counts(self) -> None:
        """Показати кількість активних клітин теплокарт (> 0) по фігурам і сумарно."""
        try:
            # Ліниве створення лейблу, якщо тепер з'явилися хітмапи
            if not hasattr(self, "lbl_heatmap_counts") or self.lbl_heatmap_counts is None:
                # Спробуємо додати віджет у вкладку Heatmaps
                layout = getattr(self.heatmap_tab, 'layout', lambda: None)()
                if layout and callable(getattr(layout, 'addWidget', None)):
                    layout.addWidget(QLabel("Статистика теплокарт:"))
                    self.lbl_heatmap_counts = QLabel()
                    self.lbl_heatmap_counts.setWordWrap(True)
                    self.lbl_heatmap_counts.setStyleSheet(
                        "QLabel { background-color: #f3f6ff; border: 1px solid #ccd8ff; border-radius: 4px; padding: 6px; }"
                    )
                    layout.addWidget(self.lbl_heatmap_counts)
                else:
                    return
            heatmaps = self.drawer_manager.heatmaps or {}
            if not heatmaps:
                self.lbl_heatmap_counts.setText("Набір теплокарт порожній.")
                return
            parts = []
            total_cells = 0
            for name, grid in sorted(heatmaps.items()):
                # grid очікується як 8x8; рахуємо клітини з інтенсивністю > 0
                try:
                    cnt = sum(1 for row in grid for v in row if (v or 0) > 0)
                except Exception:
                    cnt = 0
                total_cells += cnt
                parts.append(f"{name}: {cnt}")
            summary = f"Всього: {total_cells} | " + ", ".join(parts)
            self.lbl_heatmap_counts.setText(summary)
        except Exception as exc:
            logger.warning(f"Failed to compute heatmap counts: {exc}")

    def _update_title_with_elo(self):
        """Update the title to include ELO ratings for both bots."""
        try:
            # Get ELO ratings for both bots
            white_rating = self.elo_manager.get_bot_rating(WHITE_AGENT)
            black_rating = self.elo_manager.get_bot_rating(BLACK_AGENT)
            
            # Format ELO display with additional info
            white_elo_text = ""
            black_elo_text = ""
            
            if white_rating:
                games_text = f" ({white_rating.games_played} games)" if white_rating.games_played > 0 else ""
                white_elo_text = f" (ELO: {white_rating.elo:.0f}{games_text})"
            if black_rating:
                games_text = f" ({black_rating.games_played} games)" if black_rating.games_played > 0 else ""
                black_elo_text = f" (ELO: {black_rating.elo:.0f}{games_text})"
            
            # Update title
            title_text = f"White: {WHITE_AGENT}{white_elo_text}    |    Black: {BLACK_AGENT}{black_elo_text}"
            self.title_label.setText(title_text)
            
        except Exception as exc:
            logger.warning(f"Failed to load ELO ratings: {exc}")
            # Fallback to basic title without ELO
            self.title_label.setText(f"White: {WHITE_AGENT}    |    Black: {BLACK_AGENT}")

    def _count_heatmaps(self):
        """Підрахувати кількість хітмапів по фігурам та загально."""
        try:
            piece_counts = {}
            total_heatmaps = 0
            
            # Підрахунок хітмапів по фігурам
            for piece_name, heatmap_data in self.drawer_manager.heatmaps.items():
                if isinstance(heatmap_data, list) and len(heatmap_data) > 0:
                    # Перевіряємо, чи це двовимірний масив (8x8)
                    if isinstance(heatmap_data[0], list) and len(heatmap_data) == 8:
                        piece_counts[piece_name] = 1
                        total_heatmaps += 1
                    else:
                        piece_counts[piece_name] = len(heatmap_data)
                        total_heatmaps += len(heatmap_data)
                else:
                    piece_counts[piece_name] = 0
            
            return piece_counts, total_heatmaps
            
        except Exception as exc:
            logger.warning(f"Failed to count heatmaps: {exc}")
            return {}, 0

    def _update_heatmap_stats(self):
        """Оновити статистику хітмапів у вкладці."""
        try:
            piece_counts, total_heatmaps = self._count_heatmaps()
            
            if total_heatmaps == 0:
                stats_text = "🔥 <b>Heatmap Statistics</b><br>No heatmaps available"
            else:
                stats_text = f"🔥 <b>Heatmap Statistics</b><br>"
                stats_text += f"<b>Total heatmaps:</b> {total_heatmaps}<br>"
                stats_text += f"<b>By piece type:</b><br>"
                
                for piece_name, count in sorted(piece_counts.items()):
                    if count > 0:
                        stats_text += f"  • {piece_name}: {count}<br>"
                
                # Додаємо інформацію про активний хітмап
                if self.drawer_manager.active_heatmap_piece:
                    stats_text += f"<br><b>Active:</b> {self.drawer_manager.active_heatmap_piece}"
                else:
                    stats_text += f"<br><b>Active:</b> None"
            
            self.heatmap_stats_label.setText(stats_text)
            
        except Exception as exc:
            logger.warning(f"Failed to update heatmap stats: {exc}")
            self.heatmap_stats_label.setText("🔥 <b>Heatmap Statistics</b><br>Error loading statistics")

    def _ensure_bots_registered(self):
        """Ensure both bots are registered in the ELO system with initial ratings."""
        try:
            # Register bots with default ELO ratings if not already registered
            if not self.elo_manager.get_bot_rating(WHITE_AGENT):
                self.elo_manager.register_bot(WHITE_AGENT, 1500.0)
                logger.info(f"Registered {WHITE_AGENT} with initial ELO 1500")
            
            if not self.elo_manager.get_bot_rating(BLACK_AGENT):
                self.elo_manager.register_bot(BLACK_AGENT, 1500.0)
                logger.info(f"Registered {BLACK_AGENT} with initial ELO 1500")
                
        except Exception as exc:
            logger.warning(f"Failed to register bots: {exc}")

    def _refresh_elo_ratings(self):
        """Refresh ELO ratings from the ratings file and update display."""
        try:
            # Reload ratings from file
            self.elo_manager.load_ratings()
            self._update_title_with_elo()
            logger.info("ELO ratings refreshed successfully")
        except Exception as exc:
            logger.error(f"Failed to refresh ELO ratings: {exc}")
            QMessageBox.warning(
                self,
                "⚠️ ELO Refresh Failed",
                f"🔧 <b>Failed to refresh ELO ratings:</b> {exc}\n\n"
                f"<b>This may indicate:</b>\n"
                f"• Ratings file is missing or corrupted\n"
                f"• ELO sync manager is not properly initialized\n"
                f"• File permission issues\n\n"
                f"<b>Try:</b>\n"
                f"• Check if ratings.json exists\n"
                f"• Verify file permissions\n"
                f"• Restart the application"
            )

    def _draw_board_widgets(self):
        for row in range(8):
            for col in range(8):
                cell = Cell(row, col, self.drawer_manager)
                self.grid.addWidget(cell, row, col)
                self.cell_grid[row][col] = cell

    def _init_pieces(self):
        try:
            self.piece_objects.clear()
            for square in chess.SQUARES:
                piece = self.board.piece_at(square)
                if piece:
                    pos = (chess.square_rank(square), chess.square_file(square))
                    self.piece_objects[square] = piece_class_factory(piece, pos)
        except Exception as exc:
            logger.error(f"Failed to initialize pieces: {exc}")
            QMessageBox.warning(
                self,
                "⚠️ Piece Initialization Error",
                f"🔧 <b>Failed to initialize chess pieces:</b> {exc}\n\n"
                f"<b>This may cause display issues.</b> Try refreshing the board."
            )

    def _refresh_board(self):
        try:
            # Оверлеї
            for sq, obj in self.piece_objects.items():
                try:
                    name = obj.__class__.__name__
                    if name == "King":
                        obj.update_king_moves(self.board)
                    elif name == "Rook":
                        obj.update_defended(self.board)
                    elif name == "Knight":
                        obj.update_fork(self.board)
                    elif name == "Queen":
                        obj.update_hanging(self.board)
                        obj.update_pin_and_check(self.board)
                except Exception as exc:
                    logger.warning(f"Failed to update piece {obj.__class__.__name__} at square {sq}: {exc}")

            self.drawer_manager.collect_overlays(self.piece_objects, self.board)

            # Символи та лічильники атак на клітинках
            for row in range(8):
                for col in range(8):
                    try:
                        square = chess.square(col, 7 - row)
                        piece = self.board.piece_at(square)
                        cell = self.cell_grid[row][col]
                        cell.set_piece(piece.symbol() if piece else None)
                        attackers = self.board.attackers(not self.board.turn, square)
                        cell.set_attack_count(len(attackers))
                        cell.set_highlight(False)
                        cell.update()
                    except Exception as exc:
                        logger.warning(f"Failed to update cell at row {row}, col {col}: {exc}")
                        
        except Exception as exc:
            logger.error(f"Failed to refresh board: {exc}")
            QMessageBox.warning(
                self,
                "⚠️ Board Refresh Error",
                f"🔧 <b>Failed to refresh the chess board:</b> {exc}\n\n"
                f"<b>This may cause display issues.</b> Try restarting the game."
            )

    # ---------- Контролери гри ----------

    def start_auto(self):
        # Якщо стартуємо з початку партії — скинемо usage і таймлайн
        if not self.board.move_stack:
            self.usage_w.clear()
            self.usage_b.clear()
            self.timeline_w.clear()
            self.timeline_b.clear()
            self.timeline.set_data(self.timeline_w, self.timeline_b)
            self._update_usage_charts()
            self.moves_list.clear()
            self.fen_history.clear()

        if not self.auto_running:
            self.auto_running = True
            self.auto_timer.start()
            self.auto_step()

    def pause_auto(self):
        self.auto_timer.stop()
        self.auto_running = False
        
    def start_auto_play(self):
        """Начать автоматическое воспроизведение 10 игр подряд"""
        self.auto_play_mode = True
        self.current_auto_game = 0
        self.auto_play_results = []
        self.btn_auto_play.setEnabled(False)
        self.btn_auto.setEnabled(False)
        self.btn_pause.setEnabled(True)
        
        # Очищаем консоль и добавляем начальное сообщение
        self.console_output.clear()
        self._append_to_console("=== Starting Auto Play Mode ===")
        self._append_to_console(f"Playing {self.auto_play_games} games: {WHITE_AGENT} vs {BLACK_AGENT}")
        self._append_to_console("")
        
        # Обновляем заголовок
        self.setWindowTitle(f"Chess Viewer — Auto Play Mode (Game 1/{self.auto_play_games})")
        
        # Начинаем первую игру
        self._start_next_auto_game()
        
    def _start_next_auto_game(self):
        """Начать следующую игру в режиме автоматического воспроизведения"""
        if self.current_auto_game >= self.auto_play_games:
            self._finish_auto_play()
            return
            
        # Сбрасываем доску для новой игры
        self.board = chess.Board()
        self.piece_objects = {}
        self.usage_w.clear()
        self.usage_b.clear()
        self.timeline_w.clear()
        self.timeline_b.clear()
        self.timeline.set_data(self.timeline_w, self.timeline_b)
        self._update_usage_charts()
        self.moves_list.clear()
        self.fen_history.clear()
        
        # Добавляем информацию о новой игре в консоль
        self._append_to_console(f"--- Starting Game {self.current_auto_game + 1} ---")
        
        # Инициализируем фигуры
        self._init_pieces()
        self._refresh_board()
        self._update_status("-", None)
        
        # Обновляем заголовок
        self.setWindowTitle(f"Chess Viewer — Auto Play Mode (Game {self.current_auto_game + 1}/{self.auto_play_games})")
        
        # Начинаем автоматическую игру
        self.auto_running = True
        self.auto_timer.start()
        self.auto_step()
        
    def _finish_auto_play(self):
        """Завершить автоматическое воспроизведение"""
        self.auto_play_mode = False
        self.auto_running = False
        self.auto_timer.stop()
        
        # Восстанавливаем кнопки
        self.btn_auto_play.setEnabled(True)
        self.btn_auto.setEnabled(True)
        self.btn_pause.setEnabled(False)
        
        # Обновляем заголовок
        self.setWindowTitle("Chess Viewer — Auto Play Complete")
        
        # Показываем статистику в консоли
        self._show_auto_play_summary_in_console()
        
    def _show_auto_play_summary_in_console(self):
        """Показать сводку автоматических игр в консоли"""
        if not self.auto_play_results:
            return
            
        # Подсчитываем статистику
        results_count = {}
        total_moves = 0
        total_duration = 0
        
        for result in self.auto_play_results:
            game_result = result.get('result', '*')
            results_count[game_result] = results_count.get(game_result, 0) + 1
            total_moves += result.get('moves', 0)
            total_duration += result.get('duration_ms', 0)
            
        # Добавляем сводку в консоль
        self._append_to_console("=" * 50)
        self._append_to_console("🎮 AUTO PLAY SUMMARY")
        self._append_to_console("=" * 50)
        self._append_to_console(f"Total games: {len(self.auto_play_results)}")
        self._append_to_console("")
        self._append_to_console("Results:")
        
        for result, count in results_count.items():
            percentage = (count / len(self.auto_play_results)) * 100
            self._append_to_console(f"  {result}: {count} games ({percentage:.1f}%)")
            
        self._append_to_console("")
        self._append_to_console("Statistics:")
        self._append_to_console(f"  Total moves: {total_moves}")
        self._append_to_console(f"  Average moves per game: {total_moves / len(self.auto_play_results):.1f}")
        self._append_to_console(f"  Total duration: {total_duration / 1000:.1f}s")
        self._append_to_console(f"  Average game duration: {total_duration / len(self.auto_play_results) / 1000:.1f}s")
        self._append_to_console("=" * 50)
        self._append_to_console("Auto Play Complete!")
        self._append_to_console("")

    def auto_step(self):
        try:
            # Захист від реентрантних викликів, поки застосування попереднього ходу не завершено
            if self.move_in_progress:
                return
            if self.board.is_game_over():
                if self.auto_play_mode:
                    self._handle_auto_play_game_over()
                else:
                    self.pause_auto()
                    self._show_game_over()
                return

            # Спрощена логіка без складного таймінгу

            mover_color = self.board.turn
            agent = self.white_agent if mover_color == chess.WHITE else self.black_agent

            # Отримати хід з обробкою помилок
            try:
                move = agent.choose_move(self.board)
            except Exception as exc:
                logger.error(f"Agent {agent.__class__.__name__} failed to choose move: {exc}")
                self.pause_auto()
                QMessageBox.warning(
                    self,
                    "⚠️ AI Agent Error",
                    f"🤖 <b>Agent failed to choose a move:</b>\n\n"
                    f"<b>Agent:</b> {agent.__class__.__name__}\n"
                    f"<b>Error:</b> {exc}\n\n"
                    f"<b>Game paused.</b> You can try resuming or resetting the game."
                )
                return

            if move is None:
                self.pause_auto()
                self._show_game_over()
                return

            # Перевірити легальність ходу
            if not self.board.is_legal(move):
                logger.error(f"Agent {agent.__class__.__name__} returned illegal move: {move}")
                self.pause_auto()
                QMessageBox.warning(
                    self,
                    "⚠️ Invalid Move",
                    f"🚫 <b>Agent returned an illegal move:</b> {move}\n\n"
                    f"<b>Agent:</b> {agent.__class__.__name__}\n"
                    f"<b>Game paused.</b> This may indicate a bug in the agent logic."
                )
                return

            # Підготовка до попереднього показу теплокарти фігури, що ходить
            san = self.board.san(move)  # до push
            move_no = self.board.fullmove_number
            prefix = f"{move_no}. " if mover_color == chess.WHITE else f"{move_no}... "

            moving_piece = self.board.piece_at(move.from_square)
            piece_name = self._piece_type_to_name(moving_piece.piece_type) if moving_piece else None
            if piece_name and piece_name in self.drawer_manager.heatmaps:
                # Увімкнути відповідну теплокарту і оновити оверлеї перед ходом
                self.drawer_manager.active_heatmap_piece = piece_name
                # Не змінюємо вибір у комбобоксі нав’язливо; але якщо він є — синхронізуємо
                if self.heatmap_piece_combo:
                    idx = self.heatmap_piece_combo.findText(piece_name)
                    if idx >= 0 and self.heatmap_piece_combo.currentIndex() != idx:
                        self.heatmap_piece_combo.blockSignals(True)
                        self.heatmap_piece_combo.setCurrentIndex(idx)
                        self.heatmap_piece_combo.blockSignals(False)
                self._refresh_board()

            # Застосовуємо хід одразу
            self.board.push(move)
            self.fen_history.append(self.board.fen())

            # Оновлюємо дошку
            self._init_pieces()
            self._refresh_board()

            # Отримуємо інформацію про хід
            reason = agent.get_last_reason() if hasattr(agent, "get_last_reason") else "-"
            feats = agent.get_last_features() if hasattr(agent, "get_last_features") else None

            # Оновлюємо статистику
            key = self._extract_reason_key(reason)
            if mover_color == chess.WHITE:
                self.usage_w[key] += 1
                self.timeline_w.append(key)
            else:
                self.usage_b[key] += 1
                self.timeline_b.append(key)

            # Додаємо хід до списку
            self.moves_list.addItem(f"{prefix}{san}")
            self.moves_list.setCurrentRow(self.moves_list.count() - 1)
            self.moves_list.scrollToBottom()

            # Оновлюємо статус
            self._update_status(reason, feats)

            # Консольний вивід
            if self.debug_verbose.isChecked():
                print(f"[{WHITE_AGENT if mover_color==chess.WHITE else BLACK_AGENT}] {san} | reason={reason} | key={key} | feats={feats}")

            if self.auto_play_mode:
                move_info = f"Move {len(self.board.move_stack)}: {prefix}{san} ({key})"
                self._append_to_console(move_info)

            # Знімаємо блокування
            self.move_in_progress = False
                
        except Exception as exc:
            logger.error(f"Unexpected error in auto_step: {exc}")
            if self.auto_play_mode:
                self._handle_auto_play_error(exc)
            else:
                self.pause_auto()
                QMessageBox.critical(
                    self,
                    "❌ Game Error",
                    f"🚨 <b>An unexpected error occurred during gameplay:</b>\n\n"
                    f"<b>Error:</b> {exc}\n\n"
                    f"<b>Game paused.</b> You may need to restart the application."
                )


    def _load_heatmap_for_piece(self, move):
        """Завантажити хітмап для фігури, яка робить хід."""
        try:
            # Отримуємо фігуру, яка робить хід
            piece = self.board.piece_at(move.from_square)
            if piece is None:
                return
            
            # Визначаємо тип фігури
            piece_type = piece.piece_type
            piece_name = None
            
            if piece_type == chess.PAWN:
                piece_name = "pawn"
            elif piece_type == chess.KNIGHT:
                piece_name = "knight"
            elif piece_type == chess.BISHOP:
                piece_name = "bishop"
            elif piece_type == chess.ROOK:
                piece_name = "rook"
            elif piece_type == chess.QUEEN:
                piece_name = "queen"
            elif piece_type == chess.KING:
                piece_name = "king"
            
            if piece_name and piece_name in self.drawer_manager.heatmaps:
                # Встановлюємо активний хітмап для цієї фігури
                self.drawer_manager.active_heatmap_piece = piece_name
                self._update_heatmap_stats()
                
                # Оновлюємо комбобокс, якщо він існує
                if self.heatmap_piece_combo:
                    self._populate_heatmap_pieces(piece_name)
                
                logger.info(f"Loaded heatmap for {piece_name} piece")
            
        except Exception as exc:
            logger.warning(f"Failed to load heatmap for piece: {exc}")
                
    def _handle_auto_play_game_over(self):
        """Обработка завершения игры в режиме автоматического воспроизведения"""
        import time
        
        # Сохраняем результат текущей игры
        result = self.board.result()
        moves_count = len(self.board.move_stack)
        duration_ms = int(time.time() * 1000)  # Простое время (можно улучшить)
        
        game_result = {
            'game_id': self.current_auto_game,
            'result': result,
            'moves': moves_count,
            'duration_ms': duration_ms,
            'modules_w': list(self.usage_w.keys()),
            'modules_b': list(self.usage_b.keys()),
            'moves_san': self._moves_san_string(),
            'pgn': self._game_pgn_string()
        }
        
        self.auto_play_results.append(game_result)
        
        # Добавляем результат в консоль вместо показа окна
        self._append_to_console(f"=== Game {self.current_auto_game + 1} Complete ===")
        self._append_to_console(f"Result: {result}")
        self._append_to_console(f"Moves: {moves_count}")
        self._append_to_console(f"Duration: {duration_ms}ms")
        self._append_to_console(f"White modules: {', '.join(self.usage_w.keys())}")
        self._append_to_console(f"Black modules: {', '.join(self.usage_b.keys())}")
        self._append_to_console("")
        
        # Обновляем счетчик игр
        self.current_auto_game += 1
        
        # Небольшая пауза перед следующей игрой
        QTimer.singleShot(2000, self._start_next_auto_game)
        
    def _handle_auto_play_error(self, exc):
        """Обработка ошибки в режиме автоматического воспроизведения"""
        logger.error(f"Error in auto play game {self.current_auto_game + 1}: {exc}")
        
        # Сохраняем результат с ошибкой
        game_result = {
            'game_id': self.current_auto_game,
            'result': 'ERROR',
            'moves': len(self.board.move_stack),
            'duration_ms': 0,
            'error': str(exc),
            'modules_w': list(self.usage_w.keys()),
            'modules_b': list(self.usage_b.keys())
        }
        
        self.auto_play_results.append(game_result)
        
        # Добавляем ошибку в консоль
        self._append_to_console(f"=== Game {self.current_auto_game + 1} ERROR ===")
        self._append_to_console(f"Error: {exc}")
        self._append_to_console("")
        
        self.current_auto_game += 1
        
        # Продолжаем со следующей игрой
        QTimer.singleShot(1000, self._start_next_auto_game)
    
    def _append_to_console(self, text):
        """Добавить текст в консольный вывод"""
        self.console_output.append(text)
        # Автоматически прокручиваем вниз
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ---------- Копі-кнопки ----------

    def _moves_san_string(self) -> str:
        temp = chess.Board()
        parts = []
        for mv in self.board.move_stack:
            parts.append(temp.san(mv))
            temp.push(mv)
        out = []
        for i, san in enumerate(parts, start=1):
            if i % 2 == 1:
                move_no = (i + 1) // 2
                out.append(f"{move_no}. {san}")
            else:
                out.append(san)
        return " ".join(out)

    def _game_pgn_string(self) -> str:
        res = self.board.result() if self.board.is_game_over() else "*"
        return (
            f"[Event \"Viewer\"]\n[Site \"Local\"]\n"
            f"[White \"{WHITE_AGENT}\"]\n[Black \"{BLACK_AGENT}\"]\n"
            f"[Result \"{res}\"]\n\n{self._moves_san_string()} {res}\n"
        )

    def copy_san(self):
        try:
            san_text = self._moves_san_string()
            QApplication.clipboard().setText(san_text, QClipboard.Clipboard)
            QMessageBox.information(
                self, 
                "✅ Copied Successfully", 
                f"📋 <b>SAN sequence copied to clipboard</b>\n\n"
                f"<b>Moves:</b> {san_text[:100]}{'...' if len(san_text) > 100 else ''}"
            )
        except Exception as exc:
            logger.error(f"Failed to copy SAN: {exc}")
            QMessageBox.critical(
                self,
                "❌ Copy Failed",
                f"🚨 <b>Failed to copy SAN sequence:</b> {exc}\n\n"
                f"<b>Try:</b>\n"
                f"• Check if clipboard is accessible\n"
                f"• Try again in a moment\n"
                f"• Restart the application if the problem persists"
            )

    def copy_pgn(self):
        try:
            pgn_text = self._game_pgn_string()
            QApplication.clipboard().setText(pgn_text, QClipboard.Clipboard)
            QMessageBox.information(
                self, 
                "✅ Copied Successfully", 
                f"📋 <b>PGN game copied to clipboard</b>\n\n"
                f"<b>Game:</b> {pgn_text[:200]}{'...' if len(pgn_text) > 200 else ''}"
            )
        except Exception as exc:
            logger.error(f"Failed to copy PGN: {exc}")
            QMessageBox.critical(
                self,
                "❌ Copy Failed",
                f"🚨 <b>Failed to copy PGN game:</b> {exc}\n\n"
                f"<b>Try:</b>\n"
                f"• Check if clipboard is accessible\n"
                f"• Try again in a moment\n"
                f"• Restart the application if the problem persists"
            )

    def save_png(self):
        """Save current board state as PNG image for XRPA analysis."""
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти PNG для XRPA",
            f"xrpa_analysis_{len(self.board.move_stack)}.png",
            "PNG Images (*.png);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Capture the board frame as pixmap
            pixmap = self.board_frame.grab()
            
            # Add metadata overlay with current position info
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setFont(QFont("Arial", 12))
            
            # Add position info
            fen = self.board.fen()
            move_count = len(self.board.move_stack)
            turn = "White" if self.board.turn == chess.WHITE else "Black"
            
            info_text = f"Move: {move_count} | Turn: {turn}\nFEN: {fen[:50]}..."
            painter.drawText(10, 20, info_text)
            
            # Add heatmap info if active
            if self.drawer_manager.active_heatmap_piece:
                heatmap_text = f"Heatmap: {self.drawer_manager.active_heatmap_piece}"
                painter.drawText(10, 50, heatmap_text)
            
            painter.end()
            
            # Save the image
            pixmap.save(file_path, "PNG")
            
            # Also save UI data as JSON for XRPA analysis
            json_path = file_path.replace('.png', '_data.json')
            ui_data = self.drawer_manager.export_ui_data()
            ui_data.update({
                "fen": fen,
                "move_count": move_count,
                "turn": turn,
                "heatmap_piece": self.drawer_manager.active_heatmap_piece,
                "heatmap_set": self.drawer_manager.active_heatmap_set,
                "timestamp": QTimer().remainingTime()  # Simple timestamp
            })
            
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ui_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self, 
                "Збережено", 
                f"PNG збережено: {file_path}\nJSON дані: {json_path}"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Не вдалося зберегти PNG: {e}")

    def _auto_save_xrpa_png(self, result):
        """Automatically save PNG for XRPA analysis when game ends."""
        import os
        from datetime import datetime
        
        # Create XRPA output directory
        xrpa_dir = "xrpa_analysis"
        os.makedirs(xrpa_dir, exist_ok=True)
        
        # Generate filename with timestamp and result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"xrpa_{timestamp}_{result.replace('-', '_')}_{len(self.board.move_stack)}moves.png"
        file_path = os.path.join(xrpa_dir, filename)
        
        # Capture board as pixmap
        pixmap = self.board_frame.grab()
        
        # Add metadata overlay
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setFont(QFont("Arial", 10))
        
        # Add game info
        fen = self.board.fen()
        move_count = len(self.board.move_stack)
        turn = "White" if self.board.turn == chess.WHITE else "Black"
        
        info_lines = [
            f"XRPA Analysis - {timestamp}",
            f"Result: {result} | Moves: {move_count} | Turn: {turn}",
            f"White: {WHITE_AGENT} | Black: {BLACK_AGENT}",
            f"FEN: {fen[:60]}...",
        ]
        
        if self.drawer_manager.active_heatmap_piece:
            info_lines.append(f"Heatmap: {self.drawer_manager.active_heatmap_piece}")
        
        y_offset = 15
        for line in info_lines:
            painter.drawText(10, y_offset, line)
            y_offset += 15
        
        painter.end()
        
        # Save PNG
        pixmap.save(file_path, "PNG")
        
        # Save JSON data
        json_path = file_path.replace('.png', '_data.json')
        ui_data = self.drawer_manager.export_ui_data()
        ui_data.update({
            "fen": fen,
            "result": result,
            "move_count": move_count,
            "turn": turn,
            "white_agent": WHITE_AGENT,
            "black_agent": BLACK_AGENT,
            "heatmap_piece": self.drawer_manager.active_heatmap_piece,
            "heatmap_set": self.drawer_manager.active_heatmap_set,
            "timestamp": timestamp,
            "moves_san": self._moves_san_string(),
            "game_pgn": self._game_pgn_string()
        })
        
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ui_data, f, indent=2, ensure_ascii=False)
        
        print(f"XRPA analysis saved: {file_path}")

    # ---------- Метрики / статуси ----------

    def _truthy_features_preview(self, feats: dict | None) -> str:
        if not feats:
            return "—"
        items = []
        for k, v in feats.items():
            if isinstance(v, bool):
                if v: items.append(k)
            elif isinstance(v, (int, float)):
                if v != 0: items.append(f"{k}={v}")
            elif isinstance(v, (list, tuple, set)):
                if v: items.append(f"{k}[{len(v)}]")
            elif isinstance(v, dict):
                if v: items.append(f"{k}{{{len(v)}}}")
            elif isinstance(v, str):
                if v: items.append(f"{k}={v}")
            else:
                if v: items.append(f"{k}={v}")
            if len(items) >= 10:
                break
        return ", ".join(items) if items else "—"

    def _phase(self) -> str:
        count = sum(1 for pc in self.board.piece_map().values() if pc.piece_type != chess.KING)
        if count <= 12: return "endgame"
        if count <= 20: return "midgame"
        return "opening"

    def _extract_reason_key(self, reason: str) -> str:
        """
        Витягуємо «ключ модуля/тега» із reason:
        - спочатку шукаємо токени з whitelist (REASON_PRIORITY) у заданому порядку;
        - інакше беремо перший UPPER_CASE токен з рядка;
        - інакше 'OTHER'.
        """
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

    def _update_usage_charts(self) -> None:
        """Refresh per-side usage charts with current counts."""
        try:
            self.chart_usage_w.set_data(self.usage_w)
            self.chart_usage_b.set_data(self.usage_b)
        except Exception as exc:
            logger.warning(f"Failed to update usage charts: {exc}")
            # Charts will show empty data rather than crashing

    def _generate_heatmaps(self) -> None:
        """Invoke heatmap generation and notify the user."""
        try:
            fens_file = Path("fens.txt")
            if fens_file.exists():
                with fens_file.open("r", encoding="utf-8") as fh:
                    fens = [line.strip() for line in fh if line.strip()]
                logger.info(f"📁 Loaded {len(fens)} FEN positions from fens.txt")
            else:
                fens = [self.board.fen()]
                logger.info("📁 Using current board position for heatmap generation")
            
            logger.info("🔄 Starting heatmap generation...")
            generate_heatmaps(fens, pattern_set="default")
            
            # Оновлюємо статистику після генерації
            self.drawer_manager._load_heatmaps()
            self._update_heatmap_stats()
            
            QMessageBox.information(
                self,
                "✅ Heatmaps Generated Successfully",
                f"🎉 Heatmap generation completed!\n\n"
                f"📊 Generated heatmaps for {len(fens)} position(s)\n"
                f"📁 Saved to: analysis/heatmaps/default/\n\n"
                f"🔄 Heatmap statistics updated!",
            )
        except FileNotFoundError as exc:
            if "Rscript" in str(exc) or "wolframscript" in str(exc):
                ErrorHandler.handle_heatmap_error(exc, "missing software")
                QMessageBox.critical(
                    self,
                    "❌ Missing Required Software",
                    f"🔧 <b>Required software not found:</b> {exc}\n\n"
                    f"<b>To fix this:</b>\n"
                    f"• Install R from https://www.r-project.org/\n"
                    f"• OR install Wolfram Engine from https://www.wolfram.com/engine/\n\n"
                    f"<b>After installation:</b>\n"
                    f"• Restart your terminal/command prompt\n"
                    f"• Try generating heatmaps again"
                )
            else:
                ErrorHandler.handle_file_error(exc, "heatmap generation")
                QMessageBox.critical(
                    self,
                    "❌ File Not Found",
                    f"🔍 <b>Missing file:</b> {exc}\n\n"
                    f"<b>Possible solutions:</b>\n"
                    f"• Check if the file path is correct\n"
                    f"• Ensure the file exists and is readable\n"
                    f"• Try running the application from the correct directory"
                )
        except subprocess.CalledProcessError as exc:
            ErrorHandler.handle_heatmap_error(exc, "script execution")
            QMessageBox.critical(
                self,
                "❌ Script Execution Failed",
                f"🔧 <b>Heatmap generation script failed:</b>\n\n"
                f"<b>Error details:</b> {exc}\n\n"
                f"<b>Common causes:</b>\n"
                f"• R/Wolfram script has syntax errors\n"
                f"• Missing required R packages\n"
                f"• Insufficient permissions\n"
                f"• Corrupted script files\n\n"
                f"<b>Try:</b>\n"
                f"• Check R package installation\n"
                f"• Run the script manually to see detailed errors\n"
                f"• Reinstall the application"
            )
        except Exception as exc:
            ErrorHandler.handle_heatmap_error(exc, "unexpected error")
            QMessageBox.critical(
                self,
                "❌ Unexpected Error",
                f"🚨 <b>An unexpected error occurred:</b>\n\n"
                f"<b>Error:</b> {exc}\n\n"
                f"<b>Please try:</b>\n"
                f"• Restart the application\n"
                f"• Check available disk space\n"
                f"• Verify file permissions\n"
                f"• Report this issue if it persists"
            )

    def _sync_heatmap_set_selection(self) -> None:
        """Ensure the set combo reflects :class:`DrawerManager` state."""

        if not self.heatmap_set_combo:
            return
        active = self.drawer_manager.active_heatmap_set
        index = self.heatmap_set_combo.findText(active)
        if index >= 0 and self.heatmap_set_combo.currentIndex() != index:
            self.heatmap_set_combo.blockSignals(True)
            self.heatmap_set_combo.setCurrentIndex(index)
            self.heatmap_set_combo.blockSignals(False)

    def _populate_heatmap_pieces(self, current_piece: str | None) -> None:
        """Rebuild the piece combo according to the active set."""

        if not self.heatmap_piece_combo:
            return
        self.heatmap_piece_combo.blockSignals(True)
        self.heatmap_piece_combo.clear()
        self.heatmap_piece_combo.addItem("none")
        for name in self.drawer_manager.heatmaps:
            self.heatmap_piece_combo.addItem(name)

        selection = (
            current_piece
            if current_piece is not None
            else self.drawer_manager.active_heatmap_piece
        )
        if selection is None:
            self.heatmap_piece_combo.setCurrentIndex(0)
        else:
            idx = self.heatmap_piece_combo.findText(selection)
            if idx >= 0:
                self.heatmap_piece_combo.setCurrentIndex(idx)
            else:
                self.heatmap_piece_combo.setCurrentIndex(0)
        self.heatmap_piece_combo.setEnabled(self.heatmap_piece_combo.count() > 1)
        self.heatmap_piece_combo.blockSignals(False)

    def _save_heatmap_preferences(
        self, *, set_name: str | None = None, piece_name: str | None = None
    ) -> None:
        """Persist the chosen heatmap set/piece across viewer sessions."""

        if set_name is not None:
            self.settings.setValue("heatmap/set", set_name)
        if piece_name is not None:
            value = "none" if piece_name is None else piece_name
            self.settings.setValue("heatmap/piece", value)

    def _on_heatmap_set(self, set_name: str) -> None:
        """Callback for heatmap set selection."""

        if not set_name:
            return

        previous_piece_raw = self.settings.value("heatmap/piece")
        previous_piece_missing = previous_piece_raw is None
        previous_piece = None
        if not previous_piece_missing:
            previous_piece_str = str(previous_piece_raw)
            previous_piece = None if previous_piece_str == "none" else previous_piece_str

        self.drawer_manager.set_heatmap_set(set_name)
        self._sync_heatmap_set_selection()

        active_piece = self.drawer_manager.active_heatmap_piece
        if not previous_piece_missing:
            if previous_piece is None:
                active_piece = None
            elif previous_piece in self.drawer_manager.heatmaps:
                active_piece = previous_piece

        self.drawer_manager.active_heatmap_piece = active_piece
        self._populate_heatmap_pieces(active_piece)
        self._save_heatmap_preferences(
            set_name=self.drawer_manager.active_heatmap_set,
            piece_name=active_piece,
        )
        self._update_heatmap_stats()
        self._refresh_board()
        self._update_heatmap_counts()

    def _on_heatmap_piece(self, piece: str | None) -> None:
        """Callback for heatmap piece selection."""
        self.drawer_manager.active_heatmap_piece = piece
        self._save_heatmap_preferences(
            set_name=self.drawer_manager.active_heatmap_set,
            piece_name=piece,
        )
        self._update_heatmap_stats()
        self._refresh_board()
        # Підрахунки залежать від набору; але оновимо і тут для консистентності
        self._update_heatmap_counts()

    def _on_timeline_click(self, index: int, is_white: bool) -> None:
        """Handle click on the usage timeline by reporting the move index."""
        side = "W" if is_white else "B"
        print(f"Timeline click: {side} move {index}")
        row = index * 2 + (0 if is_white else 1)
        if row < self.moves_list.count():
            self.moves_list.setCurrentRow(row)
            self.moves_list.scrollToItem(self.moves_list.item(row))

    def _update_status(self, reason: str, feats: dict | None):
        try:
            self.lbl_module.setText(f"Модуль: {reason}")
            self.lbl_features.setText(f"Фічі: {self._truthy_features_preview(feats)}")

            try:
                metrics_lines = build_sidebar_metrics(
                    self.board,
                    {
                        chess.WHITE: self.tmap_white,
                        chess.BLACK: self.tmap_black,
                    },
                )
            except Exception as exc:
                logger.warning(f"Failed to build sidebar metrics: {exc}")
                metrics_lines = ["ThreatMap: Error", "Attacks: Error", "Leaders: Error", "King: Error"]

            # Ensure UI labels stay in sync even if helper adds/removes lines later.
            labels = (
                self.lbl_threat,
                self.lbl_attacks,
                self.lbl_leaders,
                self.lbl_king,
            )
            for label, text in zip(labels, metrics_lines):
                label.setText(text)
            for label in labels[len(metrics_lines):]:
                label.setText("")

            # Оновити usage-діаграми і графік
            self._update_usage_charts()
            self.timeline.set_data(self.timeline_w, self.timeline_b)
            
        except Exception as exc:
            logger.error(f"Failed to update status: {exc}")
            # Don't show error dialog for status updates to avoid spam

    def _show_critical_error(self, title: str, message: str):
        """Display a critical error message and close the application."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
        self.close()

    def _save_game_to_runs(self, result: str) -> None:
        """Save the current game to the runs folder."""
        import json
        import os
        from datetime import datetime
        
        # Create runs directory if it doesn't exist
        os.makedirs("runs", exist_ok=True)
        
        # Generate timestamp for filename
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_path = os.path.join("runs", f"{ts}.json")
        
        # Collect game data
        moves_log = []
        fens_log = []
        modules_w = []
        modules_b = []
        
        # Replay the game to collect data
        temp_board = chess.Board()
        for move in self.board.move_stack:
            san = temp_board.san(move)
            moves_log.append(san)
            temp_board.push(move)
            fens_log.append(temp_board.fen())
            
            # Get reason for the move (simplified - would need agent access)
            if temp_board.turn == chess.BLACK:  # Move was made by white
                modules_w.append("UI_Game")
            else:  # Move was made by black
                modules_b.append("UI_Game")
        
        # Save to file
        with open(run_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "moves": moves_log,
                    "fens": fens_log,
                    "modules_w": modules_w,
                    "modules_b": modules_b,
                    "result": result,
                    "white_agent": WHITE_AGENT,
                    "black_agent": BLACK_AGENT,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        
        logger.info(f"Game saved to {run_path}")

    def _update_elo_counter(self, result: str) -> None:
        """Update ELO ratings and game counter."""
        try:
            # Initialize ELO sync manager
            elo_manager = ELOSyncManager()
            
            # Determine winner
            if result == "1-0":
                winner = WHITE_AGENT
                loser = BLACK_AGENT
            elif result == "0-1":
                winner = BLACK_AGENT
                loser = WHITE_AGENT
            else:  # Draw
                winner = None
                loser = None
            
            # Update ratings
            if winner and loser:
                # Update winner
                winner_rating = elo_manager.get_bot_rating(winner)
                if winner_rating:
                    elo_manager.update_bot_rating(
                        winner, 
                        winner_rating.elo + 20,  # Simple +20 for win
                        "local",
                        "Game win"
                    )
                # Update loser
                loser_rating = elo_manager.get_bot_rating(loser)
                if loser_rating:
                    elo_manager.update_bot_rating(
                        loser, 
                        loser_rating.elo - 20,  # Simple -20 for loss
                        "local",
                        "Game loss"
                    )
            else:
                # Draw - small adjustments
                white_rating = elo_manager.get_bot_rating(WHITE_AGENT)
                if white_rating:
                    elo_manager.update_bot_rating(
                        WHITE_AGENT,
                        white_rating.elo + 2,
                        "local",
                        "Game draw"
                    )
                black_rating = elo_manager.get_bot_rating(BLACK_AGENT)
                if black_rating:
                    elo_manager.update_bot_rating(
                        BLACK_AGENT,
                        black_rating.elo + 2,
                        "local",
                        "Game draw"
                    )
            
            logger.info(f"ELO ratings updated for {WHITE_AGENT} vs {BLACK_AGENT}")
            
        except Exception as exc:
            logger.error(f"Failed to update ELO counter: {exc}")

    def _show_game_over(self):
        res = self.board.result()
        winner = chess.WHITE if res == "1-0" else chess.BLACK
        if res in {"1-0", "0-1"}:
            try:
                update_from_board(self.board, winner)
                update_from_history(list(self.board.move_stack), winner, steps=[15, 21, 35])
            except Exception as exc:
                logger.warning(f"Failed to update PST training data: {exc}")
                
        heatmap_msg = ""
        if self.fen_history:
            active_set = self.drawer_manager.active_heatmap_set or "default"
            try:
                generate_heatmaps(self.fen_history, pattern_set=active_set)
            except Exception as exc:  # pragma: no cover - UI notification
                heatmap_msg = f"\n\n⚠️ Heatmap update failed: {exc}"
                logger.error(f"Heatmap generation failed: {exc}")
            else:
                self.fen_history.clear()
                self.drawer_manager.set_heatmap_set(active_set)
                self._sync_heatmap_set_selection()
                self._populate_heatmap_pieces(self.drawer_manager.active_heatmap_piece)
                self._save_heatmap_preferences(
                    set_name=self.drawer_manager.active_heatmap_set,
                    piece_name=self.drawer_manager.active_heatmap_piece,
                )
                self._update_heatmap_stats()
                self._refresh_board()
                # Оновити підсумки теплокарт після генерації
                try:
                    self._update_heatmap_counts()
                except Exception as exc:
                    logger.warning(f"Failed to update heatmap counts after generation: {exc}")
                heatmap_msg = (
                    f"\n\n✅ Heatmaps updated for set '{active_set}'."
                )
        
        # Auto-save PNG for XRPA analysis
        try:
            self._auto_save_xrpa_png(res)
        except Exception as exc:
            print(f"Auto-save PNG failed: {exc}")

        # Save game to runs folder and update ELO counter
        try:
            self._save_game_to_runs(res)
            self._update_elo_counter(res)
        except Exception as exc:
            logger.error(f"Failed to save game or update ELO: {exc}")

        # Виводимо результат в консоль замість message box
        self._append_to_console("=" * 50)
        self._append_to_console("🎯 GAME COMPLETE")
        self._append_to_console("=" * 50)
        self._append_to_console(f"🏁 Result: {res}")
        self._append_to_console(f"📋 Moves: {self._moves_san_string()}")
        if heatmap_msg:
            self._append_to_console(heatmap_msg.strip())
        self._append_to_console("=" * 50)
        self._append_to_console("")

# ====== Запуск ======
if __name__ == "__main__":
    try:
        # Initialize Qt Application with error handling
        app = QApplication(sys.argv)
        app.setApplicationName("Chess Viewer")
        app.setApplicationVersion("1.0")
        
        # Set application style for better error visibility
        app.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
            }
            QMessageBox QLabel {
                color: #212529;
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
        """)
        
        # Create and show the main window
        viewer = ChessViewer()
        viewer.show()
        
        # Start the event loop
        sys.exit(app.exec())
        
    except ImportError as exc:
        ErrorHandler.handle_import_error(exc, "application startup")
        sys.exit(1)
        
    except FileNotFoundError as exc:
        ErrorHandler.handle_file_error(exc, "application startup")
        sys.exit(1)
        
    except PermissionError as exc:
        ErrorHandler.handle_permission_error(exc, "application startup")
        sys.exit(1)
        
    except Exception as exc:
        ErrorHandler.log_error(exc, "application startup")
        print("❌ Application Launch Failed")
        print(f"🚨 Unexpected error: {exc}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if all required files are present")
        print("2. Verify Python version compatibility")
        print("3. Try running from the project root directory")
        print("4. Check file permissions")
        print("\n📝 If the problem persists, please report this issue")
        sys.exit(1)
