#!/usr/bin/env python3
"""
Турнирный скрипт для игры всех ботов между собой.
Правила: Bo3 (лучший из 3), 3 минуты на игру.
"""

import os
import sys
import time
import json
import logging
import itertools
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import chess
import chess.engine

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chess_ai.bot_agent import get_agent_names, make_agent
from core.pst_trainer import update_from_board, update_from_history

# Настройка логирования
os.makedirs('tournament_logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('tournament_logs/tournament.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TournamentRunner:
    def __init__(self):
        self.bot_names = self._get_available_bots()
        self.tournament_stats = {}
        self.tournament_patterns = []
        self.games_per_match = int(os.environ.get('GAMES_PER_MATCH', '3'))
        self.time_per_game = int(os.environ.get('TIME_PER_GAME', '180'))  # 3 минуты в секундах
        
        # Создаем директории
        os.makedirs('tournament_logs', exist_ok=True)
        os.makedirs('tournament_patterns', exist_ok=True)
        os.makedirs('tournament_stats', exist_ok=True)
        
        logger.info(f"Турнир: {len(self.bot_names)} ботов, {self.games_per_match} игр на матч, {self.time_per_game}с на игру")
        logger.info(f"Боты: {', '.join(self.bot_names)}")

    def _get_available_bots(self) -> List[str]:
        """Получить список доступных ботов"""
        available_bots = []
        bot_names = get_agent_names()
        
        # Фильтруем только основные боты (исключаем служебные)
        main_bots = [
            'RandomBot', 'AggressiveBot', 'FortifyBot', 'EndgameBot', 
            'DynamicBot', 'KingValueBot', 'PieceMateBot', 'ChessBot'
        ]
        
        for bot_name in main_bots:
            if bot_name in bot_names:
                available_bots.append(bot_name)
        
        return available_bots

    def play_match(self, bot1_name: str, bot2_name: str) -> Dict:
        """Сыграть матч между двумя ботами (Bo3)"""
        logger.info(f"Начинаем матч: {bot1_name} vs {bot2_name}")
        
        bot1_wins = 0
        bot2_wins = 0
        draws = 0
        games = []
        
        for game_num in range(1, self.games_per_match + 1):
            logger.info(f"Игра {game_num}/{self.games_per_match}: {bot1_name} vs {bot2_name}")
            
            # Создаем ботов
            bot1 = make_agent(bot1_name, chess.WHITE)
            bot2 = make_agent(bot2_name, chess.BLACK)
            
            # Играем игру
            game_result = self._play_single_game(bot1, bot2, bot1_name, bot2_name, game_num)
            games.append(game_result)
            
            # Обновляем счет
            if game_result['result'] == '1-0':
                bot1_wins += 1
            elif game_result['result'] == '0-1':
                bot2_wins += 1
            else:
                draws += 1
            
            # Проверяем, не определился ли победитель матча
            if bot1_wins > self.games_per_match // 2:
                break
            if bot2_wins > self.games_per_match // 2:
                break
        
        # Определяем победителя матча
        if bot1_wins > bot2_wins:
            winner = bot1_name
        elif bot2_wins > bot1_wins:
            winner = bot2_name
        else:
            winner = "Draw"
        
        match_result = {
            'bot1': bot1_name,
            'bot2': bot2_name,
            'bot1_wins': bot1_wins,
            'bot2_wins': bot2_wins,
            'draws': draws,
            'winner': winner,
            'games': games,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Матч завершен: {bot1_name} {bot1_wins}-{bot2_wins} {bot2_name}, Победитель: {winner}")
        
        return match_result

    def _play_single_game(self, bot1, bot2, bot1_name: str, bot2_name: str, game_num: int) -> Dict:
        """Сыграть одну игру между ботами"""
        board = chess.Board()
        moves = []
        fens = []
        start_time = time.time()
        
        while not board.is_game_over() and (time.time() - start_time) < self.time_per_game:
            current_bot = bot1 if board.turn == chess.WHITE else bot2
            current_name = bot1_name if board.turn == chess.WHITE else bot2_name
            
            try:
                move = current_bot.choose_move(board)
                if move is None:
                    break
                
                san_move = board.san(move)
                board.push(move)
                moves.append(san_move)
                fens.append(board.fen())
                
            except Exception as e:
                logger.error(f"Ошибка в игре {game_num}: {e}")
                break
        
        # Определяем результат
        if board.is_checkmate():
            result = "1-0" if board.turn == chess.BLACK else "0-1"
        elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
            result = "1/2-1/2"
        else:
            result = "1/2-1/2"  # Время истекло - ничья
        
        game_data = {
            'game_num': game_num,
            'white_bot': bot1_name,
            'black_bot': bot2_name,
            'result': result,
            'moves': moves,
            'fens': fens,
            'move_count': len(moves),
            'duration': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Сохраняем паттерны для анализа
        if len(moves) > 10:  # Только для игр с достаточным количеством ходов
            self._extract_patterns(board, moves, bot1_name, bot2_name, result)
        
        # Обновляем PST таблицы для победителя
        if result in ("1-0", "0-1"):
            winner = chess.WHITE if result == "1-0" else chess.BLACK
            update_from_board(board, winner)
            update_from_history(list(board.move_stack), winner, steps=[15, 21, 35])
        
        return game_data

    def _extract_patterns(self, board: chess.Board, moves: List[str], bot1_name: str, bot2_name: str, result: str):
        """Извлечь паттерны из игры"""
        pattern_data = {
            'bot1': bot1_name,
            'bot2': bot2_name,
            'result': result,
            'moves': moves,
            'final_fen': board.fen(),
            'move_count': len(moves),
            'timestamp': datetime.now().isoformat()
        }
        self.tournament_patterns.append(pattern_data)

    def run_tournament(self):
        """Запустить полный турнир"""
        logger.info("Начинаем турнир!")
        start_time = time.time()
        
        # Создаем все возможные пары ботов
        matches = list(itertools.combinations(self.bot_names, 2))
        total_matches = len(matches)
        
        logger.info(f"Всего матчей: {total_matches}")
        
        tournament_results = []
        
        for i, (bot1, bot2) in enumerate(matches, 1):
            logger.info(f"Матч {i}/{total_matches}")
            match_result = self.play_match(bot1, bot2)
            tournament_results.append(match_result)
            
            # Сохраняем промежуточные результаты
            self._save_tournament_data(tournament_results)
        
        # Подсчитываем финальную статистику
        self._calculate_final_stats(tournament_results)
        
        total_time = time.time() - start_time
        logger.info(f"Турнир завершен за {total_time:.2f} секунд")
        
        # Сохраняем финальные результаты
        self._save_final_results(tournament_results)

    def _calculate_final_stats(self, tournament_results: List[Dict]):
        """Подсчитать финальную статистику турнира"""
        bot_stats = {}
        
        for bot_name in self.bot_names:
            bot_stats[bot_name] = {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'matches_played': 0,
                'games_won': 0,
                'games_lost': 0,
                'games_drawn': 0
            }
        
        for match in tournament_results:
            bot1 = match['bot1']
            bot2 = match['bot2']
            
            # Обновляем статистику матчей
            bot_stats[bot1]['matches_played'] += 1
            bot_stats[bot2]['matches_played'] += 1
            
            if match['winner'] == bot1:
                bot_stats[bot1]['wins'] += 1
                bot_stats[bot2]['losses'] += 1
            elif match['winner'] == bot2:
                bot_stats[bot2]['wins'] += 1
                bot_stats[bot1]['losses'] += 1
            else:
                bot_stats[bot1]['draws'] += 1
                bot_stats[bot2]['draws'] += 1
            
            # Обновляем статистику игр
            bot_stats[bot1]['games_won'] += match['bot1_wins']
            bot_stats[bot1]['games_lost'] += match['bot2_wins']
            bot_stats[bot1]['games_drawn'] += match['draws']
            
            bot_stats[bot2]['games_won'] += match['bot2_wins']
            bot_stats[bot2]['games_lost'] += match['bot1_wins']
            bot_stats[bot2]['games_drawn'] += match['draws']
        
        # Сортируем по количеству побед в матчах
        sorted_bots = sorted(bot_stats.items(), key=lambda x: (x[1]['wins'], x[1]['games_won']), reverse=True)
        
        self.tournament_stats = {
            'bot_rankings': sorted_bots,
            'total_matches': len(tournament_results),
            'total_games': sum(match['bot1_wins'] + match['bot2_wins'] + match['draws'] for match in tournament_results),
            'timestamp': datetime.now().isoformat()
        }

    def _save_tournament_data(self, tournament_results: List[Dict]):
        """Сохранить промежуточные данные турнира"""
        # Сохраняем результаты матчей
        with open('tournament_stats/matches.json', 'w', encoding='utf-8') as f:
            json.dump(tournament_results, f, ensure_ascii=False, indent=2)
        
        # Сохраняем паттерны
        with open('tournament_patterns/patterns.json', 'w', encoding='utf-8') as f:
            json.dump(self.tournament_patterns, f, ensure_ascii=False, indent=2)

    def _save_final_results(self, tournament_results: List[Dict]):
        """Сохранить финальные результаты турнира"""
        final_results = {
            'tournament_stats': self.tournament_stats,
            'matches': tournament_results,
            'patterns': self.tournament_patterns
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Сохраняем полные результаты
        with open(f'tournament_stats/final_results_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        # Создаем читаемый отчет
        self._create_readable_report(timestamp)

    def _create_readable_report(self, timestamp: str):
        """Создать читаемый отчет о турнире"""
        report_path = f'tournament_stats/tournament_report_{timestamp}.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== ОТЧЕТ О ТУРНИРЕ ===\n\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Ботов: {len(self.bot_names)}\n")
            f.write(f"Матчей: {self.tournament_stats['total_matches']}\n")
            f.write(f"Игр: {self.tournament_stats['total_games']}\n")
            f.write(f"Игр на матч: {self.games_per_match}\n")
            f.write(f"Время на игру: {self.time_per_game}с\n\n")
            
            f.write("=== РЕЙТИНГ БОТОВ ===\n")
            for i, (bot_name, stats) in enumerate(self.tournament_stats['bot_rankings'], 1):
                f.write(f"{i}. {bot_name}:\n")
                f.write(f"   Матчи: {stats['wins']}W-{stats['losses']}L-{stats['draws']}D\n")
                f.write(f"   Игры: {stats['games_won']}W-{stats['games_lost']}L-{stats['games_drawn']}D\n\n")
        
        logger.info(f"Отчет сохранен: {report_path}")

def main():
    """Главная функция"""
    try:
        runner = TournamentRunner()
        runner.run_tournament()
        logger.info("Турнир успешно завершен!")
    except Exception as e:
        logger.error(f"Ошибка в турнире: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()