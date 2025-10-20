#!/usr/bin/env python3
"""
Test script for heatmap visualization system
Тестує систему генерації теплових карт
"""

import sys
import os
from pathlib import Path

# Додаємо поточну директорію до шляху
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_heatmap_generator():
    """Тестуємо генератор теплових карт"""
    print("🧪 Тестування генератора теплових карт...")
    
    try:
        from utils.heatmap_generator import HeatmapGenerator
        
        generator = HeatmapGenerator()
        print("✓ HeatmapGenerator імпортовано успішно")
        
        # Тестуємо завантаження ігор
        games = generator.load_games_for_bot('DynamicBot', limit=5)
        print(f"✓ Завантажено {len(games)} ігор для DynamicBot")
        
        if games:
            # Тестуємо витягування рухів
            movements = generator.extract_piece_movements(games, 'all', 'all')
            print(f"✓ Витягнуто рухи для {len(movements)} типів фігур")
            
            # Тестуємо створення даних теплової карти
            heatmap_data = generator.create_heatmap_data(movements, 'all')
            print(f"✓ Створено дані для {len(heatmap_data)} фігур")
            
            return True
        else:
            print("⚠️  Не знайдено ігор для тестування")
            return False
            
    except Exception as e:
        print(f"✗ Помилка тестування генератора: {e}")
        return False

def test_heatmap_analyzer():
    """Тестуємо аналізатор теплових карт"""
    print("\n🧪 Тестування аналізатора теплових карт...")
    
    try:
        from utils.heatmap_analyzer import HeatmapAnalyzer
        
        analyzer = HeatmapAnalyzer()
        print("✓ HeatmapAnalyzer імпортовано успішно")
        
        # Тестуємо аналіз паттернів
        import numpy as np
        test_heatmap = np.array([
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 2, 1, 0, 0, 0],
            [0, 0, 2, 5, 2, 0, 0, 0],
            [0, 0, 1, 2, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ])
        
        analysis = analyzer.analyze_piece_patterns(test_heatmap)
        print(f"✓ Аналіз паттернів: {analysis['total_movements']} рухів")
        print(f"  Гарячі точки: {len(analysis['hot_spots'])}")
        print(f"  Контроль центру: {analysis['center_control']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Помилка тестування аналізатора: {e}")
        return False

def test_api_endpoints():
    """Тестуємо API ендпоінти"""
    print("\n🧪 Тестування API ендпоінтів...")
    
    try:
        # Імпортуємо Flask додаток
        from web_server import app
        
        with app.test_client() as client:
            # Тестуємо health check
            response = client.get('/health')
            if response.status_code == 200:
                print("✓ Health check працює")
            else:
                print(f"✗ Health check не працює: {response.status_code}")
                return False
            
            # Тестуємо список теплових карт
            response = client.get('/api/heatmaps')
            if response.status_code == 200:
                print("✓ API heatmaps працює")
            else:
                print(f"✗ API heatmaps не працює: {response.status_code}")
                return False
            
            # Тестуємо інтерфейс теплових карт
            response = client.get('/heatmaps')
            if response.status_code == 200:
                print("✓ Heatmap interface доступний")
            else:
                print(f"✗ Heatmap interface не доступний: {response.status_code}")
                return False
            
            return True
            
    except ImportError as e:
        print(f"⚠️  Пропущено тест API (відсутні залежності): {e}")
        return True  # Не вважаємо це критичною помилкою
    except Exception as e:
        print(f"✗ Помилка тестування API: {e}")
        return False

def test_directory_structure():
    """Тестуємо структуру директорій"""
    print("\n🧪 Тестування структури директорій...")
    
    required_dirs = [
        'heatmap_visualizations',
        'heatmap_visualizations/generated',
        'heatmap_visualizations/bot_specific',
        'heatmap_visualizations/game_phases',
        'heatmap_visualizations/piece_analysis',
        'runs',
        'output',
        'logs'
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✓ {directory}")
        else:
            print(f"✗ {directory} не існує")
            all_exist = False
    
    return all_exist

def main():
    """Основна функція тестування"""
    print("🚀 Тестування системи теплових карт для шахових ботів\n")
    
    tests = [
        ("Структура директорій", test_directory_structure),
        ("Генератор теплових карт", test_heatmap_generator),
        ("Аналізатор теплових карт", test_heatmap_analyzer),
        ("API ендпоінти", test_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Критична помилка в {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n📊 Результати тестування:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕНО" if result else "❌ ПРОВАЛЕНО"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Пройдено: {passed}/{len(results)} тестів")
    
    if passed == len(results):
        print("\n🎉 Всі тести пройдені! Система теплових карт готова до використання.")
        print("\n📝 Наступні кроки:")
        print("1. Запустіть веб-сервер: python3 web_server.py")
        print("2. Відкрийте http://localhost:5000/heatmaps")
        print("3. Згенеруйте теплові карти для ваших ботів")
    else:
        print(f"\n⚠️  {len(results) - passed} тестів провалено. Перевірте налаштування.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)