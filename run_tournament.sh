#!/bin/bash

# Скрипт для запуска турнира шахматных ботов

echo "=== ЗАПУСК ТУРНИРА ШАХМАТНЫХ БОТОВ ==="

# Создаем необходимые директории
mkdir -p tournament_logs tournament_patterns tournament_stats

# Останавливаем и удаляем предыдущий контейнер если есть
echo "Останавливаем предыдущий контейнер..."
docker-compose -f docker-compose.tournament.yml down

# Собираем и запускаем турнир
echo "Собираем Docker образ..."
docker-compose -f docker-compose.tournament.yml build

echo "Запускаем турнир..."
docker-compose -f docker-compose.tournament.yml up

# Показываем результаты
echo "=== РЕЗУЛЬТАТЫ ТУРНИРА ==="
if [ -f "tournament_stats/tournament_report_*.txt" ]; then
    echo "Отчет о турнире:"
    cat tournament_stats/tournament_report_*.txt
fi

echo "=== ФАЙЛЫ РЕЗУЛЬТАТОВ ==="
echo "Логи: tournament_logs/"
echo "Паттерны: tournament_patterns/"
echo "Статистика: tournament_stats/"

echo "Турнир завершен!"