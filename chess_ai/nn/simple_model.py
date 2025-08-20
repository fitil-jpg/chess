"""Simple feed-forward neural network for chess positions.

This module defines :class:`SimpleChessModel`, a tiny PyTorch network that
produces policy and value outputs for a given board. It is intentionally
small and meant for tests and prototyping rather than playing strength.
"""

from __future__ import annotations

import chess
import torch
import torch.nn as nn
import torch.nn.functional as F

INPUT_DIM = 773  # 12 * 64 board planes + 5 auxiliary features
POLICY_DIM = 64 * 64  # from-square x to-square


# ---------------------------------------------------------------------------
# Board encoding
# ---------------------------------------------------------------------------

def board_to_tensor(board: chess.Board) -> torch.Tensor:
    """Encode ``board`` into a flat tensor of size :data:`INPUT_DIM`."""
    planes = torch.zeros(12, 8, 8, dtype=torch.float32)
    for square, piece in board.piece_map().items():
        idx = piece.piece_type - 1 + (0 if piece.color == chess.WHITE else 6)
        planes[idx, square // 8, square % 8] = 1.0
    flat = planes.view(-1)
    extras = torch.tensor(
        [
            1.0 if board.turn == chess.WHITE else 0.0,
            1.0 if board.has_kingside_castling_rights(chess.WHITE) else 0.0,
            1.0 if board.has_queenside_castling_rights(chess.WHITE) else 0.0,
            1.0 if board.has_kingside_castling_rights(chess.BLACK) else 0.0,
            1.0 if board.has_queenside_castling_rights(chess.BLACK) else 0.0,
        ],
        dtype=torch.float32,
    )
    return torch.cat([flat, extras])


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class SimpleChessModel(nn.Module):
    """Very small fully connected network with policy and value heads."""

    def __init__(self, hidden: int = 128) -> None:
        super().__init__()
        self.fc1 = nn.Linear(INPUT_DIM, hidden)
        self.fc_policy = nn.Linear(hidden, POLICY_DIM)
        self.fc_value = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = F.relu(self.fc1(x))
        policy_logits = self.fc_policy(x)
        value = torch.tanh(self.fc_value(x))  # value in [-1,1]
        return policy_logits, value.squeeze(-1)


# ---------------------------------------------------------------------------
# Weights helpers
# ---------------------------------------------------------------------------

def load_dummy_weights(model: nn.Module) -> None:
    """Initialise ``model`` with deterministic dummy weights.

    The dummy weights produce uniform policy and zero value, allowing the
    surrounding code to operate before real training data exists.
    """
    for p in model.parameters():
        nn.init.zeros_(p)
