#!/usr/bin/env python3
"""
Тестовый скрипт для интерактивного viewer'а
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Тестируем импорты"""
    try:
        print("🔍 Проверка импортов...")
        
        # PySide6
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        print("✅ PySide6 - OK")
        
        # Chess
        import chess
        print("✅ Chess - OK")
        
        # Наши модули
        from chess_ai.bot_agent import make_agent
        print("✅ Bot Agent - OK")
        
        from ui.interactive_charts import InteractiveBarChart, InteractivePieChart
        print("✅ Interactive Charts - OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_basic_functionality():
    """Тестируем базовую функциональность"""
    try:
        print("\n🧪 Тестирование базовой функциональности...")
        
        # Создаем приложение
        app = QApplication(sys.argv)
        
        # Тестируем создание интерактивных графиков
        from ui.interactive_charts import InteractiveBarChart, InteractivePieChart
        
        # Тестовые данные
        test_data = {
            "Module1": 10,
            "Module2": 15,
            "Module3": 8,
            "Module4": 12
        }
        
        # Создаем график
        chart = InteractiveBarChart("Test Chart")
        chart.set_data(test_data)
        
        print("✅ Создание интерактивного графика - OK")
        
        # Тестируем создание агентов
        from chess_ai.bot_agent import make_agent
        
        white_agent = make_agent("RandomBot", chess.WHITE)
        black_agent = make_agent("RandomBot", chess.BLACK)
        
        print("✅ Создание агентов - OK")
        
        # Тестируем игру
        board = chess.Board()
        move = white_agent.choose_move(board)
        if move:
            board.push(move)
            print("✅ Выполнение хода - OK")
        
        print("✅ Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция"""
    print("🚀 Тестирование интерактивного Chess Viewer")
    print("=" * 50)
    
    # Тестируем импорты
    if not test_imports():
        print("\n❌ Тест импортов не пройден")
        return False
    
    # Тестируем базовую функциональность
    if not test_basic_functionality():
        print("\n❌ Тест функциональности не пройден")
        return False
    
    print("\n🎉 Все тесты пройдены! Интерактивный viewer готов к использованию.")
    print("\nДля запуска используйте:")
    print("python run_interactive_viewer.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)