#!/usr/bin/env python3
"""
Скрипт для запуску веб-сервера Chess AI Dashboard
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Перевірити наявність залежностей"""
    try:
        import flask
        import flask_cors
        print("✅ Flask залежності знайдені")
        return True
    except ImportError:
        print("❌ Flask залежності не знайдені")
        return False

def install_dependencies():
    """Встановити залежності"""
    print("📦 Встановлення залежностей...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "web_requirements.txt"
        ], check=True)
        print("✅ Залежності встановлені успішно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Помилка встановлення залежностей: {e}")
        return False

def main():
    """Головна функція"""
    print("🚀 Запуск Chess AI Web Dashboard")
    print("=" * 50)
    
    # Перевіряємо залежності
    if not check_dependencies():
        print("Встановлюємо залежності...")
        if not install_dependencies():
            print("❌ Не вдалося встановити залежності")
            sys.exit(1)
    
    # Встановлюємо змінні середовища
    if not os.environ.get("STOCKFISH_PATH"):
        stockfish_path = "/workspace/bin/stockfish-bin"
        if os.path.exists(stockfish_path):
            os.environ["STOCKFISH_PATH"] = stockfish_path
            print(f"✅ Встановлено STOCKFISH_PATH: {stockfish_path}")
    
    # Запускаємо сервер
    print("\n🌐 Запуск веб-сервера...")
    print("Відкрийте http://localhost:5000 у браузері")
    print("Натисніть Ctrl+C для зупинки")
    print("=" * 50)
    
    try:
        from web_server import run_server
        run_server(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Сервер зупинено")
    except Exception as e:
        print(f"❌ Помилка запуску сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()