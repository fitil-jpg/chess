# Турнир шахматных ботов

Этот модуль предоставляет систему для проведения турниров между шахматными ботами с записью статистики и сохранением паттернов.

## Особенности

- **Турнирный формат**: Bo3 (лучший из 3 игр)
- **Время на игру**: 3 минуты
- **Участники**: Все доступные боты
- **Статистика**: Подробная запись результатов
- **Паттерны**: Автоматическое сохранение интересных позиций
- **Визуализация**: Интерфейс для просмотра результатов и паттернов

## Структура файлов

```
tournament_runner.py          # Основной скрипт турнира
tournament_pattern_viewer.py  # Вьювер для турнирных паттернов
Dockerfile.tournament         # Docker образ для турнира
docker-compose.tournament.yml # Docker Compose конфигурация
run_tournament.sh            # Скрипт запуска турнира
run_tournament_pattern_viewer.py # Скрипт запуска вьювера
```

## Быстрый запуск

### 1. Запуск турнира через Docker

```bash
# Запустить турнир
./run_tournament.sh

# Или вручную
docker-compose -f docker-compose.tournament.yml up --build
```

### 2. Запуск турнира локально

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить турнир
python tournament_runner.py
```

### 3. Просмотр результатов

```bash
# Запустить вьювер турнирных паттернов
python run_tournament_pattern_viewer.py
```

## Настройка турнира

### Переменные окружения

- `GAMES_PER_MATCH` - количество игр в матче (по умолчанию: 3)
- `TIME_PER_GAME` - время на игру в секундах (по умолчанию: 180)
- `LOG_LEVEL` - уровень логирования (по умолчанию: INFO)

### Пример настройки

```bash
export GAMES_PER_MATCH=5
export TIME_PER_GAME=300
export LOG_LEVEL=DEBUG
python tournament_runner.py
```

## Результаты турнира

### Структура результатов

Турнир создает следующие файлы:

```
tournament_logs/
├── tournament.log          # Основной лог турнира

tournament_patterns/
├── patterns.json          # Сохраненные паттерны

tournament_stats/
├── matches.json           # Результаты матчей
├── final_results_*.json   # Финальные результаты
└── tournament_report_*.txt # Читаемый отчет
```

### Формат данных

#### Результаты матчей (matches.json)
```json
[
  {
    "bot1": "DynamicBot",
    "bot2": "FortifyBot", 
    "bot1_wins": 2,
    "bot2_wins": 1,
    "draws": 0,
    "winner": "DynamicBot",
    "games": [...],
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

#### Турнирные паттерны (patterns.json)
```json
[
  {
    "id": "pattern_123",
    "bot1": "DynamicBot",
    "bot2": "FortifyBot",
    "result": "1-0",
    "moves": ["e4", "e5", "Nf3", ...],
    "final_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "move_count": 25,
    "timestamp": "2024-01-01T12:00:00",
    "game_context": {...},
    "pattern_type": "tournament"
  }
]
```

## Интерфейс вьювера

### Основные функции

1. **Просмотр паттернов** - список всех турнирных паттернов
2. **Фильтрация** - по ботам, результатам, поиск
3. **Статистика** - рейтинг ботов по результатам
4. **Детали паттерна** - информация о конкретной игре
5. **Шахматная доска** - визуализация позиций
6. **Список ходов** - последовательность ходов игры

### Фильтры

- **Bot Filter** - фильтр по участникам
- **Result Filter** - фильтр по результатам (1-0, 0-1, 1/2-1/2)
- **Search** - текстовый поиск

### Действия

- **Refresh** - обновить список паттернов
- **Delete** - удалить выбранный паттерн
- **Export** - экспорт паттернов в JSON

## Участники турнира

По умолчанию в турнире участвуют следующие боты:

- RandomBot
- AggressiveBot  
- FortifyBot
- EndgameBot
- DynamicBot
- KingValueBot
- PieceMateBot
- ChessBot

## Мониторинг турнира

### Логи

Турнир ведет подробные логи в файле `tournament_logs/tournament.log`:

```
2024-01-01 12:00:00 [INFO] Турнир: 8 ботов, 3 игр на матч, 180с на игру
2024-01-01 12:00:01 [INFO] Боты: RandomBot, AggressiveBot, FortifyBot, ...
2024-01-01 12:00:02 [INFO] Начинаем матч: DynamicBot vs FortifyBot
2024-01-01 12:00:03 [INFO] Игра 1/3: DynamicBot vs FortifyBot
...
```

### Прогресс

Турнир показывает прогресс выполнения:

```
Матч 1/28: DynamicBot vs FortifyBot
Игра 1/3: DynamicBot vs FortifyBot
Игра 2/3: DynamicBot vs FortifyBot  
Игра 3/3: DynamicBot vs FortifyBot
Матч завершен: DynamicBot 2-1 FortifyBot, Победитель: DynamicBot
```

## Устранение неполадок

### Проблемы с Docker

```bash
# Очистить Docker кэш
docker system prune -a

# Пересобрать образ
docker-compose -f docker-compose.tournament.yml build --no-cache
```

### Проблемы с зависимостями

```bash
# Обновить зависимости
pip install -r requirements.txt --upgrade

# Проверить установку chess
python -c "import chess; print('Chess module OK')"
```

### Проблемы с GUI

```bash
# Установить PySide6
pip install PySide6

# Проверить GUI
python -c "from PySide6.QtWidgets import QApplication; print('GUI OK')"
```

## Расширение функциональности

### Добавление новых ботов

1. Создайте новый бот в `chess_ai/`
2. Добавьте его в `get_agent_names()` в `bot_agent.py`
3. Обновите список в `tournament_runner.py`

### Настройка детекции паттернов

Измените параметры в `tournament_runner.py`:

```python
# Минимальное количество ходов для сохранения паттерна
if len(moves) > 10:  # Изменить на нужное значение
    self._extract_patterns(...)
```

### Кастомные форматы турнира

Измените логику в `play_match()` для других форматов:

```python
# Изменить с Bo3 на другой формат
if bot1_wins > self.games_per_match // 2:
    break
```

## Лицензия

Этот модуль является частью проекта Chess AI и распространяется под той же лицензией.