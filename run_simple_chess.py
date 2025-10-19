#!/usr/bin/env python3
"""
Скрипт для запуска простой веб-версии шахмат
"""

import os
import sys
from pathlib import Path

# Добавляем текущую директорию к пути
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    print("♟️ Запуск простой веб-версии шахмат...")
    print("=" * 50)
    
    # Проверяем наличие Flask
    try:
        import flask
        print(f"✅ Flask версия: {flask.__version__}")
    except ImportError:
        print("❌ Flask не установлен. Устанавливаем...")
        os.system("pip install flask")
    
    # Проверяем наличие chess
    try:
        import chess
        print(f"✅ Python-chess версия: {chess.__version__}")
    except ImportError:
        print("❌ Python-chess не установлен. Устанавливаем...")
        os.system("pip install python-chess")
    
    # Проверяем наличие модулей ботов
    try:
        from chess_ai.bot_agent import make_agent
        print("✅ Модули ботов найдены")
    except ImportError:
        print("⚠️  Модули ботов не найдены, но это не критично")
    
    print("=" * 50)
    print("🚀 Запускаем сервер...")
    print("📱 Откройте http://localhost:5001 в браузере")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    # Запускаем сервер
    try:
        from simple_chess_web import app
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()