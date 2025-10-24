#!/bin/bash

# Скрипт для восстановления логов после git stash pop
# Использование: ./restore_logs_after_stash.sh <backup_directory>

set -e

if [ $# -eq 0 ]; then
    echo "❌ Ошибка: Укажите папку с резервной копией"
    echo "Использование: $0 <backup_directory>"
    echo ""
    echo "Доступные папки с бэкапами:"
    ls -d logs_backup_* 2>/dev/null || echo "  (папки с бэкапами не найдены)"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Ошибка: Папка '$BACKUP_DIR' не существует"
    exit 1
fi

echo "🔄 Восстанавливаю логи из папки: $BACKUP_DIR"

# Проверяем, что папка содержит файлы бэкапа
if [ ! -f "$BACKUP_DIR/backup_info.txt" ]; then
    echo "❌ Ошибка: Папка '$BACKUP_DIR' не содержит файл backup_info.txt"
    echo "Это не похоже на папку с резервной копией логов"
    exit 1
fi

# Показываем информацию о бэкапе
echo "📋 Информация о резервной копии:"
cat "$BACKUP_DIR/backup_info.txt"
echo ""

# Восстанавливаем папки
if [ -d "$BACKUP_DIR/runs" ]; then
    echo "📁 Восстанавливаю папку runs/..."
    if [ -d "runs" ]; then
        # Создаем резервную копию существующей папки runs
        mv runs "runs_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    fi
    cp -r "$BACKUP_DIR/runs" .
    echo "✅ Восстановлено $(find runs -name "*.json" | wc -l) файлов в runs/"
else
    echo "⚠️  Папка runs/ не найдена в бэкапе"
fi

if [ -d "$BACKUP_DIR/logs" ]; then
    echo "📁 Восстанавливаю папку logs/..."
    if [ -d "logs" ]; then
        # Создаем резервную копию существующей папки logs
        mv logs "logs_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    fi
    cp -r "$BACKUP_DIR/logs" .
    echo "✅ Восстановлено $(find logs -name "*.log" | wc -l) файлов в logs/"
else
    echo "⚠️  Папка logs/ не найдена в бэкапе"
fi

if [ -d "$BACKUP_DIR/output" ]; then
    echo "📁 Восстанавливаю папку output/..."
    if [ -d "output" ]; then
        # Создаем резервную копию существующей папки output
        mv output "output_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
    fi
    cp -r "$BACKUP_DIR/output" .
    echo "✅ Восстановлено $(find output -type f | wc -l) файлов в output/"
else
    echo "⚠️  Папка output/ не найдена в бэкапе"
fi

# Восстанавливаем файл ratings.json
if [ -f "$BACKUP_DIR/ratings.json" ]; then
    echo "📄 Восстанавливаю ratings.json..."
    if [ -f "ratings.json" ]; then
        # Создаем резервную копию существующего файла
        cp ratings.json "ratings_backup_$(date +%Y%m%d_%H%M%S).json" 2>/dev/null || true
    fi
    cp "$BACKUP_DIR/ratings.json" .
    echo "✅ Восстановлен ratings.json"
else
    echo "⚠️  Файл ratings.json не найден в бэкапе"
fi

echo ""
echo "✅ Логи успешно восстановлены!"
echo "📊 Статистика:"
echo "  - Игр в runs/: $(find runs -name "*.json" | wc -l)"
echo "  - Логов в logs/: $(find logs -name "*.log" | wc -l)"
echo "  - Файлов в output/: $(find output -type f | wc -l)"
echo "  - Файл ratings.json: $([ -f "ratings.json" ] && echo "✅ восстановлен" || echo "❌ не найден")"
echo ""
echo "Теперь можно удалить папку с бэкапом:"
echo "  rm -rf $BACKUP_DIR"