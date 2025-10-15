# ELO Synchronization System

Система для синхронізації ELO рейтингів ваших шахових ботів з глобальними платформами (Lichess, Chess.com).

## Особливості

- 🔄 **Автоматична синхронізація** ELO рейтингів з Lichess та Chess.com
- 🤖 **Підтримка всіх ботів** з вашого проекту
- 📊 **Web інтерфейс** для моніторингу та управління
- 🐳 **Docker контейнери** для легкого розгортання
- ⏰ **Планувальник** для регулярної синхронізації
- 📈 **Статистика** та історія змін рейтингів
- 🔔 **Сповіщення** про успішні/неуспішні синхронізації

## Швидкий старт

### 1. Налаштування

```bash
# Копіюйте файл конфігурації
cp .env.example .env

# Відредагуйте .env файл, додавши ваші API ключі
nano .env
```

### 2. Запуск з Docker Compose

```bash
# Запустити всі сервіси
docker-compose -f docker-compose.elo-sync.yml up -d

# Переглянути логи
docker-compose -f docker-compose.elo-sync.yml logs -f elo-sync

# Зупинити сервіси
docker-compose -f docker-compose.elo-sync.yml down
```

### 3. Доступ до веб-інтерфейсу

Відкрийте браузер і перейдіть до:
- **HTTP**: http://localhost:8080
- **HTTPS**: https://localhost (якщо налаштовано SSL)

## API Endpoints

### Отримання рейтингів

```bash
# Всі рейтинги
curl http://localhost:8080/api/ratings

# Конкретний бот
curl http://localhost:8080/api/ratings/DynamicBot
```

### Синхронізація

```bash
# Синхронізація з Lichess
curl -X POST http://localhost:8080/api/sync/lichess \
  -H "Content-Type: application/json" \
  -d '{"bot_names": ["DynamicBot", "StockfishBot"]}'

# Синхронізація з Chess.com
curl -X POST http://localhost:8080/api/sync/chesscom \
  -H "Content-Type: application/json" \
  -d '{"bot_names": ["DynamicBot", "StockfishBot"]}'

# Синхронізація з усіх платформ
curl -X POST http://localhost:8080/api/sync/all \
  -H "Content-Type: application/json" \
  -d '{"bot_names": ["DynamicBot", "StockfishBot"]}'
```

### Управління планувальником

```bash
# Статус планувальника
curl http://localhost:8080/api/scheduler/status

# Запуск планувальника
curl -X POST http://localhost:8080/api/scheduler/start

# Зупинка планувальника
curl -X POST http://localhost:8080/api/scheduler/stop
```

## Налаштування

### 1. Отримання API ключів

#### Lichess
1. Перейдіть до https://lichess.org/account/oauth/token
2. Створіть новий токен з правами на читання профілю
3. Додайте токен до `.env` файлу

#### Chess.com
1. Використовуйте ваші звичайні облікові дані Chess.com
2. Додайте їх до `.env` файлу

### 2. Налаштування маппінгу ботів

```python
from chess_ai.elo_sync_manager import ELOSyncManager, ELOPlatform

manager = ELOSyncManager()

# Встановити маппінг для Lichess
manager.set_platform_mapping(ELOPlatform.LICHESS, "DynamicBot", "your_lichess_bot_username")
manager.set_platform_mapping(ELOPlatform.LICHESS, "StockfishBot", "your_stockfish_bot_username")

# Встановити маппінг для Chess.com
manager.set_platform_mapping(ELOPlatform.CHESSCOM, "DynamicBot", "your_chesscom_bot_username")
manager.set_platform_mapping(ELOPlatform.CHESSCOM, "StockfishBot", "your_stockfish_bot_username")
```

### 3. Налаштування планувальника

```python
from chess_ai.elo_scheduler import ELOScheduler, SyncConfig

scheduler = ELOScheduler(manager)

# Додати конфігурацію синхронізації
config = SyncConfig(
    bot_names=["DynamicBot", "StockfishBot"],
    platforms=[ELOPlatform.LICHESS, ELOPlatform.CHESSCOM],
    interval_minutes=60,  # Синхронізація кожну годину
    enabled=True
)
scheduler.add_config("hourly_sync", config)
```

## Структура файлів

```
chess_ai/
├── lichess_api.py          # Lichess API інтеграція
├── chesscom_api.py         # Chess.com API інтеграція
├── elo_sync_manager.py     # Центральний менеджер
└── elo_scheduler.py        # Планувальник синхронізації

scripts/
├── elo_sync.py            # Веб-сервіс
└── start_elo_sync.sh      # Скрипт запуску

Dockerfile.elo-sync         # Docker образ
docker-compose.elo-sync.yml # Docker Compose конфігурація
nginx.conf                  # Nginx конфігурація
.env.example               # Приклад конфігурації
```

## Моніторинг

### Логи

```bash
# Логи синхронізації
docker-compose -f docker-compose.elo-sync.yml logs -f elo-sync

# Логи nginx
docker-compose -f docker-compose.elo-sync.yml logs -f nginx
```

### Файли даних

- `/app/data/ratings.json` - Локальні рейтинги ботів
- `/app/data/sync_config.json` - Конфігурація планувальника
- `/app/logs/elo_sync.log` - Логи сервісу
- `/app/logs/sync_notifications.log` - Логи сповіщень

### Health Check

```bash
curl http://localhost:8080/health
```

## Розширення

### Додавання нових платформ

1. Створіть новий модуль API (наприклад, `chess24_api.py`)
2. Додайте підтримку в `elo_sync_manager.py`
3. Оновіть `ELOPlatform` enum

### Кастомні сповіщення

```python
def custom_notification(config_name: str, results: List[SyncResult]):
    # Ваша логіка сповіщень
    pass

scheduler.add_notification_callback(custom_notification)
```

### Інтеграція з зовнішніми системами

```python
# Webhook для зовнішніх систем
async def webhook_notification(config_name: str, results: List[SyncResult]):
    async with aiohttp.ClientSession() as session:
        await session.post('https://your-webhook-url.com', 
                          json={'config': config_name, 'results': results})

scheduler.add_notification_callback(webhook_notification)
```

## Troubleshooting

### Проблеми з API

1. **Lichess API помилки**: Перевірте валідність токену та права доступу
2. **Chess.com API помилки**: Перевірте облікові дані та rate limits
3. **Rate limiting**: Збільште інтервали синхронізації

### Проблеми з Docker

1. **Контейнер не запускається**: Перевірте логи `docker-compose logs elo-sync`
2. **Немає доступу до файлів**: Перевірте права доступу до volumes
3. **Мережеві проблеми**: Перевірте налаштування nginx

### Проблеми з синхронізацією

1. **Боти не знайдені**: Перевірте маппінг імен ботів
2. **Неправильні рейтинги**: Перевірте API відповіді платформ
3. **Часті помилки**: Збільште retry delays та max_retries

## Безпека

- 🔐 Використовуйте HTTPS в продакшені
- 🔑 Зберігайте API ключі в безпечному місці
- 🛡️ Налаштуйте файрвол для обмеження доступу
- 📝 Регулярно оновлюйте залежності

## Ліцензія

Цей проект використовує ту ж ліцензію, що й основний проект шахових ботів.