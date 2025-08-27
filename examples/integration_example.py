import json
from utils.integration import parse_fen, generate_heatmaps, compute_metrics

fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

board = parse_fen(fen)
heatmaps = generate_heatmaps([fen])
metrics = compute_metrics(fen)

print("Board:")
print(board)
print("Heatmaps:")
print(json.dumps(heatmaps, indent=2))
print("Metrics:")
print(json.dumps(metrics, indent=2))
