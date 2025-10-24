#!/bin/bash

# Умный git stash с сохранением логов
# Использование: 
#   ./git_stash_with_logs.sh stash [message]  - создать stash с бэкапом логов
#   ./git_stash_with_logs.sh pop              - восстановить stash и логи
#   ./git_stash_with_logs.sh list             - показать доступные stash'и и бэкапы

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_PREFIX="logs_backup_"
STASH_INFO_FILE=".git_stash_logs_info"

# Функция для создания бэкапа логов
create_logs_backup() {
    local backup_dir="${BACKUP_PREFIX}$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    echo "🔄 Создаю резервную копию логов в папке: $backup_dir"
    
    # Копируем важные папки с логами
    local files_copied=0
    
    if [ -d "runs" ] && [ "$(ls -A runs 2>/dev/null)" ]; then
        echo "📁 Копирую папку runs/..."
        cp -r runs "$backup_dir/"
        files_copied=$((files_copied + $(find runs -name "*.json" | wc -l)))
    fi
    
    if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
        echo "📁 Копирую папку logs/..."
        cp -r logs "$backup_dir/"
        files_copied=$((files_copied + $(find logs -name "*.log" | wc -l)))
    fi
    
    if [ -d "output" ] && [ "$(ls -A output 2>/dev/null)" ]; then
        echo "📁 Копирую папку output/..."
        cp -r output "$backup_dir/"
        files_copied=$((files_copied + $(find output -type f | wc -l)))
    fi
    
    if [ -f "ratings.json" ]; then
        echo "📄 Копирую ratings.json..."
        cp ratings.json "$backup_dir/"
        files_copied=$((files_copied + 1))
    fi
    
    # Создаем файл с информацией о бэкапе
    cat > "$backup_dir/backup_info.txt" << EOF
Резервная копия логов создана: $(date)
Команда git stash: git stash push -m "$1"
Файлов скопировано: $files_copied
Папки в бэкапе:
$(ls -la "$backup_dir")
EOF
    
    echo "$backup_dir"
}

# Функция для восстановления логов
restore_logs() {
    local backup_dir="$1"
    
    if [ ! -d "$backup_dir" ]; then
        echo "❌ Ошибка: Папка '$backup_dir' не существует"
        return 1
    fi
    
    echo "🔄 Восстанавливаю логи из папки: $backup_dir"
    
    # Восстанавливаем папки
    if [ -d "$backup_dir/runs" ]; then
        echo "📁 Восстанавливаю папку runs/..."
        if [ -d "runs" ]; then
            mv runs "runs_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
        fi
        cp -r "$backup_dir/runs" .
    fi
    
    if [ -d "$backup_dir/logs" ]; then
        echo "📁 Восстанавливаю папку logs/..."
        if [ -d "logs" ]; then
            mv logs "logs_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
        fi
        cp -r "$backup_dir/logs" .
    fi
    
    if [ -d "$backup_dir/output" ]; then
        echo "📁 Восстанавливаю папку output/..."
        if [ -d "output" ]; then
            mv output "output_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
        fi
        cp -r "$backup_dir/output" .
    fi
    
    if [ -f "$backup_dir/ratings.json" ]; then
        echo "📄 Восстанавливаю ratings.json..."
        if [ -f "ratings.json" ]; then
            cp ratings.json "ratings_backup_$(date +%Y%m%d_%H%M%S).json" 2>/dev/null || true
        fi
        cp "$backup_dir/ratings.json" .
    fi
    
    echo "✅ Логи успешно восстановлены!"
}

# Основная логика
case "${1:-}" in
    "stash")
        message="${2:-Stash with logs backup}"
        echo "🚀 Создаю git stash с сохранением логов..."
        
        # Создаем бэкап логов
        backup_dir=$(create_logs_backup "$message")
        
        # Сохраняем информацию о бэкапе
        echo "$backup_dir" > "$STASH_INFO_FILE"
        
        # Выполняем git stash
        echo "📦 Выполняю git stash..."
        git stash push -m "$message"
        
        echo ""
        echo "✅ Git stash создан с сообщением: '$message'"
        echo "📁 Логи сохранены в: $backup_dir"
        echo ""
        echo "Для восстановления используйте:"
        echo "  $0 pop"
        ;;
        
    "pop")
        echo "🚀 Восстанавливаю git stash и логи..."
        
        # Проверяем, есть ли информация о последнем бэкапе
        if [ -f "$STASH_INFO_FILE" ]; then
            backup_dir=$(cat "$STASH_INFO_FILE")
            echo "📁 Найден бэкап логов: $backup_dir"
        else
            echo "⚠️  Файл с информацией о бэкапе не найден"
            echo "Доступные папки с бэкапами:"
            ls -d ${BACKUP_PREFIX}* 2>/dev/null || echo "  (папки с бэкапами не найдены)"
            echo ""
            read -p "Введите имя папки с бэкапом (или нажмите Enter для пропуска): " backup_dir
        fi
        
        # Восстанавливаем git stash
        echo "📦 Восстанавливаю git stash..."
        git stash pop
        
        # Восстанавливаем логи если есть бэкап
        if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
            restore_logs "$backup_dir"
            echo ""
            echo "🗑️  Удаляю временный файл с информацией о бэкапе..."
            rm -f "$STASH_INFO_FILE"
            echo ""
            read -p "Удалить папку с бэкапом '$backup_dir'? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf "$backup_dir"
                echo "✅ Папка с бэкапом удалена"
            else
                echo "📁 Папка с бэкапом сохранена: $backup_dir"
            fi
        else
            echo "⚠️  Логи не восстановлены (бэкап не найден)"
        fi
        ;;
        
    "list")
        echo "📋 Доступные git stash'и:"
        git stash list
        echo ""
        echo "📁 Доступные папки с бэкапами логов:"
        ls -d ${BACKUP_PREFIX}* 2>/dev/null || echo "  (папки с бэкапами не найдены)"
        echo ""
        if [ -f "$STASH_INFO_FILE" ]; then
            echo "🔗 Связанный бэкап: $(cat "$STASH_INFO_FILE")"
        fi
        ;;
        
    *)
        echo "Умный git stash с сохранением логов"
        echo ""
        echo "Использование:"
        echo "  $0 stash [message]  - создать stash с бэкапом логов"
        echo "  $0 pop              - восстановить stash и логи"
        echo "  $0 list             - показать доступные stash'и и бэкапы"
        echo ""
        echo "Примеры:"
        echo "  $0 stash 'Work in progress'"
        echo "  $0 pop"
        echo "  $0 list"
        ;;
esac