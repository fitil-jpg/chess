"""
Автоматичний вибір між реальним та mock ScreenshotHelper залежно від середовища.
"""

import os
import sys
from pathlib import Path

# Додаємо поточну директорію до шляху для імпорту
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def get_screenshot_helper():
    """
    Повертає відповідний ScreenshotHelper залежно від середовища.
    
    Returns:
        ScreenshotHelper або MockScreenshotHelper
    """
    # Перевіряємо чи є графічне середовище
    if os.environ.get('DISPLAY') and os.environ.get('DISPLAY') != '':
        try:
            # Спробуємо імпортувати реальний helper
            from screenshot_helper import ScreenshotHelper
            print("Використовується реальний ScreenshotHelper")
            return ScreenshotHelper()
        except ImportError as e:
            print(f"Не вдалося імпортувати реальний ScreenshotHelper: {e}")
            print("Переходимо на MockScreenshotHelper")
        except Exception as e:
            print(f"Помилка при ініціалізації реального ScreenshotHelper: {e}")
            print("Переходимо на MockScreenshotHelper")
    
    # Використовуємо mock версію
    try:
        from screenshot_helper_mock import MockScreenshotHelper
        print("Використовується MockScreenshotHelper")
        return MockScreenshotHelper()
    except ImportError as e:
        print(f"Критична помилка: не вдалося імпортувати MockScreenshotHelper: {e}")
        raise


# Створюємо глобальний екземпляр
screenshot_helper = get_screenshot_helper()

# Експортуємо функції для зручного використання
def take_screenshot(test_name: str, description: str = "", region: tuple = None) -> str:
    """Швидка функція для створення скріншота."""
    return screenshot_helper.take_screenshot(test_name, description, region)


def take_fullscreen(test_name: str, description: str = "") -> str:
    """Швидка функція для створення скріншота всього екрану."""
    return screenshot_helper.take_fullscreen(test_name, description)


def take_region_screenshot(test_name: str, description: str, x: int, y: int, width: int, height: int) -> str:
    """Швидка функція для створення скріншота області."""
    return screenshot_helper.take_region_screenshot(test_name, description, x, y, width, height)


def list_screenshots() -> list:
    """Повертає список всіх збережених скріншотів."""
    return screenshot_helper.list_screenshots()


def cleanup_old_screenshots(days: int = 7):
    """Видаляє старі скріншоти."""
    return screenshot_helper.cleanup_old_screenshots(days)