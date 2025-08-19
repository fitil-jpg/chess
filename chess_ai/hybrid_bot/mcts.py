"""Batch-style Monte Carlo tree search with optional Dirichlet noise."""

from __future__ import annotations

import math
import random
import chess
from .evaluation import evaluate_position


def _dirichlet(alpha: float, size: int) -> list[float]:
    samples = [random.gammavariate(alpha, 1) for _ in range(size)]
    s = sum(samples)
    return [v / s for v in samples]


class Node:
    def __init__(self, board: chess.Board, parent: 'Node | None' = None, prior: float = 0.0):
        self.board = board
        self.parent = parent
        self.prior = prior
        self.children: dict[chess.Move, Node] = {}
        self.n = 0
        self.w = 0.0

    def q(self) -> float:
        return self.w / self.n if self.n else 0.0

    def u(self, c_puct: float) -> float:
        if self.parent is None:
            return self.q()
        return self.q() + c_puct * self.prior * math.sqrt(self.parent.n) / (1 + self.n)


class BatchMCTS:
    def __init__(self, c_puct: float = 1.4):
        self.c_puct = c_puct

    def search(
        self,
        board: chess.Board,
        n_simulations: int = 32,
        temperature: float = 1.0,
        dirichlet_alpha: float = 0.3,
        epsilon: float = 0.25,
        batch_size: int = 1,
    ) -> tuple[chess.Move | None, Node]:
        root = Node(board.copy())
        legal = list(board.legal_moves)
        if not legal:
            return None, root
        priors = [1 / len(legal)] * len(legal)
        noise = _dirichlet(dirichlet_alpha, len(legal))
        priors = [(1 - epsilon) * p + epsilon * n for p, n in zip(priors, noise)]
        for m, p in zip(legal, priors):
            b = board.copy()
            b.push(m)
            root.children[m] = Node(b, root, p)

        for _ in range(n_simulations):
            node = root
            b = board.copy()
            # Selection
            while node.children:
                move, node = max(node.children.items(), key=lambda kv: kv[1].u(self.c_puct))
                b.push(move)
            # Expansion
            if not b.is_game_over():
                moves = list(b.legal_moves)
                pri = [1 / len(moves)] * len(moves)
                for m, p in zip(moves, pri):
                    nb = b.copy()
                    nb.push(m)
                    node.children[m] = Node(nb, node, p)
            # Evaluation
            value = evaluate_position(b)
            # Backup
            while node is not None:
                node.n += 1
                node.w += value
                value = -value
                node = node.parent

        # Choose move from root
        if temperature <= 1e-3:
            move = max(root.children.items(), key=lambda kv: kv[1].n)[0]
        else:
            visits = [child.n ** (1 / temperature) for child in root.children.values()]
            s = sum(visits)
            probs = [v / s for v in visits]
            move = random.choices(list(root.children.keys()), weights=probs, k=1)[0]
        return move, root

