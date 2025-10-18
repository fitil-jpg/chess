#!/usr/bin/env python3
"""
Скрипт для запуска интерактивного PySide viewer'а с автоматическим воспроизведением игр
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Главная функция запуска"""
    try:
        # Проверяем наличие PySide6
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
        except ImportError:
            print("❌ PySide6 не установлен!")
            print("Установите его командой: pip install PySide6")
            sys.exit(1)
        
        # Проверяем наличие необходимых модулей
        try:
            import chess
            from chess_ai.bot_agent import make_agent
        except ImportError as e:
            print(f"❌ Отсутствует необходимый модуль: {e}")
            print("Убедитесь, что все зависимости установлены")
            sys.exit(1)
        
        print("🚀 Запуск интерактивного Chess Viewer...")
        print("📊 Режим: Автоматическое воспроизведение 10 игр")
        print("🎮 Белые: StockfishBot | Черные: DynamicBot")
        print("=" * 50)
        
        # Импортируем и запускаем viewer
        from interactive_viewer import main as viewer_main
        viewer_main()
        
    except KeyboardInterrupt:
        print("\n⏹ Остановка по запросу пользователя")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()