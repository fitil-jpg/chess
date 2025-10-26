# Быстрый Старт - Система Паттернов

## Запуск PySide Viewer с Паттернами

```bash
python pyside_viewer.py
```

Теперь в viewer есть:
- **🎯 Вкладка "Паттерни"** - показывает все обнаруженные паттерны во время игры
- **🔄 Кнопка "Ресет"** - сбросить игру и начать новую
- **▶ Старт / ⏸ Стоп** - управление игрой

## Что Отображается в Паттернах

### В JSON файле паттерна:

```json
{
  "pattern_id": "fork_20251026_123456",
  "fen": "позиция до хода",
  "triggering_move": "e2e4",
  "pattern_type": "fork",
  
  "participating_pieces": [
    {
      "square": "e4",
      "piece_type": "knight",
      "color": "white",
      "role": "moved",          // moved, attacker, defender, target, support
      "moved_in_pattern": true  // ходила ли фигура
    }
  ],
  
  "exchange_sequence": {
    "moves": ["d6e4", "f3e4"],     // Последовательность обменов
    "material_balance": 200,        // Материальный баланс
    "forced": true,                 // Форсированный размен?
    "evaluation_change": 2.0        // Изменение оценки
  },
  
  "metadata": {
    "move_number": 5,
    "turn": "white",
    "pieces_in_pattern": 2  // Количество участвующих фигур
  }
}
```

## Только Участвующие Фигуры!

Система показывает **ТОЛЬКО** фигуры, которые:
- ✅ Сделали ход
- ✅ Атакуют цель
- ✅ Защищают позицию
- ✅ Являются целью атаки
- ✅ Поддерживают комбинацию

Фигуры, которые **НЕ участвуют** в паттерне - **не показываются**!

## Размены (2-3 хода вперед)

Система автоматически обнаруживает:
- Форсированные обмены
- Материальный баланс (+200 = выигрыш лёгкой фигуры)
- Участвующие клетки

Пример размена:
```
Ход 1: Nxe4 (мы берём)
Ход 2: dxe4 (противник забирает)
Результат: +100 (выиграли пешку)
```

## Управление Паттернами

### В UI (PySide Viewer):

1. **Фильтрация:**
   - По боту (DynamicBot, StockfishBot, Все)
   - По типу (fork, pin, exchange, и т.д.)

2. **Статистика:**
   - Всего паттернов
   - С обменами
   - По типам
   - По ботам

3. **Детали паттерна:**
   - Нажмите на паттерн в списке
   - Увидите все участвующие фигуры
   - Последовательность обменов (если есть)

### В коде:

```python
from chess_ai.pattern_manager import PatternManager

manager = PatternManager()

# Включить только тактические паттерны
manager.set_enabled_types(["fork", "pin", "exchange"])

# Найти все вилки
forks = manager.search_patterns(pattern_types=["fork"])

# Экспорт паттернов
manager.export_patterns("my_patterns.json", pattern_ids=forks)
```

## Улучшенный DynamicBot

Для использования улучшенного бота с паттернами:

```python
from chess_ai.enhanced_dynamic_bot import EnhancedDynamicBot
import chess

# Создать улучшенного бота
bot = EnhancedDynamicBot(chess.WHITE, use_patterns=True)

# Выбрать ход
board = chess.Board()
move, reason = bot.choose_move(board, debug=True)

print(f"Move: {move}")
print(f"Reason: {reason}")

# Если использовал паттерн, reason будет:
# "PATTERN[fork] | Forced exchange: +200"
```

## Типы Паттернов

- **fork** - Вилка (атака 2+ фигур)
- **pin** - Связка
- **skewer** - Рентген
- **exchange** - Размен
- **capture** - Взятие
- **check** - Шах
- **discovered_attack** - Вскрытая атака
- **centralization** - Централизация

## Создание Своих Паттернов

```python
from chess_ai.pattern_manager import PatternManager

manager = PatternManager()

# Создать паттерн вручную
pattern = manager.create_pattern_from_game(
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    move_uci="e2e4",
    pattern_type="opening",
    description="Мой любимый дебют",
    participating_pieces=[
        {
            "square": "e4",
            "piece_type": "pawn",
            "color": "white",
            "role": "moved",
            "moved_in_pattern": True
        }
    ]
)

if pattern:
    print(f"Создан паттерн: {pattern.pattern_id}")
```

## Где Хранятся Паттерны

```
patterns/
  detected/          # Автоматически обнаруженные паттерны
    config.json      # Настройки системы
    fork_*.json      # Паттерны вилок
    pin_*.json       # Паттерны связок
    exchange_*.json  # Паттерны обменов
    ...
```

## Настройки

Файл `patterns/detected/config.json`:

```json
{
  "enabled_types": ["fork", "pin", "exchange", "capture", "check"],
  "min_confidence": 0.5,
  "prefer_exchanges": true,
  "max_patterns_per_position": 3
}
```

Изменить настройки:

```python
manager = PatternManager()
manager.config.min_confidence = 0.7  # Повысить порог
manager.save_config()
```

## Борьба с Stockfish

Для максимальной эффективности:

1. **Включите debug режим** - видно причины ходов
2. **Играйте несколько партий** - соберите базу паттернов
3. **Фильтруйте паттерны** - оставьте только успешные
4. **Используйте EnhancedDynamicBot** вместо обычного DynamicBot

## Горячие Клавиши в Viewer

- **Ресет** - Сброс игры
- **Старт** - Начать/продолжить
- **Стоп** - Остановить
- **Debug** (checkbox) - Детальные логи

## Отладка

Если паттерны не обнаруживаются:

1. Проверьте, что debug включен
2. Посмотрите консоль на ошибки
3. Убедитесь, что директория `patterns/detected/` существует
4. Проверьте, что паттерны включены в config.json

## Полная Документация

См. `PATTERN_SYSTEM_README.md` для полной документации.

## Примеры

### Пример 1: Автоматическое Обнаружение

Просто играйте! Паттерны обнаруживаются автоматически и показываются на вкладке 🎯 Паттерни.

### Пример 2: Экспорт Лучших Паттернов

```python
from chess_ai.pattern_manager import PatternManager

manager = PatternManager()

# Найти все паттерны с выгодными обменами
good_exchanges = manager.search_patterns(
    has_exchange=True
)

# Экспортировать
manager.export_patterns("best_patterns.json", pattern_ids=good_exchanges)
```

### Пример 3: Использование в Игре

```python
from chess_ai.enhanced_dynamic_bot import EnhancedDynamicBot
import chess

bot = EnhancedDynamicBot(chess.WHITE)
board = chess.Board()

for _ in range(10):
    move, reason = bot.choose_move(board, debug=True)
    if move:
        print(f"{board.san(move)}: {reason}")
        board.push(move)
    
    # Статистика
    stats = bot.get_statistics()
    print(f"Паттернов использовано: {stats['patterns_used']}")
```

---

**Готово!** Система паттернов полностью интегрирована. Запустите `python pyside_viewer.py` и играйте!
