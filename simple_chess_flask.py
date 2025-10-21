#!/usr/bin/env python3
"""
Простий Flask додаток для відображення шахової дошки
"""

import os
import sys
from pathlib import Path

# Додаємо поточну директорію до шляху
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from flask import Flask, render_template, jsonify, request
import chess
import chess.engine
from utils.metrics_sidebar import build_sidebar_metrics

app = Flask(__name__)

# Глобальна змінна для поточної дошки
current_board = chess.Board()

# Символи шахових фігур (Unicode)
PIECE_SYMBOLS = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',  # Білі
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'   # Чорні
}

def get_piece_symbol(piece):
    """Отримати символ фігури"""
    if piece is None:
        return ''
    return PIECE_SYMBOLS.get(piece.symbol(), '')

def board_to_array(board):
    """Перетворити дошку в масив для відображення"""
    board_array = []
    for rank in range(7, -1, -1):  # Від 8-го рангу до 1-го
        row = []
        for file in range(8):  # Від a до h
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            row.append({
                'symbol': get_piece_symbol(piece),
                'color': 'white' if piece and piece.color == chess.WHITE else 'black' if piece else None,
                'square': chess.square_name(square)
            })
        board_array.append(row)
    return board_array

def _moves_san_list(board: chess.Board):
    """Return list of SAN moves for the current game."""
    temp = chess.Board()
    san_list = []
    for mv in board.move_stack:
        san_list.append(temp.san(mv))
        temp.push(mv)
    return san_list

def _moves_san_string(board: chess.Board) -> str:
    """Return SAN string with move numbers like '1. e4 e5 2. Nf3 ...'."""
    parts = _moves_san_list(board)
    out = []
    for i, san in enumerate(parts, start=1):
        if i % 2 == 1:
            move_no = (i + 1) // 2
            out.append(f"{move_no}. {san}")
        else:
            out.append(san)
    return " ".join(out)

def _game_pgn_string(board: chess.Board) -> str:
    """Return a minimal PGN string for the current game."""
    res = board.result() if board.is_game_over() else "*"
    return (
        f"[Event \"WebViewer\"]\n[Site \"Local\"]\n"
        f"[White \"Web\"]\n[Black \"Web\"]\n"
        f"[Result \"{res}\"]\n\n{_moves_san_string(board)} {res}\n"
    )

@app.route('/')
def index():
    """Головна сторінка з шаховою дошкою"""
    return render_template('simple_chess.html')

@app.route('/api/board')
def get_board():
    """Отримати поточний стан дошки"""
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
    """Зробити хід"""
    try:
        data = request.get_json()
        move_notation = data.get('move')
        
        if not move_notation:
            return jsonify({'error': 'Не вказано хід'}), 400
        
        # Намагаємося виконати хід
        try:
            move = current_board.parse_san(move_notation)
        except ValueError:
            # Пробуємо UCI нотацію
            try:
                move = chess.Move.from_uci(move_notation)
            except ValueError:
                return jsonify({'error': 'Недопустимий хід'}), 400
        
        if not current_board.is_legal(move):
            return jsonify({'error': 'Недопустимий хід'}), 400
        
        # Виконуємо хід
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
    """Отримати список можливих ходів"""
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
    """Скинути дошку до початкової позиції"""
    global current_board
    current_board = chess.Board()
    return jsonify({
        'success': True,
        'board': board_to_array(current_board),
        'fen': current_board.fen()
    })

@app.route('/api/bot_move', methods=['POST'])
def make_bot_move():
    """Зробити хід ботом"""
    try:
        data = request.get_json()
        bot_name = data.get('bot', 'RandomBot')
        
        # Простий випадковий бот
        moves = list(current_board.legal_moves)
        if not moves:
            return jsonify({'error': 'Немає можливих ходів'}), 400
        
        move = moves[0]  # Беремо перший доступний хід
        
        # Виконуємо хід
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
    """Завантажити позицію з FEN"""
    try:
        data = request.get_json()
        fen = data.get('fen')
        
        if not fen:
            return jsonify({'error': 'Не вказано FEN'}), 400
        
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
@app.route('/api/stats')
def get_stats():
    """Повернути розширені статистики та текстові метрики як у PySide в’ювері."""
    try:
        # High-level text metrics (ThreatMap, Attacks, Leaders, King coeff)
        metrics_lines = build_sidebar_metrics(current_board)

        # Phase heuristic similar to PySide viewer
        non_king_count = sum(1 for pc in current_board.piece_map().values() if pc.piece_type != chess.KING)
        if non_king_count <= 12:
            phase = 'endgame'
        elif non_king_count <= 20:
            phase = 'midgame'
        else:
            phase = 'opening'

        # Legal moves count and list preview (SAN + UCI for current side)
        legal = []
        for mv in current_board.legal_moves:
            legal.append({
                'san': current_board.san(mv),
                'uci': mv.uci(),
                'from': chess.square_name(mv.from_square),
                'to': chess.square_name(mv.to_square),
            })

        # Moves and PGN
        san_list = _moves_san_list(current_board)
        san_text = _moves_san_string(current_board)
        pgn_text = _game_pgn_string(current_board)

        return jsonify({
            'fen': current_board.fen(),
            'turn': 'white' if current_board.turn == chess.WHITE else 'black',
            'is_check': current_board.is_check(),
            'is_checkmate': current_board.is_checkmate(),
            'is_stalemate': current_board.is_stalemate(),
            'is_game_over': current_board.is_game_over(),
            'result': current_board.result() if current_board.is_game_over() else None,
            'phase': phase,
            'metrics': metrics_lines,
            'legal_moves_count': len(legal),
            'legal_moves': legal,
            'moves_san_list': san_list,
            'moves_san': san_text,
            'pgn': pgn_text,
            'move_count': len(current_board.move_stack),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Створюємо директорію для шаблонів якщо її немає
    os.makedirs('templates', exist_ok=True)
    
    print("Запуск простого шахового веб-сервера...")
    print("Відкрийте http://localhost:5000 у браузері")
    
    app.run(host='0.0.0.0', port=5001, debug=True)