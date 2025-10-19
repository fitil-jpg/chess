#!/usr/bin/env python3
"""
Простий веб-сервер для тестування React Chess додатку
"""

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app)

# Мокові дані для тестування
mock_bots = [
    'RandomBot', 'AggressiveBot', 'FortifyBot', 'EndgameBot', 
    'DynamicBot', 'CriticalBot', 'TrapBot', 'KingValueBot', 
    'NeuralBot', 'UtilityBot', 'PieceMateBot', 'StockfishBot'
]

mock_game_data = {
    'current_game': None,
    'game_history': [],
    'is_playing': False,
    'agents': {},
    'analytics': {
        'whiteModules': [
            {'name': 'RandomBot', 'count': 5},
            {'name': 'AggressiveBot', 'count': 3}
        ],
        'blackModules': [
            {'name': 'DynamicBot', 'count': 4},
            {'name': 'NeuralBot', 'count': 2}
        ],
        'moveTimes': [1.2, 0.8, 1.5, 0.9],
        'positionEvals': [0.1, -0.2, 0.3, -0.1]
    }
}

@app.route('/')
def index():
    return send_from_directory('.', 'chess-react-demo.html')

@app.route('/test_chess_js.html')
def test_chess():
    return send_from_directory('.', 'test_chess_js.html')

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'ok',
        'message': 'Chess React API is running'
    })

@app.route('/api/bots')
def api_bots():
    return jsonify(mock_bots)

@app.route('/api/games')
def api_games():
    return jsonify(mock_game_data['game_history'])

@app.route('/api/game/start', methods=['POST'])
def api_game_start():
    data = request.get_json() or {}
    white_bot = data.get('white_bot', 'RandomBot')
    black_bot = data.get('black_bot', 'RandomBot')
    
    mock_game_data['current_game'] = {
        'white_bot': white_bot,
        'black_bot': black_bot,
        'moves': [],
        'status': 'playing'
    }
    mock_game_data['is_playing'] = True
    
    return jsonify({
        'success': True,
        'message': f'Game started: {white_bot} vs {black_bot}',
        'white_bot': white_bot,
        'black_bot': black_bot
    })

@app.route('/api/game/move', methods=['POST'])
def api_game_move():
    if not mock_game_data['is_playing']:
        return jsonify({
            'success': False,
            'error': 'No game in progress'
        })
    
    # Генеруємо випадковий хід
    moves = ['e2e4', 'd2d4', 'g1f3', 'c2c4', 'f2f4']
    move = random.choice(moves)
    bot = random.choice(mock_bots)
    confidence = round(random.uniform(0.6, 0.95), 2)
    
    return jsonify({
        'success': True,
        'move': move,
        'bot': bot,
        'confidence': confidence
    })

@app.route('/api/game/reset', methods=['POST'])
def api_game_reset():
    mock_game_data['current_game'] = None
    mock_game_data['is_playing'] = False
    return jsonify({'success': True, 'message': 'Game reset'})

@app.route('/api/game/state')
def api_game_state():
    return jsonify({
        'is_playing': mock_game_data['is_playing'],
        'current_game': mock_game_data['current_game']
    })

@app.route('/api/game/analytics')
def api_game_analytics():
    return jsonify(mock_game_data['analytics'])

if __name__ == '__main__':
    print("🚀 Starting simple React Chess server...")
    print("📱 Open http://localhost:5000 in your browser")
    print("🧪 Test chess.js: http://localhost:5000/test_chess_js.html")
    app.run(host='0.0.0.0', port=5000, debug=True)