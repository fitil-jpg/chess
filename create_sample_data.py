#!/usr/bin/env python3
"""
Create sample game data for testing heatmap generation
Створює зразкові дані ігор для тестування генерації теплових карт
"""

import json
import os
from pathlib import Path
from datetime import datetime

def create_sample_runs():
    """Створити зразкові дані ігор"""
    
    # Створюємо директорію runs якщо не існує
    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)
    
    # Зразкові ігри з різними ботами
    sample_games = [
        {
            "result": "1-0",
            "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7", 
                     "Re1", "b5", "Bb3", "d6", "c3", "O-O", "h3", "Nb8", "d4", "Nbd7",
                     "c4", "c6", "cxb5", "axb5", "Nc3", "Bb7", "Bg5", "b4", "Nb1", "h6",
                     "Bh4", "c5", "dxc5", "dxc5", "Nbd2", "Qc7", "Bxf6", "Nxf6", "Nc4", "Rfd8"],
            "fens": ["rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                    "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
                    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
                    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"],
            "modules_w": ["DynamicBot", "DynamicBot", "DynamicBot", "DynamicBot", "DynamicBot"],
            "modules_b": ["StockfishBot", "StockfishBot", "StockfishBot", "StockfishBot", "StockfishBot"],
            "duration_ms": 45000
        },
        {
            "result": "0-1", 
            "moves": ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4", "e3", "b6", "Nge2", "Ba6",
                     "a3", "Bxc3+", "Nxc3", "d5", "cxd5", "exd5", "b4", "O-O", "Bb2", "c5",
                     "bxc5", "bxc5", "Qc2", "Nc6", "Rd1", "Qe7", "Be2", "Rfd8", "O-O", "Ne4"],
            "modules_w": ["RandomBot", "RandomBot", "RandomBot", "RandomBot", "RandomBot"],
            "modules_b": ["AggressiveBot", "AggressiveBot", "AggressiveBot", "AggressiveBot", "AggressiveBot"],
            "duration_ms": 32000
        },
        {
            "result": "1/2-1/2",
            "moves": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6",
                     "Be3", "e5", "Nb3", "Be6", "f3", "Be7", "Qd2", "O-O", "O-O-O", "Nbd7",
                     "g4", "b5", "g5", "b4", "Ne2", "Ne8", "h4", "a5", "Bg2", "a4"],
            "modules_w": ["FortifyBot", "FortifyBot", "FortifyBot", "FortifyBot", "FortifyBot"],
            "modules_b": ["EndgameBot", "EndgameBot", "EndgameBot", "EndgameBot", "EndgameBot"],
            "duration_ms": 28000
        },
        {
            "result": "1-0",
            "moves": ["Nf3", "d5", "d4", "Nf6", "c4", "e6", "Nc3", "Be7", "Bf4", "O-O",
                     "e3", "c5", "dxc5", "Nc6", "Qc2", "Qa5", "a3", "Bxc5", "Rd1", "Qc7",
                     "Be2", "Rd8", "O-O", "a6", "b4", "Be7", "Rac1", "b6", "cxd5", "exd5"],
            "modules_w": ["CriticalBot", "CriticalBot", "CriticalBot", "CriticalBot", "CriticalBot"],
            "modules_b": ["TrapBot", "TrapBot", "TrapBot", "TrapBot", "TrapBot"],
            "duration_ms": 38000
        },
        {
            "result": "0-1",
            "moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "c3", "Nf6", "d4", "exd4",
                     "cxd4", "Bb4+", "Bd2", "Bxd2+", "Nbxd2", "d5", "exd5", "Nxd5", "O-O", "Be6",
                     "Re1", "Be7", "Bxd5", "Qxd5", "Nc4", "Qd6", "Qe2", "O-O", "Rad1", "Rfd8"],
            "modules_w": ["KingValueBot", "KingValueBot", "KingValueBot", "KingValueBot", "KingValueBot"],
            "modules_b": ["NeuralBot", "NeuralBot", "NeuralBot", "NeuralBot", "NeuralBot"],
            "duration_ms": 41000
        }
    ]
    
    # Створюємо файл з даними
    run_data = {
        "timestamp": datetime.now().isoformat(),
        "games": sample_games,
        "metadata": {
            "total_games": len(sample_games),
            "bots_used": ["DynamicBot", "StockfishBot", "RandomBot", "AggressiveBot", 
                         "FortifyBot", "EndgameBot", "CriticalBot", "TrapBot", 
                         "KingValueBot", "NeuralBot"],
            "created_by": "sample_data_generator"
        }
    }
    
    # Зберігаємо в файл
    runs_file = runs_dir / "sample_run_001.json"
    with open(runs_file, 'w', encoding='utf-8') as f:
        json.dump(run_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Створено зразкові дані: {runs_file}")
    print(f"  Кількість ігор: {len(sample_games)}")
    print(f"  Боти: {', '.join(set([bot for game in sample_games for bot in game['modules_w'] + game['modules_b']]))}")
    
    return runs_file

def create_additional_sample_data():
    """Створити додаткові зразкові дані для різних етапів гри"""
    
    # Ігри з більшою кількістю ходів для тестування етапів
    long_games = [
        {
            "result": "1-0",
            "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7",
                     "Re1", "b5", "Bb3", "d6", "c3", "O-O", "h3", "Nb8", "d4", "Nbd7",
                     "c4", "c6", "cxb5", "axb5", "Nc3", "Bb7", "Bg5", "b4", "Nb1", "h6",
                     "Bh4", "c5", "dxc5", "dxc5", "Nbd2", "Qc7", "Bxf6", "Nxf6", "Nc4", "Rfd8",
                     "Qe2", "Be7", "Bxf6", "Bxf6", "Nxd6", "Qb6", "Nc4", "Qc7", "Ne5", "Bxe5",
                     "Rxe5", "f6", "Re1", "Rd6", "Qe4", "Rf7", "Qe6", "Qd8", "Qxd6", "Qxd6",
                     "Rxd6", "Rf8", "Rd7", "Rf7", "Rxf7", "Kxf7", "Kf1", "Ke6", "Ke2", "Kd5",
                     "Kd3", "Kc5", "Kc3", "Kb5", "Kb3", "Ka5", "Kc4", "Ka4", "Kd5", "Kb3",
                     "Ke5", "Kc3", "Kf5", "Kd2", "Kg5", "Ke1", "Kh5", "Kf1", "Kg4", "Ke1", "Kh3"],
            "modules_w": ["DynamicBot"] * 20 + ["EndgameBot"] * 20,
            "modules_b": ["StockfishBot"] * 20 + ["EndgameBot"] * 20,
            "duration_ms": 120000
        }
    ]
    
    runs_dir = Path("runs")
    run_data = {
        "timestamp": datetime.now().isoformat(),
        "games": long_games,
        "metadata": {
            "total_games": len(long_games),
            "bots_used": ["DynamicBot", "StockfishBot", "EndgameBot"],
            "created_by": "sample_data_generator_long_games"
        }
    }
    
    runs_file = runs_dir / "sample_run_002.json"
    with open(runs_file, 'w', encoding='utf-8') as f:
        json.dump(run_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Створено довгі ігри: {runs_file}")
    return runs_file

if __name__ == "__main__":
    print("🎮 Створення зразкових даних для тестування теплових карт...")
    
    create_sample_runs()
    create_additional_sample_data()
    
    print("\n✅ Зразкові дані створено!")
    print("Тепер можна тестувати генерацію теплових карт.")