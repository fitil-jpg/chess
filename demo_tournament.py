#!/usr/bin/env python3
"""
Демонстрационный турнир - быстрый тест системы
"""

import os
import sys
import time
import json
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_demo_tournament():
    """Запускает демонстрационный турнир с 2 ботами"""
    print("=== ДЕМОНСТРАЦИОННЫЙ ТУРНИР ===")
    print("Участники: RandomBot vs DynamicBot")
    print("Формат: Bo3 (лучший из 3 игр)")
    print("Время: 30 секунд на игру")
    print()
    
    try:
        from tournament_runner import TournamentRunner
        import chess
        
        # Создаем демо-версию турнира
        class DemoTournamentRunner(TournamentRunner):
            def __init__(self):
                # Переопределяем настройки для демо
                self.bot_names = ["RandomBot", "DynamicBot"]
                self.tournament_stats = {}
                self.tournament_patterns = []
                self.games_per_match = 3
                self.time_per_game = 30  # 30 секунд для демо
                
                # Создаем директории
                os.makedirs('tournament_logs', exist_ok=True)
                os.makedirs('tournament_patterns', exist_ok=True)
                os.makedirs('tournament_stats', exist_ok=True)
                
                print(f"Демо-турнир: {len(self.bot_names)} ботов, {self.games_per_match} игр на матч, {self.time_per_game}с на игру")
                print(f"Боты: {', '.join(self.bot_names)}")
        
        # Запускаем демо-турнир
        runner = DemoTournamentRunner()
        
        print("\n🚀 Начинаем демо-турнир...")
        start_time = time.time()
        
        # Играем один матч
        match_result = runner.play_match("RandomBot", "DynamicBot")
        
        total_time = time.time() - start_time
        
        print(f"\n✅ Демо-турнир завершен за {total_time:.2f} секунд")
        print(f"Результат: {match_result['bot1']} {match_result['bot1_wins']}-{match_result['bot2_wins']} {match_result['bot2']}")
        print(f"Победитель: {match_result['winner']}")
        print(f"Сохранено паттернов: {len(runner.tournament_patterns)}")
        
        # Сохраняем результаты
        runner._save_tournament_data([match_result])
        
        print("\n📁 Результаты сохранены в:")
        print("  - tournament_logs/")
        print("  - tournament_patterns/")
        print("  - tournament_stats/")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в демо-турнире: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_tournament_files():
    """Показывает созданные файлы турнира"""
    print("\n=== ФАЙЛЫ ТУРНИРА ===")
    
    directories = ["tournament_logs", "tournament_patterns", "tournament_stats"]
    
    for dir_name in directories:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            print(f"\n📁 {dir_name}/")
            for file in files:
                file_path = os.path.join(dir_name, file)
                size = os.path.getsize(file_path)
                print(f"  📄 {file} ({size} bytes)")
        else:
            print(f"\n📁 {dir_name}/ - не создана")

def main():
    """Главная функция демо"""
    print("🎮 ДЕМОНСТРАЦИЯ ТУРНИРНОЙ СИСТЕМЫ")
    print("=" * 50)
    
    # Запускаем демо-турнир
    success = run_demo_tournament()
    
    if success:
        # Показываем созданные файлы
        show_tournament_files()
        
        print("\n🎉 Демонстрация завершена успешно!")
        print("\nДля полного турнира используйте:")
        print("  ./run_tournament.sh")
        print("\nДля просмотра результатов:")
        print("  python3 run_tournament_pattern_viewer.py")
    else:
        print("\n❌ Демонстрация не удалась")
        print("Проверьте настройку системы: python3 test_tournament.py")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)