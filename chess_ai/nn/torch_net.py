"""PyTorch network wrapper for chess AI.

The :class:`TorchNet` class exposes a ``predict_many`` method compatible with
:mod:`chess_ai.batched_mcts`. It can load either dummy weights or real weights
from disk based on a configuration file.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import chess
import torch
import yaml

from .simple_model import (
    SimpleChessModel,
    board_to_tensor,
    load_dummy_weights,
)


class TorchNet:
    """Wrapper around :class:`SimpleChessModel` providing ``predict_many``."""

    def __init__(self, model: SimpleChessModel | None = None, device: str | None = None) -> None:
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model = model or SimpleChessModel()
        self.model.to(self.device)
        self.model.eval()

    # ------------------------------------------------------------------
    @classmethod
    def from_config(cls, path: str = "configs/nn.yaml") -> "TorchNet":
        """Create a :class:`TorchNet` based on a YAML config file."""
        with open(path, "r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh) or {}
        net = cls()
        if cfg.get("use_dummy_model", True):
            load_dummy_weights(net.model)
        else:
            weights = cfg.get("weights")
            if weights:
                state = torch.load(weights, map_location=net.device)
                net.model.load_state_dict(state)
        return net

    # ------------------------------------------------------------------
    def load_dummy_weights(self) -> None:
        """Public helper to load dummy weights into the model."""
        load_dummy_weights(self.model)

    # ------------------------------------------------------------------
    def predict_many(self, boards: Iterable[chess.Board]) -> List[Tuple[Dict[chess.Move, float], float]]:
        """Evaluate a batch of boards returning policy and value for each."""
        boards_list = list(boards)
        if not boards_list:
            return []
        batch = torch.stack([board_to_tensor(b) for b in boards_list]).to(self.device)
        with torch.no_grad():
            policy_logits, values = self.model(batch)
        results: List[Tuple[Dict[chess.Move, float], float]] = []
        for b, logits, v in zip(boards_list, policy_logits, values):
            legal = list(b.legal_moves)
            policy: Dict[chess.Move, float] = {}
            if legal:
                idx = torch.tensor([m.from_square * 64 + m.to_square for m in legal], device=logits.device)
                probs = torch.softmax(logits[idx], dim=0).cpu().tolist()
                policy = {m: p for m, p in zip(legal, probs)}
            results.append((policy, float(v.item())))
        return results


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TorchNet demo")
    parser.add_argument("--config", default="configs/nn.yaml", help="Path to nn config file")
    args = parser.parse_args()

    net = TorchNet.from_config(args.config)
    board = chess.Board()
    policy, value = net.predict_many([board])[0]
    print(f"Value: {value:.3f}, policy moves: {len(policy)}")
