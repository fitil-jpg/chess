"""
board.py
Мета файлу: простий клас дошки з підтримкою підсвітки ходів.
Зміни: додано метод `highlight_valid_moves(knight_rules=True)` і базову інтеграцію з self.selected_square.
Примітка: якщо у вашому проєкті вже є розширений ChessBoard з GUI (PySide6),
— просто перенесіть метод `highlight_valid_moves` у ваш клас і під’єднайте до вашого малювання бордерів.
"""

from __future__ import annotations
from typing import List, Set, Optional

try:  # Optional dependency used only by ``ChessBoard``
    import logging
    logger = logging.getLogger(__name__)
    import chess  # type: ignore
except Exception:  # pragma: no cover - chess may be absent in test env
    chess = None


class Board:
    """Minimal board representation used in tests.

    The class stores piece objects and exposes a :meth:`get_pieces` helper so
    that other components do not access the internal ``pieces`` container
    directly.  Only the features required by the tests are implemented.
    """

    def __init__(self) -> None:
        self.pieces: list = []

    def place_piece(self, piece) -> None:
        self.pieces.append(piece)

    def get_pieces(self, color: Optional[str] = None) -> List:
        if color is None:
            return list(self.pieces)
        return [p for p in self.pieces if p.color == color]

if chess:
    CENTER_16 = {
        chess.C3, chess.D3, chess.E3, chess.F3,
        chess.C4, chess.D4, chess.E4, chess.F4,
        chess.C5, chess.D5, chess.E5, chess.F5,
        chess.C6, chess.D6, chess.E6, chess.F6,
    }

    class ChessBoard:
        def __init__(self, fen: Optional[str] = None, *, view=None):
            self.board: chess.Board = chess.Board(fen) if fen else chess.Board()
            # Очікується, що у вашому UI це оновлюється при кліку
            self.selected_square: Optional[int] = None  # 0..63 (python-chess)
            # Набір квадратів, які треба підсвітити (бордери)
            self.highlighted_squares: Set[int] = set()
            # Опційно: PySide/Qt в'ю, яке відповідає за малювання клітинок
            # (наприклад, ``ui.mini_board.MiniBoard`` або кастомний віджет).
            # Базова реалізація очікує наявність методів
            # ``set_border_highlights`` та ``request_repaint``.
            self.view = view

        def load_fen(self, fen: str) -> None:
            self.board.set_fen(fen)
            self.clear_selection()

        def clear_selection(self) -> None:
            self.selected_square = None
            self.highlighted_squares.clear()
            self._apply_border_highlight()
            self._request_repaint()

        def select_square(self, square: int) -> List[int]:
            """
            Викликайте з UI при натисканні на клітинку (0..63).
            Повертає список квадратів для підсвітки.
            """
            self.selected_square = square
            return self.highlight_valid_moves(knight_rules=True)

        def play_move(self, move: chess.Move) -> None:
            """Зробити хід та очистити підсвітки."""
            if move in self.board.legal_moves:
                self.board.push(move)
            self.clear_selection()

        # --- НОВЕ: підсвітка можливих ходів ---
        def highlight_valid_moves(self, knight_rules: bool = True) -> List[int]:
            """
            Обчислює та зберігає в self.highlighted_squares усі валідні клітинки призначення
            для наразі обраного self.selected_square. Повертає список int-квадратів (0..63).

            knight_rules=True:
                - Немає спеціального винятку: python-chess і так враховує «стрибок коня».
                - Прапорець залишено для сумісності з вашим інтерфейсом/налаштуванням.
            """
            self.highlighted_squares.clear()
            if self.selected_square is None:
                self._request_repaint()
                return []

            piece = self.board.piece_at(self.selected_square)
            if not piece:
                self._request_repaint()
                return []

            legal_targets = [
                m.to_square
                for m in self.board.legal_moves
                if m.from_square == self.selected_square
            ]

            # При бажанні можна додати особливу обробку коня (UI-анімації, інший бордер тощо)
            if knight_rules and piece.piece_type == chess.KNIGHT:
                # Ніяких додаткових обмежень — просто коментар для ясності.
                pass

            self.highlighted_squares.update(legal_targets)
            self._apply_border_highlight()  # бордери, як ви просили, а не фон
            self._request_repaint()
            return list(self.highlighted_squares)

        # ---- Нижче — гачки під ваш GUI. Залишаються як TODO, якщо у вас інша реалізація. ----
        def _apply_border_highlight(self) -> None:
            """Forward highlighted squares to the attached GUI view.

            The default implementation looks for a ``view`` attribute that
            exposes a :meth:`set_border_highlights` method (as provided by
            :class:`ui.mini_board.MiniBoard`).  Custom GUIs can either supply a
            compatible view object when constructing :class:`ChessBoard` or
            override this hook to perform framework specific rendering.
            """

            view = getattr(self, "view", None)
            if view is None:
                return

            if hasattr(view, "set_border_highlights"):
                view.set_border_highlights(self.highlighted_squares)
            elif hasattr(view, "highlight_squares"):
                # Залишено для сумісності зі старими в'ю, які малювали фон
                view.highlight_squares(self.highlighted_squares)
            else:
                logger.debug(
                    "ChessBoard view %s has no border highlight API", type(view)
                )

        def _request_repaint(self) -> None:
            """Trigger a repaint on the attached view, if any.

            The helper prefers a dedicated ``request_repaint`` hook but will
            gracefully fall back to common Qt methods such as ``update`` or
            ``repaint``.  Projects embedding :class:`ChessBoard` in a different
            UI toolkit can override the method or provide a view object exposing
            one of these entry points.
            """

            view = getattr(self, "view", None)
            if view is None:
                return

            if hasattr(view, "request_repaint"):
                view.request_repaint()
            elif hasattr(view, "update"):
                view.update()
            elif hasattr(view, "repaint"):
                view.repaint()
            else:
                logger.debug(
                    "ChessBoard view %s has no repaint API", type(view)
                )
else:  # chess package not available
    CENTER_16 = set()

    class ChessBoard:  # pragma: no cover - simplified fallback
        pass
