#!/bin/bash

# Скрипт для запуска игры ботов в Docker с логированием

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Параметры по умолчанию
WHITE_BOT="DynamicBot"
BLACK_BOT="FortifyBot"
NUM_GAMES=2
WEB_INTERFACE=false
CLEAN_BUILD=false

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --white-bot)
            WHITE_BOT="$2"
            shift 2
            ;;
        --black-bot)
            BLACK_BOT="$2"
            shift 2
            ;;
        --games)
            NUM_GAMES="$2"
            shift 2
            ;;
        --web)
            WEB_INTERFACE=true
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --help)
            echo "Использование: $0 [ОПЦИИ]"
            echo ""
            echo "ОПЦИИ:"
            echo "  --white-bot BOT    Бот для белых фигур (по умолчанию: DynamicBot)"
            echo "  --black-bot BOT    Бот для черных фигур (по умолчанию: FortifyBot)"
            echo "  --games N          Количество игр (по умолчанию: 2)"
            echo "  --web              Запустить веб-интерфейс"
            echo "  --clean            Пересобрать образы"
            echo "  --help             Показать эту справку"
            echo ""
            echo "Доступные боты:"
            echo "  - StockfishBot"
            echo "  - DynamicBot"
            echo "  - RandomBot"
            echo "  - AggressiveBot"
            echo "  - FortifyBot"
            echo "  - EndgameBot"
            echo "  - CriticalBot"
            echo "  - TrapBot"
            echo "  - KingValueBot"
            echo "  - NeuralBot"
            echo "  - UtilityBot"
            echo "  - PieceMateBot"
            exit 0
            ;;
        *)
            error "Неизвестная опция: $1"
            echo "Используйте --help для справки"
            exit 1
            ;;
    esac
done

# Создание директорий для логов
log "Создание директорий для логов..."
mkdir -p logs runs output

# Очистка образов если нужно
if [ "$CLEAN_BUILD" = true ]; then
    log "Очистка Docker образов..."
    docker-compose -f docker-compose.bot-game.yml down --rmi all --volumes
fi

# Экспорт переменных окружения
export WHITE_BOT BLACK_BOT NUM_GAMES

log "Настройки игры:"
log "  Белые: $WHITE_BOT"
log "  Черные: $BLACK_BOT"
log "  Игр: $NUM_GAMES"

# Запуск контейнеров
if [ "$WEB_INTERFACE" = true ]; then
    log "Запуск игры ботов с веб-интерфейсом..."
    docker-compose -f docker-compose.bot-game.yml --profile web up --build
else
    log "Запуск игры ботов..."
    docker-compose -f docker-compose.bot-game.yml up --build bot-game
fi

# Проверка результатов
if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
    success "Логи сохранены в директории logs/"
    log "Последние логи:"
    ls -la logs/ | tail -5
fi

if [ -d "runs" ] && [ "$(ls -A runs)" ]; then
    success "Результаты игр сохранены в директории runs/"
    log "Последние результаты:"
    ls -la runs/ | tail -5
fi

success "Игра завершена!"