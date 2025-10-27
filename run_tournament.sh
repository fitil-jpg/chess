#!/bin/bash

# Скрипт для запуска турнира шахматных ботов

echo "=== ЗАПУСК ТУРНИРА ШАХМАТНЫХ БОТОВ ==="

# Создаем необходимые директории
mkdir -p tournament_logs tournament_patterns tournament_stats

# Останавливаем и удаляем предыдущий контейнер если есть
echo "Останавливаем предыдущий контейнер..."
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f docker-compose.tournament.yml down
else
  docker compose -f docker-compose.tournament.yml down || true
fi

# Собираем и запускаем турнир
echo "Собираем Docker образ..."
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f docker-compose.tournament.yml build
else
  docker compose -f docker-compose.tournament.yml build
fi

echo "Запускаем турнир..."
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose -f docker-compose.tournament.yml up
else
  docker compose -f docker-compose.tournament.yml up
fi

# Показываем результаты
echo "=== РЕЗУЛЬТАТЫ ТУРНИРА ==="
# Показать последний отчёт, если существует
latest_report=$(ls -1t tournament_stats/tournament_report_*.txt 2>/dev/null | head -n 1)
if [ -n "$latest_report" ]; then
    echo "Отчет о турнире:"
    cat "$latest_report"
fi

echo "=== ФАЙЛЫ РЕЗУЛЬТАТОВ ==="
echo "Логи: tournament_logs/"
echo "Паттерны: tournament_patterns/"
echo "Статистика: tournament_stats/"

echo "Турнир завершен!"