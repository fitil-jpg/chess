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

# Настройка логирования - только важные события
os.makedirs('tournament_logs', exist_ok=True)

# Создаем два логгера - один для детальных логов, другой для консоли
logging.basicConfig(level=logging.WARNING)  # Отключаем детальные логи по умолчанию

# Детальный логгер (только в файл)
detailed_handler = logging.FileHandler('tournament_logs/tournament.log')
detailed_handler.setLevel(logging.WARNING)

# Консольный логгер (только важная информация)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Формат для консоли
console_formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(console_formatter)

# Основной логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(detailed_handler)

# Отключаем логи от chess бібліотеки
logging.getLogger('chess').setLevel(logging.WARNING)
logging.getLogger('chess.engine').setLevel(logging.WARNING)

class TournamentRunner:
    def __init__(self):
        self.bot_names = self._get_available_bots()
        self.tournament_stats = {}
        self.tournament_patterns = []
        self.games_per_match = int(os.environ.get('GAMES_PER_MATCH', '3'))
        self.time_per_game = int(os.environ.get('TIME_PER_GAME', '180'))  # 3 минуты в секундах
        
        # Метрики использования ботов
        self.bot_metrics = {}
        for bot_name in self.bot_names:
            self.bot_metrics[bot_name] = {
                'moves_count': 0,
                'total_think_time': 0.0,
                'avg_think_time': 0.0,
                'games_played': 0
            }
        
        # Создаем директории
        os.makedirs('tournament_logs', exist_ok=True)
        os.makedirs('tournament_patterns', exist_ok=True)
        os.makedirs('tournament_stats', exist_ok=True)
        
        print(f"🏆 Турнир: {len(self.bot_names)} ботов, {self.games_per_match} игр на матч, {self.time_per_game}с на игру")
        print(f"🤖 Участники: {', '.join(self.bot_names)}")
        print()

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
        print(f"⚔️  Матч: {bot1_name} vs {bot2_name}")
        
        bot1_wins = 0
        bot2_wins = 0
        draws = 0
        games = []
        match_start_time = time.time()
        
        for game_num in range(1, self.games_per_match + 1):
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
        
        match_duration = time.time() - match_start_time
        
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
        
        # Выводим результат матча с метриками
        self._show_match_result(bot1_name, bot2_name, bot1_wins, bot2_wins, draws, winner, match_duration)
        
        return match_result

    def _play_single_game(self, bot1, bot2, bot1_name: str, bot2_name: str, game_num: int) -> Dict:
        """Сыграть одну игру между ботами"""
        board = chess.Board()
        moves = []
        fens = []
        start_time = time.time()
        
        # Счетчики ходов для метрик
        bot1_moves = 0
        bot2_moves = 0
        
        while not board.is_game_over() and (time.time() - start_time) < self.time_per_game:
            current_bot = bot1 if board.turn == chess.WHITE else bot2
            current_name = bot1_name if board.turn == chess.WHITE else bot2_name
            
            try:
                move_start = time.time()
                move_result = current_bot.choose_move(board)
                move_time = time.time() - move_start
                
                # Handle different return formats from bots
                if move_result is None:
                    break
                elif isinstance(move_result, tuple):
                    move = move_result[0]
                else:
                    move = move_result
                
                if move is None:
                    break
                
                # Validate that the move is legal
                if move not in board.legal_moves:
                    # Записываем в файл логов только ошибки
                    with open('tournament_logs/tournament.log', 'a') as f:
                        f.write(f"{datetime.now().isoformat()} [ERROR] Ошибка в игре {game_num}: Illegal move {move} for {current_name} in position {board.fen()}\n")
                    break
                
                # Обновляем метрики
                if current_name == bot1_name:
                    bot1_moves += 1
                    self.bot_metrics[bot1_name]['moves_count'] += 1
                    self.bot_metrics[bot1_name]['total_think_time'] += move_time
                else:
                    bot2_moves += 1
                    self.bot_metrics[bot2_name]['moves_count'] += 1
                    self.bot_metrics[bot2_name]['total_think_time'] += move_time
                
                san_move = board.san(move)
                board.push(move)
                moves.append(san_move)
                fens.append(board.fen())
                
            except Exception as e:
                # Записываем в файл логов только ошибки
                with open('tournament_logs/tournament.log', 'a') as f:
                    f.write(f"{datetime.now().isoformat()} [ERROR] Ошибка в игре {game_num}: {e}\n")
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
        
        # Обновляем счетчик игр
        self.bot_metrics[bot1_name]['games_played'] += 1
        self.bot_metrics[bot2_name]['games_played'] += 1
        
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

    def _show_match_result(self, bot1_name: str, bot2_name: str, bot1_wins: int, bot2_wins: int, draws: int, winner: str, duration: float):
        """Показать результат матча с метриками"""
        # Вычисляем среднее время мышления
        for bot_name in [bot1_name, bot2_name]:
            if self.bot_metrics[bot_name]['moves_count'] > 0:
                self.bot_metrics[bot_name]['avg_think_time'] = (
                    self.bot_metrics[bot_name]['total_think_time'] / 
                    self.bot_metrics[bot_name]['moves_count']
                )
        
        print(f"   Результат: {bot1_wins}-{draws}-{bot2_wins} | Победитель: {winner} | Время: {duration:.1f}s")
        print(f"   📊 Метрики:")
        print(f"      {bot1_name}: {self.bot_metrics[bot1_name]['moves_count']} ходов, "
              f"{self.bot_metrics[bot1_name]['avg_think_time']:.3f}s сред. время")
        print(f"      {bot2_name}: {self.bot_metrics[bot2_name]['moves_count']} ходов, "
              f"{self.bot_metrics[bot2_name]['avg_think_time']:.3f}s сред. время")
        print()

    def run_tournament(self):
        """Запустить полный турнир"""
        print("🚀 Начинаем турнир!")
        start_time = time.time()
        
        # Создаем все возможные пары ботов
        matches = list(itertools.combinations(self.bot_names, 2))
        total_matches = len(matches)
        
        print(f"📋 Всего матчей: {total_matches}\n")
        
        tournament_results = []
        
        for i, (bot1, bot2) in enumerate(matches, 1):
            print(f"📍 Матч {i}/{total_matches}")
            match_result = self.play_match(bot1, bot2)
            tournament_results.append(match_result)
            
            # Показываем промежуточную таблицу
            if i % 7 == 0 or i == total_matches:  # Каждые 7 матчей или в конце
                self._show_current_standings(tournament_results)
            
            # Сохраняем промежуточные результаты
            self._save_tournament_data(tournament_results)
        
        # Подсчитываем финальную статистику
        self._calculate_final_stats(tournament_results)
        
        total_time = time.time() - start_time
        print(f"\n🏁 Турнир завершен за {total_time:.2f} секунд")
        
        # Сохраняем финальные результаты
        self._save_final_results(tournament_results)

    def _show_current_standings(self, tournament_results: List[Dict]):
        """Показать текущую турнирную таблицу"""
        print("\n📊 Текущая турнирная таблица:")
        print("=" * 60)
        
        bot_stats = {}
        for bot_name in self.bot_names:
            bot_stats[bot_name] = {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'points': 0.0
            }
        
        for match in tournament_results:
            bot1 = match['bot1']
            bot2 = match['bot2']
            
            if match['winner'] == bot1:
                bot_stats[bot1]['wins'] += 1
                bot_stats[bot1]['points'] += 1.0
                bot_stats[bot2]['losses'] += 1
            elif match['winner'] == bot2:
                bot_stats[bot2]['wins'] += 1
                bot_stats[bot2]['points'] += 1.0
                bot_stats[bot1]['losses'] += 1
            else:
                bot_stats[bot1]['draws'] += 1
                bot_stats[bot2]['draws'] += 1
                bot_stats[bot1]['points'] += 0.5
                bot_stats[bot2]['points'] += 0.5
        
        # Сортируем по очкам
        sorted_bots = sorted(bot_stats.items(), key=lambda x: x[1]['points'], reverse=True)
        
        print(f"{'Место':<6} {'Бот':<15} {'Очки':<6} {'В-П-Н':<10} {'Ходов':<8} {'Время/ход':<10}")
        print("-" * 60)
        
        for i, (bot_name, stats) in enumerate(sorted_bots, 1):
            moves = self.bot_metrics[bot_name]['moves_count']
            avg_time = self.bot_metrics[bot_name]['avg_think_time']
            print(f"{i:<6} {bot_name:<15} {stats['points']:<6.1f} "
                  f"{stats['wins']}-{stats['losses']}-{stats['draws']:<3} "
                  f"{moves:<8} {avg_time:<10.3f}")
        
        print()

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
        
        # Сохраняем метрики ботов
        with open('tournament_stats/bot_metrics.json', 'w', encoding='utf-8') as f:
            json.dump(self.bot_metrics, f, ensure_ascii=False, indent=2)

    def _save_final_results(self, tournament_results: List[Dict]):
        """Сохранить финальные результаты турнира"""
        final_results = {
            'tournament_stats': self.tournament_stats,
            'matches': tournament_results,
            'patterns': self.tournament_patterns,
            'bot_metrics': self.bot_metrics
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
            
            # Додаємо поглиблений аналіз
            self._add_detailed_analysis(f)
        
        print(f"📄 Отчет сохранен: {report_path}")
    
    def _add_detailed_analysis(self, file):
        """Додати поглиблений аналіз до звіту"""
        file.write("=== ПОГЛИБЛЕНИЙ АНАЛІЗ СТРАТЕГІЙ ===\n\n")
        
        # Аналіз ефективності по часових контрольних
        file.write("1. ЕФЕКТИВНІСТЬ ЗА ЧАСОВИМ КОНТРОЛЕМ:\n")
        file.write(f"   - Таймінг на хід: ~{self.time_per_game // 40}с (середньо)\n")
        file.write(f"   - Загальний час турніру: {self.tournament_stats['total_games'] * self.time_per_game // 60:.1f} хв\n\n")
        
        # Аналіз стилів гри
        file.write("2. АНАЛІЗ СТИЛІВ ГРИ:\n")
        for bot_name, stats in self.tournament_stats['bot_rankings']:
            total_games = stats['games_won'] + stats['games_lost'] + stats['games_drawn']
            if total_games > 0:
                win_rate = (stats['games_won'] / total_games) * 100
                draw_rate = (stats['games_drawn'] / total_games) * 100
                loss_rate = (stats['games_lost'] / total_games) * 100
                
                if win_rate > 40:
                    style = "Агресивний"
                elif draw_rate > 70:
                    style = "Оборонний"
                elif win_rate > 20:
                    style = "Збалансований"
                else:
                    style = "Нестабільний"
                
                file.write(f"   - {bot_name}: {style} ({win_rate:.1f}% перемог, {draw_rate:.1f}% нічиїх)\n")
        file.write("\n")
        
        # Аналіз помилок
        file.write("3. ТИПОВІ ПОМИЛКИ ТА СЛАБКІСТІ:\n")
        for bot_name, stats in self.tournament_stats['bot_rankings']:
            total_games = stats['games_won'] + stats['games_lost'] + stats['games_drawn']
            if total_games > 0:
                loss_rate = (stats['games_lost'] / total_games) * 100
                if loss_rate > 30:
                    file.write(f"   - {bot_name}: Високий відсоток поразок ({loss_rate:.1f}%) - перевірити тактику\n")
                elif stats['games_drawn'] / total_games > 0.8:
                    file.write(f"   - {bot_name}: Занадто оборонний стиль - {stats['games_drawn']} нічиїх\n")
        file.write("\n")
        
        # Рекомендації
        file.write("4. РЕКОМЕНДАЦІЇ ДЛЯ ОПТИМІЗАЦІЇ:\n")
        file.write("   - Провести тестування з різними таймінгами (1хв, 5хв)\n")
        file.write("   - Аналізувати ендшпільні позиції для ботів з високим % нічиїх\n")
        file.write("   - Перевірити агресивні стратегії на тактичні помилки\n")
        file.write("   - Розглянути адаптивні таймінги для різних фаз гри\n\n")

def main():
    """Главная функция"""
    try:
        runner = TournamentRunner()
        runner.run_tournament()
        print("✅ Турнир успешно завершен!")
    except KeyboardInterrupt:
        print("\n⏹️  Турнир прерван пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка в турнире: {e}")
        # Записываем ошибку в лог
        with open('tournament_logs/tournament.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} [ERROR] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()