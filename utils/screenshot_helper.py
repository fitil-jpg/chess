"""
Утиліта для збереження скріншотів UI тестів з автоматичним іменуванням.
Зберігає скріншоти в папці test_screenshots/ з унікальними іменами файлів.
"""

import os
import pyautogui
from datetime import datetime
from pathlib import Path
from typing import Optional


class ScreenshotHelper:
    """Клас для збереження скріншотів UI тестів."""
    
    def __init__(self, base_dir: str = "test_screenshots"):
        """
        Ініціалізація ScreenshotHelper.
        
        Args:
            base_dir: Базова директорія для збереження скріншотів
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Налаштування pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
    
    def take_screenshot(self, 
                       test_name: str, 
                       description: str = "", 
                       region: Optional[tuple] = None) -> str:
        """
        Робить скріншот та зберігає його з унікальним іменем.
        
        Args:
            test_name: Назва тесту (буде використана в імені файлу)
            description: Додатковий опис (опціонально)
            region: Область для скріншоту (x, y, width, height) або None для всього екрану
            
        Returns:
            Шлях до збереженого файлу
        """
        # Створюємо унікальне ім'я файлу
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # мілісекунди
        
        # Очищаємо назву тесту від небезпечних символів
        safe_test_name = "".join(c for c in test_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_test_name = safe_test_name.replace(' ', '_')
        
        # Формуємо ім'я файлу
        if description:
            safe_description = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_description = safe_description.replace(' ', '_')
            filename = f"{safe_test_name}_{safe_description}_{timestamp}.png"
        else:
            filename = f"{safe_test_name}_{timestamp}.png"
        
        # Повний шлях до файлу
        file_path = self.base_dir / filename
        
        try:
            # Робимо скріншот
            if region:
                img = pyautogui.screenshot(region=region)
            else:
                img = pyautogui.screenshot()
            
            # Зберігаємо
            img.save(str(file_path))
            
            print(f"Скріншот збережено: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"Помилка при збереженні скріншота: {e}")
            raise
    
    def take_fullscreen(self, test_name: str, description: str = "") -> str:
        """
        Робить скріншот всього екрану.
        
        Args:
            test_name: Назва тесту
            description: Додатковий опис
            
        Returns:
            Шлях до збереженого файлу
        """
        return self.take_screenshot(test_name, description)
    
    def take_region_screenshot(self, 
                              test_name: str, 
                              description: str, 
                              x: int, y: int, 
                              width: int, height: int) -> str:
        """
        Робить скріншот певної області екрану.
        
        Args:
            test_name: Назва тесту
            description: Опис області
            x, y: Координати лівого верхнього кута
            width, height: Ширина та висота області
            
        Returns:
            Шлях до збереженого файлу
        """
        return self.take_screenshot(test_name, description, region=(x, y, width, height))
    
    def list_screenshots(self) -> list:
        """
        Повертає список всіх збережених скріншотів.
        
        Returns:
            Список шляхів до файлів скріншотів
        """
        screenshots = []
        for file_path in self.base_dir.glob("*.png"):
            screenshots.append(str(file_path))
        return sorted(screenshots)
    
    def cleanup_old_screenshots(self, days: int = 7):
        """
        Видаляє старі скріншоти (старші за вказану кількість днів).
        
        Args:
            days: Кількість днів, після яких скріншоти вважаються старими
        """
        import time
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        deleted_count = 0
        for file_path in self.base_dir.glob("*.png"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
        
        print(f"Видалено {deleted_count} старих скріншотів")


# Глобальний екземпляр для зручного використання
screenshot_helper = ScreenshotHelper()


# Функції для швидкого доступу
def take_screenshot(test_name: str, description: str = "", region: tuple = None) -> str:
    """Швидка функція для створення скріншота."""
    return screenshot_helper.take_screenshot(test_name, description, region)


def take_fullscreen(test_name: str, description: str = "") -> str:
    """Швидка функція для створення скріншота всього екрану."""
    return screenshot_helper.take_fullscreen(test_name, description)


def take_region_screenshot(test_name: str, description: str, x: int, y: int, width: int, height: int) -> str:
    """Швидка функція для створення скріншота області."""
    return screenshot_helper.take_region_screenshot(test_name, description, x, y, width, height)