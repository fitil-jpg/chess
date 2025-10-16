# pyside_viewer.py
# Ліворуч: дошка (припіднята). Праворуч: кнопки + статуси + лічильник використання модулів.
# Додано: Usage таймлайн (два ряди кольорових прямокутників для W/B).
# Боти задаються тут у коді.

from utils.usage_logger import record_usage
record_usage(__file__)

import sys
import re
import chess
from collections import defaultdict
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
    QListWidget, QScrollArea, QFileDialog,
)
from PySide6.QtCore import QTimer, QRect, Qt, QSettings
from PySide6.QtGui import QClipboard, QPainter, QColor, QPen, QPixmap

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

        # Логіка позиції
        self.board = chess.Board()
        self.piece_objects = {}
        self.settings = QSettings("ChessViewer", "Preferences")
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
        self.white_agent = make_agent(WHITE_AGENT, chess.WHITE)
        self.black_agent = make_agent(BLACK_AGENT, chess.BLACK)

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
        self.btn_save_png = QPushButton("📷 PNG")
        self.debug_verbose = QCheckBox("Debug")
        for b in (self.btn_auto, self.btn_pause, self.btn_copy_san, self.btn_copy_pgn, self.btn_save_png, self.debug_verbose):
            btn_row.addWidget(b)
        right_col.addLayout(btn_row)

        # Зв’язки
        self.btn_auto.clicked.connect(self.start_auto)
        self.btn_pause.clicked.connect(self.pause_auto)
        self.btn_copy_san.clicked.connect(self.copy_san)
        self.btn_copy_pgn.clicked.connect(self.copy_pgn)
        self.btn_save_png.clicked.connect(self.save_png)

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
                "Heatmap data missing – generate files via "
                "`utils.integration.generate_heatmaps` or "
                "`analysis/heatmaps/generate_heatmaps.R`."
            )
            msg.setWordWrap(True)
            right_col.addWidget(msg)
            btn_gen_heatmaps = QPushButton("Generate heatmaps")
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
        self.piece_objects.clear()
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                pos = (chess.square_rank(square), chess.square_file(square))
                self.piece_objects[square] = piece_class_factory(piece, pos)

    def _refresh_board(self):
        # Оверлеї
        for sq, obj in self.piece_objects.items():
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

        self.drawer_manager.collect_overlays(self.piece_objects, self.board)

        # Символи та лічильники атак на клітинках
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                cell = self.cell_grid[row][col]
                cell.set_piece(piece.symbol() if piece else None)
                attackers = self.board.attackers(not self.board.turn, square)
                cell.set_attack_count(len(attackers))
                cell.set_highlight(False)
                cell.update()

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
        if self.board.is_game_over():
            self.pause_auto()
            self._show_game_over()
            return

        mover_color = self.board.turn
        agent = self.white_agent if mover_color == chess.WHITE else self.black_agent

        move = agent.choose_move(self.board)
        if move is None:
            self.pause_auto()
            self._show_game_over()
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
        QApplication.clipboard().setText(self._moves_san_string(), QClipboard.Clipboard)
        QMessageBox.information(self, "Копійовано", "SAN послідовність скопійовано у буфер.")

    def copy_pgn(self):
        QApplication.clipboard().setText(self._game_pgn_string(), QClipboard.Clipboard)
        QMessageBox.information(self, "Копійовано", "PGN скопійовано у буфер.")

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
        self.chart_usage_w.set_data(self.usage_w)
        self.chart_usage_b.set_data(self.usage_b)

    def _generate_heatmaps(self) -> None:
        """Invoke heatmap generation and notify the user."""
        try:
            fens_file = Path("fens.txt")
            if fens_file.exists():
                with fens_file.open("r", encoding="utf-8") as fh:
                    fens = [line.strip() for line in fh if line.strip()]
            else:
                fens = [self.board.fen()]
            generate_heatmaps(fens, pattern_set="default")
            QMessageBox.information(
                self,
                "Heatmaps",
                "Heatmaps generated. Restart viewer to load them.",
            )
        except Exception as exc:
            QMessageBox.warning(self, "Heatmaps", f"Generation failed: {exc}")

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
        self.lbl_module.setText(f"Модуль: {reason}")
        self.lbl_features.setText(f"Фічі: {self._truthy_features_preview(feats)}")

        metrics_lines = build_sidebar_metrics(
            self.board,
            {
                chess.WHITE: self.tmap_white,
                chess.BLACK: self.tmap_black,
            },
        )

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

    def _show_game_over(self):
        res = self.board.result()
        winner = chess.WHITE if res == "1-0" else chess.BLACK
        if res in {"1-0", "0-1"}:
            update_from_board(self.board, winner)
            update_from_history(list(self.board.move_stack), winner, steps=[15, 21, 35])
        heatmap_msg = ""
        if self.fen_history:
            active_set = self.drawer_manager.active_heatmap_set or "default"
            try:
                generate_heatmaps(self.fen_history, pattern_set=active_set)
            except Exception as exc:  # pragma: no cover - UI notification
                heatmap_msg = f"\n\nHeatmap update failed: {exc}"
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
                    f"\n\nHeatmaps updated for set '{active_set}'."
                )
        
        # Auto-save PNG for XRPA analysis
        try:
            self._auto_save_xrpa_png(res)
        except Exception as exc:
            print(f"Auto-save PNG failed: {exc}")

        QMessageBox.information(
            self,
            "Гру завершено",
            f"Результат: {res}\n\n{self._moves_san_string()}" + heatmap_msg,
        )

# ====== Запуск ======
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ChessViewer()
    viewer.show()
    sys.exit(app.exec())
