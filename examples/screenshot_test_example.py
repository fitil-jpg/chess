"""
Приклад використання ScreenshotHelper для UI тестів.
Демонструє різні способи створення скріншотів під час тестування.
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.screenshot_helper import ScreenshotHelper, take_screenshot, take_fullscreen, take_region_screenshot


def example_basic_usage():
    """Базовий приклад використання."""
    print("=== Базовий приклад ===")
    
    # Створюємо екземпляр helper'а
    helper = ScreenshotHelper()
    
    # Скріншот всього екрану
    screenshot_path = helper.take_fullscreen("basic_test", "full_screen")
    print(f"Збережено: {screenshot_path}")
    
    # Скріншот з описом
    screenshot_path = helper.take_fullscreen("basic_test", "after_click")
    print(f"Збережено: {screenshot_path}")


def example_region_screenshots():
    """Приклад скріншотів певних областей."""
    print("\n=== Скріншоти областей ===")
    
    helper = ScreenshotHelper()
    
    # Скріншот лівого верхнього кута (400x300 пікселів)
    screenshot_path = helper.take_region_screenshot(
        "region_test", 
        "top_left_corner", 
        x=0, y=0, width=400, height=300
    )
    print(f"Збережено: {screenshot_path}")
    
    # Скріншот центру екрану (600x400 пікселів)
    # Припускаємо, що екран 1920x1080
    center_x = 1920 // 2 - 300
    center_y = 1080 // 2 - 200
    screenshot_path = helper.take_region_screenshot(
        "region_test", 
        "center_area", 
        x=center_x, y=center_y, width=600, height=400
    )
    print(f"Збережено: {screenshot_path}")


def example_test_scenario():
    """Приклад тестового сценарію з кількома скріншотами."""
    print("\n=== Тестовий сценарій ===")
    
    helper = ScreenshotHelper()
    
    # Початок тесту
    helper.take_fullscreen("chess_ui_test", "initial_state")
    print("1. Початковий стан збережено")
    
    # Імітуємо клік (затримка для демонстрації)
    time.sleep(1)
    helper.take_fullscreen("chess_ui_test", "after_first_click")
    print("2. Після першого кліку збережено")
    
    # Скріншот тільки шахової дошки (припускаємо координати)
    helper.take_region_screenshot(
        "chess_ui_test", 
        "chess_board_only", 
        x=100, y=100, width=800, height=800
    )
    print("3. Тільки шахова дошка збережена")
    
    # Кінець тесту
    time.sleep(1)
    helper.take_fullscreen("chess_ui_test", "final_state")
    print("4. Фінальний стан збережено")


def example_quick_functions():
    """Приклад використання швидких функцій."""
    print("\n=== Швидкі функції ===")
    
    # Використання глобальних функцій
    screenshot_path = take_fullscreen("quick_test", "using_global_function")
    print(f"Швидкий скріншот: {screenshot_path}")
    
    # Скріншот області через швидку функцію
    screenshot_path = take_region_screenshot(
        "quick_test", 
        "small_area", 
        x=500, y=300, width=200, height=150
    )
    print(f"Швидкий скріншот області: {screenshot_path}")


def example_cleanup():
    """Приклад очищення старих скріншотів."""
    print("\n=== Очищення ===")
    
    helper = ScreenshotHelper()
    
    # Показуємо всі скріншоти
    screenshots = helper.list_screenshots()
    print(f"Знайдено {len(screenshots)} скріншотів:")
    for screenshot in screenshots[:5]:  # Показуємо тільки перші 5
        print(f"  - {screenshot}")
    if len(screenshots) > 5:
        print(f"  ... та ще {len(screenshots) - 5} файлів")
    
    # Очищуємо старі скріншоти (старші за 1 день для демонстрації)
    helper.cleanup_old_screenshots(days=1)


if __name__ == "__main__":
    print("Демонстрація ScreenshotHelper для UI тестів")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_region_screenshots()
        example_test_scenario()
        example_quick_functions()
        example_cleanup()
        
        print("\n" + "=" * 50)
        print("Всі приклади виконано успішно!")
        print("Перевірте папку test_screenshots/ для перегляду збережених скріншотів.")
        
    except Exception as e:
        print(f"Помилка під час виконання: {e}")
        print("Переконайтеся, що pyautogui встановлено: pip install pyautogui")