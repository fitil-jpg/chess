import chess

from chess_ai.batched_mcts import BatchedMCTS, Node, choose_move_one_shot


class DummyNet:
    """Simple deterministic network used for tests."""

    def __init__(self):
        self.calls = []

    def predict_many(self, boards):
        results = []
        for b in boards:
            self.calls.append(b.fen())
            legal = list(b.legal_moves)
            if legal:
                prob = 1.0 / len(legal)
                policy = {m: prob for m in legal}
            else:
                policy = {}
            results.append((policy, 0.0))
        return results


def test_search_batch_calls_net_and_returns_move():
    board = chess.Board()
    net = DummyNet()
    mcts = BatchedMCTS(net)
    root = Node(board.copy())
    move, root_after = mcts.search_batch(
        root, n_simulations=4, batch_size=2, add_dirichlet=False, temperature=0.0
    )
    assert move in board.legal_moves
    # predict_many should be called for root + two batches
    assert len(net.calls) == 3
    assert root_after.n == 4
    assert sum(child.n for child in root_after.children.values()) == 4


def test_choose_move_one_shot_uses_policy():
    class PrefNet(DummyNet):
        def predict_many(self, boards):
            results = []
            for b in boards:
                self.calls.append(b.fen())
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
    assert len(net.calls) == 1
