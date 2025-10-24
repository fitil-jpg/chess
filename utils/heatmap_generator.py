#!/usr/bin/env python3
"""
Heatmap Generator for Chess Bots
Генерує теплові карти для різних ботів на різних етапах гри
"""

import os
import json
import chess
import chess.pgn
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HeatmapGenerator:
    """Генератор теплових карт для шахових ботів"""
    
    def __init__(self, runs_dir: str = "runs", output_dir: str = "heatmap_visualizations"):
        self.runs_dir = Path(runs_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Налаштування для різних етапів гри
        self.game_phases = {
            'opening': (1, 15),      # Ходи 1-15
            'middlegame': (16, 40),  # Ходи 16-40
            'endgame': (41, 200)     # Ходи 41+
        }
        
        # Символи фігур
        self.piece_symbols = {
            'pawn': ['P', 'p'],
            'knight': ['N', 'n'],
            'bishop': ['B', 'b'],
            'rook': ['R', 'r'],
            'queen': ['Q', 'q'],
            'king': ['K', 'k']
        }
    
    def load_games_for_bot(self, bot_name: str, limit: int = 100) -> List[Dict]:
        """Завантажити ігри для конкретного бота"""
        games = []
        
        try:
            # Спочатку пробуємо завантажити через load_runs
            try:
                from utils.load_runs import load_runs
                runs = load_runs(self.runs_dir)
                
                for run in runs:
                    for game in run.get('games', []):
                        # Перевіряємо чи бот брав участь у грі
                        modules_w = game.get('modules_w', [])
                        modules_b = game.get('modules_b', [])
                        
                        if bot_name in modules_w or bot_name in modules_b:
                            games.append({
                                'moves': game.get('moves', []),
                                'modules_w': modules_w,
                                'modules_b': modules_b,
                                'result': game.get('result', '*'),
                                'duration': game.get('duration_ms', 0)
                            })
                            
                            if len(games) >= limit:
                                break
                    
                    if len(games) >= limit:
                        break
            except Exception as e:
                logger.warning(f"Не вдалося завантажити через load_runs: {e}")
                
                # Fallback: завантажуємо напряму з JSON файлів
                for json_file in self.runs_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        for game in data.get('games', []):
                            modules_w = game.get('modules_w', [])
                            modules_b = game.get('modules_b', [])
                            
                            if bot_name in modules_w or bot_name in modules_b:
                                games.append({
                                    'moves': game.get('moves', []),
                                    'modules_w': modules_w,
                                    'modules_b': modules_b,
                                    'result': game.get('result', '*'),
                                    'duration': game.get('duration_ms', 0)
                                })
                                
                                if len(games) >= limit:
                                    break
                        
                        if len(games) >= limit:
                            break
                    except Exception as file_error:
                        logger.warning(f"Помилка завантаження файлу {json_file}: {file_error}")
                        continue
                    
        except Exception as e:
            logger.error(f"Помилка завантаження ігор для {bot_name}: {e}")
        
        return games
    
    def extract_piece_movements(self, games: List[Dict], piece_type: str = 'all', 
                               game_phase: str = 'all') -> Dict[str, List[Tuple[int, int]]]:
        """Витягти рухи фігур з ігор"""
        movements = defaultdict(list)
        
        for game in games:
            moves = game.get('moves', [])
            modules_w = game.get('modules_w', [])
            modules_b = game.get('modules_b', [])
            
            # Визначаємо діапазон ходів для етапу гри
            if game_phase != 'all' and game_phase in self.game_phases:
                start_move, end_move = self.game_phases[game_phase]
                moves = moves[start_move-1:end_move] if len(moves) >= start_move else []
            
            # Створюємо дошку для відстеження позицій
            board = chess.Board()
            
            for i, move_san in enumerate(moves):
                try:
                    move = board.parse_san(move_san)
                    piece = board.piece_at(move.from_square)
                    
                    if piece:
                        piece_symbol = piece.symbol()
                        
                        # Фільтруємо за типом фігури
                        if piece_type != 'all':
                            if piece_type in self.piece_symbols:
                                if piece_symbol not in self.piece_symbols[piece_type]:
                                    board.push(move)
                                    continue
                        
                        # Конвертуємо квадрат в координати
                        to_file = chess.square_file(move.to_square)
                        to_rank = chess.square_rank(move.to_square)
                        
                        movements[piece_symbol].append((to_file, to_rank))
                    
                    board.push(move)
                    
                except Exception as e:
                    logger.warning(f"Помилка парсингу ходу {move_san}: {e}")
                    continue
        
        return dict(movements)
    
    def create_heatmap_data(self, movements: Dict[str, List[Tuple[int, int]]], 
                           piece_type: str = 'all') -> Dict[str, np.ndarray]:
        """Створити дані для теплової карти"""
        heatmap_data = {}
        
        if piece_type == 'all':
            pieces_to_analyze = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
        else:
            pieces_to_analyze = self.piece_symbols.get(piece_type, [])
        
        for piece_symbol in pieces_to_analyze:
            if piece_symbol in movements:
                # Створюємо 8x8 сітку
                heatmap = np.zeros((8, 8))
                
                for file, rank in movements[piece_symbol]:
                    # Конвертуємо в індекси масиву (0-7)
                    heatmap[7-rank, file] += 1
                
                heatmap_data[piece_symbol] = heatmap
        
        return heatmap_data
    
    def generate_heatmap_visualization(self, heatmap_data: Dict[str, np.ndarray], 
                                     bot_name: str, game_phase: str, piece_type: str) -> str:
        """Генерувати візуалізацію теплової карти"""
        
        # Визначаємо кількість підграфіків
        pieces = list(heatmap_data.keys())
        if not pieces:
            return None
        
        n_pieces = len(pieces)
        cols = min(4, n_pieces)
        rows = (n_pieces + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3))
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes
        else:
            axes = axes.flatten()
        
        fig.suptitle(f'Heatmap: {bot_name} - {game_phase} - {piece_type}', fontsize=16)
        
        for i, piece_symbol in enumerate(pieces):
            ax = axes[i] if i < len(axes) else None
            if ax is None:
                break
                
            heatmap = heatmap_data[piece_symbol]
            
            if np.sum(heatmap) > 0:
                sns.heatmap(heatmap, 
                           annot=True, 
                           fmt='.0f', 
                           cmap='Reds',
                           ax=ax,
                           cbar_kws={'shrink': 0.8})
                ax.set_title(f'{piece_symbol} movements')
            else:
                ax.set_title(f'{piece_symbol} (no data)')
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            
            # Налаштування осей
            ax.set_xlabel('File (a-h)')
            ax.set_ylabel('Rank (1-8)')
            ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
            ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])
        
        # Приховуємо зайві підграфіки
        for i in range(len(pieces), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        # Зберігаємо файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{bot_name}_{game_phase}_{piece_type}_{timestamp}.png"
        filepath = self.output_dir / filename
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(filepath)
    
    def generate_heatmap(self, bot_name: str, game_phase: str = 'all', 
                        piece_type: str = 'all', games_limit: int = 100) -> Dict:
        """Основна функція генерації теплової карти"""
        
        logger.info(f"Генерація теплової карти для {bot_name} - {game_phase} - {piece_type}")
        
        # Завантажуємо ігри
        games = self.load_games_for_bot(bot_name, games_limit)
        
        if not games:
            return {
                'success': False,
                'error': f'Не знайдено ігор для бота {bot_name}',
                'games_count': 0
            }
        
        # Витягуємо рухи фігур
        movements = self.extract_piece_movements(games, piece_type, game_phase)
        
        if not movements:
            return {
                'success': False,
                'error': 'Не знайдено рухів фігур для аналізу',
                'games_count': len(games)
            }
        
        # Створюємо дані теплової карти
        heatmap_data = self.create_heatmap_data(movements, piece_type)
        
        # Генеруємо візуалізацію
        filepath = self.generate_heatmap_visualization(heatmap_data, bot_name, game_phase, piece_type)
        
        if not filepath:
            return {
                'success': False,
                'error': 'Не вдалося створити візуалізацію',
                'games_count': len(games)
            }
        
        # Зберігаємо дані в JSON
        json_data = {}
        for piece_symbol, heatmap in heatmap_data.items():
            json_data[piece_symbol] = heatmap.tolist()
        
        json_filename = filepath.replace('.png', '.json')
        with open(json_filename, 'w') as f:
            json.dump({
                'bot_name': bot_name,
                'game_phase': game_phase,
                'piece_type': piece_type,
                'games_count': len(games),
                'generated_at': datetime.now().isoformat(),
                'heatmap_data': json_data
            }, f, indent=2)
        
        return {
            'success': True,
            'filepath': filepath,
            'json_filepath': json_filename,
            'games_count': len(games),
            'pieces_analyzed': list(heatmap_data.keys()),
            'total_movements': sum(len(moves) for moves in movements.values())
        }
    
    def generate_all_bot_heatmaps(self, bots: List[str] = None, 
                                 game_phases: List[str] = None, 
                                 piece_types: List[str] = None) -> Dict:
        """Генерувати теплові карти для всіх ботів"""
        
        if bots is None:
            bots = ['DynamicBot', 'StockfishBot', 'RandomBot', 'AggressiveBot', 'FortifyBot']
        
        if game_phases is None:
            game_phases = ['opening', 'middlegame', 'endgame', 'all']
        
        if piece_types is None:
            piece_types = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'all']
        
        results = {}
        
        for bot in bots:
            results[bot] = {}
            for phase in game_phases:
                results[bot][phase] = {}
                for piece in piece_types:
                    try:
                        result = self.generate_heatmap(bot, phase, piece)
                        results[bot][phase][piece] = result
                    except Exception as e:
                        logger.error(f"Помилка генерації для {bot}-{phase}-{piece}: {e}")
                        results[bot][phase][piece] = {
                            'success': False,
                            'error': str(e)
                        }
        
        return results