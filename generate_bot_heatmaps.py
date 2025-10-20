#!/usr/bin/env python3
"""
Generate heatmaps for all chess bots
Генерує теплові карти для всіх ботів з різними налаштуваннями
"""

import sys
import argparse
from pathlib import Path

# Додаємо поточну директорію до шляху
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.heatmap_generator import HeatmapGenerator
import logging

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Generate heatmaps for chess bots')
    parser.add_argument('--bot', type=str, help='Specific bot to analyze')
    parser.add_argument('--phase', type=str, choices=['opening', 'middlegame', 'endgame', 'all'], 
                       default='all', help='Game phase to analyze')
    parser.add_argument('--piece', type=str, 
                       choices=['pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'all'],
                       default='all', help='Piece type to analyze')
    parser.add_argument('--games', type=int, default=100, help='Number of games to analyze')
    parser.add_argument('--all-bots', action='store_true', help='Generate heatmaps for all bots')
    parser.add_argument('--output-dir', type=str, default='heatmap_visualizations', 
                       help='Output directory for heatmaps')
    
    args = parser.parse_args()
    
    # Створюємо генератор
    generator = HeatmapGenerator(output_dir=args.output_dir)
    
    if args.all_bots:
        logger.info("Генерація теплових карт для всіх ботів...")
        
        bots = [
            'DynamicBot', 'StockfishBot', 'RandomBot', 'AggressiveBot', 
            'FortifyBot', 'EndgameBot', 'CriticalBot', 'TrapBot',
            'KingValueBot', 'NeuralBot', 'UtilityBot', 'PieceMateBot'
        ]
        
        game_phases = ['opening', 'middlegame', 'endgame', 'all']
        piece_types = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'all']
        
        results = generator.generate_all_bot_heatmaps(bots, game_phases, piece_types)
        
        # Зберігаємо результати
        import json
        results_file = Path(args.output_dir) / "generation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Результати збережено в {results_file}")
        
        # Підрахунок успішних генерацій
        total_attempts = 0
        successful = 0
        
        for bot in results:
            for phase in results[bot]:
                for piece in results[bot][phase]:
                    total_attempts += 1
                    if results[bot][phase][piece].get('success', False):
                        successful += 1
        
        logger.info(f"Згенеровано {successful}/{total_attempts} теплових карт")
        
    elif args.bot:
        logger.info(f"Генерація теплової карти для {args.bot} - {args.phase} - {args.piece}")
        
        result = generator.generate_heatmap(
            bot_name=args.bot,
            game_phase=args.phase,
            piece_type=args.piece,
            games_limit=args.games
        )
        
        if result['success']:
            logger.info(f"✓ Теплова карта згенерована: {result['filepath']}")
            logger.info(f"  Ігор проаналізовано: {result['games_count']}")
            logger.info(f"  Фігури: {result['pieces_analyzed']}")
            logger.info(f"  Всього рухів: {result['total_movements']}")
        else:
            logger.error(f"✗ Помилка генерації: {result.get('error', 'Невідома помилка')}")
            sys.exit(1)
    else:
        logger.error("Вкажіть --bot або --all-bots")
        sys.exit(1)

if __name__ == "__main__":
    main()