# 🔥 Chess Heatmap Viewer Guide

## Відповідь на ваше питання

**`visualize_heatmap_matplotlib.py`** - це **просто генератор зображень**, а не інтерактивний переглядач. Вікно закривається одразу, тому що скрипт:
- Генерує PNG файли
- Зберігає їх у папку `heatmap_visualizations/`
- Автоматично закривається після завершення

## 🎯 Доступні способи перегляду heatmap

### 1. 📊 Генератор зображень (що ви запускали)
```bash
python3 visualize_heatmap_matplotlib.py
```
- ✅ Створює PNG файли
- ❌ Не показує інтерактивне вікно
- 📁 Зберігає в `heatmap_visualizations/`

### 2. 🌐 Веб-інтерфейс (рекомендовано)
```bash
python3 open_heatmap_viewer.py
```
- ✅ Інтерактивний переглядач
- ✅ Показує всі фігури
- ✅ Можна перемикати між режимами
- ✅ Відкривається в браузері

### 3. 🖼️ Перегляд згенерованих зображень
```bash
python3 view_generated_heatmaps.py
```
- ✅ Відкриває всі PNG файли
- ✅ Показує в стандартному переглядачі зображень

### 4. 🖥️ Десктоп переглядачі (якщо є графічний інтерфейс)
```bash
python3 run_enhanced_viewer.py      # Розширений переглядач
python3 run_interactive_viewer.py   # Інтерактивний переглядач
```

## 📁 Структура файлів

```
/workspace/
├── visualize_heatmap_matplotlib.py     # Генератор PNG
├── interactive_heatmap_web.html        # Веб-інтерфейс
├── open_heatmap_viewer.py              # Запуск веб-інтерфейсу
├── view_generated_heatmaps.py          # Перегляд PNG
├── heatmap_visualizations/             # Згенеровані зображення
│   ├── pawn_heatmap.png
│   ├── knight_heatmap.png
│   ├── bishop_heatmap.png
│   ├── rook_heatmap.png
│   ├── queen_heatmap.png
│   ├── king_heatmap.png
│   ├── combined_heatmap.png
│   └── all_pieces_heatmap.png
└── heatmap_*.json                      # Дані heatmap
```

## 🚀 Швидкий старт

1. **Згенерувати зображення:**
   ```bash
   python3 visualize_heatmap_matplotlib.py
   ```

2. **Відкрити інтерактивний переглядач:**
   ```bash
   python3 open_heatmap_viewer.py
   ```

3. **Переглянути згенеровані зображення:**
   ```bash
   python3 view_generated_heatmaps.py
   ```

## 💡 Пояснення

- **Генератор** - створює статичні зображення
- **Переглядач** - показує інтерактивний інтерфейс
- **Веб-версія** - працює в браузері без графічного інтерфейсу
- **PNG файли** - можна відкрити в будь-якому переглядачі зображень

Тепер ви знаєте різницю між генератором і переглядачем! 🎉