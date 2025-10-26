<<<<<<< HEAD
# Chess Pattern Editor/Viewer

## Overview

The Chess Pattern Editor/Viewer is an advanced chess analysis tool that transforms the basic interactive viewer into a comprehensive pattern detection and analysis system. It automatically identifies interesting chess patterns during bot games and provides tools for categorizing, saving, and analyzing these patterns.

## Features

### 🎯 Pattern Detection
- **Automatic Detection**: Identifies critical moves and positions with multiple viable options during bot games
- **Multi-Bot Analysis**: Compares evaluations from different chess engines to find decisive moments
- **Complexity Analysis**: Measures move complexity based on number of alternatives and piece activity
- **Context Awareness**: Considers game phase, material balance, and position characteristics

### 📊 Pattern Categories
The system automatically categorizes patterns into:
- **Tactical**: Captures, checks, forks, pins, skewers
- **Opening**: Early game patterns and traps
- **Middlegame**: Complex positional and tactical themes
- **Endgame**: Endgame-specific patterns
- **Positional**: Long-term strategic moves
- **Defensive**: Defensive maneuvers and blocks
- **Attacking**: Aggressive moves and combinations

### 💾 Pattern Storage & Management
- **Persistent Storage**: Patterns saved to JSON files for future analysis
- **Search & Filter**: Find patterns by description, tags, or categories
- **Pattern Editing**: Add descriptions, tags, and modify categorization
- **Pattern Deletion**: Remove unwanted patterns from the database

### 🎮 Interactive Interface
- **Real-time Detection**: Patterns detected and displayed as games progress
- **Chess Board Visualization**: Visual representation of pattern positions
- **Detailed Analysis**: View bot evaluations, alternative moves, and game context
- **Scrollable Pattern List**: Browse through all detected patterns
- **Pattern Details Table**: Comprehensive information about each pattern

## Usage

### Starting the Pattern Editor
```bash
python run_pattern_editor.py
```

### Basic Workflow
1. **Start Auto Play**: Click "▶ Start Auto Play" to begin bot games
2. **Pattern Detection**: Patterns are automatically detected and added to the list
3. **Pattern Review**: Click on patterns in the list to view details
4. **Pattern Editing**: Use "✏️ Edit Pattern" to add descriptions and tags
5. **Pattern Management**: Save, edit, or delete patterns as needed

### Game Controls
- **▶ Start Auto Play**: Begin automatic game playing with pattern detection
- **⏸ Pause**: Pause the current game session
- **⏹ Stop**: Stop all games and pattern detection
- **🔄 Reset**: Reset the system to initial state

### Pattern Management
- **💾 Save Pattern**: Save current pattern with any modifications
- **✏️ Edit Pattern**: Open dialog to edit pattern details
- **🗑️ Delete Pattern**: Remove pattern from storage
- **Search**: Filter patterns by text search
- **Category Filter**: Filter patterns by category

## Pattern Data Structure

Each detected pattern contains:

```python
{
    "id": "unique_pattern_id",
    "position_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "move_san": "e4",
    "move_uci": "e2e4",
    "categories": ["opening", "tactical"],
    "confidence": 0.85,
    "piece_positions": {
        "P": ["a2", "b2", "c2", "d2", "f2", "g2", "h2"],
        "R": ["a1", "h1"],
        # ... other pieces
    },
    "heatmap_influences": {
        "e4": 0.8,
        "d4": 0.6,
        # ... other squares
    },
    "bot_evaluations": {
        "StockfishBot": {
            "confidence": 0.9,
            "evaluation_score": 0.2,
            "reason": "Opening principle"
        }
    },
    "alternative_moves": [
        {
            "move_san": "d4",
            "move_uci": "d2d4",
            "is_capture": false,
            "is_check": false,
            "evaluation_score": 0.15
        }
    ],
    "game_context": {
        "move_number": 1,
        "turn": "white",
        "material_balance": 0,
        "game_phase": "opening"
    },
    "timestamp": 1640995200.0,
    "description": "King's pawn opening - central control",
    "tags": ["e4", "opening", "central-control"]
}
```

## Configuration

### Bot Selection
The system uses two bots by default:
- **White**: StockfishBot (if available, falls back to RandomBot)
- **Black**: DynamicBot (if available, falls back to RandomBot)

### Pattern Detection Thresholds
- **Minimum Alternatives**: 3 (minimum legal moves to consider pattern)
- **Confidence Threshold**: 0.6 (minimum confidence to save pattern)
- **Evaluation Threshold**: 0.5 (minimum evaluation difference for significance)

### Storage Location
Patterns are stored in the `patterns/` directory as JSON files.

## Technical Details

### Architecture
- **PatternDetector**: Core pattern detection logic
- **PatternStorage**: Handles saving/loading patterns to/from disk
- **GameWorker**: Background thread for playing games and detecting patterns
- **PatternEditorViewer**: Main GUI application
- **ChessBoardWidget**: Custom widget for displaying chess positions

### Dependencies
- **PySide6**: GUI framework
- **python-chess**: Chess logic and board representation
- **Standard Library**: JSON, threading, pathlib, etc.

### Performance
- Games run in background threads to keep UI responsive
- Pattern detection is optimized for real-time analysis
- JSON storage provides fast loading and saving

## Troubleshooting

### Common Issues

1. **Grayed Out Start Button**: Fixed in this version - button should be enabled on startup
2. **No Patterns Detected**: Check that bots are properly initialized and games are running
3. **Import Errors**: Ensure PySide6 and python-chess are installed
4. **Stockfish Not Found**: Set STOCKFISH_PATH environment variable or place binary in bin/

### Error Messages
- Check the console output for detailed error messages
- Enable debug logging by setting logging level to DEBUG

## Future Enhancements

Potential improvements for future versions:
- **Machine Learning**: Train models on detected patterns for better classification
- **Pattern Matching**: Find similar patterns in databases
- **Export/Import**: Share pattern collections between users
- **Advanced Visualization**: Heatmaps and arrow overlays on the board
- **Pattern Statistics**: Analytics on pattern frequency and success rates
- **Integration**: Connect with chess databases and opening books

## Contributing

To contribute to the pattern editor:
1. Follow the existing code style and patterns
2. Add comprehensive docstrings and comments
3. Test new features thoroughly
4. Update this README for any new functionality

## License

This pattern editor is part of the chess analysis project and follows the same licensing terms.
=======
# Chess Pattern Editor & Viewer

Инструмент для автоматического обнаружения и каталогизации интересных шахматных паттернов во время игр ботов.

## Возможности

### 🎯 Автоматическое обнаружение паттернов
- **Тактические моменты** - позиции с резкими изменениями оценки (>1.5 пешки)
- **Вилки** - ситуации где конь или слон атакует две ценные фигуры
- **Связки** - фигуры прикованные к королю
- **Висячие фигуры** - атакованные но не защищенные фигуры
- **Критические решения** - позиции с множеством альтернатив
- **Дебютные трюки** - необычные ходы в дебюте
- **Эндшпильная техника** - важные позиции в окончаниях
- **Жертвы** - позиционные жертвы материала

### 📚 Библиотека паттернов
- Сохранение обнаруженных паттернов в постоянную библиотеку
- Фильтрация по типам паттернов
- Просмотр паттернов на интерактивной доске
- Удаление ненужных паттернов
- Экспорт паттернов в PGN формат

### 🔍 Анализ паттернов
Для каждого паттерна сохраняется:
- **FEN позиции** - точная позиция на доске
- **Ход** - ход который создал паттерн
- **Типы паттерна** - классификация (тактика, вилка, и т.д.)
- **Описание** - текстовое описание паттерна
- **Влияющие фигуры** - фигуры которые влияют на хитмап хода
- **Оценка** - изменение оценки позиции
- **Метаданные** - номер партии, номер хода, цвет, и т.д.

## Запуск

### Основной способ
```bash
python3 run_pattern_editor.py
```

### Прямой запуск
```bash
python3 pattern_editor_viewer.py
```

## Использование

### 1. Обнаружение паттернов (вкладка Pattern Detection)

1. **Настройте параметры:**
   - Количество игр (1-50)
   - Бот за белых (StockfishBot, DynamicBot, RandomBot, AggressiveBot)
   - Бот за черных

2. **Запустите игры:**
   - Нажмите "▶ Start Auto Play" (зеленая кнопка)
   - Игры будут играться автоматически
   - Паттерны будут обнаруживаться в реальном времени

3. **Управление процессом:**
   - "⏸ Pause" - приостановить обнаружение
   - "⏹ Stop" - полностью остановить

4. **Просмотр обнаруженных паттернов:**
   - Кликните на паттерн в списке "Detected Patterns"
   - Позиция отобразится на доске слева
   - Информация о паттерне появится под доской

5. **Сохранение паттернов:**
   - Нажмите "💾 Save Detected Patterns to Library"
   - Паттерны сохранятся в `patterns/catalog.json`

### 2. Библиотека паттернов (вкладка Pattern Library)

1. **Фильтрация паттернов:**
   - Отметьте нужные типы паттернов
   - Список автоматически обновится
   - "Select All" / "Clear All" для быстрого выбора

2. **Просмотр паттернов:**
   - Кликните на паттерн в библиотеке
   - Позиция отобразится на доске
   - Детальная информация под доской

3. **Управление библиотекой:**
   - "🗑 Delete Pattern" - удалить выбранный паттерн
   - "📤 Export to PGN" - экспортировать паттерны в PGN
   - "🗑 Clear Library" - очистить всю библиотеку

### 3. Статистика (вкладка Statistics)

Просмотр статистики по всей библиотеке:
- Общее количество паттернов
- Распределение по типам
- Среднее изменение оценки
- Количество дебютных/эндшпильных паттернов

## Структура файлов

```
patterns/
  ├── catalog.json      # Основной каталог паттернов
  └── export.pgn        # Экспортированные паттерны (при экспорте)
```

## Формат паттерна (JSON)

```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": "Nf3",
  "pattern_types": ["opening_trick", "critical_decision"],
  "description": "Unusual opening move; Critical position with many alternatives",
  "influencing_pieces": [
    {
      "square": "e2",
      "piece": "Pawn",
      "color": "white",
      "relationship": "defender"
    }
  ],
  "evaluation": {
    "before": {"total": 0},
    "after": {"total": 15},
    "change": 15
  },
  "metadata": {
    "game_id": 0,
    "fullmove_number": 1,
    "turn": "white",
    "is_capture": false,
    "is_check": false,
    "added_at": "2025-10-24T10:30:00"
  }
}
```

## Типы паттернов

| Тип | Описание | Критерии обнаружения |
|-----|----------|---------------------|
| `tactical_moment` | Тактический момент | Изменение оценки > 150 сантипешек |
| `fork` | Вилка | Конь/слон атакует 2+ ценные фигуры |
| `pin` | Связка | Фигура прикована к королю |
| `hanging_piece` | Висячая фигура | Атакована но не защищена |
| `critical_decision` | Критическое решение | Много альтернатив (>5) |
| `opening_trick` | Дебютный трюк | Необычный ход в первых 10 ходах |
| `endgame_technique` | Эндшпильная техника | Эндшпиль + оценка > 200 |
| `sacrifice` | Жертва | Улучшение оценки несмотря на висячую фигуру |

## Использование паттернов

Обнаруженные паттерны можно использовать для:

1. **Обучения ботов** - использовать паттерны для улучшения оценки позиций
2. **Анализа игр** - понимание критических моментов
3. **Создания тренировочных позиций** - экспорт в PGN для изучения
4. **Улучшения PST таблиц** - влияющие фигуры показывают важные позиции
5. **Тактических тренажеров** - база тактических позиций

## Технические детали

### Зависимости
- PySide6 - для GUI
- python-chess - для шахматной логики
- Стандартные библиотеки Python 3.8+

### Архитектура
- `PatternDetector` - обнаружение паттернов во время игр
- `PatternCatalog` - хранение и управление паттернами
- `PatternWorker` - фоновый поток для игр
- `PatternEditorViewer` - главный GUI класс

### Производительность
- Обнаружение паттернов происходит в фоновом потоке
- GUI остается отзывчивым во время игр
- Паттерны сохраняются в JSON для быстрого доступа

## Советы

1. **Начните с небольшого количества игр** (3-5) чтобы понять какие паттерны обнаруживаются
2. **Используйте сильных ботов** (StockfishBot) для более интересных паттернов
3. **Регулярно сохраняйте обнаруженные паттерны** в библиотеку
4. **Фильтруйте паттерны по типу** для целевого анализа
5. **Экспортируйте в PGN** для анализа в других программах

## Решение проблем

### Кнопка "Start Auto Play" неактивна
- Проверьте что путь к Stockfish правильный: `STOCKFISH_PATH` environment variable
- Проверьте что `bin/stockfish-bin` существует

### Паттерны не обнаруживаются
- Убедитесь что боты играют достаточно сильно (не RandomBot vs RandomBot)
- Проверьте что игры достаточно длинные (не мгновенные маты)
- Некоторые позиции могут не соответствовать критериям паттернов

### Библиотека не сохраняется
- Проверьте права на запись в директорию `patterns/`
- Проверьте что диск не заполнен

## Дальнейшее развитие

Возможные улучшения:
- [ ] Добавить машинное обучение для классификации паттернов
- [ ] Интеграция с Stockfish для анализа позиций
- [ ] Визуализация хитмапов влияющих фигур
- [ ] Автоматические рекомендации по улучшению PST таблиц
- [ ] Поиск паттернов по FEN или позиции
- [ ] Сравнение паттернов между разными ботами
- [ ] Экспорт паттернов в обучающие датасеты

## Лицензия

Часть проекта chess AI. См. основной README для лицензии.
>>>>>>> main
