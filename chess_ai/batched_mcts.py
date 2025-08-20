"""Batched Monte Carlo tree search using a neural network for policy and value.

This module provides a simple MCTS implementation that evaluates a batch of
leaf positions at once using ``net.predict_many``.  The network is expected to
return a pair ``(policy, value)`` for each board where ``policy`` is a mapping
from :class:`chess.Move` to prior probability and ``value`` is the position
value from the perspective of the side to move.

The search method mirrors a very small subset of AlphaZero style MCTS and is
sufficient for unit tests and simple experimentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Dict, Iterable, List, Optional, Tuple

import chess


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _dirichlet(alpha: float, size: int) -> List[float]:
    """Return a Dirichlet noise vector of ``size`` elements."""
    samples = [random.gammavariate(alpha, 1.0) for _ in range(size)]
    s = sum(samples)
    if s == 0:
        return [1.0 / size for _ in range(size)]
    return [v / s for v in samples]


@dataclass
class Node:
    """Node in the search tree."""

    board: chess.Board
    parent: Optional["Node"] = None
    prior: float = 0.0
    children: Dict[chess.Move, "Node"] = field(default_factory=dict)
    n: int = 0  # visit count
    w: float = 0.0  # total value

    # ------------------------------------------------------------------
    def q(self) -> float:
        return self.w / self.n if self.n else 0.0

    # ------------------------------------------------------------------
    def u(self, c_puct: float) -> float:
        if self.parent is None:
            return self.q()
        return self.q() + c_puct * self.prior * math.sqrt(self.parent.n) / (1 + self.n)


# ---------------------------------------------------------------------------
# Batched MCTS
# ---------------------------------------------------------------------------


class BatchedMCTS:
    """Monte Carlo tree search that evaluates positions in batches."""

    def __init__(
        self,
        net,
        c_puct: float = 1.4,
        dirichlet_alpha: float = 0.3,
        epsilon: float = 0.25,
    ) -> None:
        self.net = net
        self.c_puct = c_puct
        self.dirichlet_alpha = dirichlet_alpha
        self.epsilon = epsilon

    # ------------------------------------------------------------------
    def search_batch(
        self,
        root: Node,
        n_simulations: int = 32,
        batch_size: int = 8,
        add_dirichlet: bool = True,
        temperature: float = 1.0,
    ) -> Tuple[Optional[chess.Move], Node]:
        """Run MCTS starting from ``root``.

        Returns the selected move from ``root`` and the root itself.  ``root``
        must already contain the current board state.
        """

        board = root.board
        legal = list(board.legal_moves)
        if not legal:
            return None, root

        sims_done = 0
        while sims_done < n_simulations:
            batch: List[Node] = []
            batch_boards: List[chess.Board] = []
            batch_paths: List[List[Node]] = []
            # ----------------------------------------------------------
            while (
                len(batch) < batch_size
                and sims_done + len(batch) < n_simulations
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
                batch.append(node)
                batch_boards.append(b)
                batch_paths.append(path)
                if node is root:
                    break
            # ----------------------------------------------------------
            policies_values = self.net.predict_many(batch_boards)
            for leaf, (policy, value), path, b in zip(
                batch, policies_values, batch_paths, batch_boards
            ):
                # Expansion of leaf
                if not b.is_game_over() and not leaf.children:
                    legal_moves = list(b.legal_moves)
                    priors = [policy.get(m, 0.0) for m in legal_moves]
                    tot = sum(priors)
                    if tot <= 0:
                        priors = [1.0 / len(legal_moves)] * len(legal_moves)
                    else:
                        priors = [p / tot for p in priors]
                    if leaf is root and add_dirichlet:
                        noise = _dirichlet(self.dirichlet_alpha, len(legal_moves))
                        priors = [
                            (1 - self.epsilon) * p + self.epsilon * n
                            for p, n in zip(priors, noise)
                        ]
                    for m, p in zip(legal_moves, priors):
                        nb = b.copy()
                        nb.push(m)
                        leaf.children[m] = Node(nb, leaf, p)
                # Backup
                for node in reversed(path):
                    node.n += 1
                    node.w += value
                    value = -value
            sims_done += len(batch)

        # --------------------------------------------------------------
        # Choose move from root based on visit counts
        if temperature <= 1e-3:
            move = max(root.children.items(), key=lambda kv: kv[1].n)[0]
        else:
            visits = [child.n ** (1.0 / temperature) for child in root.children.values()]
            s = sum(visits)
            probs = [v / s for v in visits]
            move = random.choices(list(root.children.keys()), weights=probs, k=1)[0]
        return move, root


# ---------------------------------------------------------------------------
# One-shot helper
# ---------------------------------------------------------------------------


def choose_move_one_shot(
    board: chess.Board,
    net,
    add_dirichlet: bool = False,
    temperature: float = 1.0,
    dirichlet_alpha: float = 0.3,
    epsilon: float = 0.25,
) -> Optional[chess.Move]:
    """Choose a move using only the network's policy for the current board."""
    legal = list(board.legal_moves)
    if not legal:
        return None
    policy, _ = net.predict_many([board])[0]
    priors = [policy.get(m, 0.0) for m in legal]
    tot = sum(priors)
    if tot <= 0:
        priors = [1.0 / len(legal)] * len(legal)
    else:
        priors = [p / tot for p in priors]
    if add_dirichlet:
        noise = _dirichlet(dirichlet_alpha, len(legal))
        priors = [(1 - epsilon) * p + epsilon * n for p, n in zip(priors, noise)]
    if temperature <= 1e-3:
        idx = max(range(len(legal)), key=lambda i: priors[i])
    else:
        weights = [p ** (1.0 / temperature) for p in priors]
        s = sum(weights)
        probs = [w / s for w in weights]
        idx = random.choices(range(len(legal)), weights=probs, k=1)[0]
    return legal[idx]
