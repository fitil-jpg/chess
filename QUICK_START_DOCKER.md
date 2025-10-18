# Быстрый старт: Игра ботов в Docker

## Что создано

✅ **Dockerfile.bot-game** - Образ с ботами и Xvfb для headless режима  
✅ **docker-compose.bot-game.yml** - Оркестрация контейнеров  
✅ **run_bot_game_docker.sh** - Удобный скрипт запуска  
✅ **DOCKER_BOT_GAME_README.md** - Подробная документация  

## Быстрый запуск

### 1. Простая игра (2 игры, DynamicBot vs FortifyBot)
```bash
./run_bot_game_docker.sh
```

### 2. Кастомные боты
```bash
./run_bot_game_docker.sh --white-bot StockfishBot --black-bot DynamicBot --games 5
```

### 3. С веб-интерфейсом
```bash
./run_bot_game_docker.sh --web
```

## Доступные боты

- `StockfishBot` - Движок Stockfish
- `DynamicBot` - Мета-бот (по умолчанию для белых)
- `FortifyBot` - Оборонительный бот (по умолчанию для черных)
- `RandomBot`, `AggressiveBot`, `EndgameBot`, `CriticalBot`, `TrapBot`, `KingValueBot`, `NeuralBot`, `UtilityBot`, `PieceMateBot`

## Логи

- **Детальные логи**: `./logs/bot_game_YYYYMMDD_HHMMSS.log`
- **Результаты**: `./logs/results_YYYYMMDD_HHMMSS.json`
- **Данные партий**: `./runs/YYYYMMDD_HHMMSS_ffffff.json`

## Что логируется

- 🎯 Каждый ход с SAN нотацией
- 🧠 Причина выбора хода (модуль бота)
- 📊 Диаграммы доски в ключевые моменты
- ⚔️ Взятия фигур и атаки
- 🔄 Переходы между фазами игры
- 📈 Статистика производительности

## Пример вывода

```
2025-10-18 18:25:01,980 [INFO] Game 1 finished | White=DynamicBot vs Black=FortifyBot | Result=1/2-1/2 | Moves=119 (236 ply) | Time=37.25s
2025-10-18 18:25:01,980 [INFO] SAN: 1. e3 d6 2. Qe2 Qd7 3. d3 a6 4. Nd2 c6 5. Nb3 f6...
2025-10-18 18:25:01,980 [INFO] PERF: avg L=23.6 | avg L^2=566.8 over 236 positions
```

## Требования

- Docker и Docker Compose
- 2GB RAM (рекомендуется)
- Linux/macOS/Windows с WSL2

## Устранение неполадок

**Docker не найден**: Установите Docker Desktop  
**Недостаточно памяти**: Увеличьте лимиты в docker-compose.bot-game.yml  
**Xvfb ошибки**: Проверьте, что образ собран с Xvfb  

## Интеграция с веб-интерфейсом

Существующий веб-интерфейс (`web_server.py`) полностью совместим и может быть запущен в том же контейнере для просмотра результатов в браузере.