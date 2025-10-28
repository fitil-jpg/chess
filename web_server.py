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
import signal
import socket
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
from werkzeug.serving import WSGIRequestHandler

# Імпортуємо існуючі компоненти
from chess_ai.bot_agent import make_agent
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage
from utils.module_colors import MODULE_COLORS, REASON_PRIORITY
# Опційно імпортуємо ELOSyncManager (може вимагати aiohttp)
try:
    from chess_ai.elo_sync_manager import ELOSyncManager  # type: ignore
except Exception as e:  # ImportError, RuntimeError, etc.
    ELOSyncManager = None  # type: ignore
    print(f"[web_server] ELOSyncManager недоступний: {e}", file=sys.stderr)
from utils.integration import generate_heatmaps as integration_generate_heatmaps
from utils.metrics_sidebar import build_sidebar_metrics

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chess_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Налаштування для обробки помилок сокетів
socket.setdefaulttimeout(30)  # 30 секунд таймаут для сокетів

# Ініціалізація Flask додатку
app = Flask(__name__)
CORS(app)

# Налаштування для обробки помилок
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_SORT_KEYS'] = False

# Глобальна змінна для контролю сервера
server_shutdown = threading.Event()

# Статистика з'єднань
connection_stats = {
    'total_requests': 0,
    'failed_requests': 0,
    'active_connections': 0,
    'last_reset': time.time()
}

def log_connection_stats():
    """Логування статистики з'єднань"""
    if connection_stats['total_requests'] > 0:
        success_rate = ((connection_stats['total_requests'] - connection_stats['failed_requests']) / 
                       connection_stats['total_requests']) * 100
        logger.info(f"Статистика з'єднань: {connection_stats['total_requests']} запитів, "
                   f"успішність {success_rate:.1f}%, активних з'єднань: {connection_stats['active_connections']}")

# Запускаємо логування статистики кожні 60 секунд
def stats_logger():
    """Фонове логування статистики"""
    while not server_shutdown.is_set():
        time.sleep(60)
        if not server_shutdown.is_set():
            log_connection_stats()

stats_thread = threading.Thread(target=stats_logger, daemon=True)

# Глобальні змінні
game_data = {
    'current_game': None,
    'game_history': [],
    'is_playing': False,
    'agents': {},
    'elo_manager': None
}

# Декоратор для обробки помилок API
def handle_api_errors(f):
    """Декоратор для обробки помилок API з логуванням"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            if duration > 5:  # Логуємо повільні запити
                logger.warning(f"Повільний запит {f.__name__}: {duration:.2f}s")
            return result
        except (ConnectionResetError, OSError, socket.error) as e:
            connection_stats['failed_requests'] += 1
            logger.warning(f"Помилка з'єднання в {f.__name__}: {e}")
            return jsonify({'error': 'Помилка з\'єднання', 'details': str(e)}), 503
        except Exception as e:
            connection_stats['failed_requests'] += 1
            logger.error(f"Неочікувана помилка в {f.__name__}: {e}", exc_info=True)
            return jsonify({'error': 'Внутрішня помилка сервера', 'details': str(e)}), 500
        finally:
            # Оновлюємо статистику активних з'єднань
            connection_stats['active_connections'] = max(0, connection_stats['active_connections'] - 1)
    wrapper.__name__ = f.__name__
    return wrapper

# Middleware для обробки помилок сокетів
@app.before_request
def before_request():
    """Обробка запитів перед виконанням"""
    try:
        # Перевіряємо чи сервер не закривається
        if server_shutdown.is_set():
            return jsonify({'error': 'Сервер закривається'}), 503
        
        # Оновлюємо статистику
        connection_stats['total_requests'] += 1
        connection_stats['active_connections'] += 1
        
        # Логуємо запит (тільки для API endpoints)
        if request.path.startswith('/api/'):
            logger.debug(f"API запит: {request.method} {request.path} від {request.remote_addr}")
            
    except Exception as e:
        logger.error(f"Помилка в before_request: {e}")

@app.after_request
def after_request(response):
    """Обробка відповідей після виконання"""
    try:
        # Оновлюємо статистику
        connection_stats['active_connections'] = max(0, connection_stats['active_connections'] - 1)
        
        if response.status_code >= 400:
            connection_stats['failed_requests'] += 1
        
        # Додаємо заголовки для стабільності
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=30, max=100'
        response.headers['X-Request-ID'] = str(int(time.time() * 1000))  # Унікальний ID запиту
        
        return response
    except Exception as e:
        logger.error(f"Помилка в after_request: {e}")
        return response

# Обробник помилок для різних типів винятків
@app.errorhandler(ConnectionResetError)
def handle_connection_reset(e):
    """Обробка помилок скидання з'єднання"""
    logger.warning(f"З'єднання скинуто: {e}")
    return jsonify({'error': 'З\'єднання втрачено'}), 503

@app.errorhandler(OSError)
def handle_os_error(e):
    """Обробка помилок операційної системи"""
    if e.errno == 57:  # Socket is not connected
        logger.warning(f"Сокет не підключений: {e}")
        return jsonify({'error': 'З\'єднання втрачено'}), 503
    else:
        logger.error(f"Помилка ОС: {e}")
        return jsonify({'error': 'Помилка з\'єднання'}), 500

@app.errorhandler(socket.error)
def handle_socket_error(e):
    """Обробка помилок сокетів"""
    logger.warning(f"Помилка сокета: {e}")
    return jsonify({'error': 'Помилка мережі'}), 503

@app.errorhandler(500)
def handle_internal_error(e):
    """Обробка внутрішніх помилок сервера"""
    logger.error(f"Внутрішня помилка сервера: {e}")
    return jsonify({'error': 'Внутрішня помилка сервера'}), 500

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
        """Зробити хід з покращеною обробкою помилок"""
        try:
            if self.current_board.is_game_over():
                return None
                
            mover_color = self.current_board.turn
            agent = self.white_agent if mover_color == chess.WHITE else self.black_agent
            
            if not agent:
                logger.warning(f"Агент не знайдено для кольору {mover_color}")
                return None
                
            # Додаткова перевірка стану доски
            if not self.current_board.is_valid():
                logger.error("Недійсний стан доски")
                return None
                
            move = agent.choose_move(self.current_board)
            if not move:
                logger.warning("Агент не зміг зробити хід")
                return None
                
            if not self.current_board.is_legal(move):
                logger.warning(f"Недійсний хід: {move}")
                return None
                
            # Отримуємо інформацію про модуль
            try:
                reason = agent.get_last_reason() if hasattr(agent, "get_last_reason") else "UNKNOWN"
                module_key = self._extract_reason_key(reason)
            except Exception as e:
                logger.warning(f"Помилка отримання причини ходу: {e}")
                module_key = "UNKNOWN"
            
            # Записуємо хід
            try:
                san_move = self.current_board.san(move)
                self.game_moves.append(san_move)
            except Exception as e:
                logger.error(f"Помилка конвертації ходу в SAN: {e}")
                return None
            
            if mover_color == chess.WHITE:
                self.game_modules['white'].append(module_key)
            else:
                self.game_modules['black'].append(module_key)
            
            # Виконуємо хід
            try:
                self.current_board.push(move)
            except Exception as e:
                logger.error(f"Помилка виконання ходу: {e}")
                return None
            
            return {
                'move': san_move,
                'module': module_key,
                'color': 'white' if mover_color == chess.WHITE else 'black',
                'fen': self.current_board.fen(),
                'is_game_over': self.current_board.is_game_over(),
                'result': self.current_board.result() if self.current_board.is_game_over() else None
            }
            
        except (ConnectionResetError, OSError, socket.error) as e:
            logger.warning(f"Помилка з'єднання при виконанні ходу: {e}")
            return None
        except Exception as e:
            logger.error(f"Неочікувана помилка при виконанні ходу: {e}", exc_info=True)
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
@handle_api_errors
def index():
    """Головна сторінка: віддаємо оновлений UI або запасні сторінки."""
    candidates = [
        'web_interface.html',   # Новий повноцінний інтерфейс
        'index.html',           # Легкий демо‑інтерфейс
        'chess_board.html',     # Альтернативна дошка
        'chess_board_standalone.html',
        'chess-demo-simple.html',
        'minimal_chess_test.html',
    ]
    for name in candidates:
        if Path(name).exists():
            return send_from_directory('.', name)
    logger.warning("Жодну HTML‑сторінку інтерфейсу не знайдено")
    return jsonify({'error': 'Веб-інтерфейс не знайдено'}), 404

# Lightweight board viewer (simple Flask UI)
@app.route('/board')
@handle_api_errors
def simple_board_page():
    try:
        return render_template('simple_chess.html')
    except Exception as e:
        logger.error(f"Помилка рендерингу simple_chess.html: {e}")
        return jsonify({'error': 'Не вдалося завантажити дошку'}), 500

@app.route('/heatmaps')
@handle_api_errors
def heatmap_interface():
    """Інтерфейс управління тепловими картами"""
    try:
        return send_from_directory('.', 'heatmap_web_interface.html')
    except FileNotFoundError:
        logger.warning("Файл heatmap_web_interface.html не знайдено")
        return jsonify({'error': 'Інтерфейс теплових карт не знайдено'}), 404

@app.route('/health')
@handle_api_errors
def health_check():
    """Перевірка здоров'я сервера"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - (getattr(health_check, 'start_time', time.time())),
        'server_info': {
            'python_version': sys.version,
            'flask_version': getattr(Flask, '__version__', 'unknown')
        }
    })

# Ініціалізуємо час запуску для health check
health_check.start_time = time.time()

@app.route('/favicon.ico')
def favicon():
    """Повертає favicon для браузера"""
    # Підтримуємо як svg у static, так і запасний шлях
    static_path = Path('static')
    svg_path = static_path / 'favicon.svg'
    if svg_path.exists():
        return send_from_directory('static', 'favicon.svg')
    # Якщо немає svg, спробуємо ico, інакше 404 відправить Flask
    ico_path = static_path / 'favicon.ico'
    if ico_path.exists():
        return send_from_directory('static', 'favicon.ico')
    return ('', 204)

@app.route('/api/status')
@handle_api_errors
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
@handle_api_errors
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
@handle_api_errors
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
@handle_api_errors
def start_game():
    """Почати нову гру"""
    try:
        data = request.get_json() or {}
        white_bot = data.get('white_bot', 'StockfishBot')
        black_bot = data.get('black_bot', 'DynamicBot')
        infinite_mode = data.get('infinite_mode', False)
        
        # Ініціалізуємо ботів
        if not game_manager.initialize_agents(white_bot, black_bot):
            return jsonify({'error': 'Не вдалося ініціалізувати ботів'}), 400
        
        # Скидаємо гру
        game_manager.reset_game()
        game_data['is_playing'] = True
        game_manager.start_time = time.time()
        
        # Зберігаємо режим гри
        game_data['infinite_mode'] = infinite_mode
        
        return jsonify({
            'success': True,
            'message': f'Гра розпочата: {white_bot} vs {black_bot}',
            'board_state': game_manager.get_board_state(),
            'infinite_mode': infinite_mode
        })
        
    except Exception as e:
        logger.error(f"Помилка початку гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/move', methods=['POST'])
@handle_api_errors
def make_move():
    """Зробити хід"""
    try:
        data = request.get_json() or {}
        
        # Якщо передано FEN, використовуємо його замість поточної гри
        if 'fen' in data:
            temp_board = chess.Board(data['fen'])
            if not temp_board.is_game_over():
                # Виконуємо хід ботом
                mover_color = temp_board.turn
                agent = game_manager.white_agent if mover_color == chess.WHITE else game_manager.black_agent
                
                if agent:
                    move = agent.choose_move(temp_board)
                    if move and temp_board.is_legal(move):
                        san_move = temp_board.san(move)
                        temp_board.push(move)
                        
                        return jsonify({
                            'success': True,
                            'move': san_move,
                            'fen': temp_board.fen(),
                            'is_game_over': temp_board.is_game_over(),
                            'result': temp_board.result() if temp_board.is_game_over() else None,
                            'bot': 'WhiteBot' if mover_color == chess.WHITE else 'BlackBot',
                            'confidence': 0.85  # Приклад значення
                        })
            
            return jsonify({'error': 'Не вдалося зробити хід'}), 400
        
        # Стандартна логіка для активної гри
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
@handle_api_errors
def stop_game():
    """Зупинити гру"""
    try:
        game_data['is_playing'] = False
        return jsonify({'success': True, 'message': 'Гра зупинена'})
    except Exception as e:
        logger.error(f"Помилка зупинки гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/end', methods=['POST'])
@handle_api_errors
def end_game():
    """Обробка завершення гри з оновленням ELO та збереженням hitmap"""
    try:
        data = request.get_json() or {}
        result = data.get('result', '*')
        moves = data.get('moves', [])
        modules = data.get('modules', {'white': [], 'black': []})
        game_number = data.get('game_number', 1)
        
        # Оновлюємо ELO рейтинги
        update_elo_ratings(result, modules)
        
        # Зберігаємо дані для hitmap (тільки JSON, без зображень)
        save_hitmap_data(result, moves, modules, game_number)
        
        # Оновлюємо статистику
        game_data['game_history'].append({
            'id': len(game_data['game_history']) + 1,
            'result': result,
            'moves': moves,
            'modules': modules,
            'duration': int((time.time() - game_manager.start_time) * 1000) if game_manager.start_time else 0,
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'game_number': game_number
        })
        
        return jsonify({
            'success': True,
            'message': f'Гра #{game_number} завершена: {result}',
            'elo_updated': True,
            'hitmap_saved': True
        })
        
    except Exception as e:
        logger.error(f"Помилка обробки завершення гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/reset', methods=['POST'])
@handle_api_errors
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
@handle_api_errors
def get_game_state():
    """Отримати поточний стан гри"""
    try:
        return jsonify(game_manager.get_board_state())
    except Exception as e:
        logger.error(f"Помилка отримання стану гри: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bots', methods=['GET'])
@handle_api_errors
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

# ===== Compatibility helpers for simple board endpoints =====
# Unicode symbols for pieces (for simple board UI)
PIECE_SYMBOLS = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

def _get_piece_symbol(piece):
    if piece is None:
        return ''
    return PIECE_SYMBOLS.get(piece.symbol(), '')

def _board_to_array(board: chess.Board):
    board_array = []
    for rank in range(7, -1, -1):
        row = []
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            row.append({
                'symbol': _get_piece_symbol(piece),
                'color': 'white' if piece and piece.color == chess.WHITE else 'black' if piece else None,
                'square': chess.square_name(square)
            })
        board_array.append(row)
    return board_array

@app.route('/api/board')
@handle_api_errors
def api_board():
    bd = game_manager.current_board
    return jsonify({
        'board': _board_to_array(bd),
        'fen': bd.fen(),
        'turn': 'white' if bd.turn == chess.WHITE else 'black',
        'is_check': bd.is_check(),
        'is_checkmate': bd.is_checkmate(),
        'is_stalemate': bd.is_stalemate(),
        'is_game_over': bd.is_game_over(),
        'result': bd.result() if bd.is_game_over() else None
    })

@app.route('/api/legal_moves')
@handle_api_errors
def api_legal_moves():
    bd = game_manager.current_board
    moves = []
    for mv in bd.legal_moves:
        moves.append({
            'san': bd.san(mv),
            'uci': mv.uci(),
            'from': chess.square_name(mv.from_square),
            'to': chess.square_name(mv.to_square),
        })
    return jsonify({'moves': moves})

@app.route('/api/move', methods=['POST'])
@handle_api_errors
def api_make_move():
    data = request.get_json() or {}
    move_notation = data.get('move')
    if not move_notation:
        return jsonify({'error': 'Не вказано хід'}), 400
    bd = game_manager.current_board
    # Try SAN first, then UCI
    try:
        move = bd.parse_san(move_notation)
    except Exception:
        try:
            move = chess.Move.from_uci(move_notation)
        except Exception:
            return jsonify({'error': 'Недопустимий хід'}), 400
    if not bd.is_legal(move):
        return jsonify({'error': 'Недопустимий хід'}), 400
    # Push and record SAN
    san_move = bd.san(move)
    bd.push(move)
    game_manager.game_moves.append(san_move)
    return jsonify({
        'success': True,
        'move': san_move,
        'board': _board_to_array(bd),
        'fen': bd.fen(),
        'turn': 'white' if bd.turn == chess.WHITE else 'black',
        'is_check': bd.is_check(),
        'is_checkmate': bd.is_checkmate(),
        'is_stalemate': bd.is_stalemate(),
        'is_game_over': bd.is_game_over(),
        'result': bd.result() if bd.is_game_over() else None
    })

@app.route('/api/reset', methods=['POST'])
@handle_api_errors
def api_reset():
    game_manager.reset_game()
    return jsonify({'success': True, 'board': _board_to_array(game_manager.current_board), 'fen': game_manager.current_board.fen()})

@app.route('/api/bot_move', methods=['POST'])
@handle_api_errors
def api_bot_move():
    data = request.get_json() or {}
    bot_name = (data.get('bot') or '').strip() or 'RandomBot'
    bd = game_manager.current_board
    mover_color = bd.turn
    # Ensure agent exists for current mover
    try:
        if mover_color == chess.WHITE and game_manager.white_agent is None:
            game_manager.white_agent = make_agent(bot_name, chess.WHITE)
        if mover_color == chess.BLACK and game_manager.black_agent is None:
            game_manager.black_agent = make_agent(bot_name, chess.BLACK)
    except Exception as e:
        logger.warning(f"Не вдалося ініціалізувати агента {bot_name}: {e}. Використовуємо випадковий хід.")
    agent = game_manager.white_agent if mover_color == chess.WHITE else game_manager.black_agent
    if agent is None:
        # Fallback: random legal move
        legal = list(bd.legal_moves)
        if not legal:
            return jsonify({'error': 'Немає можливих ходів'}), 400
        mv = legal[0]
    else:
        mv = agent.choose_move(bd)
        if mv is None or not bd.is_legal(mv):
            legal = list(bd.legal_moves)
            if not legal:
                return jsonify({'error': 'Немає можливих ходів'}), 400
            mv = legal[0]
    san_move = bd.san(mv)
    bd.push(mv)
    game_manager.game_moves.append(san_move)
    return jsonify({
        'success': True,
        'move': san_move,
        'bot': bot_name,
        'board': _board_to_array(bd),
        'fen': bd.fen(),
        'turn': 'white' if bd.turn == chess.WHITE else 'black',
        'is_check': bd.is_check(),
        'is_checkmate': bd.is_checkmate(),
        'is_stalemate': bd.is_stalemate(),
        'is_game_over': bd.is_game_over(),
        'result': bd.result() if bd.is_game_over() else None
    })

@app.route('/api/stats')
@handle_api_errors
def api_stats():
    """Return rich metrics similar to PySide viewer sidebar."""
    bd = game_manager.current_board
    # Phase heuristic similar to elsewhere
    non_kings = sum(1 for pc in bd.piece_map().values() if pc.piece_type != chess.KING)
    if non_kings <= 12:
        phase = 'endgame'
    elif non_kings <= 20:
        phase = 'midgame'
    else:
        phase = 'opening'
    legal = []
    for mv in bd.legal_moves:
        legal.append({
            'san': bd.san(mv),
            'uci': mv.uci(),
            'from': chess.square_name(mv.from_square),
            'to': chess.square_name(mv.to_square),
        })
    # Build sidebar metrics
    metrics_lines = build_sidebar_metrics(bd)
    # SAN/PGN
    # Reconstruct SAN list for current game
    temp = chess.Board()
    san_list = []
    for mv in bd.move_stack:
        san_list.append(temp.san(mv))
        temp.push(mv)
    def _moves_san_string(parts):
        out = []
        for i, san in enumerate(parts, start=1):
            if i % 2 == 1:
                move_no = (i + 1) // 2
                out.append(f"{move_no}. {san}")
            else:
                out.append(san)
        return " ".join(out)
    san_text = _moves_san_string(san_list)
    res = bd.result() if bd.is_game_over() else "*"
    pgn_text = (
        f"[Event \"WebViewer\"]\n[Site \"Local\"]\n"
        f"[White \"Web\"]\n[Black \"Web\"]\n"
        f"[Result \"{res}\"]\n\n{san_text} {res}\n"
    )
    return jsonify({
        'fen': bd.fen(),
        'turn': 'white' if bd.turn == chess.WHITE else 'black',
        'is_check': bd.is_check(),
        'is_checkmate': bd.is_checkmate(),
        'is_stalemate': bd.is_stalemate(),
        'is_game_over': bd.is_game_over(),
        'result': bd.result() if bd.is_game_over() else None,
        'phase': phase,
        'metrics': metrics_lines,
        'legal_moves_count': len(legal),
        'legal_moves': legal,
        'moves_san_list': san_list,
        'moves_san': san_text,
        'pgn': pgn_text,
        'move_count': len(bd.move_stack),
    })

@app.route('/api/elo', methods=['GET'])
@handle_api_errors
def get_elo_ratings():
    """Отримати ELO рейтинги"""
    try:
        if ELOSyncManager is None:
            logger.info("ELOSyncManager відключено (aiohttp не встановлено)")
            return jsonify({})
        if not game_data['elo_manager']:
            game_data['elo_manager'] = ELOSyncManager()
        
        ratings = game_data['elo_manager'].get_all_ratings()
        return jsonify(ratings)
    except Exception as e:
        logger.error(f"Помилка завантаження ELO: {e}")
        return jsonify({})

HEATMAPS_BASE_DIR = Path(os.environ.get("HEATMAPS_DIR", "analysis/heatmaps"))

def _compute_phase_from_fen(fen: str) -> str:
    """Груба оцінка фази гри за кількістю некоролівських фігур у позиції."""
    bd = chess.Board(fen)
    non_kings = sum(1 for p in bd.piece_map().values() if p.piece_type != chess.KING)
    if non_kings <= 12:
        return "endgame"
    if non_kings <= 20:
        return "midgame"
    return "opening"

def _list_sets() -> List[Dict[str, Any]]:
    HEATMAPS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    sets: List[Dict[str, Any]] = []
    for sub in sorted(HEATMAPS_BASE_DIR.iterdir()):
        if not sub.is_dir():
            continue
        pieces = sorted([p.stem.replace("heatmap_", "") for p in sub.glob("heatmap_*.json")])
        if not pieces:
            continue
        sets.append({"name": sub.name, "pieces": pieces, "path": str(sub)})
    # Also expose base JSONs in repo root (if present) as a virtual set
    base_jsons = list(Path('.').glob('heatmap_*.json'))
    if base_jsons:
        pieces = sorted([p.stem.replace("heatmap_", "") for p in base_jsons])
        sets.insert(0, {"name": "base", "pieces": pieces, "path": "."})
    return sets

def _read_heatmap(pattern_set: str, piece: str) -> Optional[List[List[int]]]:
    if pattern_set == "base":
        json_path = Path(f"heatmap_{piece}.json")
    else:
        json_path = HEATMAPS_BASE_DIR / pattern_set / f"heatmap_{piece}.json"
    if not json_path.exists():
        return None
    with json_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def _aggregate_piece_grids_for_piece(heatmaps: Dict[str, List[List[int]]], piece: str) -> Optional[List[List[int]]]:
    """Aggregate upper/lower case piece grids into a single 8x8 grid for overlay.
    piece: one of pawn, knight, bishop, rook, queen, king
    """
    mapping = {
        'pawn': ['P', 'p'], 'knight': ['N', 'n'], 'bishop': ['B', 'b'],
        'rook': ['R', 'r'], 'queen': ['Q', 'q'], 'king': ['K', 'k']
    }
    symbols = mapping.get(piece.lower())
    if not symbols:
        return None
    agg = [[0 for _ in range(8)] for _ in range(8)]
    for sym in symbols:
        grid = heatmaps.get(sym)
        if not grid:
            continue
        for r in range(8):
            for c in range(8):
                agg[r][c] += int(grid[r][c])
    return agg

def _normalize_grid(grid: List[List[int]]) -> List[List[float]]:
    max_val = max((v for row in grid for v in row), default=0)
    if max_val <= 0:
        return [[0.0 for _ in range(8)] for _ in range(8)]
    return [[(v / max_val) for v in row] for row in grid]

def _heatmap_from_current_game(piece: str) -> Dict[str, Any]:
    """Build per-piece heatmap from current game's SAN move history for overlay."""
    moves_san = list(game_manager.game_moves)
    bd = chess.Board()
    grids = {sym: [[0 for _ in range(8)] for _ in range(8)] for sym in ['P','N','B','R','Q','K','p','n','b','r','q','k']}
    for san in moves_san:
        try:
            mv = bd.parse_san(san)
            piece_at = bd.piece_at(mv.from_square)
            if piece_at is not None:
                sym = piece_at.symbol()
                to_file = chess.square_file(mv.to_square)
                to_rank = chess.square_rank(mv.to_square)
                grids[sym][7 - to_rank][to_file] += 1
            bd.push(mv)
        except Exception:
            # Skip unparsable moves
            continue
    agg = _aggregate_piece_grids_for_piece(grids, piece)
    total = sum(sum(row) for row in agg) if agg else 0
    return {'heatmap': agg, 'total': total}

@app.route('/api/heatmaps/sets', methods=['GET'])
@handle_api_errors
def api_heatmap_sets():
    return jsonify({'sets': _list_sets()})

@app.route('/api/heatmap/overlay', methods=['GET'])
@handle_api_errors
def api_heatmap_overlay():
    """Return a single 8x8 grid for a given piece suitable for board overlay.
    Query params:
      - source: 'current' (default) or 'set'
      - piece: pawn|knight|bishop|rook|queen|king (required)
      - pattern_set: when source='set', name of set (e.g. 'base' or folder name)
      - normalize: 0/1 to scale to [0,1]
    """
    piece = (request.args.get('piece') or '').lower()
    source = (request.args.get('source') or 'current').lower()
    normalize = request.args.get('normalize', '1') in ('1', 'true', 'yes')
    if piece not in ('pawn','knight','bishop','rook','queen','king'):
        return jsonify({'error': 'piece required: pawn|knight|bishop|rook|queen|king'}), 400
    grid: Optional[List[List[int]]] = None
    total = 0
    if source == 'set':
        pattern_set = (request.args.get('pattern_set') or 'base')
        # Read JSONs for both cases and aggregate
        upper_lower = {
            'pawn': ['P','p'], 'knight': ['N','n'], 'bishop': ['B','b'],
            'rook': ['R','r'], 'queen': ['Q','q'], 'king': ['K','k']
        }[piece]
        hm = {}
        for sym in upper_lower:
            # filenames use lowercase piece names in some repos; here _read_heatmap expects names like 'knight', etc.
            name_map = {'P':'pawn','N':'knight','B':'bishop','R':'rook','Q':'queen','K':'king',
                        'p':'pawn','n':'knight','b':'bishop','r':'rook','q':'queen','k':'king'}
            arr = _read_heatmap(pattern_set, name_map[sym])
            if arr:
                hm[sym] = arr
        grid = _aggregate_piece_grids_for_piece(hm, piece)
        total = sum(sum(row) for row in grid) if grid else 0
    else:
        res = _heatmap_from_current_game(piece)
        grid = res.get('heatmap')
        total = int(res.get('total') or 0)
    if grid is None:
        return jsonify({'error': 'heatmap not available'}), 404
    out = _normalize_grid(grid) if normalize else grid
    return jsonify({'piece': piece, 'source': source, 'normalize': normalize, 'total': total, 'heatmap': out})

@app.route('/api/heatmaps', methods=['GET'])
@handle_api_errors
def get_heatmaps():
    """Отримати список доступних теплових карт"""
    try:
        import os
        from pathlib import Path
        
        heatmap_dir = Path("heatmap_visualizations")
        if not heatmap_dir.exists():
            return jsonify({'heatmaps': []})
        
        heatmaps = []
        for file_path in heatmap_dir.glob("*.png"):
            heatmaps.append({
                'name': file_path.stem,
                'filename': file_path.name,
                'path': str(file_path),
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime
            })
        
        return jsonify({'heatmaps': sorted(heatmaps, key=lambda x: x['modified'], reverse=True)})
    except Exception as e:
        logger.error(f"Помилка завантаження теплових карт: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmaps/generate', methods=['POST'])
@handle_api_errors
def generate_heatmap():
    """Генерувати теплову карту для конкретного бота та етапу гри"""
    try:
        data = request.get_json() or {}
        bot_name = data.get('bot_name', 'DynamicBot')
        game_phase = data.get('game_phase', 'all')  # 'opening', 'middlegame', 'endgame', 'all'
        piece_type = data.get('piece_type', 'all')  # 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king', 'all'
        games_limit = data.get('games_limit', 100)
        
        # Імпортуємо heatmap generator
        from utils.heatmap_generator import HeatmapGenerator
        
        generator = HeatmapGenerator()
        result = generator.generate_heatmap(
            bot_name=bot_name,
            game_phase=game_phase,
            piece_type=piece_type,
            games_limit=games_limit
        )
        
        return jsonify({
            'success': True,
            'message': f'Heatmap generated for {bot_name} - {game_phase} - {piece_type}',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Помилка генерації теплової карти: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/heatmaps/<path:filename>')
@handle_api_errors
def serve_heatmap(filename):
    """Обслуговування файлів теплових карт"""
    try:
        return send_from_directory('heatmap_visualizations', filename)
    except FileNotFoundError:
        return jsonify({'error': 'Heatmap file not found'}), 404

@app.route('/api/heatmaps/analyze', methods=['POST'])
@handle_api_errors
def analyze_heatmap():
    """Аналіз теплової карти для конкретного бота"""
    try:
        data = request.get_json() or {}
        bot_name = data.get('bot_name', 'DynamicBot')
        piece_type = data.get('piece_type', 'all')
        
        from utils.heatmap_analyzer import HeatmapAnalyzer
        
        analyzer = HeatmapAnalyzer()
        analysis = analyzer.analyze_bot_patterns(bot_name, piece_type)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Помилка аналізу теплової карти: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/analytics', methods=['GET'])
@handle_api_errors
def get_game_analytics():
    """Отримати аналітику поточної гри"""
    try:
        if not game_manager.current_board:
            return jsonify({'error': 'Немає активної гри'}), 400
        
        # Аналіз модулів
        white_modules = {}
        black_modules = {}
        
        for module in game_manager.game_modules['white']:
            white_modules[module] = white_modules.get(module, 0) + 1
        
        for module in game_manager.game_modules['black']:
            black_modules[module] = black_modules.get(module, 0) + 1
        
        # Конвертуємо в список для фронтенду
        white_modules_list = [{'name': k, 'count': v} for k, v in white_modules.items()]
        black_modules_list = [{'name': k, 'count': v} for k, v in black_modules.items()]
        
        return jsonify({
            'whiteModules': white_modules_list,
            'blackModules': black_modules_list,
            'totalMoves': len(game_manager.game_moves),
            'gameDuration': int((time.time() - game_manager.start_time) * 1000) if game_manager.start_time else 0,
            'currentPosition': game_manager.current_board.fen(),
            'isGameOver': game_manager.current_board.is_game_over(),
            'result': game_manager.current_board.result() if game_manager.current_board.is_game_over() else None
        })
    except Exception as e:
        logger.error(f"Помилка отримання аналітики: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/move/analyze', methods=['POST'])
@handle_api_errors
def analyze_move():
    """Аналіз конкретного ходу"""
    try:
        data = request.get_json() or {}
        move_san = data.get('move')
        fen = data.get('fen')
        
        if not move_san or not fen:
            return jsonify({'error': 'Необхідні параметри: move, fen'}), 400
        
        # Створюємо тимчасову дошку для аналізу
        temp_board = chess.Board(fen)
        
        # Перевіряємо чи хід легальний
        try:
            move = temp_board.parse_san(move_san)
        except:
            return jsonify({'error': 'Недійсний хід'}), 400
        
        # Аналізуємо хід
        analysis = {
            'move': move_san,
            'isLegal': temp_board.is_legal(move),
            'isCheck': False,
            'isCheckmate': False,
            'isStalemate': False,
            'isCapture': temp_board.is_capture(move),
            'isCastling': temp_board.is_castling(move),
            'isEnPassant': temp_board.is_en_passant(move),
            'isPromotion': temp_board.is_promotion(move)
        }
        
        # Виконуємо хід для аналізу
        temp_board.push(move)
        analysis.update({
            'isCheck': temp_board.is_check(),
            'isCheckmate': temp_board.is_checkmate(),
            'isStalemate': temp_board.is_stalemate(),
            'isGameOver': temp_board.is_game_over(),
            'result': temp_board.result() if temp_board.is_game_over() else None
        })
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Помилка аналізу ходу: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/game/position/evaluate', methods=['POST'])
@handle_api_errors
def evaluate_position():
    """Оцінка позиції"""
    try:
        data = request.get_json() or {}
        fen = data.get('fen')
        
        if not fen:
            return jsonify({'error': 'Необхідний параметр: fen'}), 400
        
        board = chess.Board(fen)
        
        # Базова оцінка позиції
        evaluation = {
            'fen': fen,
            'turn': 'white' if board.turn == chess.WHITE else 'black',
            'isCheck': board.is_check(),
            'isCheckmate': board.is_checkmate(),
            'isStalemate': board.is_stalemate(),
            'isGameOver': board.is_game_over(),
            'result': board.result() if board.is_game_over() else None,
            'legalMoves': len(list(board.legal_moves)),
            'materialBalance': calculate_material_balance(board),
            'kingSafety': evaluate_king_safety(board),
            'centerControl': evaluate_center_control(board),
            'mobility': evaluate_mobility(board)
        }
        
        return jsonify(evaluation)
        
    except Exception as e:
        logger.error(f"Помилка оцінки позиції: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_material_balance(board):
    """Розрахунок матеріального балансу"""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    
    white_material = 0
    black_material = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                white_material += value
            else:
                black_material += value
    
    return white_material - black_material

def evaluate_king_safety(board):
    """Оцінка безпеки короля"""
    white_king_safety = 0
    black_king_safety = 0
    
    # Простий алгоритм оцінки безпеки короля
    for color in [chess.WHITE, chess.BLACK]:
        king_square = board.king(color)
        if king_square is not None:
            # Перевіряємо кількість атак на короля
            attacks = len(board.attackers(not color, king_square))
            if color == chess.WHITE:
                white_king_safety = max(0, 10 - attacks * 2)
            else:
                black_king_safety = max(0, 10 - attacks * 2)
    
    return {
        'white': white_king_safety,
        'black': black_king_safety
    }

def evaluate_center_control(board):
    """Оцінка контролю центру"""
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    
    white_control = 0
    black_control = 0
    
    for square in center_squares:
        white_attackers = len(board.attackers(chess.WHITE, square))
        black_attackers = len(board.attackers(chess.BLACK, square))
        
        if white_attackers > black_attackers:
            white_control += 1
        elif black_attackers > white_attackers:
            black_control += 1
    
    return {
        'white': white_control,
        'black': black_control
    }

def evaluate_mobility(board):
    """Оцінка мобільності фігур"""
    white_moves = 0
    black_moves = 0
    
    for move in board.legal_moves:
        if board.turn == chess.WHITE:
            white_moves += 1
        else:
            black_moves += 1
    
    return {
        'white': white_moves,
        'black': black_moves
    }

def update_elo_ratings(result, modules):
    """Оновлення ELO рейтингів після завершення гри"""
    try:
        if ELOSyncManager is None:
            logger.info("ELOSyncManager відключено, пропускаємо оновлення ELO")
            return
        
        if not game_data['elo_manager']:
            game_data['elo_manager'] = ELOSyncManager()
        
        # Визначаємо ботів з модулів
        white_bot = modules.get('white', ['Unknown'])[0] if modules.get('white') else 'Unknown'
        black_bot = modules.get('black', ['Unknown'])[0] if modules.get('black') else 'Unknown'
        
        # Реєструємо ботів якщо вони не існують
        if not game_data['elo_manager'].get_bot_rating(white_bot):
            game_data['elo_manager'].register_bot(white_bot, 1500.0)
        if not game_data['elo_manager'].get_bot_rating(black_bot):
            game_data['elo_manager'].register_bot(black_bot, 1500.0)
        
        # Оновлюємо рейтинги на основі результату
        if result == '1-0':  # Білі виграли
            update_bot_elo(white_bot, black_bot, 1.0)
        elif result == '0-1':  # Чорні виграли
            update_bot_elo(black_bot, white_bot, 1.0)
        else:  # Нічия
            update_bot_elo(white_bot, black_bot, 0.5)
            
        logger.info(f"ELO оновлено: {white_bot} vs {black_bot} - {result}")
        
    except Exception as e:
        logger.error(f"Помилка оновлення ELO: {e}")

def update_bot_elo(winner_bot, loser_bot, score):
    """Оновлення ELO рейтингів для двох ботів"""
    try:
        K = 32  # K-фактор для ELO
        
        winner_rating = game_data['elo_manager'].get_bot_rating(winner_bot)
        loser_rating = game_data['elo_manager'].get_bot_rating(loser_bot)
        
        if winner_rating and loser_rating:
            # Розрахунок очікуваного результату
            expected_winner = 1 / (1 + 10 ** ((loser_rating.elo - winner_rating.elo) / 400))
            expected_loser = 1 - expected_winner
            
            # Оновлення рейтингів
            new_winner_elo = winner_rating.elo + K * (score - expected_winner)
            new_loser_elo = loser_rating.elo + K * ((1 - score) - expected_loser)
            
            # Зберігаємо оновлення
            game_data['elo_manager'].update_bot_rating(winner_bot, new_winner_elo, reason=f"Game result: {score}")
            game_data['elo_manager'].update_bot_rating(loser_bot, new_loser_elo, reason=f"Game result: {1 - score}")
            
    except Exception as e:
        logger.error(f"Помилка розрахунку ELO: {e}")

def save_hitmap_data(result, moves, modules, game_number):
    """Збереження даних для hitmap (тільки JSON, без зображень)"""
    try:
        # Створюємо директорію для hitmap даних
        hitmap_dir = Path("heatmaps/infinite_games")
        hitmap_dir.mkdir(parents=True, exist_ok=True)
        
        # Створюємо дані для hitmap
        hitmap_data = {
            'game_number': game_number,
            'result': result,
            'moves': moves,
            'modules': modules,
            'timestamp': datetime.now().isoformat(),
            'piece_movements': extract_piece_movements(moves)
        }
        
        # Зберігаємо JSON файл
        json_file = hitmap_dir / f"game_{game_number:06d}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(hitmap_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Hitmap дані збережено: {json_file}")
        
    except Exception as e:
        logger.error(f"Помилка збереження hitmap даних: {e}")

def extract_piece_movements(moves):
    """Витягти рухи фігур з списку ходів"""
    try:
        board = chess.Board()
        movements = {}
        
        for move_san in moves:
            try:
                move = board.parse_san(move_san)
                piece = board.piece_at(move.from_square)
                
                if piece:
                    piece_symbol = piece.symbol()
                    if piece_symbol not in movements:
                        movements[piece_symbol] = []
                    
                    # Конвертуємо квадрат в координати
                    to_file = chess.square_file(move.to_square)
                    to_rank = chess.square_rank(move.to_square)
                    movements[piece_symbol].append([to_file, to_rank])
                
                board.push(move)
                
            except Exception as e:
                logger.warning(f"Помилка парсингу ходу {move_san}: {e}")
                continue
        
        return movements
        
    except Exception as e:
        logger.error(f"Помилка витягування рухів фігур: {e}")
        return {}

# Статичні файли
@app.route('/static/<path:filename>')
@handle_api_errors
def static_files(filename):
    """Обслуговування статичних файлів"""
    try:
        return send_from_directory('static', filename)
    except FileNotFoundError:
        logger.warning(f"Статичний файл не знайдено: {filename}")
        return jsonify({'error': 'Файл не знайдено'}), 404

def signal_handler(signum, frame):
    """Обробник сигналів для graceful shutdown"""
    logger.info(f"Отримано сигнал {signum}, закриваємо сервер...")
    server_shutdown.set()
    
    # Логуємо фінальну статистику
    log_connection_stats()
    
    # Даємо час на завершення активних з'єднань
    logger.info("Очікуємо завершення активних з'єднань...")
    for i in range(10):  # Максимум 10 секунд
        if connection_stats['active_connections'] == 0:
            break
        time.sleep(1)
        logger.info(f"Активних з'єднань: {connection_stats['active_connections']}")
    
    logger.info("Сервер готовий до закриття")
    # Завершуємо процес, щоб зупинити werkzeug/Flask dev-сервер
    # Спробуємо коректно зупинити Flask сервер. Якщо не вдається — форсований вихід.
    try:
        # Якщо запускалось через Werkzeug, можна завершити через shutdown ф-ю
        func = request.environ.get('werkzeug.server.shutdown') if 'request' in globals() else None
        if callable(func):
            func()
        else:
            sys.exit(0)
    except Exception:
        os._exit(0)

def _detect_local_ip() -> Optional[str]:
    """Attempt to detect a non-loopback local IPv4 address for logging purposes."""
    try:
        candidates = {
            addr[4][0]
            for addr in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)
        }
        for ip in sorted(candidates):
            if not ip.startswith("127."):
                return ip
    except Exception:
        pass
    try:
        # Fallback technique that infers the preferred outbound interface locally
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Запуск сервера з покращеною обробкою помилок"""
    logger.info(f"Запуск веб-сервера на {host}:{port}")
    if host in ("0.0.0.0", "::"):
        logger.info(f"Відкрийте http://127.0.0.1:{port} у браузері")
        local_ip = _detect_local_ip()
        if local_ip:
            logger.info(f"Або у локальній мережі: http://{local_ip}:{port}")
    else:
        logger.info(f"Відкрийте http://{host}:{port} у браузері")
    
    # Встановлюємо обробники сигналів тільки у головному потоці
    try:
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        else:
            logger.debug("Пропущено встановлення обробників сигналів (не головний потік)")
    except Exception as e:
        logger.debug(f"Не вдалося встановити обробники сигналів: {e}")
    
    # Запускаємо фонове логування статистики
    global stats_thread
    stats_thread.start()
    logger.info("Запущено моніторинг статистики з'єднань")
    
    # Встановлюємо шлях до Stockfish
    if not os.environ.get("STOCKFISH_PATH"):
        stockfish_path = "/workspace/bin/stockfish-bin"
        if os.path.exists(stockfish_path):
            os.environ["STOCKFISH_PATH"] = stockfish_path
    
    try:
        # Налаштування для покращеної стабільності
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        # Запуск сервера з покращеними налаштуваннями
        app.run(
            host=host, 
            port=port, 
            debug=debug, 
            threaded=True,
            use_reloader=False,  # Відключаємо reloader для стабільності
            request_handler=None,  # Використовуємо стандартний обробник
            passthrough_errors=False  # Обробляємо всі помилки
        )
    except (OSError, socket.error) as e:
        if e.errno == 48:  # Address already in use
            logger.error(f"Порт {port} вже використовується. Спробуйте інший порт.")
        else:
            logger.error(f"Помилка запуску сервера: {e}")
        raise
    except KeyboardInterrupt:
        logger.info("Сервер зупинено користувачем")
    except Exception as e:
        logger.error(f"Неочікувана помилка сервера: {e}", exc_info=True)
        raise
    finally:
        logger.info("Сервер закрито")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Chess AI Web Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    
    args = parser.parse_args()
    
    # Встановлюємо таймаут для запитів
    socket.setdefaulttimeout(args.timeout)
    
    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info("Сервер зупинено користувачем")
    except Exception as e:
        logger.error(f"Критична помилка сервера: {e}", exc_info=True)
        sys.exit(1)