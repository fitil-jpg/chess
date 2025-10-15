# Проста система синхронізації ELO рейтингів

Спрощена система для синхронізації ELO рейтингів ваших шахових ботів з зовнішніми платформами без веб-інтерфейсу.

## Особливості

- 🔄 **Синхронізація ELO** з Lichess та Chess.com
- 📊 **JSON вивід** для легкого парсингу
- 🖥️ **CLI інтерфейс** для управління
- 🤖 **Підтримка всіх ботів** з вашого проекту
- ⏰ **Автоматичний планувальник** (опціонально)
- 🐳 **Docker підтримка** без веб-залежностей

## Обмеження платформ

- **Lichess**: Повна підтримка (читання рейтингів + можливість гри через API)
- **Chess.com**: Тільки читання рейтингів (не дозволяє ботам грати через API)

## Швидкий старт

### 1. Налаштування

```bash
# Копіюйте файл конфігурації
cp .env.example .env

# Відредагуйте .env файл
nano .env
```

### 2. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 3. Базове використання

```bash
# Зареєструвати бота
python scripts/simple_elo_sync.py register DynamicBot --initial-elo 1500

# Встановити маппінг для Lichess
python scripts/simple_elo_sync.py mapping set lichess DynamicBot your_lichess_bot

# Синхронізувати рейтинги
python scripts/simple_elo_sync.py sync DynamicBot --platforms lichess

# Показати всі рейтинги
python scripts/simple_elo_sync.py list
```

### 4. Запуск з Docker

```bash
# Запустити контейнер
docker-compose -f docker-compose.simple.yml up -d

# Переглянути логи
docker-compose -f docker-compose.simple.yml logs -f

# Зупинити
docker-compose -f docker-compose.simple.yml down
```

## CLI Команди

### Реєстрація ботів

```bash
# Зареєструвати одного бота
python scripts/simple_elo_sync.py register BotName --initial-elo 1500

# Зареєструвати кілька ботів (через Python скрипт)
python examples/simple_elo_example.py
```

### Управління маппінгом

```bash
# Встановити маппінг
python scripts/simple_elo_sync.py mapping set lichess BotName lichess_username
python scripts/simple_elo_sync.py mapping set chesscom BotName chesscom_username

# Показати всі маппінги
python scripts/simple_elo_sync.py mapping list
```

### Синхронізація

```bash
# Синхронізувати з Lichess
python scripts/simple_elo_sync.py sync BotName --platforms lichess

# Синхронізувати з Chess.com
python scripts/simple_elo_sync.py sync BotName --platforms chesscom

# Синхронізувати з обох платформ
python scripts/simple_elo_sync.py sync BotName
```

### Перегляд рейтингів

```bash
# Всі рейтинги
python scripts/simple_elo_sync.py list

# Конкретний бот
python scripts/simple_elo_sync.py list --bot BotName

# Тільки JSON (без логів)
python scripts/simple_elo_sync.py list --quiet
```

## Програмне використання

```python
import asyncio
from chess_ai.simple_elo_sync import SimpleELOSync

async def main():
    # Ініціалізація
    sync_system = SimpleELOSync(
        lichess_token="your_token",
        chesscom_username="your_username",
        chesscom_password="your_password"
    )
    
    # Реєстрація ботів
    bot_configs = {
        "DynamicBot": 1500.0,
        "StockfishBot": 2000.0
    }
    sync_system.register_bots(bot_configs)
    
    # Встановлення маппінгів
    mappings = {
        "lichess": {
            "DynamicBot": "your_lichess_bot",
            "StockfishBot": "your_stockfish_bot"
        }
    }
    sync_system.set_platform_mappings(mappings)
    
    # Синхронізація
    results = await sync_system.sync_ratings(["DynamicBot", "StockfishBot"])
    print(results)
    
    # Отримання рейтингів
    summary = sync_system.get_ratings_summary()
    print(summary)

asyncio.run(main())
```

## Автоматичний планувальник

```python
# Налаштування планувальника
configs = {
    "hourly_sync": {
        "bot_names": ["DynamicBot", "StockfishBot"],
        "platforms": ["lichess"],
        "interval_minutes": 60,
        "enabled": True
    }
}

sync_system.setup_scheduler(configs)
await sync_system.start_scheduler()
```

## Структура JSON виводу

### Результат синхронізації

```json
{
  "lichess": [
    {
      "bot_name": "DynamicBot",
      "success": true,
      "old_elo": 1500.0,
      "new_elo": 1525.0,
      "rating_change": 25.0,
      "error": null,
      "platform_rating": 1525,
      "provisional": false
    }
  ],
  "chesscom": [
    {
      "bot_name": "DynamicBot",
      "success": false,
      "old_elo": 1500.0,
      "new_elo": 1500.0,
      "rating_change": 0.0,
      "error": "No Chess.com rating found",
      "platform_rating": null,
      "provisional": false
    }
  ]
}
```

### Підсумок рейтингів

```json
{
  "total_bots": 4,
  "platforms_enabled": {
    "lichess": true,
    "chesscom": true
  },
  "last_sync": "2024-01-15T10:30:00",
  "bots": {
    "DynamicBot": {
      "elo": 1525.0,
      "games_played": 10,
      "last_updated": "2024-01-15T10:30:00",
      "confidence": 0.95,
      "platform_ratings": {
        "lichess": {
          "rating": 1525,
          "last_updated": "2024-01-15T10:30:00"
        }
      }
    }
  }
}
```

## Налаштування

### Змінні середовища

```bash
# .env файл
LICHESS_TOKEN=your_lichess_token_here
CHESSCOM_USERNAME=your_chesscom_username
CHESSCOM_PASSWORD=your_chesscom_password
```

### Файли конфігурації

- `ratings.json` - Локальні рейтинги ботів
- `sync_config.json` - Конфігурація планувальника (автоматично створюється)

## Обмеження Chess.com

Chess.com **НЕ дозволяє** ботам грати через їх API. Можна тільки:

- ✅ Читати рейтинги існуючих акаунтів
- ✅ Отримувати статистику гравців
- ❌ Створювати нові ігри
- ❌ Робити ходи в іграх
- ❌ Автоматично грати

Для автоматичної гри використовуйте **Lichess API**.

## Troubleshooting

### Помилки API

```bash
# Перевірити токени
python scripts/simple_elo_sync.py list --quiet

# Якщо помилка - перевірити .env файл
cat .env
```

### Проблеми з Docker

```bash
# Переглянути логи
docker-compose -f docker-compose.simple.yml logs

# Перебудувати контейнер
docker-compose -f docker-compose.simple.yml build --no-cache
```

### Проблеми з маппінгом

```bash
# Перевірити маппінги
python scripts/simple_elo_sync.py mapping list

# Перевірити рейтинги
python scripts/simple_elo_sync.py list --bot BotName
```

## Приклади використання

Дивіться файли в папці `examples/`:

- `simple_elo_example.py` - Базові приклади
- `elo_sync_example.py` - Розширені приклади

## Ліцензія

Цей проект використовує ту ж ліцензію, що й основний проект шахових ботів.