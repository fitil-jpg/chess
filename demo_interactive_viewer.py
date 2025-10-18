#!/usr/bin/env python3
"""
Демонстрация функциональности интерактивного viewer'а без GUI
"""

import sys
import os
from pathlib import Path
import time
import json

# Добавляем корневую директорию проекта в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_game_simulation():
    """Демонстрация симуляции игр"""
    print("🎮 Демонстрация автоматического воспроизведения игр")
    print("=" * 60)
    
    try:
        import chess
        from chess_ai.bot_agent import make_agent
        
        # Создаем агентов
        print("🤖 Создание агентов...")
        white_agent = make_agent("RandomBot", chess.WHITE)
        black_agent = make_agent("RandomBot", chess.BLACK)
        print("✅ Агенты созданы успешно")
        
        # Симулируем 5 игр
        results = []
        for game_id in range(5):
            print(f"\n🎯 Игра {game_id + 1}/5")
            
            board = chess.Board()
            moves = []
            modules_w = []
            modules_b = []
            fens = [board.fen()]
            
            start_time = time.time()
            move_count = 0
            
            while not board.is_game_over() and move_count < 50:  # Ограничиваем количество ходов
                mover_color = board.turn
                agent = white_agent if mover_color == chess.WHITE else black_agent
                
                try:
                    move = agent.choose_move(board)
                    if move is None or not board.is_legal(move):
                        break
                        
                    san = board.san(move)
                    moves.append(san)
                    
                    # Получаем информацию о модуле
                    reason = agent.get_last_reason() if hasattr(agent, "get_last_reason") else "RANDOM"
                    
                    if mover_color == chess.WHITE:
                        modules_w.append(reason)
                    else:
                        modules_b.append(reason)
                    
                    board.push(move)
                    fens.append(board.fen())
                    move_count += 1
                    
                    print(f"  Ход {move_count}: {san} ({reason})")
                    
                except Exception as e:
                    print(f"  ❌ Ошибка хода: {e}")
                    break
            
            duration_ms = int((time.time() - start_time) * 1000)
            result = board.result()
            
            game_result = {
                'game_id': game_id,
                'result': result,
                'moves': moves,
                'modules_w': modules_w,
                'modules_b': modules_b,
                'fens': fens,
                'duration_ms': duration_ms,
                'move_count': move_count
            }
            
            results.append(game_result)
            
            print(f"  ✅ Результат: {result} ({move_count} ходов, {duration_ms}ms)")
        
        return results
        
    except Exception as e:
        print(f"❌ Ошибка симуляции: {e}")
        import traceback
        traceback.print_exc()
        return []

def demo_statistics(results):
    """Демонстрация статистики"""
    if not results:
        print("❌ Нет данных для статистики")
        return
        
    print("\n📊 Статистика игр")
    print("=" * 40)
    
    # Подсчитываем результаты
    results_count = {}
    total_moves = 0
    total_duration = 0
    
    for result in results:
        game_result = result.get('result', '*')
        results_count[game_result] = results_count.get(game_result, 0) + 1
        total_moves += result.get('move_count', 0)
        total_duration += result.get('duration_ms', 0)
    
    print(f"Всего игр: {len(results)}")
    print(f"Общее количество ходов: {total_moves}")
    print(f"Общее время: {total_duration / 1000:.1f}s")
    print(f"Среднее время игры: {total_duration / len(results) / 1000:.1f}s")
    print(f"Среднее количество ходов: {total_moves / len(results):.1f}")
    
    print("\nРезультаты:")
    for result, count in results_count.items():
        percentage = (count / len(results)) * 100
        print(f"  {result}: {count} игр ({percentage:.1f}%)")

def demo_module_analysis(results):
    """Демонстрация анализа модулей"""
    if not results:
        return
        
    print("\n🔍 Анализ использования модулей")
    print("=" * 40)
    
    all_modules = {}
    
    for result in results:
        for module in result.get('modules_w', []) + result.get('modules_b', []):
            all_modules[module] = all_modules.get(module, 0) + 1
    
    if all_modules:
        print("Топ модулей:")
        sorted_modules = sorted(all_modules.items(), key=lambda x: -x[1])
        for module, count in sorted_modules[:10]:
            percentage = (count / sum(all_modules.values())) * 100
            print(f"  {module}: {count} раз ({percentage:.1f}%)")
    else:
        print("Нет данных о модулях")

def demo_interactive_features():
    """Демонстрация интерактивных возможностей"""
    print("\n🎯 Интерактивные возможности")
    print("=" * 40)
    
    print("В реальном GUI приложении доступны:")
    print("✅ Кликабельные графики с детальной информацией")
    print("✅ Hover эффекты при наведении мыши")
    print("✅ Фильтрация игр по результатам")
    print("✅ Выбор игр для просмотра на доске")
    print("✅ Интерактивная временная шкала ходов")
    print("✅ Статистические диаграммы")
    print("✅ Управление воспроизведением (старт/пауза/стоп)")
    print("✅ Настройка количества игр и выбора ботов")

def save_results_to_file(results):
    """Сохранить результаты в файл"""
    if not results:
        return
        
    output_file = "demo_results.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Результаты сохранены в {output_file}")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

def main():
    """Главная функция демонстрации"""
    print("🚀 Демонстрация интерактивного Chess Viewer")
    print("=" * 60)
    print("Это демонстрация функциональности без GUI")
    print("В реальном приложении будет графический интерфейс")
    print("=" * 60)
    
    # Демонстрируем симуляцию игр
    results = demo_game_simulation()
    
    if results:
        # Показываем статистику
        demo_statistics(results)
        
        # Анализируем модули
        demo_module_analysis(results)
        
        # Сохраняем результаты
        save_results_to_file(results)
        
        # Показываем интерактивные возможности
        demo_interactive_features()
        
        print("\n🎉 Демонстрация завершена успешно!")
        print("\nДля запуска полного GUI приложения:")
        print("python3 run_interactive_viewer.py")
        print("\n(Требуется графическая среда)")
        
    else:
        print("\n❌ Демонстрация не удалась")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)