"""
Приклад використання MockScreenshotHelper для UI тестів в headless середовищі.
Демонструє різні способи створення mock скріншотів під час тестування.
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.screenshot_helper_mock import MockScreenshotHelper, take_screenshot, take_fullscreen, take_region_screenshot


def example_basic_usage():
    """Базовий приклад використання."""
    print("=== Базовий приклад ===")
    
    # Створюємо екземпляр mock helper'а
    helper = MockScreenshotHelper()
    
    # Mock скріншот всього екрану
    screenshot_path = helper.take_fullscreen("basic_test", "full_screen")
    print(f"Збережено: {screenshot_path}")
    
    # Mock скріншот з описом
    screenshot_path = helper.take_fullscreen("basic_test", "after_click")
    print(f"Збережено: {screenshot_path}")


def example_region_screenshots():
    """Приклад mock скріншотів певних областей."""
    print("\n=== Mock скріншоти областей ===")
    
    helper = MockScreenshotHelper()
    
    # Mock скріншот лівого верхнього кута (400x300 пікселів)
    screenshot_path = helper.take_region_screenshot(
        "region_test", 
        "top_left_corner", 
        x=0, y=0, width=400, height=300
    )
    print(f"Збережено: {screenshot_path}")
    
    # Mock скріншот центру екрану (600x400 пікселів)
    center_x = 1920 // 2 - 300
    center_y = 1080 // 2 - 200
    screenshot_path = helper.take_region_screenshot(
        "region_test", 
        "center_area", 
        x=center_x, y=center_y, width=600, height=400
    )
    print(f"Збережено: {screenshot_path}")


def example_test_scenario():
    """Приклад тестового сценарію з кількома mock скріншотами."""
    print("\n=== Тестовий сценарій ===")
    
    helper = MockScreenshotHelper()
    
    # Початок тесту
    helper.take_fullscreen("chess_ui_test", "initial_state")
    print("1. Початковий стан збережено")
    
    # Імітуємо клік (затримка для демонстрації)
    time.sleep(0.5)
    helper.take_fullscreen("chess_ui_test", "after_first_click")
    print("2. Після першого кліку збережено")
    
    # Mock скріншот тільки шахової дошки (припускаємо координати)
    helper.take_region_screenshot(
        "chess_ui_test", 
        "chess_board_only", 
        x=100, y=100, width=800, height=800
    )
    print("3. Тільки шахова дошка збережена")
    
    # Кінець тесту
    time.sleep(0.5)
    helper.take_fullscreen("chess_ui_test", "final_state")
    print("4. Фінальний стан збережено")


def example_quick_functions():
    """Приклад використання швидких функцій."""
    print("\n=== Швидкі функції ===")
    
    # Використання глобальних функцій
    screenshot_path = take_fullscreen("quick_test", "using_global_function")
    print(f"Швидкий mock скріншот: {screenshot_path}")
    
    # Mock скріншот області через швидку функцію
    screenshot_path = take_region_screenshot(
        "quick_test", 
        "small_area", 
        x=500, y=300, width=200, height=150
    )
    print(f"Швидкий mock скріншот області: {screenshot_path}")


def example_cleanup():
    """Приклад очищення старих mock скріншотів."""
    print("\n=== Очищення ===")
    
    helper = MockScreenshotHelper()
    
    # Показуємо всі mock скріншоти
    screenshots = helper.list_screenshots()
    print(f"Знайдено {len(screenshots)} mock скріншотів:")
    for screenshot in screenshots[:5]:  # Показуємо тільки перші 5
        print(f"  - {screenshot}")
    if len(screenshots) > 5:
        print(f"  ... та ще {len(screenshots) - 5} файлів")
    
    # Очищуємо старі mock скріншоти (старші за 1 день для демонстрації)
    helper.cleanup_old_screenshots(days=1)


def example_chess_ui_scenario():
    """Приклад сценарію тестування шахового UI."""
    print("\n=== Шаховий UI сценарій ===")
    
    helper = MockScreenshotHelper()
    
    # 1. Відкриття гри
    helper.take_fullscreen("chess_game", "game_start")
    print("1. Початок гри збережено")
    
    # 2. Початкова позиція
    helper.take_region_screenshot(
        "chess_game", 
        "initial_board", 
        x=200, y=100, width=600, height=600
    )
    print("2. Початкова позиція збережена")
    
    # 3. Після першого ходу
    time.sleep(0.3)
    helper.take_fullscreen("chess_game", "after_e4")
    print("3. Після ходу e4 збережено")
    
    # 4. Після відповіді суперника
    time.sleep(0.3)
    helper.take_fullscreen("chess_game", "after_opponent_move")
    print("4. Після ходу суперника збережено")
    
    # 5. Скріншот тільки дошки після кількох ходів
    helper.take_region_screenshot(
        "chess_game", 
        "board_after_5_moves", 
        x=200, y=100, width=600, height=600
    )
    print("5. Доска після 5 ходів збережена")
    
    # 6. Кінець гри
    time.sleep(0.3)
    helper.take_fullscreen("chess_game", "game_end")
    print("6. Кінець гри збережено")


if __name__ == "__main__":
    print("Демонстрація MockScreenshotHelper для UI тестів")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_region_screenshots()
        example_test_scenario()
        example_quick_functions()
        example_chess_ui_scenario()
        example_cleanup()
        
        print("\n" + "=" * 50)
        print("Всі приклади виконано успішно!")
        print("Перевірте папку test_screenshots/ для перегляду збережених mock скріншотів.")
        
    except Exception as e:
        print(f"Помилка під час виконання: {e}")
        import traceback
        traceback.print_exc()