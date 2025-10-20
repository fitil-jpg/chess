#!/usr/bin/env python3
"""
Скрипт для запуску шахового веб-сервера
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Перевірити наявність залежностей"""
    try:
        import flask
        import chess
        print("✅ Flask та chess залежності знайдені")
        return True
    except ImportError as e:
        print(f"❌ Відсутні залежності: {e}")
        return False

def install_dependencies():
    """Встановити залежності"""
    print("📦 Встановлення залежностей...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "flask", "python-chess"
        ], check=True)
        print("✅ Залежності встановлені успішно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Помилка встановлення залежностей: {e}")
        return False

def main():
    """Головна функція"""
    print("🚀 Запуск шахового веб-сервера")
    print("=" * 50)
    
    # Перевіряємо залежності
    if not check_dependencies():
        print("Встановлюємо залежності...")
        if not install_dependencies():
            print("❌ Не вдалося встановити залежності")
            sys.exit(1)
    
    # Запускаємо сервер
    print("\n🌐 Запуск веб-сервера...")
    print("Відкрийте http://localhost:5001 у браузері")
    print("Натисніть Ctrl+C для зупинки")
    print("=" * 50)
    
    try:
        from simple_chess_flask import app
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Сервер зупинено")
    except Exception as e:
        print(f"❌ Помилка запуску сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()