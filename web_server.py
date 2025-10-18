#!/usr/bin/env python3
"""
Веб-сервер для Chess AI Analytics Dashboard
Надає API для взаємодії з шаховими ботами та веб-інтерфейсом
"""

import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Додаємо поточну директорію до шляху
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import chess
import chess.engine

# Імпортуємо існуючі компоненти
from chess_ai.bot_agent import make_agent
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage
from utils.module_colors import MODULE_COLORS, REASON_PRIORITY
from chess_ai.elo_sync_manager import ELOSyncManager

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ініціалізація Flask додатку
app = Flask(__name__)
CORS(app)

# Глобальні змінні
game_data = {
    'current_game': None,
    'game_history': [],
    'is_playing': False,
    'agents': {},
    'elo_manager': None
}

# Директорія з логами ігор (можна перевизначити через RUNS_DIR)
RUNS_DIR = os.environ.get("RUNS_DIR", "runs")

class GameManager:
    """Менеджер для управління іграми та ботами"""
    
    def __init__(self):
        self.current_board = chess.Board()
        self.game_moves = []
        self.game_modules = {'white': [], 'black': []}
        self.start_time = None
        self.white_agent = None
        self.black_agent = None
        
    def initialize_agents(self, white_bot: str, black_bot: str):
        """Ініціалізація ботів"""
        try:
            self.white_agent = make_agent(white_bot, chess.WHITE)
            self.black_agent = make_agent(black_bot, chess.BLACK)
            logger.info(f"Ініціалізовано ботів: {white_bot} vs {black_bot}")
            return True
        except Exception as e:
            logger.error(f"Помилка ініціалізації ботів: {e}")
            return False
    
    def reset_game(self):
        """Скидання гри"""
        self.current_board = chess.Board()
        self.game_moves = []
        self.game_modules = {'white': [], 'black': []}
        self.start_time = None
    
    def make_move(self) -> Optional[Dict[str, Any]]:
        """Зробити хід"""
        if self.current_board.is_game_over():
            return None
            
        try:
            mover_color = self.current_board.turn
            agent = self.white_agent if mover_color == chess.WHITE else self.black_agent
            
            if not agent:
                return None
                
            move = agent.choose_move(self.current_board)
            if not move or not self.current_board.is_legal(move):
                return None
                
            # Отримуємо інформацію про модуль
            reason = agent.get_last_reason() if hasattr(agent, "get_last_reason") else "UNKNOWN"
            module_key = self._extract_reason_key(reason)
            
            # Записуємо хід
            san_move = self.current_board.san(move)
            self.game_moves.append(san_move)
            
            if mover_color == chess.WHITE:
                self.game_modules['white'].append(module_key)
            else:
                self.game_modules['black'].append(module_key)
            
            self.current_board.push(move)
            
            return {
                'move': san_move,
                'module': module_key,
                'color': 'white' if mover_color == chess.WHITE else 'black',
                'fen': self.current_board.fen(),
                'is_game_over': self.current_board.is_game_over(),
                'result': self.current_board.result() if self.current_board.is_game_over() else None
            }
            
        except Exception as e:
            logger.error(f"Помилка при виконанні ходу: {e}")
            return None
    
    def _extract_reason_key(self, reason: str) -> str:
        """Витягти ключ модуля з reason"""
        if not reason or reason == "-":
            return "OTHER"
        up = reason.upper()
        
        for tok in REASON_PRIORITY:
            if tok in up:
                return tok
                
        import re
        m = re.search(r"\b[A-Z][A-Z_]{1,}\b", up)
        if m:
            return m.group(0)
            
        return "OTHER"
    
    def get_board_state(self) -> Dict[str, Any]:
        """Отримати поточний стан доски"""
        return {
            'fen': self.current_board.fen(),
            'moves': self.game_moves,
            'modules': self.game_modules,
            'is_game_over': self.current_board.is_game_over(),
            'result': self.current_board.result() if self.current_board.is_game_over() else None,
            'turn': 'white' if self.current_board.turn == chess.WHITE else 'black'
        }

# Ініціалізація менеджера ігор
game_manager = GameManager()

@app.route('/')
def index():
    """Головна сторінка"""
    return send_from_directory('.', 'web_interface.html')

@app.route('/api/status')
def get_status():
    """Отримати статус системи"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'game_data': {
            'is_playing': game_data['is_playing'],
            'current_game': game_manager.get_board_state() if game_manager.current_board else None
        }
    })

@app.route('/api/games', methods=['GET'])
def get_games():
    """Отримати список ігор"""
    try:
        # Завантажуємо існуючі ігри з файлів
        runs = load_runs(RUNS_DIR)
        games = []
        
        for run in runs:
            for game in run.get('games', []):
                games.append({
                    'id': len(games) + 1,
                    'result': game.get('result', '*'),
                    'moves': len(game.get('moves', [])),
                    'duration': game.get('duration_ms', 0),
                    'modules': {
                        'white': game.get('modules_w', [])[0] if game.get('modules_w') else 'Unknown',
                        'black': game.get('modules_b', [])[0] if game.get('modules_b') else 'Unknown'
                    },
                    'movesList': game.get('moves', [])[:20]  # Перші 20 ходів
                })
        
        return jsonify(games)
    except Exception as e:
        logger.error(f"Помилка завантаження ігор: {e}")
        return jsonify([])

@app.route('/api/modules', methods=['GET'])
def get_modules():
    """Отримати статистику модулів"""
    try:
        runs = load_runs(RUNS_DIR)
        module_stats = {}
        
        for run in runs:
            for game in run.get('games', []):
                for module in game.get('modules_w', []) + game.get('modules_b', []):
                    module_stats[module] = module_stats.get(module, 0) + 1
        
        return jsonify(module_stats)
    except Exception as e:
        logger.error(f"Помилка завантаження модулів: {e}")
        return jsonify({})

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Почати нову гру"""
    try:
        data = request.get_json() or {}
        white_bot = data.get('white_bot', 'StockfishBot')
        black_bot = data.get('black_bot', 'DynamicBot')
        
        # Ініціалізуємо ботів
        if not game_manager.initialize_agents(white_bot, black_bot):
            return jsonify({'error': 'Не вдалося ініціалізувати ботів'}), 400
        
        # Скидаємо гру
        game_manager.reset_game()
        game_data['is_playing'] = True
        game_manager.start_time = time.time()
        
        return jsonify({
            'success': True,
            'message': f'Гра розпочата: {white_bot} vs {black_bot}',
            'board_state': game_manager.get_board_state()
        })
        
    except Exception as e:
        logger.error(f"Помилка початку гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/move', methods=['POST'])
def make_move():
    """Зробити хід"""
    try:
        if not game_data['is_playing']:
            return jsonify({'error': 'Гра не активна'}), 400
        
        move_result = game_manager.make_move()
        if not move_result:
            return jsonify({'error': 'Не вдалося зробити хід'}), 400
        
        # Якщо гра закінчена, зберігаємо результат
        if move_result['is_game_over']:
            game_data['is_playing'] = False
            game_data['game_history'].append({
                'id': len(game_data['game_history']) + 1,
                'result': move_result['result'],
                'moves': game_manager.game_moves,
                'modules': game_manager.game_modules,
                'duration': int((time.time() - game_manager.start_time) * 1000) if game_manager.start_time else 0,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': True,
            'move_result': move_result,
            'board_state': game_manager.get_board_state()
        })
        
    except Exception as e:
        logger.error(f"Помилка виконання ходу: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/stop', methods=['POST'])
def stop_game():
    """Зупинити гру"""
    try:
        game_data['is_playing'] = False
        return jsonify({'success': True, 'message': 'Гра зупинена'})
    except Exception as e:
        logger.error(f"Помилка зупинки гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """Скинути гру"""
    try:
        game_data['is_playing'] = False
        game_manager.reset_game()
        return jsonify({'success': True, 'message': 'Гра скинута'})
    except Exception as e:
        logger.error(f"Помилка скидання гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """Отримати поточний стан гри"""
    try:
        return jsonify(game_manager.get_board_state())
    except Exception as e:
        logger.error(f"Помилка отримання стану гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots', methods=['GET'])
def get_available_bots():
    """Отримати список доступних ботів"""
    bots = [
        'StockfishBot',
        'DynamicBot', 
        'RandomBot',
        'AggressiveBot',
        'FortifyBot',
        'EndgameBot',
        'CriticalBot',
        'TrapBot',
        'KingValueBot',
        'NeuralBot',
        'UtilityBot',
        'PieceMateBot'
    ]
    return jsonify(bots)

@app.route('/api/elo', methods=['GET'])
def get_elo_ratings():
    """Отримати ELO рейтинги"""
    try:
        if not game_data['elo_manager']:
            game_data['elo_manager'] = ELOSyncManager()
        
        ratings = game_data['elo_manager'].get_all_ratings()
        return jsonify(ratings)
    except Exception as e:
        logger.error(f"Помилка завантаження ELO: {e}")
        return jsonify({})

@app.route('/api/heatmaps', methods=['GET'])
def get_heatmaps():
    """Отримати теплові карти"""
    try:
        # Тут можна додати логіку для генерації теплових карт
        return jsonify({'message': 'Heatmaps endpoint - to be implemented'})
    except Exception as e:
        logger.error(f"Помилка завантаження теплових карт: {e}")
        return jsonify({'error': str(e)}), 500

# Статичні файли
@app.route('/static/<path:filename>')
def static_files(filename):
    """Обслуговування статичних файлів"""
    return send_from_directory('static', filename)

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Запуск сервера"""
    logger.info(f"Запуск веб-сервера на {host}:{port}")
    logger.info(f"Відкрийте http://{host}:{port} у браузері")
    
    # Встановлюємо шлях до Stockfish
    if not os.environ.get("STOCKFISH_PATH"):
        stockfish_path = "/workspace/bin/stockfish-bin"
        if os.path.exists(stockfish_path):
            os.environ["STOCKFISH_PATH"] = stockfish_path
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Chess AI Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)