import os
import json
from fen_handler import load_fens_from_file
from metrics import MetricsManager

def print_ascii_board(board_state):
    print("  a b c d e f g h")
    for row_idx, row in enumerate(board_state):
        row_str = f"{8 - row_idx} "
        for cell in row:
            if cell is None:
                row_str += ". "
            else:
                symbol = cell.split('-')[1][0].upper() if "white" in cell else cell.split('-')[1][0].lower()
                row_str += symbol + " "
        print(row_str + f"{8 - row_idx}")
    print("  a b c d e f g h\n")

def save_position_as_json(position_id, board_state, metrics_dict):
    os.makedirs("output", exist_ok=True)
    data = {
        "position": position_id,
        "board": board_state,
        "metrics": metrics_dict
    }
    with open(f"output/position_{position_id:02}.json", "w") as f:
        json.dump(data, f, indent=2)

def main():
    all_positions = load_fens_from_file("fens.txt")
    for i, board_state in enumerate(all_positions):
        print(f"🔁 Позиція #{i + 1}")
        print_ascii_board(board_state)
        metrics = MetricsManager(board_state)
        metrics.update_all_metrics()
        metrics_data = metrics.get_metrics()
        print("📊 Метрики:")
        print(metrics_data)
        print("-" * 40)
        save_position_as_json(i + 1, board_state, metrics_data)

if __name__ == "__main__":
    main()
