# Heatmap Generation System

Ця система дозволяє генерувати хітмапи рухів шахових фігур з FEN позицій та візуалізувати їх.

## Компоненти системи

### 1. R скрипт (основний)
- **Файл**: `analysis/heatmaps/generate_heatmaps.R`
- **Призначення**: Генерація хітмап з CSV даних
- **Використання**: `Rscript analysis/heatmaps/generate_heatmaps.R input.csv [output_dir]`

### 2. Python fallback скрипт
- **Файл**: `analysis/heatmaps/generate_heatmaps_python.py`
- **Призначення**: Альтернативна реалізація на Python (використовується коли R недоступний)
- **Використання**: `python3 analysis/heatmaps/generate_heatmaps_python.py input.csv [output_dir]`

### 3. Python інтеграція
- **Файл**: `utils/integration.py`
- **Функція**: `generate_heatmaps(fens, out_dir, pattern_set, use_wolfram)`
- **Призначення**: Головний API для генерації хітмап з FEN позицій

### 4. Візуалізація
- **Файл**: `visualize_heatmap_matplotlib.py`
- **Призначення**: Створення графічних хітмап за допомогою matplotlib
- **Використання**: `python3 visualize_heatmap_matplotlib.py`

## Як використовувати

### Базове використання

```python
from utils.integration import generate_heatmaps

# FEN позиції для аналізу
fens = [
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
    'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
    # ... більше FEN позицій
]

# Генерація хітмап
result = generate_heatmaps(fens, out_dir='heatmaps', pattern_set='my_analysis')

# Результат містить хітмапи для кожної фігури
pawn_heatmap = result['my_analysis']['pawn']
```

### Генерація з PGN файлів

```python
from analysis.generate_heatmaps_from_wins import generate_heatmaps_from_wins

# Генерація хітмап з виграшних партій
result = generate_heatmaps_from_wins('games.pgn', out_dir='heatmaps')
```

### Візуалізація

```bash
# Створення графічних хітмап
python3 visualize_heatmap_matplotlib.py
```

## Формат даних

### Вхідні дані (CSV)
```csv
fen_id,piece,to
0,pawn,e4
0,knight,f3
0,bishop,c4
```

### Вихідні дані (JSON)
```json
[
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0]
]
```

## Система fallback

1. **R скрипт** (пріоритет) - використовується якщо R встановлений
2. **Python скрипт** (fallback) - використовується якщо R недоступний
3. **Wolfram** (опціонально) - можна увімкнути через `use_wolfram=True`

## Встановлення залежностей

### Python
```bash
pip install python-chess matplotlib
```

### R (опціонально)
```bash
# Встановлення R
sudo apt-get install r-base

# Встановлення пакетів
R -e "install.packages(c('jsonlite', 'dplyr'))"
```

## Тестування

Запустіть тестовий скрипт для перевірки всієї системи:

```bash
python3 test_heatmap_integration.py
```

## Структура файлів

```
analysis/heatmaps/
├── generate_heatmaps.R          # R скрипт
├── generate_heatmaps_python.py  # Python fallback
└── generate_heatmaps.wl         # Wolfram скрипт (опціонально)

utils/
└── integration.py               # Головний API

heatmap_visualizations/          # Згенеровані зображення
├── pawn_heatmap.png
├── knight_heatmap.png
├── combined_heatmap.png
└── all_pieces_heatmap.png
```

## Приклад використання

```python
# Повний приклад
from utils.integration import generate_heatmaps
import matplotlib.pyplot as plt

# 1. Генерація хітмап
fens = ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1']
result = generate_heatmaps(fens, out_dir='my_heatmaps')

# 2. Отримання даних
pawn_data = result['default']['pawn']

# 3. Візуалізація
plt.imshow(pawn_data, cmap='YlOrRd')
plt.title('Pawn Movement Heatmap')
plt.show()
```

## Відомі обмеження

1. R не встановлений за замовчуванням - система автоматично переключається на Python
2. Wolfram Engine потрібен для Wolfram режиму
3. Візуалізація потребує matplotlib

## Підтримка

Система автоматично визначає доступні інструменти та використовує найкращий доступний варіант.