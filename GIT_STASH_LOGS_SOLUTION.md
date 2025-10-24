# Решение проблемы с пропадающими логами при git stash

## Проблема

Когда вы делаете `git stash`, пропадают логи игр и остается только 2 игры в статистике. Это происходит потому, что папки `runs/`, `logs/`, `output/` указаны в `.gitignore` и git не сохраняет их содержимое при stash.

## Решения

### 1. Автоматическое решение (Рекомендуется)

Используйте умный скрипт `git_stash_with_logs.sh`:

```bash
# Создать stash с автоматическим бэкапом логов
./git_stash_with_logs.sh stash "Work in progress"

# Восстановить stash и логи
./git_stash_with_logs.sh pop

# Показать доступные stash'и и бэкапы
./git_stash_with_logs.sh list
```

### 2. Ручное решение

Если предпочитаете ручное управление:

```bash
# Перед git stash
./backup_logs_before_stash.sh
git stash push -m "Your message"

# После git stash pop
git stash pop
./restore_logs_after_stash.sh logs_backup_YYYYMMDD_HHMMSS
```

### 3. Изменение .gitignore (Альтернативное решение)

Переключиться на улучшенную версию `.gitignore`, которая сохраняет важные логи:

```bash
# Переключиться на улучшенную версию
./switch_gitignore.sh improved

# Вернуться к оригинальной версии
./switch_gitignore.sh original

# Показать статус
./switch_gitignore.sh status
```

## Что сохраняется

- **runs/**: Файлы игр в формате JSON
- **logs/**: Логи игр и системы
- **output/**: Результаты анализа и турниров
- **ratings.json**: Файл с рейтингами ботов

## Файлы решения

- `git_stash_with_logs.sh` - Основной умный скрипт
- `backup_logs_before_stash.sh` - Ручное создание бэкапа
- `restore_logs_after_stash.sh` - Ручное восстановление
- `switch_gitignore.sh` - Переключение версий .gitignore
- `.gitignore.improved` - Улучшенная версия .gitignore

## Примеры использования

### Создание stash с логами
```bash
# Создать stash с автоматическим бэкапом
./git_stash_with_logs.sh stash "Feature development"

# Или с ручным бэкапом
./backup_logs_before_stash.sh
git stash push -m "Feature development"
```

### Восстановление stash с логами
```bash
# Автоматическое восстановление
./git_stash_with_logs.sh pop

# Или ручное восстановление
git stash pop
./restore_logs_after_stash.sh logs_backup_20250117_143022
```

### Проверка статуса
```bash
# Показать доступные stash'и и бэкапы
./git_stash_with_logs.sh list

# Показать статус .gitignore
./switch_gitignore.sh status
```

## Рекомендации

1. **Используйте автоматическое решение** (`git_stash_with_logs.sh`) для удобства
2. **Регулярно очищайте старые бэкапы** чтобы не засорять диск
3. **Проверяйте статус** перед важными операциями
4. **Создавайте резервные копии** перед экспериментами

## Устранение неполадок

### Если скрипты не работают
```bash
# Сделать скрипты исполняемыми
chmod +x *.sh

# Проверить права доступа
ls -la *.sh
```

### Если логи не восстанавливаются
```bash
# Проверить доступные бэкапы
ls -d logs_backup_*

# Восстановить вручную
./restore_logs_after_stash.sh logs_backup_YYYYMMDD_HHMMSS
```

### Если .gitignore не переключается
```bash
# Создать резервную копию
./switch_gitignore.sh backup

# Переключиться на улучшенную версию
./switch_gitignore.sh improved
```

## Автоматизация

Можно создать алиасы в `.bashrc` или `.zshrc`:

```bash
# Добавить в ~/.bashrc или ~/.zshrc
alias gstash='./git_stash_with_logs.sh stash'
alias gpop='./git_stash_with_logs.sh pop'
alias gstash-list='./git_stash_with_logs.sh list'
```

Тогда можно использовать:
```bash
gstash "Work in progress"
gpop
gstash-list
```