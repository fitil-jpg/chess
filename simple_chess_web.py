#!/usr/bin/env python3
"""
Простая веб-версия шахмат с Flask
Использует Python chess модуль и отображает фигуры через шрифт
"""

import os
import sys
from pathlib import Path

# Добавляем текущую директорию к пути
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from flask import Flask, render_template, jsonify, request
import chess
import chess.engine
from chess_ai.bot_agent import make_agent

app = Flask(__name__)

# Глобальная переменная для текущей доски
current_board = chess.Board()

# Символы шахматных фигур (Unicode)
PIECE_SYMBOLS = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',  # Белые
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'   # Черные
}

def get_piece_symbol(piece):
    """Получить символ фигуры"""
    if piece is None:
        return ''
    return PIECE_SYMBOLS.get(piece.symbol(), '')

def board_to_array(board):
    """Преобразовать доску в массив для отображения"""
    board_array = []
    for rank in range(7, -1, -1):  # От 8-го ранга к 1-му
        row = []
        for file in range(8):  # От a до h
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            row.append({
                'symbol': get_piece_symbol(piece),
                'color': 'white' if piece and piece.color == chess.WHITE else 'black' if piece else None,
                'square': chess.square_name(square)
            })
        board_array.append(row)
    return board_array

@app.route('/')
def index():
    """Главная страница с шахматной доской"""
    return render_template('chess_board.html')

@app.route('/api/board')
def get_board():
    """Получить текущее состояние доски"""
    return jsonify({
        'board': board_to_array(current_board),
        'fen': current_board.fen(),
        'turn': 'white' if current_board.turn == chess.WHITE else 'black',
        'is_check': current_board.is_check(),
        'is_checkmate': current_board.is_checkmate(),
        'is_stalemate': current_board.is_stalemate(),
        'is_game_over': current_board.is_game_over(),
        'result': current_board.result() if current_board.is_game_over() else None
    })

@app.route('/api/move', methods=['POST'])
def make_move():
    """Сделать ход"""
    try:
        data = request.get_json()
        move_notation = data.get('move')
        
        if not move_notation:
            return jsonify({'error': 'Не указан ход'}), 400
        
        # Пытаемся выполнить ход
        try:
            move = current_board.parse_san(move_notation)
        except ValueError:
            # Пробуем UCI нотацию
            try:
                move = chess.Move.from_uci(move_notation)
            except ValueError:
                return jsonify({'error': 'Недопустимый ход'}), 400
        
        if not current_board.is_legal(move):
            return jsonify({'error': 'Недопустимый ход'}), 400
        
        # Выполняем ход
        current_board.push(move)
        
        return jsonify({
            'success': True,
            'move': move_notation,
            'board': board_to_array(current_board),
            'fen': current_board.fen(),
            'turn': 'white' if current_board.turn == chess.WHITE else 'black',
            'is_check': current_board.is_check(),
            'is_checkmate': current_board.is_checkmate(),
            'is_stalemate': current_board.is_stalemate(),
            'is_game_over': current_board.is_game_over(),
            'result': current_board.result() if current_board.is_game_over() else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/legal_moves')
def get_legal_moves():
    """Получить список возможных ходов"""
    try:
        moves = []
        for move in current_board.legal_moves:
            moves.append({
                'san': current_board.san(move),
                'uci': move.uci(),
                'from': chess.square_name(move.from_square),
                'to': chess.square_name(move.to_square)
            })
        return jsonify({'moves': moves})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_board():
    """Сбросить доску к начальной позиции"""
    global current_board
    current_board = chess.Board()
    return jsonify({
        'success': True,
        'board': board_to_array(current_board),
        'fen': current_board.fen()
    })

@app.route('/api/bot_move', methods=['POST'])
def make_bot_move():
    """Сделать ход ботом"""
    try:
        data = request.get_json()
        bot_name = data.get('bot', 'RandomBot')
        
        # Создаем бота
        bot = make_agent(bot_name, current_board.turn)
        
        # Получаем ход от бота
        move = bot.choose_move(current_board)
        
        if not move or not current_board.is_legal(move):
            return jsonify({'error': 'Бот не смог сделать ход'}), 400
        
        # Выполняем ход
        san_move = current_board.san(move)
        current_board.push(move)
        
        return jsonify({
            'success': True,
            'move': san_move,
            'bot': bot_name,
            'board': board_to_array(current_board),
            'fen': current_board.fen(),
            'turn': 'white' if current_board.turn == chess.WHITE else 'black',
            'is_check': current_board.is_check(),
            'is_checkmate': current_board.is_checkmate(),
            'is_stalemate': current_board.is_stalemate(),
            'is_game_over': current_board.is_game_over(),
            'result': current_board.result() if current_board.is_game_over() else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_fen', methods=['POST'])
def load_fen():
    """Загрузить позицию из FEN"""
    try:
        data = request.get_json()
        fen = data.get('fen')
        
        if not fen:
            return jsonify({'error': 'Не указан FEN'}), 400
        
        global current_board
        current_board = chess.Board(fen)
        
        return jsonify({
            'success': True,
            'board': board_to_array(current_board),
            'fen': current_board.fen(),
            'turn': 'white' if current_board.turn == chess.WHITE else 'black',
            'is_check': current_board.is_check(),
            'is_checkmate': current_board.is_checkmate(),
            'is_stalemate': current_board.is_stalemate(),
            'is_game_over': current_board.is_game_over(),
            'result': current_board.result() if current_board.is_game_over() else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Создаем директорию для шаблонов если её нет
    os.makedirs('templates', exist_ok=True)
    
    print("Запуск простого шахматного веб-сервера...")
    print("Откройте http://localhost:5000 в браузере")
    
    app.run(host='0.0.0.0', port=5001, debug=True)