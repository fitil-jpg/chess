#!/usr/bin/env python3
"""
Setup script for heatmap visualization directories
Створює необхідні директорії для зберігання теплових карт
"""

import os
from pathlib import Path

def setup_heatmap_directories():
    """Створити необхідні директорії для теплових карт"""
    
    directories = [
        "heatmap_visualizations",
        "heatmap_visualizations/generated",
        "heatmap_visualizations/bot_specific",
        "heatmap_visualizations/game_phases",
        "heatmap_visualizations/piece_analysis",
        "runs",
        "output",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Створюємо .gitkeep файли для порожніх директорій
        gitkeep_file = Path(directory) / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.touch()
        
        print(f"✓ Створено директорію: {directory}")

def create_heatmap_config():
    """Створити конфігураційний файл для теплових карт"""
    
    config = {
        "heatmap_settings": {
            "default_bots": [
                "DynamicBot",
                "StockfishBot", 
                "RandomBot",
                "AggressiveBot",
                "FortifyBot",
                "EndgameBot",
                "CriticalBot",
                "TrapBot",
                "KingValueBot",
                "NeuralBot",
                "UtilityBot",
                "PieceMateBot"
            ],
            "game_phases": {
                "opening": {"moves": [1, 15], "description": "Дебют"},
                "middlegame": {"moves": [16, 40], "description": "Мітельшпіль"},
                "endgame": {"moves": [41, 200], "description": "Ендшпіль"},
                "all": {"moves": [1, 200], "description": "Вся гра"}
            },
            "piece_types": {
                "pawn": {"symbols": ["P", "p"], "description": "Пішаки"},
                "knight": {"symbols": ["N", "n"], "description": "Коні"},
                "bishop": {"symbols": ["B", "b"], "description": "Слони"},
                "rook": {"symbols": ["R", "r"], "description": "Тури"},
                "queen": {"symbols": ["Q", "q"], "description": "Ферзі"},
                "king": {"symbols": ["K", "k"], "description": "Королі"},
                "all": {"symbols": ["P", "N", "B", "R", "Q", "K", "p", "n", "b", "r", "q", "k"], "description": "Всі фігури"}
            },
            "output_formats": ["png", "json"],
            "default_games_limit": 100,
            "heatmap_colors": {
                "colormap": "Reds",
                "dpi": 300,
                "figsize": [16, 12]
            }
        },
        "analysis_settings": {
            "hot_spot_threshold": 0.8,
            "center_squares": ["d4", "d5", "e4", "e5"],
            "king_side_files": ["f", "g", "h"],
            "queen_side_files": ["a", "b", "c"]
        }
    }
    
    config_file = Path("heatmap_config.json")
    import json
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Створено конфігураційний файл: {config_file}")

if __name__ == "__main__":
    print("Налаштування директорій для теплових карт...")
    setup_heatmap_directories()
    create_heatmap_config()
    print("\n✓ Налаштування завершено!")
    print("\nСтруктура директорій:")
    print("heatmap_visualizations/")
    print("├── generated/          # Згенеровані теплові карти")
    print("├── bot_specific/       # Теплові карти для конкретних ботів")
    print("├── game_phases/        # Теплові карти по етапах гри")
    print("└── piece_analysis/     # Аналіз окремих фігур")