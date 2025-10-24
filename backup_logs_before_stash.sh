#!/bin/bash

# Скрипт для резервного копирования логов перед git stash
# Использование: ./backup_logs_before_stash.sh

set -e

# Создаем папку для бэкапа с timestamp
BACKUP_DIR="logs_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🔄 Создаю резервную копию логов в папке: $BACKUP_DIR"

# Копируем важные папки с логами
if [ -d "runs" ] && [ "$(ls -A runs 2>/dev/null)" ]; then
    echo "📁 Копирую папку runs/..."
    cp -r runs "$BACKUP_DIR/"
    echo "✅ Скопировано $(find runs -name "*.json" | wc -l) файлов из runs/"
else
    echo "⚠️  Папка runs/ пуста или не существует"
fi

if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
    echo "📁 Копирую папку logs/..."
    cp -r logs "$BACKUP_DIR/"
    echo "✅ Скопировано $(find logs -name "*.log" | wc -l) файлов из logs/"
else
    echo "⚠️  Папка logs/ пуста или не существует"
fi

if [ -d "output" ] && [ "$(ls -A output 2>/dev/null)" ]; then
    echo "📁 Копирую папку output/..."
    cp -r output "$BACKUP_DIR/"
    echo "✅ Скопировано $(find output -type f | wc -l) файлов из output/"
else
    echo "⚠️  Папка output/ пуста или не существует"
fi

# Копируем файл ratings.json если существует
if [ -f "ratings.json" ]; then
    echo "📄 Копирую ratings.json..."
    cp ratings.json "$BACKUP_DIR/"
    echo "✅ Скопирован ratings.json"
else
    echo "⚠️  Файл ratings.json не найден"
fi

# Создаем файл с информацией о бэкапе
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Резервная копия логов создана: $(date)
Команда git stash: git stash push -m "Stash with logs backup"
Папки в бэкапе:
$(ls -la "$BACKUP_DIR")

Для восстановления логов после git stash pop:
./restore_logs_after_stash.sh $BACKUP_DIR
EOF

echo ""
echo "✅ Резервная копия создана в папке: $BACKUP_DIR"
echo "📝 Информация о бэкапе сохранена в: $BACKUP_DIR/backup_info.txt"
echo ""
echo "Теперь можно безопасно выполнить:"
echo "  git stash push -m 'Stash with logs backup'"
echo ""
echo "Для восстановления логов после git stash pop:"
echo "  ./restore_logs_after_stash.sh $BACKUP_DIR"