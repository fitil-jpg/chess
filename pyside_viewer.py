# pyside_viewer.py
# Ліворуч: дошка (припіднята). Праворуч: кнопки + статуси + лічильник використання модулів.
# Додано: Usage таймлайн (два ряди кольорових прямокутників для W/B).
# Боти задаються тут у коді.

import sys
import re
import chess
from collections import defaultdict
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QCheckBox, QMessageBox, QSizePolicy,
    QListWidget,
)
from PySide6.QtCore import QTimer, QRect, Qt
from PySide6.QtGui import QClipboard, QPainter, QColor, QPen

from core.piece import piece_class_factory
from ui.cell import Cell
from ui.drawer_manager import DrawerManager
from chess_ai.bot_agent import make_agent
from chess_ai.threat_map import ThreatMap
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage
from utils.module_colors import MODULE_COLORS, REASON_PRIORITY
from ui.usage_timeline import UsageTimeline

# Фіксована пара ботів у в’ювері:
WHITE_AGENT = "DynamicBot"
BLACK_AGENT = "FortifyBot"

_PIECE_NAME = {
    chess.PAWN:  "Pawns",
    chess.KNIGHT:"Knights",
    chess.BISHOP:"Bishops",
    chess.ROOK:  "Rooks",
    chess.QUEEN: "Queen",
    chess.KING:  "King",
}

class OverallUsageChart(QWidget):
    """Simple bar chart summarising module usage across multiple runs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counts = {}
        self.setMinimumSize(280, 150)

    def set_data(self, counts):
        self.counts = dict(counts)
        self.update()

    def paintEvent(self, ev):  # pragma: no cover - GUI drawing
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        if not self.counts:
            return

        w = self.width()
        pad = 8
        bar_h = 14
        y = pad
        max_count = max(self.counts.values())
        items = sorted(self.counts.items(), key=lambda kv: (-kv[1], kv[0]))

        for name, count in items:
            bar_w = int((w - pad * 2) * (count / max_count)) if max_count else 0
            color = MODULE_COLORS.get(name, MODULE_COLORS["OTHER"])
            painter.fillRect(QRect(pad, y, bar_w, bar_h), color)
            painter.setPen(QPen(QColor(60, 60, 60)))
            painter.drawRect(QRect(pad, y, bar_w, bar_h))
            painter.drawText(pad + bar_w + 4, y + bar_h - 2, f"{name} ({count})")
            y += bar_h + pad
            if y + bar_h > self.height():
                break

class ChessViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Viewer — ThreatMap & Metrics")
        self.resize(980, 620)  # більше місця праворуч

        # Логіка позиції
        self.board = chess.Board()
        self.piece_objects = {}
        self.drawer_manager = DrawerManager()

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

        # Usage — два окремі рядки (як ти просив)
        self.lbl_usage_w  = QLabel("Dynamic usage (W): —")
        self.lbl_usage_b  = QLabel("Dynamic usage (B): —")

        for lab in (
            self.lbl_module,
            self.lbl_features,
            self.lbl_threat,
            self.lbl_attacks,
            self.lbl_leaders,
            self.lbl_king,
            self.lbl_usage_w,
            self.lbl_usage_b,
        ):
            lab.setWordWrap(True)
            right_col.addWidget(lab)

        # Список ходів SAN
        right_col.addWidget(QLabel("Moves:"))
        self.moves_list = QListWidget()
        right_col.addWidget(self.moves_list)

        # Таймлайн застосованих модулів
        right_col.addWidget(QLabel("Usage timeline:"))
        self.timeline = UsageTimeline()
        self.timeline.moveClicked.connect(self._on_timeline_click)
        right_col.addWidget(self.timeline)

        # Загальна діаграма використання модулів (нижня панель)
        right_col.addWidget(QLabel("Overall module usage:"))
        self.overall_chart = OverallUsageChart()
        runs = load_runs("runs")
        self.overall_chart.set_data(aggregate_module_usage(runs))
        right_col.addWidget(self.overall_chart)

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
            self._update_usage_labels()
            self.moves_list.clear()

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

    # ---------- Метрики / статуси ----------

    def _attack_metrics(self):
        cells_w = sum(1 for sq in chess.SQUARES if self.board.is_attacked_by(chess.WHITE, sq))
        cells_b = sum(1 for sq in chess.SQUARES if self.board.is_attacked_by(chess.BLACK, sq))
        pieces_w = 0
        pieces_b = 0
        for sq, pc in self.board.piece_map().items():
            if pc.color == chess.WHITE:
                if self.board.is_attacked_by(chess.BLACK, sq):
                    pieces_w += 1
            else:
                if self.board.is_attacked_by(chess.WHITE, sq):
                    pieces_b += 1
        return cells_w, cells_b, pieces_w, pieces_b

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

    def _attack_leaders_data(self):
        out = {}
        for color in (chess.WHITE, chess.BLACK):
            unions = {
                chess.PAWN:  set(),
                chess.KNIGHT:set(),
                chess.BISHOP:set(),
                chess.ROOK:  set(),
                chess.QUEEN: set(),
                chess.KING:  set(),
            }
            for sq, pc in self.board.piece_map().items():
                if pc.color != color: continue
                unions[pc.piece_type] |= set(self.board.attacks(sq))
            counts = {pt: len(sqs) for pt, sqs in unions.items()}
            maxc = max(counts.values()) if counts else 0
            tops = [pt for pt, c in counts.items() if c == maxc and maxc > 0]
            out[color] = (counts, tops, maxc)
        return out

    def _attack_leaders_text(self) -> str:
        data = self._attack_leaders_data()
        def display_max_for(color_bool: bool) -> str:
            counts, tops, _ = data[color_bool]
            if not counts: return "—"
            def disp(pt):
                c = counts.get(pt, 0)
                return min(c, 8) if pt == chess.KING else c
            disp_max = max(disp(pt) for pt in counts.keys())
            if disp_max == 0: return "—"
            disp_tops = [pt for pt in counts.keys() if disp(pt) == disp_max]
            names = ", ".join(_PIECE_NAME[t] for t in sorted(disp_tops))
            return f"{names}({disp_max})"
        w_txt = display_max_for(chess.WHITE)
        b_txt = display_max_for(chess.BLACK)
        return f"Attack leaders: W={w_txt} | B={b_txt}"

    def _king_coeff_text(self) -> str:
        def side(color: chess.Color) -> str:
            base = (
                8 * len(self.board.pieces(chess.PAWN, color))
                + 2 * len(self.board.pieces(chess.BISHOP, color))
                + 2 * len(self.board.pieces(chess.KNIGHT, color))
                + 2 * len(self.board.pieces(chess.ROOK, color))
                + len(self.board.pieces(chess.QUEEN, color))
            )
            modifier = 0.85 if not self.board.pieces(chess.QUEEN, not color) else 1.0
            value = int(base * modifier)
            return f"{value} (m={modifier:.2f})"

        return f"King coeff: W={side(chess.WHITE)} | B={side(chess.BLACK)}"

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

    def _usage_labels_text(self, dd: dict) -> str:
        if not dd:
            return "—"
        items = sorted(dd.items(), key=lambda kv: (-kv[1], kv[0]))
        return ", ".join(f"{k}={v}" for k, v in items)

    def _update_usage_labels(self):
        self.lbl_usage_w.setText(f"Dynamic usage (W): {self._usage_labels_text(self.usage_w)}")
        self.lbl_usage_b.setText(f"Dynamic usage (B): {self._usage_labels_text(self.usage_b)}")

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

        side_to_move = self.board.turn
        tmap = self.tmap_white if side_to_move == chess.WHITE else self.tmap_black
        summ = tmap.summary(self.board)

        thin_list = summ.get("thin_pieces", [])
        thinN = len(thin_list)
        def _n(sq): return chess.square_name(sq) if isinstance(sq, int) else "-"

        if thinN > 0:
            thin_sq = ", ".join(_n(sq) for (sq, _, _) in thin_list[:5])
            self.lbl_threat.setText(f"ThreatMap: thin={thinN} [{thin_sq}], max_def={_n(summ.get('max_defended'))}")
        else:
            self.lbl_threat.setText(f"ThreatMap: thin=0, max_att={_n(summ.get('max_attacked'))}, max_def={_n(summ.get('max_defended'))}")

        cw, cb, pw, pb = self._attack_metrics()
        self.lbl_attacks.setText(f"Attacks: cells W={cw}, B={cb} | pieces under attack W={pw}, B={pb}")

        self.lbl_leaders.setText(self._attack_leaders_text())
        self.lbl_king.setText(self._king_coeff_text())

        # Оновити usage-лейбли і графік
        self._update_usage_labels()
        self.timeline.set_data(self.timeline_w, self.timeline_b)

    def _show_game_over(self):
        res = self.board.result()
        QMessageBox.information(self, "Гру завершено", f"Результат: {res}\n\n{self._moves_san_string()}")

# ====== Запуск ======
if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ChessViewer()
    viewer.show()
    sys.exit(app.exec())
