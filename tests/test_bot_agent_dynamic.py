import importlib
import sys
import types


class DummyMove:
    def __init__(self, uci: str):
        self._uci = uci

    def uci(self) -> str:
        return self._uci

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"DummyMove({self._uci})"


class DummyBoard:
    def __init__(self, move_scores: dict[str, int], turn: bool, default_score: int = 0):
        self._move_scores = dict(move_scores)
        self._moves = [DummyMove(uci) for uci in move_scores]
        self.turn = turn
        self.default_score = default_score
        self._stack: list[DummyMove] = []

    @property
    def legal_moves(self):
        return list(self._moves)

    def push(self, move: DummyMove) -> None:
        self._stack.append(move)
        self.turn = not self.turn

    def pop(self) -> DummyMove:
        last = self._stack.pop()
        self.turn = not self.turn
        return last

    def peek(self) -> DummyMove:
        return self._stack[-1]

    def score_for_move(self, move: DummyMove) -> int:
        return self._move_scores.get(move.uci(), self.default_score)


def _load_dynamic_bot(monkeypatch):
    chess_stub = types.SimpleNamespace(WHITE=True, BLACK=False, Move=DummyMove, Board=DummyBoard)

    def evaluate(board: DummyBoard):
        move = board.peek()
        score = board.score_for_move(move)
        return score, {"total": score}

    evaluation_stub = types.SimpleNamespace(evaluate=evaluate)

    monkeypatch.setitem(sys.modules, "chess", chess_stub)
    monkeypatch.setitem(sys.modules, "evaluation", evaluation_stub)
    sys.modules.pop("bot_agent", None)
    module = importlib.import_module("bot_agent")
    return module.DynamicBot


def test_dynamic_bot_prefers_white_advantage(monkeypatch):
    DynamicBot = _load_dynamic_bot(monkeypatch)
    board = DummyBoard({
        "e2e4": 120,
        "d2d4": 80,
    }, turn=True, default_score=-999)

    bot = DynamicBot()
    move, details = bot.select_move(board)

    assert move.uci() == "e2e4"
    assert details["raw_score"] == 120


def test_dynamic_bot_minimises_white_score_for_black(monkeypatch):
    DynamicBot = _load_dynamic_bot(monkeypatch)
    board = DummyBoard({
        "e7e5": -150,
        "c7c5": 20,
    }, turn=False, default_score=300)

    bot = DynamicBot()
    move, details = bot.select_move(board)

    assert move.uci() == "e7e5"
    assert details["raw_score"] == -150
