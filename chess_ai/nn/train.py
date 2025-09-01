from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import argparse
import csv
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import chess
import torch
from torch.utils.data import DataLoader, Dataset

from .simple_model import SimpleChessModel, board_to_tensor


class FenOutcomeDataset(Dataset):
    """Dataset of FEN strings paired with game outcomes.

    The input file should contain one sample per line consisting of a FEN string
    and a numeric outcome. The delimiter can be either a comma or whitespace.
    Outcomes are expected in ``[-1, 1]`` where ``1`` means a white win,
    ``-1`` a black win and ``0`` a draw.
    """

    def __init__(self, path: str) -> None:
        self.samples: List[Tuple[str, float]] = []
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                # Try CSV first, fall back to whitespace splitting
                try:
                    fen, outcome = next(csv.reader([line]))
                except Exception:
                    parts = line.split()
                    fen, outcome = " ".join(parts[:-1]), parts[-1]
                self.samples.append((fen, float(outcome)))

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        fen, outcome = self.samples[idx]
        board = chess.Board(fen)
        tensor = board_to_tensor(board)
        target = torch.tensor(outcome, dtype=torch.float32)
        return tensor, target


def train(model: SimpleChessModel, loader: DataLoader, epochs: int, lr: float) -> None:
    """Train ``model`` on ``loader`` for a number of epochs."""
    optim = torch.optim.Adam(model.parameters(), lr=lr)
    for epoch in range(epochs):
        total = 0.0
        for batch, target in loader:
            optim.zero_grad()
            _policy, value = model(batch)
            loss = torch.nn.functional.mse_loss(value, target)
            loss.backward()
            optim.step()
            total += float(loss.item()) * batch.size(0)
        avg = total / len(loader.dataset)
        logger.info(f"Epoch {epoch + 1}: loss={avg:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train SimpleChessModel on FEN data")
    parser.add_argument("data", help="Path to training data with FEN and outcome")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument(
        "--output", default="chess_ai/nn/simple_model.pth", help="Where to save model weights"
    )
    parser.add_argument(
        "--heatmap",
        help="Save value-gradient heatmap for the first training sample to this path",
    )
    args = parser.parse_args()

    dataset = FenOutcomeDataset(args.data)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    model = SimpleChessModel()
    train(model, loader, epochs=args.epochs, lr=args.lr)
    torch.save(model.state_dict(), args.output)
    logger.info(f"Saved weights to {args.output}")
    if args.heatmap and dataset.samples:
        from .torch_net import TorchNet
        from .viz_heatmap import plot_value_gradient

        board = chess.Board(dataset.samples[0][0])
        net = TorchNet(model=model)
        plot_value_gradient(net, board, save_path=args.heatmap)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    main()