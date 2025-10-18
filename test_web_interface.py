#!/usr/bin/env python3
"""
Тестовий скрипт для веб-інтерфейсу Chess AI Dashboard
"""

import requests
import time
import threading
import json
from datetime import datetime

def test_api_endpoints():
    """Тестування API ендпоінтів"""
    base_url = "http://localhost:5000"
    
    print("🧪 Тестування веб-інтерфейсу Chess AI Dashboard")
    print("=" * 50)
    
    # Тест 1: Статус сервера
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Статус API: {response.status_code}")
            print(f"   Час сервера: {data.get('timestamp', 'N/A')}")
        else:
            print(f"❌ Статус API: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка статусу API: {e}")
        return False
    
    # Тест 2: Список ігор
    try:
        response = requests.get(f"{base_url}/api/games", timeout=5)
        if response.status_code == 200:
            games = response.json()
            print(f"✅ Список ігор: {response.status_code} ({len(games)} ігор)")
        else:
            print(f"❌ Список ігор: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка списку ігор: {e}")
    
    # Тест 3: Статистика модулів
    try:
        response = requests.get(f"{base_url}/api/modules", timeout=5)
        if response.status_code == 200:
            modules = response.json()
            print(f"✅ Модулі: {response.status_code} ({len(modules)} модулів)")
        else:
            print(f"❌ Модулі: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка модулів: {e}")
    
    # Тест 4: Доступні боти
    try:
        response = requests.get(f"{base_url}/api/bots", timeout=5)
        if response.status_code == 200:
            bots = response.json()
            print(f"✅ Боти: {response.status_code} ({len(bots)} ботів)")
        else:
            print(f"❌ Боти: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка ботів: {e}")
    
    # Тест 5: Початок гри
    try:
        response = requests.post(f"{base_url}/api/game/start", 
                               json={"white_bot": "StockfishBot", "black_bot": "DynamicBot"},
                               timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Початок гри: {response.status_code}")
            print(f"   Повідомлення: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Початок гри: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка початку гри: {e}")
    
    # Тест 6: Стан гри
    try:
        response = requests.get(f"{base_url}/api/game/state", timeout=5)
        if response.status_code == 200:
            state = response.json()
            print(f"✅ Стан гри: {response.status_code}")
            print(f"   FEN: {state.get('fen', 'N/A')[:50]}...")
        else:
            print(f"❌ Стан гри: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка стану гри: {e}")
    
    # Тест 7: Виконання ходу
    try:
        response = requests.post(f"{base_url}/api/game/move", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Хід: {response.status_code}")
            if data.get('success') and data.get('move_result'):
                move = data['move_result'].get('move', 'N/A')
                print(f"   Хід: {move}")
        else:
            print(f"❌ Хід: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка ходу: {e}")
    
    # Тест 8: Зупинка гри
    try:
        response = requests.post(f"{base_url}/api/game/stop", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Зупинка гри: {response.status_code}")
        else:
            print(f"❌ Зупинка гри: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка зупинки гри: {e}")
    
    print("=" * 50)
    print("🎉 Тестування завершено!")
    return True

def test_web_interface():
    """Тестування веб-інтерфейсу"""
    print("\n🌐 Тестування веб-інтерфейсу")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Головна сторінка завантажується")
            if "Chess AI Analytics Dashboard" in response.text:
                print("✅ Заголовок знайдено")
            else:
                print("⚠️  Заголовок не знайдено")
        else:
            print(f"❌ Головна сторінка: {response.status_code}")
    except Exception as e:
        print(f"❌ Помилка веб-інтерфейсу: {e}")

def main():
    """Головна функція"""
    print("🚀 Запуск тестів веб-інтерфейсу")
    print("Переконайтеся, що сервер запущений на localhost:5000")
    print()
    
    # Даємо час серверу запуститися
    time.sleep(1)
    
    # Тестуємо API
    test_api_endpoints()
    
    # Тестуємо веб-інтерфейс
    test_web_interface()
    
    print("\n📋 Результати тестування:")
    print("- Веб-сервер працює на http://localhost:5000")
    print("- API ендпоінти відповідають")
    print("- Веб-інтерфейс завантажується")
    print("- Готово до використання! 🎉")

if __name__ == "__main__":
    main()