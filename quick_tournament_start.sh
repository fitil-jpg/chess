#!/bin/bash

# Быстрый запуск турнирной системы

echo "=== БЫСТРЫЙ ЗАПУСК ТУРНИРНОЙ СИСТЕМЫ ==="

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker"
    exit 1
fi

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p tournament_logs tournament_patterns tournament_stats

# Запускаем тесты
echo "🧪 Запускаем тесты системы..."
python3 test_tournament.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Система готова к работе!"
    echo ""
    echo "Доступные команды:"
    echo "  ./run_tournament.sh                    - Запустить турнир"
    echo "  python3 run_tournament_pattern_viewer.py - Просмотр результатов"
    echo "  python3 test_tournament.py             - Запустить тесты"
    echo ""
    echo "Для запуска турнира нажмите Enter или введите 'y':"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]] || [[ -z "$response" ]]; then
        echo "🚀 Запускаем турнир..."
        ./run_tournament.sh
    else
        echo "Турнир не запущен. Используйте ./run_tournament.sh для запуска."
    fi
else
    echo "❌ Тесты не пройдены. Проверьте настройку системы."
    exit 1
fi