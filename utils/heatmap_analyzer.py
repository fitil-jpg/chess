#!/usr/bin/env python3
"""
Heatmap Analyzer for Chess Bots
Аналізує паттерни рухів фігур у різних ботах
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class HeatmapAnalyzer:
    """Аналізатор теплових карт для шахових ботів"""
    
    def __init__(self, heatmap_dir: str = "heatmap_visualizations"):
        self.heatmap_dir = Path(heatmap_dir)
    
    def load_heatmap_data(self, bot_name: str, game_phase: str = 'all', 
                         piece_type: str = 'all') -> Optional[Dict]:
        """Завантажити дані теплової карти"""
        
        # Шукаємо JSON файл з даними
        pattern = f"{bot_name}_{game_phase}_{piece_type}_*.json"
        json_files = list(self.heatmap_dir.glob(pattern))
        
        if not json_files:
            logger.warning(f"Не знайдено файл даних для {bot_name}-{game_phase}-{piece_type}")
            return None
        
        # Беремо найновіший файл
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Помилка завантаження файлу {latest_file}: {e}")
            return None
    
    def analyze_piece_patterns(self, heatmap_data: np.ndarray) -> Dict:
        """Аналізувати паттерни рухів фігури"""
        
        if heatmap_data is None or np.sum(heatmap_data) == 0:
            return {
                'total_movements': 0,
                'hot_spots': [],
                'cold_spots': [],
                'center_control': 0,
                'king_side_activity': 0,
                'queen_side_activity': 0
            }
        
        # Знаходимо гарячі точки (найбільша активність)
        max_value = np.max(heatmap_data)
        hot_spots = []
        cold_spots = []
        
        for i in range(8):
            for j in range(8):
                value = heatmap_data[i, j]
                square_name = chr(ord('a') + j) + str(8 - i)
                
                if value >= max_value * 0.8:  # 80% від максимуму
                    hot_spots.append({
                        'square': square_name,
                        'value': float(value),
                        'rank': 8 - i,
                        'file': chr(ord('a') + j)
                    })
                elif value == 0:
                    cold_spots.append({
                        'square': square_name,
                        'rank': 8 - i,
                        'file': chr(ord('a') + j)
                    })
        
        # Аналіз контролю центру (d4, d5, e4, e5)
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]  # d4, d5, e4, e5
        center_control = sum(heatmap_data[i, j] for i, j in center_squares)
        
        # Аналіз активності на королівському фланзі (f, g, h файли)
        king_side_activity = np.sum(heatmap_data[:, 5:8])  # f, g, h файли
        
        # Аналіз активності на ферзевому фланзі (a, b, c файли)
        queen_side_activity = np.sum(heatmap_data[:, 0:3])  # a, b, c файли
        
        return {
            'total_movements': int(np.sum(heatmap_data)),
            'hot_spots': sorted(hot_spots, key=lambda x: x['value'], reverse=True)[:5],
            'cold_spots': cold_spots[:10],  # Топ 10 холодних квадратів
            'center_control': float(center_control),
            'king_side_activity': float(king_side_activity),
            'queen_side_activity': float(queen_side_activity),
            'activity_ratio': {
                'king_side': float(king_side_activity / np.sum(heatmap_data)) if np.sum(heatmap_data) > 0 else 0,
                'queen_side': float(queen_side_activity / np.sum(heatmap_data)) if np.sum(heatmap_data) > 0 else 0,
                'center': float(center_control / np.sum(heatmap_data)) if np.sum(heatmap_data) > 0 else 0
            }
        }
    
    def compare_bot_patterns(self, bot1: str, bot2: str, game_phase: str = 'all', 
                           piece_type: str = 'all') -> Dict:
        """Порівняти паттерни двох ботів"""
        
        data1 = self.load_heatmap_data(bot1, game_phase, piece_type)
        data2 = self.load_heatmap_data(bot2, game_phase, piece_type)
        
        if not data1 or not data2:
            return {
                'success': False,
                'error': 'Не вдалося завантажити дані для порівняння'
            }
        
        comparison = {
            'bot1': bot1,
            'bot2': bot2,
            'game_phase': game_phase,
            'piece_type': piece_type,
            'comparison': {}
        }
        
        # Порівнюємо кожну фігуру
        for piece_symbol in data1.get('heatmap_data', {}):
            if piece_symbol in data2.get('heatmap_data', {}):
                heatmap1 = np.array(data1['heatmap_data'][piece_symbol])
                heatmap2 = np.array(data2['heatmap_data'][piece_symbol])
                
                analysis1 = self.analyze_piece_patterns(heatmap1)
                analysis2 = self.analyze_piece_patterns(heatmap2)
                
                comparison['comparison'][piece_symbol] = {
                    'bot1': analysis1,
                    'bot2': analysis2,
                    'differences': {
                        'total_movements_diff': analysis1['total_movements'] - analysis2['total_movements'],
                        'center_control_diff': analysis1['center_control'] - analysis2['center_control'],
                        'king_side_activity_diff': analysis1['king_side_activity'] - analysis2['king_side_activity'],
                        'queen_side_activity_diff': analysis1['queen_side_activity'] - analysis2['queen_side_activity']
                    }
                }
        
        return comparison
    
    def analyze_bot_patterns(self, bot_name: str, piece_type: str = 'all') -> Dict:
        """Аналізувати паттерни конкретного бота"""
        
        data = self.load_heatmap_data(bot_name, 'all', piece_type)
        
        if not data:
            return {
                'success': False,
                'error': f'Не знайдено дані для бота {bot_name}'
            }
        
        analysis = {
            'bot_name': bot_name,
            'piece_type': piece_type,
            'games_count': data.get('games_count', 0),
            'generated_at': data.get('generated_at', ''),
            'pieces_analysis': {}
        }
        
        # Аналізуємо кожну фігуру
        for piece_symbol, heatmap_array in data.get('heatmap_data', {}).items():
            heatmap = np.array(heatmap_array)
            piece_analysis = self.analyze_piece_patterns(heatmap)
            analysis['pieces_analysis'][piece_symbol] = piece_analysis
        
        # Загальна статистика
        total_movements = sum(analysis['pieces_analysis'][piece]['total_movements'] 
                             for piece in analysis['pieces_analysis'])
        
        analysis['summary'] = {
            'total_movements': total_movements,
            'pieces_analyzed': len(analysis['pieces_analysis']),
            'most_active_piece': max(analysis['pieces_analysis'].items(), 
                                   key=lambda x: x[1]['total_movements'])[0] if analysis['pieces_analysis'] else None,
            'least_active_piece': min(analysis['pieces_analysis'].items(), 
                                    key=lambda x: x[1]['total_movements'])[0] if analysis['pieces_analysis'] else None
        }
        
        return analysis
    
    def get_bot_recommendations(self, bot_name: str) -> Dict:
        """Отримати рекомендації для покращення бота на основі аналізу"""
        
        analysis = self.analyze_bot_patterns(bot_name)
        
        if not analysis.get('success', True):  # Якщо success = False
            return analysis
        
        recommendations = {
            'bot_name': bot_name,
            'recommendations': [],
            'strengths': [],
            'weaknesses': []
        }
        
        pieces_analysis = analysis.get('pieces_analysis', {})
        
        for piece_symbol, piece_data in pieces_analysis.items():
            total_movements = piece_data['total_movements']
            center_control = piece_data['center_control']
            king_side = piece_data['activity_ratio']['king_side']
            queen_side = piece_data['activity_ratio']['queen_side']
            
            # Аналіз активності
            if total_movements < 10:
                recommendations['weaknesses'].append(f"{piece_symbol}: Низька активність ({total_movements} рухів)")
            elif total_movements > 50:
                recommendations['strengths'].append(f"{piece_symbol}: Висока активність ({total_movements} рухів)")
            
            # Аналіз контролю центру
            if center_control < total_movements * 0.1:
                recommendations['recommendations'].append(f"{piece_symbol}: Збільшити контроль центру")
            
            # Аналіз балансу флангів
            if abs(king_side - queen_side) > 0.3:
                if king_side > queen_side:
                    recommendations['recommendations'].append(f"{piece_symbol}: Збалансувати активність між флангами (більше на королівському)")
                else:
                    recommendations['recommendations'].append(f"{piece_symbol}: Збалансувати активність між флангами (більше на ферзевому)")
        
        return recommendations