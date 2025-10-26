# 🏆 Быстрый старт турнирной системы

## 🚀 Мгновенный запуск

```bash
# Запустить все сразу
./quick_tournament_start.sh
```

## 📋 Что создано

### Основные файлы
- `tournament_runner.py` - Основной скрипт турнира
- `tournament_pattern_viewer.py` - Вьювер для просмотра результатов
- `Dockerfile.tournament` - Docker образ для турнира
- `docker-compose.tournament.yml` - Конфигурация Docker Compose

### Скрипты запуска
- `run_tournament.sh` - Запуск турнира
- `run_tournament_pattern_viewer.py` - Запуск вьювера
- `test_tournament.py` - Тестирование системы
- `quick_tournament_start.sh` - Быстрый старт

### Конфигурация
- `tournament_config.json` - Настройки турнира
- `TOURNAMENT_README.md` - Подробная документация

## 🎯 Формат турнира

- **Участники**: Все доступные боты (8 ботов)
- **Формат**: Bo3 (лучший из 3 игр)
- **Время**: 3 минуты на игру
- **Всего матчей**: 28 (каждый с каждым)

## 📊 Результаты

### Автоматически создаются:
- `tournament_logs/` - Логи турнира
- `tournament_patterns/` - Сохраненные паттерны
- `tournament_stats/` - Статистика и отчеты

### Просмотр результатов:
```bash
python3 run_tournament_pattern_viewer.py
```

## 🔧 Настройка

### Изменить параметры турнира:
```bash
export GAMES_PER_MATCH=5      # Игр в матче
export TIME_PER_GAME=300      # Секунд на игру
python3 tournament_runner.py
```

### Или отредактировать `tournament_config.json`

## 🐳 Docker запуск

```bash
# Собрать и запустить
docker-compose -f docker-compose.tournament.yml up --build

# Только собрать
docker-compose -f docker-compose.tournament.yml build

# Остановить
docker-compose -f docker-compose.tournament.yml down
```

## 🧪 Тестирование

```bash
# Запустить все тесты
python3 test_tournament.py

# Проверить отдельные компоненты
python3 -c "from tournament_runner import TournamentRunner; print('OK')"
python3 -c "from tournament_pattern_viewer import TournamentPatternViewer; print('OK')"
```

## 📈 Мониторинг

### Логи в реальном времени:
```bash
tail -f tournament_logs/tournament.log
```

### Статистика:
```bash
ls -la tournament_stats/
cat tournament_stats/tournament_report_*.txt
```

## 🎮 Интерфейс вьювера

### Основные функции:
- 📋 Список всех турнирных игр
- 🔍 Фильтрация по ботам и результатам
- 📊 Статистика турнира
- ♟️ Шахматная доска с позициями
- 📝 Список ходов игр
- 💾 Экспорт данных

### Горячие клавиши:
- `F5` - Обновить список
- `Ctrl+E` - Экспорт
- `Del` - Удалить выбранный паттерн

## ⚡ Быстрые команды

```bash
# Полный цикл
./quick_tournament_start.sh

# Только турнир
./run_tournament.sh

# Только просмотр
python3 run_tournament_pattern_viewer.py

# Только тесты
python3 test_tournament.py
```

## 🆘 Помощь

### Если что-то не работает:

1. **Проверьте зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Запустите тесты:**
   ```bash
   python3 test_tournament.py
   ```

3. **Проверьте логи:**
   ```bash
   cat tournament_logs/tournament.log
   ```

4. **Очистите Docker:**
   ```bash
   docker system prune -a
   ```

### Подробная документация:
- `TOURNAMENT_README.md` - Полное описание
- `tournament_config.json` - Настройки
- Логи в `tournament_logs/`

## 🎉 Готово!

Система полностью настроена и готова к работе. Просто запустите:

```bash
./quick_tournament_start.sh
```

И наслаждайтесь турниром! 🏆