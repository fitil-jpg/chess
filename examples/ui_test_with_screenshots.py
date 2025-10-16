"""
Приклад UI тесту з автоматичними скріншотами.
Демонструє як інтегрувати збереження скріншотів у тестові сценарії.
"""

import unittest
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.screenshot_helper_auto import screenshot_helper


class UIWithScreenshotsTest(unittest.TestCase):
    """Тестовий клас з підтримкою скріншотів."""
    
    @classmethod
    def setUpClass(cls):
        """Налаштування перед всіма тестами."""
        cls.screenshot_helper = screenshot_helper
        print("Налаштування ScreenshotHelper завершено")
    
    def setUp(self):
        """Налаштування перед кожним тестом."""
        self.test_name = self._testMethodName
        print(f"\nПочаток тесту: {self.test_name}")
        
        # Скріншот початкового стану
        self.screenshot_helper.take_fullscreen(
            self.test_name, 
            "test_start"
        )
    
    def tearDown(self):
        """Очищення після кожного тесту."""
        # Скріншот фінального стану
        self.screenshot_helper.take_fullscreen(
            self.test_name, 
            "test_end"
        )
        print(f"Завершення тесту: {self.test_name}")
    
    def test_chess_board_initialization(self):
        """Тест ініціалізації шахової дошки."""
        print("Тестуємо ініціалізацію шахової дошки...")
        
        # Імітуємо відкриття шахової дошки
        time.sleep(0.5)
        
        # Скріншот після ініціалізації
        self.screenshot_helper.take_fullscreen(
            self.test_name, 
            "board_initialized"
        )
        
        # Скріншот тільки дошки (припускаємо координати)
        self.screenshot_helper.take_region_screenshot(
            self.test_name, 
            "board_only", 
            x=200, y=100, width=600, height=600
        )
        
        # Перевірка (заглушка)
        self.assertTrue(True, "Дошка ініціалізована")
    
    def test_piece_movement(self):
        """Тест руху фігур."""
        print("Тестуємо рух фігур...")
        
        # Скріншот до руху
        self.screenshot_helper.take_fullscreen(
            self.test_name, 
            "before_move"
        )
        
        # Імітуємо рух фігури
        time.sleep(0.3)
        
        # Скріншот після руху
        self.screenshot_helper.take_fullscreen(
            self.test_name, 
            "after_move"
        )
        
        # Перевірка (заглушка)
        self.assertTrue(True, "Рух виконано")
    
    def test_ui_elements_visibility(self):
        """Тест видимості UI елементів."""
        print("Тестуємо видимість UI елементів...")
        
        # Скріншот всіх UI елементів
        self.screenshot_helper.take_fullscreen(
            self.test_name, 
            "all_ui_elements"
        )
        
        # Скріншот панелі інструментів (припускаємо координати)
        self.screenshot_helper.take_region_screenshot(
            self.test_name, 
            "toolbar", 
            x=0, y=0, width=1920, height=50
        )
        
        # Скріншот статус-бару (припускаємо координати)
        self.screenshot_helper.take_region_screenshot(
            self.test_name, 
            "status_bar", 
            x=0, y=1030, width=1920, height=50
        )
        
        # Перевірка (заглушка)
        self.assertTrue(True, "UI елементи видимі")
    
    def test_error_state_capture(self):
        """Тест збереження скріншотів при помилках."""
        print("Тестуємо збереження скріншотів при помилках...")
        
        try:
            # Імітуємо помилку
            raise ValueError("Тестова помилка для демонстрації")
            
        except Exception as e:
            # Зберігаємо скріншот при помилці
            self.screenshot_helper.take_fullscreen(
                self.test_name, 
                f"error_state_{type(e).__name__}"
            )
            
            # Перекидаємо помилку далі
            raise


def run_ui_tests():
    """Запуск UI тестів зі скріншотами."""
    print("Запуск UI тестів з автоматичними скріншотами")
    print("=" * 60)
    
    # Створюємо тестовий набір
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(UIWithScreenshotsTest)
    
    # Запускаємо тести
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Показуємо результати
    print("\n" + "=" * 60)
    print(f"Тестів виконано: {result.testsRun}")
    print(f"Помилок: {len(result.errors)}")
    print(f"Невдач: {len(result.failures)}")
    
    if result.errors:
        print("\nПомилки:")
        for test, error in result.errors:
            print(f"  {test}: {error}")
    
    if result.failures:
        print("\nНевдачі:")
        for test, failure in result.failures:
            print(f"  {test}: {failure}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ui_tests()
    exit(0 if success else 1)