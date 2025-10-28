#!/usr/bin/env python3
"""
Minimal test server to verify the move fix
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import chess

app = Flask(__name__)
CORS(app)

# Global game state
game_data = {
    'is_playing': False,
    'board': chess.Board()
}

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Start a new game"""
    try:
        data = request.get_json() or {}
        white_bot = data.get('white_bot', 'RandomBot')
        black_bot = data.get('black_bot', 'RandomBot')
        
        # Reset the board
        game_data['board'] = chess.Board()
        game_data['is_playing'] = True
        
        return jsonify({
            'success': True,
            'message': f'Game started: {white_bot} vs {black_bot}',
            'fen': game_data['board'].fen()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/move', methods=['POST'])
def make_move():
    """Make a move"""
    try:
        data = request.get_json() or {}
        
        # Check if game is active
        if not game_data['is_playing']:
            return jsonify({'error': 'Гра не активна'}), 400
        
        # Make a random legal move
        legal_moves = list(game_data['board'].legal_moves)
        if not legal_moves:
            return jsonify({'error': 'No legal moves available'}), 400
        
        # Choose first legal move (simple random)
        move = legal_moves[0]
        san_move = game_data['board'].san(move)
        game_data['board'].push(move)
        
        return jsonify({
            'success': True,
            'move': san_move,
            'fen': game_data['board'].fen(),
            'is_game_over': game_data['board'].is_game_over(),
            'result': game_data['board'].result() if game_data['board'].is_game_over() else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/board')
def get_board():
    """Get current board state"""
    return jsonify({
        'fen': game_data['board'].fen(),
        'is_playing': game_data['is_playing'],
        'turn': 'white' if game_data['board'].turn == chess.WHITE else 'black'
    })

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chess Test</title>
    </head>
    <body>
        <h1>Chess Move Test</h1>
        <button onclick="startGame()">Start Game</button>
        <button onclick="makeMove()">Make Move</button>
        <div id="status"></div>
        <div id="board"></div>
        
        <script>
            async function api(path, opts) {
                const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...opts});
                if(!res.ok) throw new Error(await res.text());
                return res.json();
            }
            
            async function startGame() {
                try {
                    const result = await api('/api/game/start', { 
                        method:'POST', 
                        body: JSON.stringify({white_bot: 'RandomBot', black_bot: 'RandomBot'}) 
                    });
                    document.getElementById('status').textContent = 'Game started: ' + result.message;
                } catch(e) {
                    document.getElementById('status').textContent = 'Error starting game: ' + e.message;
                }
            }
            
            async function makeMove() {
                try {
                    const result = await api('/api/game/move', { method:'POST', body: '{}' });
                    document.getElementById('status').textContent = 'Move made: ' + result.move;
                } catch (error) {
                    // If move fails because no game is active, start a game first
                    if (error.message.includes('Гра не активна') || error.message.includes('400') || error.message.includes('BAD REQUEST')) {
                        console.log('No active game, starting a new game...');
                        await startGame();
                        // Try the move again after starting the game
                        try {
                            const result = await api('/api/game/move', { method:'POST', body: '{}' });
                            document.getElementById('status').textContent = 'Move made after starting game: ' + result.move;
                        } catch (secondError) {
                            document.getElementById('status').textContent = 'Move failed even after starting game: ' + secondError.message;
                        }
                    } else {
                        document.getElementById('status').textContent = 'Move failed: ' + error.message;
                    }
                }
            }
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("Starting minimal test server on port 12345...")
    app.run(host='0.0.0.0', port=12345, debug=True)