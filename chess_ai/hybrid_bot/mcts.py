"""Batch-style Monte Carlo tree search with optional Dirichlet noise."""

from __future__ import annotations

import math
import random
import logging
logger = logging.getLogger(__name__)

import chess
from .evaluation import evaluate_positions
from ..utils.profile_stats import STATS, plot_profile_stats


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
        """Run MCTS and return a move and the search tree.

        The search collects up to ``batch_size`` leaf nodes before evaluation.
        All gathered boards are then evaluated in a single call to the
        evaluation routine, allowing, for example, a neural network's
        ``predict_many`` implementation to process them efficiently.  Setting
        ``batch_size`` to ``1`` reproduces standard, non-batched MCTS
        behaviour.
        """
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

        STATS.start()

        sims_done = 0
        while sims_done < n_simulations:
            batch_nodes: list[Node] = []
            batch_boards: list[chess.Board] = []
            batch_paths: list[list[Node]] = []
            while (
                len(batch_nodes) < batch_size
                and sims_done + len(batch_nodes) < n_simulations
            ):
                node = root
                b = board.copy()
                path = [node]
                # Selection
                while node.children:
                    move, node = max(
                        node.children.items(), key=lambda kv: kv[1].u(self.c_puct)
                    )
                    b.push(move)
                    path.append(node)
                # Expansion
                if not b.is_game_over():
                    moves = list(b.legal_moves)
                    pri = [1 / len(moves)] * len(moves)
                    for m, p in zip(moves, pri):
                        nb = b.copy()
                        nb.push(m)
                        node.children[m] = Node(nb, node, p)
                batch_nodes.append(node)
                batch_boards.append(b)
                batch_paths.append(path)
                STATS.nodes += len(path)

            # Evaluate all boards in a single call
            values = evaluate_positions(batch_boards)

            # Backup each result along its path
            for path, value in zip(batch_paths, values):
                v = value
                for cur in reversed(path):
                    cur.n += 1
                    cur.w += v
                    v = -v
            sims_done += len(batch_nodes)

        # Choose move from root
        if temperature <= 1e-3:
            move = max(root.children.items(), key=lambda kv: kv[1].n)[0]
        else:
            visits = [child.n ** (1 / temperature) for child in root.children.values()]
            s = sum(visits)
            probs = [v / s for v in visits]
            move = random.choices(list(root.children.keys()), weights=probs, k=1)[0]
        STATS.stop()
        logger.info("MCTS: %s", STATS.summary())
        plot_profile_stats(STATS, filename="mcts_profile.png")
        return move, root
