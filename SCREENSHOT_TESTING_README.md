# Система збереження скріншотів для UI тестів

Ця система дозволяє легко зберігати скріншоти під час UI тестування з автоматичним іменуванням та управлінням файлами.

## 🚀 Швидкий старт

### Базове використання

```python
from utils.screenshot_helper_auto import take_fullscreen, take_region_screenshot

# Скріншот всього екрану
screenshot_path = take_fullscreen("my_test", "initial_state")

# Скріншот певної області
screenshot_path = take_region_screenshot("my_test", "error_popup", 100, 100, 400, 300)
```

### Використання в тестах

```python
import unittest
from utils.screenshot_helper_auto import take_fullscreen

class MyUITest(unittest.TestCase):
    def test_ui_behavior(self):
        # Скріншот початкового стану
        take_fullscreen(self._testMethodName, "start")
        
        # Виконання тесту...
        
        # Скріншот результату
        take_fullscreen(self._testMethodName, "result")
```

## 📁 Структура файлів

```
workspace/
├── utils/
│   ├── screenshot_helper.py          # Реальний ScreenshotHelper (для GUI)
│   ├── screenshot_helper_mock.py     # Mock версія (для headless)
│   └── screenshot_helper_auto.py     # Автоматичний вибір
├── test_screenshots/                 # Папка зі скріншотами
│   ├── .gitkeep                      # Зберігає папку в Git
│   ├── README.md                     # Документація папки
│   └── [скріншоти]                  # PNG файли з автоматичними іменами
├── examples/
│   ├── screenshot_test_example.py           # Приклад з реальними скріншотами
│   ├── screenshot_test_example_mock.py      # Приклад з mock скріншотами
│   ├── simple_screenshot_example.py         # Простий приклад
│   └── ui_test_with_screenshots.py          # Приклад інтеграції з тестами
└── .gitignore                        # Ігнорує папку test_screenshots/
```

## 🔧 Налаштування

### Автоматичний режим

Система автоматично вибирає між реальним та mock режимом:

- **GUI середовище** (з DISPLAY): використовує `pyautogui` для реальних скріншотів
- **Headless середовище**: використовує mock скріншоти з PIL

### Ручний вибір режиму

```python
# Реальні скріншоти (потребує GUI)
from utils.screenshot_helper import ScreenshotHelper
helper = ScreenshotHelper()

# Mock скріншоти (працює завжди)
from utils.screenshot_helper_mock import MockScreenshotHelper
helper = MockScreenshotHelper()
```

## 📝 Формат імен файлів

Скріншоти автоматично отримують унікальні імена:

```
{test_name}_{description}_{timestamp}.png
```

Приклади:
- `chess_test_initial_state_20241201_143022_123.png`
- `ui_test_error_popup_20241201_143045_456.png`
- `game_test_board_only_20241201_143102_789.png`

## 🛠️ Доступні функції

### Основні функції

```python
from utils.screenshot_helper_auto import (
    take_fullscreen,           # Скріншот всього екрану
    take_region_screenshot,    # Скріншот області
    list_screenshots,          # Список всіх скріншотів
    cleanup_old_screenshots    # Очищення старих файлів
)
```

### Розширене використання

```python
from utils.screenshot_helper_auto import screenshot_helper

# Прямий доступ до helper'а
screenshot_helper.take_fullscreen("test", "description")
screenshots = screenshot_helper.list_screenshots()
screenshot_helper.cleanup_old_screenshots(days=7)
```

## 🧪 Приклади використання

### 1. Простий приклад

```python
from utils.screenshot_helper_auto import take_fullscreen

# Один скріншот
take_fullscreen("my_test", "demo")
```

### 2. Тестовий сценарій

```python
def test_chess_game():
    take_fullscreen("chess_test", "game_start")
    # ... виконання дій ...
    take_fullscreen("chess_test", "after_move")
    # ... ще дії ...
    take_fullscreen("chess_test", "game_end")
```

### 3. Скріншоти областей

```python
# Скріншот тільки шахової дошки
take_region_screenshot("chess_test", "board", 200, 100, 600, 600)

# Скріншот панелі інструментів
take_region_screenshot("ui_test", "toolbar", 0, 0, 1920, 50)
```

### 4. Управління файлами

```python
from utils.screenshot_helper_auto import list_screenshots, cleanup_old_screenshots

# Показати всі скріншоти
screenshots = list_screenshots()
print(f"Знайдено {len(screenshots)} скріншотів")

# Видалити старі (старші за 7 днів)
cleanup_old_screenshots(days=7)
```

## 📋 Вимоги

### Для реальних скріншотів (GUI)
- Python 3.6+
- pyautogui
- Графічне середовище (DISPLAY)

### Для mock скріншотів (headless)
- Python 3.6+
- Pillow (PIL)

### Встановлення

```bash
# Всі залежності
pip install pyautogui Pillow

# Або тільки для headless
pip install Pillow
```

## 🔒 Git інтеграція

- Папка `test_screenshots/` автоматично ігнорується в `.gitignore`
- Скріншоти зберігаються тільки локально
- Папка зберігається в Git завдяки `.gitkeep` файлу

## 🎯 Переваги

1. **Автоматичне іменування** - унікальні імена з timestamp
2. **Git-безпечність** - скріншоти не потрапляють в репозиторій
3. **Крос-платформність** - працює в GUI та headless режимах
4. **Простота використання** - мінімальний код для початку
5. **Гнучкість** - підтримка різних форматів та розмірів
6. **Управління файлами** - автоматичне очищення старих скріншотів

## 🚨 Важливі примітки

- Mock скріншоти створюються з градієнтним фоном та текстом
- Реальні скріншоти потребують графічного середовища
- Всі скріншоти зберігаються в папці `test_screenshots/`
- Система автоматично вибирає відповідний режим роботи