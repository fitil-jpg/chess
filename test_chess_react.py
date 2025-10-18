#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки Chess React компонента
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_api_endpoints():
    """Тестування API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Тестування Chess React API...")
    
    # Тест статусу
    try:
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            print("✅ API статус: OK")
        else:
            print(f"❌ API статус: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не вдалося підключитися до API. Запустіть Flask сервер:")
        print("   python web_server.py")
        return False
    
    # Тест списку ботів
    try:
        response = requests.get(f"{base_url}/api/bots")
        if response.status_code == 200:
            bots = response.json()
            print(f"✅ Доступні боти: {len(bots)}")
            print(f"   {', '.join(bots[:5])}...")
        else:
            print(f"❌ Помилка отримання ботів: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    # Тест початку гри
    try:
        response = requests.post(f"{base_url}/api/game/start", 
                               json={"white_bot": "RandomBot", "black_bot": "RandomBot"})
        if response.status_code == 200:
            print("✅ Гру успішно розпочато")
        else:
            print(f"❌ Помилка початку гри: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    # Тест ходу
    try:
        response = requests.post(f"{base_url}/api/game/move")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Хід успішно виконано")
            else:
                print(f"❌ Помилка виконання ходу: {data.get('error')}")
        else:
            print(f"❌ Помилка API ходу: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    # Тест аналітики
    try:
        response = requests.get(f"{base_url}/api/game/analytics")
        if response.status_code == 200:
            print("✅ Аналітика доступна")
        else:
            print(f"❌ Помилка аналітики: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    return True

def test_react_files():
    """Перевірка React файлів"""
    print("\n📁 Перевірка React файлів...")
    
    files_to_check = [
        "ChessBoard.jsx",
        "ChessBoard.css", 
        "ChessApp.jsx",
        "chess-react-demo.html",
        "CHESS_REACT_README.md"
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - файл не знайдено")
    
    # Перевірка розміру файлів
    for file_path in files_to_check:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"   📊 {file_path}: {size} байт")

def test_flask_integration():
    """Тест інтеграції з Flask"""
    print("\n🔗 Тестування інтеграції Flask...")
    
    # Перевірка web_server.py
    if Path("web_server.py").exists():
        print("✅ web_server.py знайдено")
        
        # Перевірка наявності нових endpoints
        with open("web_server.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        new_endpoints = [
            "/api/game/analytics",
            "/api/game/move/analyze", 
            "/api/game/position/evaluate"
        ]
        
        for endpoint in new_endpoints:
            if endpoint in content:
                print(f"✅ Endpoint {endpoint} додано")
            else:
                print(f"❌ Endpoint {endpoint} не знайдено")
    else:
        print("❌ web_server.py не знайдено")

def main():
    """Головна функція тестування"""
    print("🎯 Тестування Chess React компонента")
    print("=" * 50)
    
    # Тест файлів
    test_react_files()
    
    # Тест Flask інтеграції
    test_flask_integration()
    
    # Тест API (якщо сервер запущений)
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🏁 Тестування завершено!")
    print("\n📖 Для запуску:")
    print("1. python web_server.py")
    print("2. Відкрийте chess-react-demo.html у браузері")
    print("3. Або інтегруйте компоненти у ваш React проект")

if __name__ == "__main__":
    main()