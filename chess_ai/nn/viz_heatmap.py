"""Visualization helpers for neural-network predictions.

This module provides small utilities for inspecting the output of
:class:`chess_ai.nn.torch_net.TorchNet`.  Heatmaps can be generated either
from move probabilities (policy) or by computing the gradient of the value
head with respect to the board input.
"""

from __future__ import annotations

from typing import Dict

import logging
logger = logging.getLogger(__name__)

import chess
import matplotlib.pyplot as plt
import torch

from .simple_model import board_to_tensor
from .torch_net import TorchNet


def _setup_axes(ax: plt.Axes) -> None:
    """Label axes with chess board coordinates."""
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels(list("abcdefgh"))
    ax.set_yticklabels(list(range(8, 0, -1)))
    ax.invert_yaxis()


def plot_policy_heatmap(
    board: chess.Board,
    policy: Dict[chess.Move, float],
    save_path: str | None = None,
    show: bool = False,
) -> None:
    """Plot an 8×8 heatmap of ``policy`` probabilities.

    The probability mass for each move is accumulated on the destination
    square.  The resulting heatmap gives a quick overview of which regions the
    network prefers to move to.
    """

    grid = torch.zeros(8, 8, dtype=torch.float32)
    for move, prob in policy.items():
        r = chess.square_rank(move.to_square)
        c = chess.square_file(move.to_square)
        grid[7 - r, c] += prob

    fig, ax = plt.subplots()
    im = ax.imshow(grid, cmap="magma", vmin=0.0)
    _setup_axes(ax)
    fig.colorbar(im, ax=ax)

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_value_gradient(
    net: TorchNet,
    board: chess.Board,
    save_path: str | None = None,
    show: bool = False,
) -> None:
    """Plot a saliency map based on the value head gradient.

    The absolute gradient of the scalar value output with respect to the board
    representation is summed over piece planes to yield an 8×8 map indicating
    which squares most influence the evaluation.
    """

    net.model.zero_grad()
    inp = board_to_tensor(board).to(net.device).unsqueeze(0)
    inp.requires_grad_(True)
    _policy, value = net.model(inp)
    value.backward()
    grad = inp.grad[0][: 64 * 12].abs().view(12, 8, 8).sum(0)

    fig, ax = plt.subplots()
    im = ax.imshow(grad.cpu(), cmap="coolwarm")
    _setup_axes(ax)
    fig.colorbar(im, ax=ax)

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
