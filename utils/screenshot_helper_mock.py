"""
Mock версія ScreenshotHelper для тестування в headless середовищі.
Створює фейкові скріншоти замість реальних для демонстрації функціональності.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont


class MockScreenshotHelper:
    """Mock версія ScreenshotHelper для headless середовища."""
    
    def __init__(self, base_dir: str = "test_screenshots"):
        """
        Ініціалізація MockScreenshotHelper.
        
        Args:
            base_dir: Базова директорія для збереження скріншотів
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def _create_mock_screenshot(self, width: int = 1920, height: int = 1080, 
                               test_name: str = "", description: str = "") -> Image.Image:
        """
        Створює фейковий скріншот для демонстрації.
        
        Args:
            width: Ширина зображення
            height: Висота зображення
            test_name: Назва тесту
            description: Опис скріншота
            
        Returns:
            PIL Image об'єкт
        """
        # Створюємо зображення з градієнтом
        img = Image.new('RGB', (width, height), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Додаємо текст з інформацією про тест
        try:
            # Спробуємо використати системний шрифт
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            # Якщо не знайдемо шрифт, використаємо стандартний
            font = ImageFont.load_default()
        
        # Додаємо заголовок
        title = f"Mock Screenshot: {test_name}"
        if description:
            title += f" - {description}"
        
        # Розраховуємо позицію для центрування тексту
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 50
        
        # Малюємо текст з тінню
        draw.text((x + 2, y + 2), title, fill='black', font=font)
        draw.text((x, y), title, fill='white', font=font)
        
        # Додаємо timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_text = f"Generated: {timestamp}"
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            small_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), timestamp_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = y + text_height + 20
        
        draw.text((x + 1, y + 1), timestamp_text, fill='black', font=small_font)
        draw.text((x, y), timestamp_text, fill='lightgray', font=small_font)
        
        # Додаємо декоративні елементи
        # Рамка
        draw.rectangle([10, 10, width-10, height-10], outline='white', width=3)
        
        # Кутові маркери
        corner_size = 20
        for corner_x, corner_y in [(10, 10), (width-30, 10), (10, height-30), (width-30, height-30)]:
            draw.rectangle([corner_x, corner_y, corner_x+corner_size, corner_y+corner_size], 
                          fill='white', outline='black', width=2)
        
        return img
    
    def take_screenshot(self, 
                       test_name: str, 
                       description: str = "", 
                       region: Optional[tuple] = None) -> str:
        """
        Робить mock скріншот та зберігає його з унікальним іменем.
        
        Args:
            test_name: Назва тесту (буде використана в імені файлу)
            description: Додатковий опис (опціонально)
            region: Область для скріншота (x, y, width, height) або None для всього екрану
            
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
            # Визначаємо розміри
            if region:
                width, height = region[2], region[3]
            else:
                width, height = 1920, 1080
            
            # Створюємо mock скріншот
            img = self._create_mock_screenshot(width, height, test_name, description)
            
            # Зберігаємо
            img.save(str(file_path))
            
            print(f"Mock скріншот збережено: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"Помилка при збереженні mock скріншота: {e}")
            raise
    
    def take_fullscreen(self, test_name: str, description: str = "") -> str:
        """
        Робить mock скріншот всього екрану.
        
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
        Робить mock скріншот певної області екрану.
        
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
        
        print(f"Видалено {deleted_count} старих mock скріншотів")


# Глобальний екземпляр для зручного використання
mock_screenshot_helper = MockScreenshotHelper()


# Функції для швидкого доступу
def take_screenshot(test_name: str, description: str = "", region: tuple = None) -> str:
    """Швидка функція для створення mock скріншота."""
    return mock_screenshot_helper.take_screenshot(test_name, description, region)


def take_fullscreen(test_name: str, description: str = "") -> str:
    """Швидка функція для створення mock скріншота всього екрану."""
    return mock_screenshot_helper.take_fullscreen(test_name, description)


def take_region_screenshot(test_name: str, description: str, x: int, y: int, width: int, height: int) -> str:
    """Швидка функція для створення mock скріншота області."""
    return mock_screenshot_helper.take_region_screenshot(test_name, description, x, y, width, height)