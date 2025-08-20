import chess
import math

import pytest

from chess_ai.batched_mcts import BatchedMCTS, Node, choose_move_one_shot


class DummyNet:
    """Simple deterministic network used for tests."""

    def __init__(self):
        # Track how many times the network is invoked.
        self.calls = 0

    def predict_many(self, boards):
        self.calls += 1
        results = []
        for b in boards:
            legal = list(b.legal_moves)
            if legal:
                prob = 1.0 / len(legal)
                policy = {m: prob for m in legal}
            else:
                policy = {}
            results.append((policy, 0.0))
        return results


@pytest.mark.parametrize(
    "n_simulations,batch_size",
    [
        (4, 2),
        (5, 2),
        (8, 3),
    ],
)
def test_search_batch_calls_net_and_returns_move(n_simulations, batch_size):
    board = chess.Board()
    net = DummyNet()
    mcts = BatchedMCTS(net)
    root = Node(board.copy())
    move, root_after = mcts.search_batch(
        root,
        n_simulations=n_simulations,
        batch_size=batch_size,
        add_dirichlet=False,
        temperature=0.0,
    )
    assert move in board.legal_moves
    expected_calls = 1 + math.ceil(n_simulations / batch_size)
    assert net.calls == expected_calls
    assert root_after.n == n_simulations
    assert sum(child.n for child in root_after.children.values()) == n_simulations


def test_choose_move_one_shot_uses_policy():
    class PrefNet(DummyNet):
        def predict_many(self, boards):
            self.calls += 1
            results = []
            for b in boards:
                legal = list(b.legal_moves)
                policy = {m: 0.1 / (len(legal) - 1) for m in legal}
                for m in legal:
                    if m.uci() == "e2e4":
                        policy[m] = 0.9
                        break
                results.append((policy, 0.0))
            return results

    board = chess.Board()
    net = PrefNet()
    move = choose_move_one_shot(board, net, temperature=0.0)
    assert move == chess.Move.from_uci("e2e4")
    assert net.calls == 1
