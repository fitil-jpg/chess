# 🏁 Chess Bot Heatmap Visualization System

Система для генерації та аналізу теплових карт рухів шахових ботів на різних етапах гри.

## 🎯 Основні можливості

- **Генерація теплових карт** для різних ботів та етапів гри
- **Аналіз паттернів рухів** фігур
- **Веб-інтерфейс** для управління тепловими картами
- **API ендпоінти** для інтеграції з іншими системами
- **Порівняння ботів** за їх стилем гри
- **Збереження даних** локально з правильним gitignore

## 📁 Структура проекту

```
heatmap_visualizations/
├── generated/          # Згенеровані теплові карти
├── bot_specific/       # Теплові карти для конкретних ботів
├── game_phases/        # Теплові карти по етапах гри
└── piece_analysis/     # Аналіз окремих фігур

utils/
├── heatmap_generator.py    # Генератор теплових карт
└── heatmap_analyzer.py     # Аналізатор паттернів

runs/                   # Дані ігор (JSON файли)
output/                 # Вихідні файли
logs/                   # Логи системи
```

## 🚀 Швидкий старт

### 1. Встановлення залежностей

```bash
pip3 install chess numpy matplotlib seaborn flask flask-cors
```

### 2. Налаштування директорій

```bash
python3 setup_heatmap_directories.py
```

### 3. Створення зразкових даних

```bash
python3 create_sample_data.py
```

### 4. Генерація теплової карти

```bash
# Для конкретного бота
python3 generate_bot_heatmaps.py --bot DynamicBot --phase all --piece all --games 10

# Для всіх ботів
python3 generate_bot_heatmaps.py --all-bots
```

### 5. Запуск веб-сервера

```bash
python3 web_server.py
```

Відкрийте http://localhost:5000/heatmaps для веб-інтерфейсу.

## 🔧 API Ендпоінти

### Отримати список теплових карт
```http
GET /api/heatmaps
```

### Генерувати теплову карту
```http
POST /api/heatmaps/generate
Content-Type: application/json

{
    "bot_name": "DynamicBot",
    "game_phase": "opening",
    "piece_type": "pawn",
    "games_limit": 100
}
```

### Аналізувати паттерни бота
```http
POST /api/heatmaps/analyze
Content-Type: application/json

{
    "bot_name": "DynamicBot",
    "piece_type": "all"
}
```

### Отримати файл теплової карти
```http
GET /api/heatmaps/{filename}
```

## 🎮 Підтримувані боти

- **DynamicBot** - Мета-агент, що поєднує різні стратегії
- **StockfishBot** - UCI engine-backed bot
- **RandomBot** - Випадкові ходи з простою оцінкою
- **AggressiveBot** - Максимізація матеріального прибутку
- **FortifyBot** - Покращення захисту та структури пішаків
- **EndgameBot** - Евристики для ендшпілю
- **CriticalBot** - Націлення на загрозливі фігури суперника
- **TrapBot** - Встановлення тактичних пасток
- **KingValueBot** - Оцінка на основі безпеки короля
- **NeuralBot** - Нейронна мережа для оцінки ходів
- **UtilityBot** - Базові утиліти оцінки
- **PieceMateBot** - Блокування втечі цільових фігур

## 📊 Етапи гри

- **opening** (1-15 ходів) - Дебют
- **middlegame** (16-40 ходів) - Мітельшпіль  
- **endgame** (41+ ходів) - Ендшпіль
- **all** - Вся гра

## ♟️ Типи фігур

- **pawn** - Пішаки
- **knight** - Коні
- **bishop** - Слони
- **rook** - Тури
- **queen** - Ферзі
- **king** - Королі
- **all** - Всі фігури

## 🐳 Docker підтримка

Система налаштована для роботи з Docker. Файли теплових карт зберігаються в volume:

```yaml
volumes:
  - ./heatmap_visualizations:/heatmap_visualizations
  - ./runs:/runs
  - ./output:/output
```

## 📈 Аналіз паттернів

Система аналізує:

- **Гарячі точки** - квадрати з найбільшою активністю
- **Холодні точки** - квадрати без активності
- **Контроль центру** - активність на d4, d5, e4, e5
- **Активність флангів** - королівський vs ферзевий фланг
- **Загальна мобільність** - кількість рухів фігур

## 🔍 Приклад використання

```python
from utils.heatmap_generator import HeatmapGenerator
from utils.heatmap_analyzer import HeatmapAnalyzer

# Генерація теплової карти
generator = HeatmapGenerator()
result = generator.generate_heatmap(
    bot_name="DynamicBot",
    game_phase="opening", 
    piece_type="pawn",
    games_limit=50
)

# Аналіз паттернів
analyzer = HeatmapAnalyzer()
analysis = analyzer.analyze_bot_patterns("DynamicBot", "all")
```

## 🧪 Тестування

```bash
python3 test_heatmap_system.py
```

## 📝 Конфігурація

Налаштування зберігаються в `heatmap_config.json`:

```json
{
  "heatmap_settings": {
    "default_bots": ["DynamicBot", "StockfishBot", ...],
    "game_phases": {
      "opening": {"moves": [1, 15], "description": "Дебют"},
      "middlegame": {"moves": [16, 40], "description": "Мітельшпіль"},
      "endgame": {"moves": [41, 200], "description": "Ендшпіль"}
    },
    "piece_types": {
      "pawn": {"symbols": ["P", "p"], "description": "Пішаки"},
      "knight": {"symbols": ["N", "n"], "description": "Коні"}
    }
  }
}
```

## 🚨 Відомі обмеження

- Потребує валідні PGN ходи для правильного парсингу
- Деякі ходи можуть не парситися через неоднозначність
- Система працює з існуючими даними ігор у форматі JSON

## 🔧 Налагодження

Логи зберігаються в `logs/` директорії. Для детального логування:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Підтримка

При виникненні проблем:

1. Перевірте наявність необхідних залежностей
2. Переконайтеся, що дані ігор у правильному форматі
3. Перевірте логи в `logs/` директорії
4. Запустіть тести: `python3 test_heatmap_system.py`

## 🎉 Результат

Система успішно створена та протестована! Всі компоненти працюють:

- ✅ API ендпоінти для генерації та отримання теплових карт
- ✅ Генератор теплових карт для різних ботів та етапів гри
- ✅ Аналізатор паттернів рухів фігур
- ✅ Веб-інтерфейс для управління
- ✅ Правильне налаштування .gitignore
- ✅ Docker підтримка з персистентним зберіганням
- ✅ Структура директорій для організації файлів
- ✅ Тестування системи з зразковими даними

Тепер ви можете генерувати та аналізувати теплові карти для ваших шахових ботів! 🏁♟️