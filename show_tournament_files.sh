#!/bin/bash

# Скрипт для показа всех созданных файлов турнирной системы

echo "🏆 ТУРНИРНАЯ СИСТЕМА ШАХМАТНЫХ БОТОВ"
echo "=================================="
echo ""

echo "📁 ОСНОВНЫЕ ФАЙЛЫ:"
echo "=================="
ls -la *.py *.sh *.yml *.json *.md | grep tournament | while read line; do
    filename=$(echo $line | awk '{print $9}')
    size=$(echo $line | awk '{print $5}')
    echo "  📄 $filename ($size bytes)"
done

echo ""
echo "📁 ДИРЕКТОРИИ РЕЗУЛЬТАТОВ:"
echo "========================="
for dir in tournament_logs tournament_patterns tournament_stats; do
    if [ -d "$dir" ]; then
        file_count=$(ls -1 "$dir" 2>/dev/null | wc -l)
        echo "  📁 $dir/ ($file_count файлов)"
        ls -la "$dir" | tail -n +2 | while read line; do
            filename=$(echo $line | awk '{print $9}')
            size=$(echo $line | awk '{print $5}')
            if [ "$filename" != "." ] && [ "$filename" != ".." ]; then
                echo "    📄 $filename ($size bytes)"
            fi
        done
    else
        echo "  📁 $dir/ - не создана"
    fi
done

echo ""
echo "🚀 КОМАНДЫ ДЛЯ ЗАПУСКА:"
echo "====================="
echo "  ./quick_tournament_start.sh     - Быстрый старт с тестами"
echo "  ./run_tournament.sh             - Полный турнир"
echo "  python3 demo_tournament.py      - Демонстрация (2 бота)"
echo "  python3 run_tournament_pattern_viewer.py - GUI вьювер"
echo "  python3 test_tournament.py      - Тестирование системы"

echo ""
echo "📊 СТАТУС СИСТЕМЫ:"
echo "================="

# Проверяем зависимости
if python3 -c "import chess" 2>/dev/null; then
    echo "  ✅ python-chess - установлен"
else
    echo "  ❌ python-chess - не установлен"
fi

if python3 -c "import PySide6" 2>/dev/null; then
    echo "  ✅ PySide6 - установлен"
else
    echo "  ❌ PySide6 - не установлен"
fi

if command -v docker &> /dev/null; then
    echo "  ✅ Docker - установлен"
else
    echo "  ❌ Docker - не установлен"
fi

# Проверяем тесты
if python3 test_tournament.py >/dev/null 2>&1; then
    echo "  ✅ Тесты системы - проходят"
else
    echo "  ❌ Тесты системы - не проходят"
fi

echo ""
echo "📖 ДОКУМЕНТАЦИЯ:"
echo "==============="
echo "  📄 README_TOURNAMENT_FINAL.md   - Основная документация"
echo "  📄 TOURNAMENT_README.md         - Подробное описание"
echo "  📄 TOURNAMENT_QUICK_START.md    - Быстрый старт"
echo "  📄 tournament_config.json       - Настройки"

echo ""
echo "🎯 ГОТОВО К ИСПОЛЬЗОВАНИЮ!"
echo "========================="
echo "Для запуска используйте: ./quick_tournament_start.sh"