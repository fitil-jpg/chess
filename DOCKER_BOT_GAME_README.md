# Запуск игры двух ботов в Docker с логированием

Этот набор файлов позволяет запускать игру между двумя шахматными ботами в Docker-контейнере с детальным логированием всех ходов и событий.

## Файлы

- `Dockerfile.bot-game` - Dockerfile для создания образа с ботами и Xvfb
- `docker-compose.bot-game.yml` - Docker Compose конфигурация
- `run_bot_game_docker.sh` - Скрипт для удобного запуска
- `.env.bot-game` - Файл с переменными окружения по умолчанию

## Быстрый старт

### 1. Простой запуск с настройками по умолчанию

```bash
./run_bot_game_docker.sh
```

Это запустит игру между DynamicBot (белые) и FortifyBot (черные) на 2 игры.

### 2. Запуск с кастомными ботами

```bash
./run_bot_game_docker.sh --white-bot StockfishBot --black-bot DynamicBot --games 5
```

### 3. Запуск с веб-интерфейсом

```bash
./run_bot_game_docker.sh --web
```

### 4. Пересборка образов

```bash
./run_bot_game_docker.sh --clean
```

## Доступные боты

- `StockfishBot` - Использует движок Stockfish
- `DynamicBot` - Мета-бот, комбинирующий несколько стратегий
- `RandomBot` - Случайные ходы с простой оценкой
- `AggressiveBot` - Агрессивная стратегия
- `FortifyBot` - Оборонительная стратегия
- `EndgameBot` - Специализируется на эндшпиле
- `CriticalBot` - Нацелен на критические ходы
- `TrapBot` - Пытается ставить тактические ловушки
- `KingValueBot` - Оценивает позиции по безопасности короля
- `NeuralBot` - Использует нейронную сеть
- `UtilityBot` - Базовые утилиты оценки
- `PieceMateBot` - Ловит фигуры противника

## Логирование

### Где найти логи

- **Детальные логи игры**: `./logs/bot_game_YYYYMMDD_HHMMSS.log`
- **Результаты игр**: `./logs/results_YYYYMMDD_HHMMSS.json`
- **Данные партий**: `./runs/YYYYMMDD_HHMMSS_ffffff.json`

### Что логируется

1. **Детальная информация о каждом ходе**:
   - SAN нотация хода
   - Причина выбора хода (модуль бота)
   - FEN позиции
   - Диаграммы доски в ключевые моменты

2. **События игры**:
   - Переходы между фазами (дебют → миттельшпиль → эндшпиль)
   - Взятия фигур
   - Атаки на "висячие" фигуры
   - Вилки конем/слоном

3. **Статистика производительности**:
   - Средний branching factor
   - Время на игру
   - Использование модулей ботов

4. **Финальные результаты**:
   - Количество побед/поражений/ничьих
   - Общее время игры
   - PGN нотация партий

## Настройка через переменные окружения

Создайте файл `.env` или экспортируйте переменные:

```bash
export WHITE_BOT=StockfishBot
export BLACK_BOT=DynamicBot
export NUM_GAMES=10
export LOG_LEVEL=DEBUG
```

## Прямой запуск через Docker Compose

```bash
# Запуск только игры ботов
docker-compose -f docker-compose.bot-game.yml up --build

# Запуск с веб-интерфейсом
docker-compose -f docker-compose.bot-game.yml --profile web up --build

# Запуск в фоне
docker-compose -f docker-compose.bot-game.yml up -d --build
```

## Мониторинг логов в реальном времени

```bash
# Просмотр логов контейнера
docker-compose -f docker-compose.bot-game.yml logs -f bot-game

# Просмотр логов из файлов
tail -f logs/bot_game_*.log
```

## Структура результатов

### JSON файл результатов (`results_*.json`)

```json
{
  "white_bot": "DynamicBot",
  "black_bot": "FortifyBot", 
  "games_played": 2,
  "wins": 1,
  "losses": 0,
  "draws": 1,
  "total_time": 45.67,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### JSON файл партии (`runs/*.json`)

```json
{
  "moves": ["e4", "e5", "Nf3", "Nc6", ...],
  "fens": ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", ...],
  "modules_w": ["OPENING", "TACTICAL", ...],
  "modules_b": ["DEFENSIVE", "POSITIONAL", ...],
  "result": "1-0"
}
```

## Устранение неполадок

### Проблема: Xvfb не запускается
```bash
# Проверьте, что Xvfb установлен в контейнере
docker run --rm -it chess-bot-game xvfb-run --help
```

### Проблема: Stockfish не найден
```bash
# Убедитесь, что Stockfish доступен
docker run --rm -it chess-bot-game ls -la /app/bin/stockfish-bin
```

### Проблема: Недостаточно памяти
```bash
# Увеличьте лимиты в docker-compose.bot-game.yml
deploy:
  resources:
    limits:
      memory: 4G
```

## Интеграция с веб-интерфейсом

Если вы запустили с флагом `--web`, веб-интерфейс будет доступен по адресу:
- http://localhost:5000

Веб-интерфейс позволяет:
- Просматривать результаты игр
- Запускать новые игры
- Анализировать статистику модулей
- Просматривать ELO рейтинги

## Примеры использования

### Турнир между несколькими ботами

```bash
# Stockfish vs DynamicBot
./run_bot_game_docker.sh --white-bot StockfishBot --black-bot DynamicBot --games 5

# DynamicBot vs FortifyBot  
./run_bot_game_docker.sh --white-bot DynamicBot --black-bot FortifyBot --games 5

# AggressiveBot vs TrapBot
./run_bot_game_docker.sh --white-bot AggressiveBot --black-bot TrapBot --games 3
```

### Анализ производительности

```bash
# Запуск большого количества игр для статистики
./run_bot_game_docker.sh --white-bot DynamicBot --black-bot RandomBot --games 50

# Анализ результатов
python -c "
import json
import glob
results = []
for f in glob.glob('logs/results_*.json'):
    with open(f) as file:
        results.append(json.load(file))
print(f'Всего игр: {sum(r[\"games_played\"] for r in results)}')
"
```