# Система Паттернов для Шахматного AI

## Обзор

Система паттернов - это улучшенная система распознавания и применения шахматных паттернов для повышения силы игры AI.

## Основные Компоненты

### 1. EnhancedPatternDetector (`chess_ai/enhanced_pattern_detector.py`)

**Что делает:**
- Обнаруживает паттерны во время игры
- Идентифицирует ТОЛЬКО фигуры, участвующие в паттерне
- Обнаруживает размены на 2-3 хода вперед
- Сохраняет каждый паттерн в отдельный JSON файл

**Типы паттернов:**
- `fork` - вилка (атака нескольких фигур одновременно)
- `pin` - связка
- `skewer` - рентген
- `exchange` - последовательность обменов
- `capture` - взятие
- `check` - шах
- `discovered_attack` - вскрытая атака
- `centralization` - централизация

**Структура JSON паттерна:**
```json
{
  "pattern_id": "fork_20251026_123456_789012",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "triggering_move": "e2e4",
  "pattern_type": "fork",
  "participating_pieces": [
    {
      "square": "e4",
      "piece_type": "knight",
      "color": "white",
      "role": "moved",
      "moved_in_pattern": true
    },
    {
      "square": "d6",
      "piece_type": "queen",
      "color": "black",
      "role": "target",
      "moved_in_pattern": false
    }
  ],
  "exchange_sequence": {
    "moves": ["d6e4", "f3e4"],
    "material_balance": 200,
    "forced": true,
    "evaluation_change": 2.0,
    "participating_squares": ["e4", "d6", "f3"]
  },
  "evaluation": {
    "material_balance": 0,
    "piece_count": 32,
    "game_phase": "opening",
    "is_check": false,
    "is_capture": false
  },
  "metadata": {
    "detected_at": "2025-10-26T12:34:56.789012",
    "move_number": 5,
    "turn": "white",
    "pieces_in_pattern": 2,
    "has_exchange": true
  }
}
```

### 2. PatternManager (`chess_ai/pattern_manager.py`)

**Что делает:**
- Управляет коллекцией паттернов
- Позволяет включать/выключать типы паттернов
- Поиск и фильтрация паттернов
- Экспорт/импорт паттернов
- Создание паттернов вручную

**Основные методы:**
```python
# Включить тип паттерна
pattern_manager.enable_pattern_type("fork")

# Отключить тип паттерна
pattern_manager.disable_pattern_type("pin")

# Получить паттерны для позиции
patterns = pattern_manager.get_patterns_for_position(fen)

# Поиск паттернов
results = pattern_manager.search_patterns(
    pattern_types=["fork", "exchange"],
    has_exchange=True,
    min_participants=2
)

# Экспорт паттернов
pattern_manager.export_patterns("my_patterns.json")

# Импорт паттернов
pattern_manager.import_patterns("downloaded_patterns.json")
```

### 3. PatternDisplayWidget (`ui/pattern_display_widget.py`)

**Что делает:**
- Отображает применённые паттерны во время игры
- Показывает детали каждого паттерна
- Фильтрация по боту и типу
- Статистика использования

**Возможности:**
- Фильтр по ботам (DynamicBot, StockfishBot)
- Фильтр по типам паттернов
- Детальная информация о каждом паттерне
- Список участвующих фигур
- Информация о последовательности обменов
- Статистика применения

### 4. EnhancedDynamicBot (`chess_ai/enhanced_dynamic_bot.py`)

**Что делает:**
- Улучшенная версия DynamicBot с поддержкой паттернов
- Использует базу паттернов для выбора хода
- Приоритизирует выгодные размены
- Распознает тактические возможности

**Порядок принятия решений:**
1. Проверка известных выигрышных паттернов
2. Проверка тактических паттернов (вилки, связки)
3. Проверка похожих позиций
4. Базовая логика DynamicBot

## Использование

### В PySide Viewer

1. **Просмотр паттернов:**
   - Откройте вкладку "🎯 Паттерни"
   - Паттерны автоматически обнаруживаются во время игры
   - Фильтруйте по боту или типу

2. **Управление игрой:**
   - ▶ Старт - начать игру
   - ⏸ Стоп - остановить игру
   - 🔄 Ресет - сбросить и начать новую партию

3. **Статистика:**
   - Просмотр количества паттернов по типам
   - Статистика по ботам
   - Паттерны с обменами

### Программное использование

```python
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector
from chess_ai.pattern_manager import PatternManager
from chess_ai.enhanced_dynamic_bot import EnhancedDynamicBot
import chess

# 1. Создать детектор паттернов
detector = EnhancedPatternDetector()

# 2. Обнаружить паттерн
board = chess.Board()
move = chess.Move.from_uci("e2e4")
board.push(move)

pattern = detector.detect_pattern(board, move, depth=3)
if pattern:
    detector.save_pattern(pattern)
    print(f"Detected: {pattern.pattern_type}")
    print(f"Participants: {len(pattern.participating_pieces)}")

# 3. Управление паттернами
manager = PatternManager()

# Включить только тактические паттерны
manager.set_enabled_types(["fork", "pin", "exchange"])

# Найти все вилки
fork_patterns = manager.search_patterns(pattern_types=["fork"])

# 4. Использовать улучшенного бота
bot = EnhancedDynamicBot(chess.WHITE)
move, reason = bot.choose_move(board, debug=True)
print(f"Move: {move}, Reason: {reason}")

# Получить статистику
stats = bot.get_statistics()
print(f"Patterns used: {stats['patterns_used']}")
```

### Создание паттернов вручную

```python
from chess_ai.pattern_manager import PatternManager

manager = PatternManager()

# Создать паттерн из игры
pattern = manager.create_pattern_from_game(
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    move_uci="e2e4",
    pattern_type="opening",
    description="King's pawn opening",
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
    print(f"Created pattern: {pattern.pattern_id}")
```

## Конфигурация

### Настройки PatternManager

Файл: `patterns/detected/config.json`

```json
{
  "enabled_types": ["fork", "pin", "exchange", "capture", "check"],
  "min_confidence": 0.5,
  "prefer_exchanges": true,
  "max_patterns_per_position": 3
}
```

### Изменение настроек

```python
manager = PatternManager()

# Изменить минимальную уверенность
manager.config.min_confidence = 0.7

# Отключить предпочтение обменов
manager.config.prefer_exchanges = False

# Сохранить настройки
manager.save_config()
```

## Директории

- `patterns/detected/` - сохранённые паттерны (JSON файлы)
- `patterns/detected/config.json` - конфигурация системы паттернов
- `chess_ai/` - модули системы паттернов
- `ui/` - виджеты отображения

## Особенности Системы

### Фильтрация Участвующих Фигур

Система показывает ТОЛЬКО фигуры, которые:
1. Сделали ход (moved)
2. Подвергаются атаке (target)
3. Атакуют (attacker)
4. Защищают (defender)
5. Поддерживают позицию (support)

Фигуры, которые не участвуют в создании паттерна, **не отображаются**.

### Обнаружение Обменов

Система анализирует 2-3 хода вперед для обнаружения:
- Форсированных обменов (обе стороны должны взять)
- Материального баланса размена
- Участвующих клеток
- Изменения оценки

### Приоритизация Паттернов

EnhancedDynamicBot приоритизирует паттерны в следующем порядке:
1. Форсированные выигрышные размены
2. Тактические паттерны (вилки, связки)
3. Позиционные паттерны
4. Похожие позиции

## Улучшение Против Stockfish

Для максимальной эффективности против Stockfish:

1. **Собирайте паттерны из игр:**
   - Играйте партии и собирайте успешные паттерны
   - Фильтруйте только выигрышные паттерны

2. **Настройте приоритеты:**
   - Включите только проверенные типы паттернов
   - Повысьте min_confidence для критических позиций

3. **Используйте EnhancedDynamicBot:**
   - Замените обычный DynamicBot на EnhancedDynamicBot
   - Мониторьте статистику использования паттернов

## Примеры Использования

### Пример 1: Обучение на Играх

```python
from chess_ai.enhanced_pattern_detector import EnhancedPatternDetector
import chess

detector = EnhancedPatternDetector()

# Играем партию и собираем паттерны
board = chess.Board()
game_moves = ["e2e4", "e7e5", "g1f3", "b8c6"]

for move_uci in game_moves:
    move = chess.Move.from_uci(move_uci)
    board.push(move)
    
    # Обнаружить паттерн
    pattern = detector.detect_pattern(board, move)
    if pattern:
        detector.save_pattern(pattern)
        print(f"Saved: {pattern.pattern_type}")
```

### Пример 2: Анализ Паттернов

```python
from chess_ai.pattern_manager import PatternManager

manager = PatternManager()
stats = manager.get_statistics()

print(f"Total patterns: {stats['total_patterns']}")
print(f"By type: {stats['by_type']}")
print(f"With exchanges: {stats['with_exchanges']}")
```

### Пример 3: Фильтрация Паттернов

```python
manager = PatternManager()

# Найти все вилки с обменами
results = manager.search_patterns(
    pattern_types=["fork"],
    has_exchange=True,
    min_participants=3
)

print(f"Found {len(results)} fork patterns with exchanges")

for pattern_id in results:
    pattern = manager.get_pattern(pattern_id)
    print(f"  {pattern_id}: {pattern.metadata.get('description', 'N/A')}")
```

## Отладка

Включите отладочный режим для просмотра деталей:

```python
# В PySide viewer
# Включите checkbox "Debug"

# В коде
bot = EnhancedDynamicBot(chess.WHITE)
move, reason = bot.choose_move(board, debug=True)
print(reason)  # Покажет детальную информацию
```

## Производительность

Система оптимизирована для:
- Быстрого поиска паттернов (индексирование по FEN)
- Эффективного хранения (отдельные JSON файлы)
- Минимального влияния на скорость игры

## Известные Ограничения

1. Точное совпадение FEN может быть слишком строгим
2. Размен обнаруживается только на простых позициях
3. Паттерны не учитывают психологию противника

## Планы Развития

- [ ] Нечеткое совпадение FEN (fuzzy matching)
- [ ] Машинное обучение для оценки паттернов
- [ ] Интеграция с базами дебютов
- [ ] Автоматическое обучение на партиях
- [ ] Экспорт/импорт в формате PGN

## Поддержка

Для вопросов и предложений см. `AGENTS.md` и основной `README.md`.
