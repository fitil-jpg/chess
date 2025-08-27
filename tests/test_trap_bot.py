import pytest

chess = pytest.importorskip('chess')
if not hasattr(chess, 'Board'):
    pytest.skip('python-chess not installed', allow_module_level=True)

from chess_ai.trap_bot import TrapBot


def test_trapbot_prefers_trapping_knight():
    board = chess.Board('3nk3/3p4/8/8/8/8/8/3QK3 w - - 0 1')
    bot = TrapBot(chess.WHITE)
    move, _ = bot.choose_move(board)
    assert move == chess.Move.from_uci('d1d8')


def test_trapbot_targets_more_mobile_piece():
    board = chess.Board('3nk3/8/8/7b/8/8/8/3QK3 w - - 0 1')
    bot = TrapBot(chess.WHITE)
    move, _ = bot.choose_move(board)
    assert move == chess.Move.from_uci('d1h5')
