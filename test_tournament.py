#!/usr/bin/env python3
"""
Тестовый скрипт для проверки турнирной системы
"""

import os
import sys
import json
import time
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tournament_setup():
    """Тестирует настройку турнира"""
    print("=== ТЕСТ НАСТРОЙКИ ТУРНИРА ===")
    
    # Проверяем наличие необходимых файлов
    required_files = [
        "tournament_runner.py",
        "tournament_pattern_viewer.py", 
        "Dockerfile.tournament",
        "docker-compose.tournament.yml",
        "run_tournament.sh",
        "tournament_config.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    else:
        print("✅ Все необходимые файлы присутствуют")
    
    # Проверяем создание директорий
    required_dirs = ["tournament_logs", "tournament_patterns", "tournament_stats"]
    missing_dirs = []
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Отсутствуют директории: {missing_dirs}")
        return False
    else:
        print("✅ Все необходимые директории созданы")
    
    # Проверяем конфигурацию
    try:
        with open("tournament_config.json", "r") as f:
            config = json.load(f)
        print("✅ Конфигурация турнира загружена")
        print(f"   - Игр на матч: {config['tournament_settings']['games_per_match']}")
        print(f"   - Время на игру: {config['tournament_settings']['time_per_game_seconds']}с")
        print(f"   - Участников: {len(config['participating_bots'])}")
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False
    
    return True

def test_bot_availability():
    """Тестирует доступность ботов"""
    print("\n=== ТЕСТ ДОСТУПНОСТИ БОТОВ ===")
    
    try:
        from chess_ai.bot_agent import get_agent_names, make_agent
        import chess
        
        available_bots = get_agent_names()
        print(f"✅ Доступно ботов: {len(available_bots)}")
        
        # Тестируем создание ботов
        test_bots = ["RandomBot", "DynamicBot", "FortifyBot"]
        for bot_name in test_bots:
            if bot_name in available_bots:
                try:
                    bot = make_agent(bot_name, chess.WHITE)
                    print(f"✅ {bot_name} - OK")
                except Exception as e:
                    print(f"❌ {bot_name} - Ошибка: {e}")
            else:
                print(f"⚠️  {bot_name} - недоступен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта ботов: {e}")
        return False

def test_pattern_storage():
    """Тестирует систему хранения паттернов"""
    print("\n=== ТЕСТ СИСТЕМЫ ПАТТЕРНОВ ===")
    
    try:
        from tournament_pattern_viewer import TournamentPatternStorage, TournamentPattern
        
        # Создаем тестовый паттерн
        test_pattern = TournamentPattern(
            id="test_123",
            bot1="TestBot1",
            bot2="TestBot2", 
            result="1-0",
            moves=["e4", "e5", "Nf3"],
            final_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            move_count=3,
            timestamp="2024-01-01T12:00:00",
            game_context={"test": True}
        )
        
        # Тестируем сохранение
        storage = TournamentPatternStorage("test_patterns")
        storage.save_pattern(test_pattern)
        print("✅ Паттерн сохранен")
        
        # Тестируем загрузку
        loaded_pattern = storage.get_pattern("test_123")
        if loaded_pattern and loaded_pattern.bot1 == "TestBot1":
            print("✅ Паттерн загружен")
        else:
            print("❌ Ошибка загрузки паттерна")
            return False
        
        # Очищаем тестовые данные
        storage.delete_pattern("test_123")
        print("✅ Тестовые данные очищены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка системы паттернов: {e}")
        return False

def test_docker_setup():
    """Тестирует настройку Docker"""
    print("\n=== ТЕСТ DOCKER НАСТРОЙКИ ===")
    
    # Проверяем наличие Docker
    import subprocess
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker установлен")
        else:
            print("❌ Docker не найден")
            return False
    except FileNotFoundError:
        print("❌ Docker не установлен")
        return False
    
    # Проверяем docker-compose
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose установлен")
        else:
            print("❌ Docker Compose не найден")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose не установлен")
        return False
    
    return True

def main():
    """Главная функция тестирования"""
    print("ЗАПУСК ТЕСТОВ ТУРНИРНОЙ СИСТЕМЫ")
    print("=" * 50)
    
    tests = [
        ("Настройка турнира", test_tournament_setup),
        ("Доступность ботов", test_bot_availability), 
        ("Система паттернов", test_pattern_storage),
        ("Docker настройка", test_docker_setup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 50)
    print(f"РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Турнирная система готова к работе.")
        print("\nДля запуска турнира используйте:")
        print("  ./run_tournament.sh")
        print("\nДля просмотра результатов:")
        print("  python run_tournament_pattern_viewer.py")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте настройку системы.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)