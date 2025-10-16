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
from collections import defaultdict
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea,
)
from PySide6.QtCore import QTimer, QRect, Qt, QSettings
from PySide6.QtGui import QClipboard, QPainter, QColor, QPen

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

# Фіксована пара ботів у в’ювері:
WHITE_AGENT = "DynamicBot"
BLACK_AGENT = "FortifyBot"

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

class ChessViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Viewer — ThreatMap & Metrics")
        self.resize(980, 620)  # більше місця праворуч

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

        # ---- ЛЕВА КОЛОНКА: ДОШКА ----
        self.board_frame = QFrame()
        self.board_frame.setFixedSize(560, 560)
        self.grid = QGridLayout(self.board_frame)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.cell_grid = [[None for _ in range(8)] for _ in range(8)]
        self._draw_board_widgets()

        left_col = QVBoxLayout()
        left_col.addWidget(self.board_frame)
        left_col.addStretch(1)  # підштовхує дошку догори

        # ---- ПРАВА КОЛОНКА: КНОПКИ + СТАТУСИ ----
        right_col = QVBoxLayout()

        title = QLabel(f"White: {WHITE_AGENT}    |    Black: {BLACK_AGENT}")
        title.setWordWrap(True)
        right_col.addWidget(title)

        # Кнопки
        btn_row = QHBoxLayout()
        self.btn_auto  = QPushButton("▶ Авто")
        self.btn_pause = QPushButton("⏸ Пауза")
        self.btn_copy_san = QPushButton("⧉ SAN")
        self.btn_copy_pgn = QPushButton("⧉ PGN")
        self.debug_verbose = QCheckBox("Debug")
        for b in (self.btn_auto, self.btn_pause, self.btn_copy_san, self.btn_copy_pgn, self.debug_verbose):
            btn_row.addWidget(b)
        right_col.addLayout(btn_row)

        # Зв’язки
        self.btn_auto.clicked.connect(self.start_auto)
        self.btn_pause.clicked.connect(self.pause_auto)
        self.btn_copy_san.clicked.connect(self.copy_san)
        self.btn_copy_pgn.clicked.connect(self.copy_pgn)

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
            right_col.addWidget(lab)

        right_col.addWidget(QLabel("Dynamic usage (W):"))
        self.chart_usage_w = OverallUsageChart()
        right_col.addWidget(self.chart_usage_w)

        right_col.addWidget(QLabel("Dynamic usage (B):"))
        self.chart_usage_b = OverallUsageChart()
        right_col.addWidget(self.chart_usage_b)

        # Список ходів SAN
        right_col.addWidget(QLabel("Moves:"))
        self.moves_list = QListWidget()
        right_col.addWidget(self.moves_list)

        # Таймлайн застосованих модулів
        right_col.addWidget(QLabel("Usage timeline:"))
        self.timeline = UsageTimeline()
        self.timeline.moveClicked.connect(self._on_timeline_click)
        right_col.addWidget(self.timeline)

        # Heatmap selection panel
        if self.drawer_manager.heatmaps:
            heatmap_layout, self.heatmap_set_combo, self.heatmap_piece_combo = create_heatmap_panel(
                self._on_heatmap_piece,
                set_callback=self._on_heatmap_set,
                sets=self.drawer_manager.list_heatmap_sets(),
                pieces=list(self.drawer_manager.heatmaps),
                current_set=default_heatmap_set,
                current_piece=default_heatmap_piece,
            )
            right_col.addLayout(heatmap_layout)
            self._populate_heatmap_pieces(default_heatmap_piece)
            self._sync_heatmap_set_selection()
            self._save_heatmap_preferences(
                set_name=self.drawer_manager.active_heatmap_set,
                piece_name=self.drawer_manager.active_heatmap_piece,
            )
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
            right_col.addWidget(msg)
            btn_gen_heatmaps = QPushButton("🔧 Generate heatmaps now")
            btn_gen_heatmaps.setStyleSheet("QPushButton { background-color: #007bff; color: white; border: none; padding: 8px; border-radius: 4px; }")
            btn_gen_heatmaps.clicked.connect(self._generate_heatmaps)
            right_col.addWidget(btn_gen_heatmaps)

        # Загальна діаграма використання модулів (нижня панель)
        right_col.addWidget(QLabel("Overall module usage:"))
        self.overall_chart = OverallUsageChart()
        runs = load_runs("runs")
        self.overall_chart.set_data(aggregate_module_usage(runs))
        chart_scroll = QScrollArea()
        chart_scroll.setWidgetResizable(True)
        chart_scroll.setWidget(self.overall_chart)
        right_col.addWidget(chart_scroll)

        right_col.addStretch(1)  # все тримаємо вгорі

        # ---- ГОЛОВНИЙ ЛЕЙАУТ ----
        main = QHBoxLayout()
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(12)
        main.addLayout(left_col, stretch=0)
        main.addLayout(right_col, stretch=1)

        self.board_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setLayout(main)

        # Таймер автогри
        self.auto_timer = QTimer()
        self.auto_timer.setInterval(650)
        self.auto_timer.timeout.connect(self.auto_step)
        self.auto_running = False

        # Початкова ініціалізація
        self._init_pieces()
        if default_heatmap_piece:
            self.drawer_manager.collect_overlays(self.piece_objects, self.board)
        self._refresh_board()
        self._update_status("-", None)

    # ---------- UI helpers ----------

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

    def auto_step(self):
        try:
            if self.board.is_game_over():
                self.pause_auto()
                self._show_game_over()
                return

            mover_color = self.board.turn
            agent = self.white_agent if mover_color == chess.WHITE else self.black_agent

            # Get move with error handling
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

            # Validate move before applying
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

            san = self.board.san(move)  # до push
            move_no = self.board.fullmove_number
            prefix = f"{move_no}. " if mover_color == chess.WHITE else f"{move_no}... "

            self.board.push(move)
            self.fen_history.append(self.board.fen())

            self._init_pieces()
            self._refresh_board()

            reason = agent.get_last_reason() if hasattr(agent, "get_last_reason") else "-"
            feats  = agent.get_last_features() if hasattr(agent, "get_last_features") else None

            # Витягнути ключ/тег і оновити usage + таймлайн
            key = self._extract_reason_key(reason)
            if mover_color == chess.WHITE:
                self.usage_w[key] += 1
                self.timeline_w.append(key)
            else:
                self.usage_b[key] += 1
                self.timeline_b.append(key)

            # Консольний дебаг
            if self.debug_verbose.isChecked():
                print(f"[{WHITE_AGENT if mover_color==chess.WHITE else BLACK_AGENT}] {san} | reason={reason} | key={key} | feats={feats}")

            self._update_status(reason, feats)

            # Append SAN move to list and highlight
            self.moves_list.addItem(f"{prefix}{san}")
            self.moves_list.setCurrentRow(self.moves_list.count() - 1)
            self.moves_list.scrollToBottom()

            if self.board.is_game_over():
                self.pause_auto()
                self._show_game_over()
                
        except Exception as exc:
            logger.error(f"Unexpected error in auto_step: {exc}")
            self.pause_auto()
            QMessageBox.critical(
                self,
                "❌ Game Error",
                f"🚨 <b>An unexpected error occurred during gameplay:</b>\n\n"
                f"<b>Error:</b> {exc}\n\n"
                f"<b>Game paused.</b> You may need to restart the application."
            )

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
            
            QMessageBox.information(
                self,
                "✅ Heatmaps Generated Successfully",
                f"🎉 Heatmap generation completed!\n\n"
                f"📊 Generated heatmaps for {len(fens)} position(s)\n"
                f"📁 Saved to: analysis/heatmaps/default/\n\n"
                f"🔄 Please restart the viewer to load the new heatmaps.",
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
        self._refresh_board()

    def _on_heatmap_piece(self, piece: str | None) -> None:
        """Callback for heatmap piece selection."""
        self.drawer_manager.active_heatmap_piece = piece
        self._save_heatmap_preferences(
            set_name=self.drawer_manager.active_heatmap_set,
            piece_name=piece,
        )
        self._refresh_board()

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
                self._refresh_board()
                heatmap_msg = (
                    f"\n\n✅ Heatmaps updated for set '{active_set}'."
                )

        QMessageBox.information(
            self,
            "🎯 Game Complete",
            f"🏁 <b>Result:</b> {res}\n\n"
            f"📋 <b>Moves:</b> {self._moves_san_string()}" + heatmap_msg,
        )

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
