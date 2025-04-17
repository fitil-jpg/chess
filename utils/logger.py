import json
from datetime import datetime

class GameLogger:
    def __init__(self):
        self.log = []

    def record_move(self, move, color, evaluation, phase):
        self.log.append({
            "move": move,
            "by": color,
            "evaluation": round(evaluation, 2),
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat()
        })

    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.log, f, indent=2)

    def print_log(self):
        for entry in self.log:
            print(f"{entry['by']} played {entry['move']} | eval: {entry['evaluation']} | {entry['phase']}")

