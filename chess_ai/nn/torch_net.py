"""PyTorch network wrapper for chess AI.

The :class:`TorchNet` class exposes a ``predict_many`` method compatible with
:mod:`chess_ai.batched_mcts`. It can load either dummy weights or real weights
from disk based on a configuration file.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple, Optional

import logging
logger = logging.getLogger(__name__)

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
        # Inference/calibration options (may be overridden by from_config)
        self.policy_temperature: float = 1.0
        self.value_scale: float = 1.0
        self.value_bias: float = 0.0
        self.clamp_value: bool = True
        self._cache_size: int = 0
        self._cache: Optional["_LRUCache"] = None
        self._use_half: bool = False
        self._quantized: bool = False

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
        # Optional precision/quantization
        try:
            if bool(cfg.get("half_precision", False)) and net.device.type == "cuda":
                net.model.half()
                net._use_half = True
            if bool(cfg.get("quantize_dynamic", False)) and net.device.type == "cpu":
                # Best-effort: quantize Linear layers dynamically
                from torch.quantization import quantize_dynamic  # type: ignore
                net.model = quantize_dynamic(net.model, {torch.nn.Linear}, dtype=torch.qint8)  # type: ignore
                net._quantized = True
        except Exception:
            logger.warning("Quantization/half precision setup failed; continuing without.")

        # Calibration and caching
        net.policy_temperature = float(cfg.get("policy_temperature", 1.0) or 1.0)
        net.value_scale = float(cfg.get("value_scale", 1.0) or 1.0)
        net.value_bias = float(cfg.get("value_bias", 0.0) or 0.0)
        net.clamp_value = bool(cfg.get("clamp_value", True))
        net._cache_size = int(cfg.get("cache_size", 0) or 0)
        if net._cache_size > 0:
            net._cache = _LRUCache(net._cache_size)
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
        # Try cache first
        cache = self._cache
        cached_indices: List[int] = []
        cached_values: Dict[int, Tuple[Dict[str, float], float]] = {}
        if cache is not None:
            for i, b in enumerate(boards_list):
                fen = b.fen()
                got = cache.get(fen)
                if got is not None:
                    cached_indices.append(i)
                    cached_values[i] = got

        # Prepare tensors for uncached boards
        to_eval_indices: List[int] = [i for i in range(len(boards_list)) if i not in cached_indices]
        eval_boards: List[chess.Board] = [boards_list[i] for i in to_eval_indices]
        results_pairs: Dict[int, Tuple[Dict[str, float], float]] = {}

        if eval_boards:
            batch = torch.stack([board_to_tensor(b) for b in eval_boards]).to(self.device)
            # Ensure dtype matches model
            try:
                param_dtype = next(self.model.parameters()).dtype
                if batch.dtype != param_dtype:
                    batch = batch.to(param_dtype)
            except StopIteration:
                pass

            with torch.inference_mode():
                policy_logits, values = self.model(batch)

            temp = max(1e-3, float(self.policy_temperature))
            for j, (b, logits, v) in enumerate(zip(eval_boards, policy_logits, values)):
                legal = list(b.legal_moves)
                policy_ucis: Dict[str, float] = {}
                if legal:
                    idx = torch.tensor([m.from_square * 64 + m.to_square for m in legal], device=logits.device)
                    sel = logits[idx] / temp
                    probs = torch.softmax(sel, dim=0).cpu().tolist()
                    policy_ucis = {m.uci(): p for m, p in zip(legal, probs)}
                val = float(v.item())
                val = self.value_scale * val + self.value_bias
                if self.clamp_value:
                    val = max(-1.0, min(1.0, val))
                global_index = to_eval_indices[j]
                results_pairs[global_index] = (policy_ucis, val)
                if cache is not None:
                    cache.set(b.fen(), (policy_ucis, val))

        # Assemble final results in original order
        results: List[Tuple[Dict[chess.Move, float], float]] = []
        for i, b in enumerate(boards_list):
            if i in cached_values:
                policy_ucis, val = cached_values[i]
            else:
                policy_ucis, val = results_pairs[i]
            # Map back to Move objects and filter to legal only
            legal = set(b.legal_moves)
            policy: Dict[chess.Move, float] = {}
            if policy_ucis:
                for uci, p in policy_ucis.items():
                    try:
                        mv = chess.Move.from_uci(uci)
                    except Exception:
                        continue
                    if mv in legal:
                        policy[mv] = p
            results.append((policy, float(val)))
        return results


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    from .viz_heatmap import plot_policy_heatmap, plot_value_gradient

    parser = argparse.ArgumentParser(description="TorchNet demo")
    parser.add_argument("--config", default="configs/nn.yaml", help="Path to nn config file")
    parser.add_argument(
        "--policy-heatmap", help="Save policy heatmap for the initial position"
    )
    parser.add_argument(
        "--value-heatmap", help="Save value-gradient heatmap for the initial position"
    )
    args = parser.parse_args()

    net = TorchNet.from_config(args.config)
    board = chess.Board()
    policy, value = net.predict_many([board])[0]
    logger.info(f"Value: {value:.3f}, policy moves: {len(policy)}")
    if args.policy_heatmap:
        plot_policy_heatmap(board, policy, save_path=args.policy_heatmap)
    if args.value_heatmap:
        plot_value_gradient(net, board, save_path=args.value_heatmap)
