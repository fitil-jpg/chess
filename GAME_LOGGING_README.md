# Легка система логування шахових ігор

## Огляд

Створено мінімалістичну систему логування для шахових AI ігор, яка зберігає essential data без зайвої навантаження.

## Компоненти

### 1. GameLogger (`utils/game_logger.py`)
Основний клас для логування ігор:
- **Компактний JSON формат** - зберігає тільки необхідні дані
- **Автоматичне управління файлами** - створює директорії та імена файлів
- **Мінімальний overhead** - оптимізовано для швидкості
- **Метадані ходів** - confidence, think time, evaluation

### 2. GameAnalytics (`utils/game_analytics.py`)
Аналітичні утиліти:
- **Статистика ботів** - win rate, avg confidence, timing
- **Аналіз дебютів** - найпопулярніші послідовності ходів
- **Часовий аналіз** - think time patterns
- **Генерація звітів** - комплексні звіти в JSON

### 3. Quick Logger Script (`scripts/quick_game_logger.py`)
Готовий скрипт для тестування:
```bash
python scripts/quick_game_logger.py --white RandomBot --black AggressiveBot --moves 50 --games 5 --summary
```

## Швидке використання

### Базове логування
```python
from utils.game_logger import GameLogger

logger = GameLogger()
game_id = logger.start_game("RandomBot", "AggressiveBot")

# Під час гри
logger.log_move(move, board, confidence=0.85, think_time=0.1, eval_score=+2.5)

# В кінці гри
game_data = logger.end_game("1-0", "checkmate")
```

### Аналіз результатів
```python
from utils.game_analytics import GameAnalytics, quick_summary

analytics = GameAnalytics()
stats = analytics.bot_performance("RandomBot", days=7)
print(quick_summary())  # Швидкий текстовий звіт
```

### Автоматична інтеграція
```python
# Для існуючих ботів - додати в choose_move метод:
def choose_move(self, board):
    start_time = time.time()
    move, confidence = self._original_choose_move(board)
    think_time = time.time() - start_time
    
    # Логування якщо активне
    if hasattr(self, '_game_logger'):
        self._game_logger.log_move(move, board, confidence, think_time)
    
    return move, confidence
```

## Формат даних

### Game Log JSON
```json
{
  "game_id": "game_1699123456_RandomBot_vs_AggressiveBot",
  "timestamp": "2025-11-12T20:30:45",
  "white_bot": "RandomBot",
  "black_bot": "AggressiveBot", 
  "time_control": "max_50_moves",
  "start_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "moves": [
    {
      "ply": 1,
      "move": "e2e4",
      "fen": "rnbqkbnr/pppppppp/8/4P3/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
      "confidence": 0.75,
      "think_time_ms": 120.5,
      "eval": 0.2
    }
  ],
  "result": "1-0",
  "termination": "checkmate",
  "duration_seconds": 45.2,
  "total_moves": 24,
  "stats": {
    "avg_confidence": 0.68,
    "avg_think_time_ms": 145.3,
    "total_think_time_ms": 3487.2
  }
}
```

## Продуктивність

- **Розмір файлу**: ~2-5KB на гру (залежно від кількості ходів)
- **Час логування**: <1ms на хід
- **Використання пам'яті**: мінімальне - дані записуються негайно
- **Масштабованість**: тисячі ігор без проблем

## Приклади використання

### Турнір з логуванням
```python
from utils.game_logger import GameLogger
from chess_ai.random_bot import RandomBot
from chess_ai.aggressive_bot import AggressiveBot

def run_tournament(games=10):
    results = []
    
    for i in range(games):
        logger = GameLogger()
        game_id = logger.start_game("RandomBot", "AggressiveBot")
        
        # ... гра ...
        
        game_data = logger.end_game(result, termination)
        results.append(game_data)
    
    return results
```

### Аналіз продуктивності ботів
```python
from utils.game_analytics import get_top_bots

# Топ-10 ботів за win rate за останній місяць
top_bots = get_top_bots(days=30, min_games=10)
for bot in top_bots:
    print(f"{bot['bot_name']}: {bot['win_rate']:.1%} win rate")
```

## Структура файлів

```
logs/
├── games/                    # Основні логи ігор
│   ├── game_1699123456_*.json
│   └── game_1699123500_*.json
├── analytics_report_*.json  # Звіти аналітики
└── .gitkeep
```

## Інтеграція з існуючими системами

Система сумісна з:
- `run_random_game.py` - може замінити поточне логування
- Турнірні скрипти - легко додати до будь-якого турніру
- UI компоненти - дані можна використовувати для візуалізації
- Pattern detection - логи можна аналізувати для пошуку патернів

## Наступні кроки

1. **Інтегрувати** в існуючі боти (додати логування в choose_move)
2. **Налаштувати** автоматичне очищення старих логів
3. **Додати** візуалізацію статистики в UI
4. **Налаштувати** регулярні звіти за розкладом

Система готова до використання і не вимагає додаткових залежностей!
