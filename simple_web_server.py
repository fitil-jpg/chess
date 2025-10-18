#!/usr/bin/env python3
"""
Спрощений веб-сервер для тестування Chess AI Dashboard
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Додаємо поточну директорію до шляху
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import chess

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація Flask додатку
app = Flask(__name__)
CORS(app)

# Глобальні змінні
game_data = {
    'current_game': None,
    'game_history': [],
    'is_playing': False,
    'board': None
}

class SimpleGameManager:
    """Спрощений менеджер для управління грою"""
    
    def __init__(self):
        self.board = chess.Board()
        self.moves = []
        self.start_time = None
        
    def reset_game(self):
        """Скидання гри"""
        self.board = chess.Board()
        self.moves = []
        self.start_time = None
    
    def make_random_move(self):
        """Зробити випадковий хід"""
        if self.board.is_game_over():
            return None
            
        try:
            moves = list(self.board.legal_moves)
            if not moves:
                return None
                
            move = moves[0]  # Беремо перший доступний хід
            san_move = self.board.san(move)
            self.moves.append(san_move)
            self.board.push(move)
            
            return {
                'move': san_move,
                'fen': self.board.fen(),
                'is_game_over': self.board.is_game_over(),
                'result': self.board.result() if self.board.is_game_over() else None
            }
            
        except Exception as e:
            logger.error(f"Помилка при виконанні ходу: {e}")
            return None
    
    def get_board_state(self):
        """Отримати поточний стан доски"""
        return {
            'fen': self.board.fen(),
            'moves': self.moves,
            'is_game_over': self.board.is_game_over(),
            'result': self.board.result() if self.board.is_game_over() else None,
            'turn': 'white' if self.board.turn == chess.WHITE else 'black'
        }

# Ініціалізація менеджера ігор
game_manager = SimpleGameManager()

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
            'current_game': game_manager.get_board_state()
        }
    })

@app.route('/api/games', methods=['GET'])
def get_games():
    """Отримати список ігор"""
    # Генеруємо тестові дані
    games = []
    results = ['1-0', '0-1', '1/2-1/2']
    modules = ['StockfishBot', 'DynamicBot', 'RandomBot', 'AggressiveBot']
    
    for i in range(10):
        games.append({
            'id': i + 1,
            'result': results[i % len(results)],
            'moves': 20 + (i * 5),
            'duration': 5000 + (i * 1000),
            'modules': {
                'white': modules[i % len(modules)],
                'black': modules[(i + 1) % len(modules)]
            },
            'movesList': [f'e{i+1}', f'd{i+1}', f'Nf{i+1}', f'Nc{i+1}']
        })
    
    return jsonify(games)

@app.route('/api/modules', methods=['GET'])
def get_modules():
    """Отримати статистику модулів"""
    modules = {
        'StockfishBot': 25,
        'DynamicBot': 20,
        'RandomBot': 15,
        'AggressiveBot': 12,
        'FortifyBot': 10,
        'EndgameBot': 8,
        'CriticalBot': 6,
        'TrapBot': 4
    }
    return jsonify(modules)

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Почати нову гру"""
    try:
        game_manager.reset_game()
        game_data['is_playing'] = True
        game_manager.start_time = time.time()
        
        return jsonify({
            'success': True,
            'message': 'Гра розпочата',
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
        
        move_result = game_manager.make_random_move()
        if not move_result:
            return jsonify({'error': 'Не вдалося зробити хід'}), 400
        
        # Якщо гра закінчена, зберігаємо результат
        if move_result['is_game_over']:
            game_data['is_playing'] = False
            game_data['game_history'].append({
                'id': len(game_data['game_history']) + 1,
                'result': move_result['result'],
                'moves': game_manager.moves,
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

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Запуск сервера"""
    logger.info(f"Запуск спрощеного веб-сервера на {host}:{port}")
    logger.info(f"Відкрийте http://{host}:{port} у браузері")
    
    app.run(host=host, port=port, debug=debug, threaded=True)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Chess AI Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)