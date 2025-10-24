#!/bin/bash

# Скрипт для переключения между версиями .gitignore
# Использование: ./switch_gitignore.sh [original|improved|backup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGINAL_GITIGNORE=".gitignore"
IMPROVED_GITIGNORE=".gitignore.improved"
BACKUP_GITIGNORE=".gitignore.backup"

show_help() {
    echo "Скрипт для переключения между версиями .gitignore"
    echo ""
    echo "Использование: $0 [original|improved|backup]"
    echo ""
    echo "Опции:"
    echo "  original  - использовать оригинальную версию (игнорирует все логи)"
    echo "  improved  - использовать улучшенную версию (сохраняет важные логи)"
    echo "  backup    - создать резервную копию текущего .gitignore"
    echo "  status    - показать текущее состояние"
    echo ""
    echo "Примеры:"
    echo "  $0 improved    # Переключиться на улучшенную версию"
    echo "  $0 original    # Вернуться к оригинальной версии"
    echo "  $0 backup      # Создать резервную копию"
    echo "  $0 status      # Показать статус"
}

create_backup() {
    if [ -f "$ORIGINAL_GITIGNORE" ]; then
        cp "$ORIGINAL_GITIGNORE" "$BACKUP_GITIGNORE"
        echo "✅ Создана резервная копия: $BACKUP_GITIGNORE"
    else
        echo "❌ Ошибка: Файл $ORIGINAL_GITIGNORE не найден"
        return 1
    fi
}

switch_to_original() {
    if [ -f "$BACKUP_GITIGNORE" ]; then
        cp "$BACKUP_GITIGNORE" "$ORIGINAL_GITIGNORE"
        echo "✅ Переключено на оригинальную версию .gitignore"
        echo "⚠️  Внимание: Все логи будут игнорироваться git stash"
    else
        echo "❌ Ошибка: Резервная копия $BACKUP_GITIGNORE не найдена"
        echo "Сначала создайте резервную копию: $0 backup"
        return 1
    fi
}

switch_to_improved() {
    if [ -f "$IMPROVED_GITIGNORE" ]; then
        # Создаем резервную копию текущего .gitignore
        if [ -f "$ORIGINAL_GITIGNORE" ]; then
            cp "$ORIGINAL_GITIGNORE" "$BACKUP_GITIGNORE"
            echo "✅ Создана резервная копия текущего .gitignore"
        fi
        
        # Переключаемся на улучшенную версию
        cp "$IMPROVED_GITIGNORE" "$ORIGINAL_GITIGNORE"
        echo "✅ Переключено на улучшенную версию .gitignore"
        echo "✅ Теперь важные логи будут сохраняться при git stash"
    else
        echo "❌ Ошибка: Файл $IMPROVED_GITIGNORE не найден"
        return 1
    fi
}

show_status() {
    echo "📋 Статус .gitignore:"
    echo ""
    
    if [ -f "$ORIGINAL_GITIGNORE" ]; then
        echo "✅ Основной файл: $ORIGINAL_GITIGNORE"
        if grep -q "runs/\*\.tmp" "$ORIGINAL_GITIGNORE" 2>/dev/null; then
            echo "   🔧 Версия: Улучшенная (сохраняет важные логи)"
        elif grep -q "runs/" "$ORIGINAL_GITIGNORE" 2>/dev/null; then
            echo "   ⚠️  Версия: Оригинальная (игнорирует все логи)"
        else
            echo "   ❓ Версия: Неизвестная"
        fi
    else
        echo "❌ Основной файл: $ORIGINAL_GITIGNORE не найден"
    fi
    
    echo ""
    if [ -f "$IMPROVED_GITIGNORE" ]; then
        echo "✅ Улучшенная версия: $IMPROVED_GITIGNORE"
    else
        echo "❌ Улучшенная версия: $IMPROVED_GITIGNORE не найдена"
    fi
    
    if [ -f "$BACKUP_GITIGNORE" ]; then
        echo "✅ Резервная копия: $BACKUP_GITIGNORE"
    else
        echo "❌ Резервная копия: $BACKUP_GITIGNORE не найдена"
    fi
    
    echo ""
    echo "📁 Содержимое папок с логами:"
    echo "  runs/: $(find runs -name "*.json" 2>/dev/null | wc -l) файлов"
    echo "  logs/: $(find logs -name "*.log" 2>/dev/null | wc -l) файлов"
    echo "  output/: $(find output -type f 2>/dev/null | wc -l) файлов"
}

# Основная логика
case "${1:-status}" in
    "original")
        switch_to_original
        ;;
    "improved")
        switch_to_improved
        ;;
    "backup")
        create_backup
        ;;
    "status")
        show_status
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo ""
        show_help
        exit 1
        ;;
esac