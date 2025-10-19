# Chess React Component з відстеженням ходів

Цей проект містить React компонент для шахової дошки з повним відстеженням ходів та інтеграцією з Flask API.

## 🎯 Що це означає?

**ChessBoard.jsx/tsx** - це React компонент, який:
- Відображає інтерактивну шахову дошку
- Відстежує всі ходи в реальному часі
- Інтегрується з Flask API для гри з ботами
- Показує аналітику та статистику ходів

**Шаблон із Chessboard.js** - використовує бібліотеку chess.js для:
- Валідації ходів
- Обробки шахової логіки
- Генерації FEN позицій

**Сторінка Flask/React** - це гібридний підхід:
- Flask сервер надає API для ботів
- React фронтенд відображає UI
- Кожен хід зберігається в базі даних

## 🚀 Як це реалізувати?

### 1. Структура файлів

```
/workspace/
├── ChessBoard.jsx          # React компонент дошки
├── ChessBoard.css          # Стилі компонента
├── ChessApp.jsx            # Головний додаток
├── chess-react-demo.html   # HTML демо
├── web_server.py           # Flask API сервер
└── CHESS_REACT_README.md   # Цей файл
```

### 2. Встановлення залежностей

```bash
# Python залежності (вже в requirements.txt)
pip install flask flask-cors chess

# JavaScript залежності (для React)
npm install react react-dom chess.js
# або використовуйте CDN (як у демо)
```

### 3. Запуск Flask сервера

```bash
python web_server.py --host 0.0.0.0 --port 5000
```

### 4. Відкриття React додатку

Відкрийте `chess-react-demo.html` у браузері або інтегруйте компоненти у ваш React проект.

## 🔧 API Endpoints

### Основні endpoints

- `GET /api/games` - список ігор
- `GET /api/modules` - статистика модулів
- `POST /api/game/start` - почати гру
- `POST /api/game/move` - зробити хід
- `POST /api/game/reset` - скинути гру
- `GET /api/game/analytics` - аналітика гри

### Нові endpoints для відстеження ходів

- `POST /api/game/move/analyze` - аналіз ходу
- `POST /api/game/position/evaluate` - оцінка позиції
- `GET /api/game/analytics` - детальна аналітика

## 📊 Відстеження ходів

### Що відстежується:

1. **Базові дані ходу:**
   - SAN нотація (e.g., "e4", "Nf3")
   - FEN позиція після ходу
   - Час виконання ходу
   - Результат гри

2. **Аналітика ботів:**
   - Який бот зробив хід
   - Рівень впевненості бота
   - Використаний модуль/стратегія

3. **Позиційна оцінка:**
   - Матеріальний баланс
   - Безпека короля
   - Контроль центру
   - Мобільність фігур

### Приклад даних ходу:

```json
{
  "move": {
    "san": "e4",
    "from": "e2",
    "to": "e4"
  },
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "turn": "black",
  "isGameOver": false,
  "timestamp": "2024-01-15T10:30:00.000Z",
  "bot": "StockfishBot",
  "confidence": 0.95,
  "module": "CENTER_CONTROL"
}
```

## 🎮 Використання компонента

### Базове використання:

```jsx
import ChessBoard from './ChessBoard';

function App() {
  const handleMove = (moveData) => {
    console.log('Хід виконано:', moveData);
  };

  const handleGameEnd = (gameEndData) => {
    console.log('Гра закінчена:', gameEndData);
  };

  return (
    <ChessBoard
      onMove={handleMove}
      onGameEnd={handleGameEnd}
      showMoveHistory={true}
      showAnalytics={true}
      autoPlay={true}
      whiteBot="StockfishBot"
      blackBot="DynamicBot"
    />
  );
}
```

### Пропси компонента:

- `onMove` - callback при виконанні ходу
- `onGameEnd` - callback при завершенні гри
- `showMoveHistory` - показувати історію ходів
- `showAnalytics` - показувати аналітику
- `apiEndpoint` - URL API сервера
- `autoPlay` - автоматична гра ботів
- `whiteBot` - бот для білих
- `blackBot` - бот для чорних

## 🔄 Інтеграція з існуючими ботами

Компонент автоматично інтегрується з усіма існуючими ботами:

- **StockfishBot** - UCI движок
- **DynamicBot** - мета-бот
- **RandomBot** - випадкові ходи
- **AggressiveBot** - агресивна гра
- **FortifyBot** - оборонна стратегія
- **EndgameBot** - ендшпіль
- **CriticalBot** - критичні позиції
- **TrapBot** - тактичні пастки
- **KingValueBot** - безпека короля
- **NeuralBot** - нейронна мережа
- **UtilityBot** - утилітарні функції
- **PieceMateBot** - матування фігур

## 📱 Адаптивність

Компонент повністю адаптивний:
- Мобільні пристрої (768px)
- Планшети (1200px)
- Десктоп (1400px+)

## 🎨 Стилізація

Використовується CSS Grid для дошки та Flexbox для UI елементів. Підтримуються:
- Темна/світла тема
- Анімації ходів
- Підсвічування можливих ходів
- Візуальні індикатори

## 🚀 Розширення

### Додавання нових типів аналітики:

```javascript
// У ChessBoard.jsx
const [customAnalytics, setCustomAnalytics] = useState({});

useEffect(() => {
  // Завантаження кастомної аналітики
  loadCustomAnalytics();
}, []);
```

### Інтеграція з зовнішніми API:

```javascript
const analyzeWithExternalAPI = async (position) => {
  const response = await fetch('/api/external/analyze', {
    method: 'POST',
    body: JSON.stringify({ fen: position })
  });
  return response.json();
};
```

## 🐛 Відладка

### Консольні логи:

```javascript
// Увімкніть детальне логування
const DEBUG = true;

if (DEBUG) {
  console.log('Хід виконано:', moveData);
  console.log('Стан гри:', game.fen());
}
```

### Перевірка API:

```bash
# Тест API endpoints
curl -X GET http://localhost:5000/api/status
curl -X POST http://localhost:5000/api/game/start \
  -H "Content-Type: application/json" \
  -d '{"white_bot": "StockfishBot", "black_bot": "DynamicBot"}'
```

## 📈 Продуктивність

- Використовує `useCallback` для оптимізації
- Мемоізація складних обчислень
- Ліниве завантаження аналітики
- Дебаунсинг API запитів

## 🔒 Безпека

- Валідація всіх ходів на сервері
- Sanitization вхідних даних
- CORS налаштування
- Rate limiting для API

## 📚 Документація

- [Chess.js документація](https://github.com/jhlywa/chess.js)
- [React hooks](https://reactjs.org/docs/hooks-intro.html)
- [Flask API](https://flask.palletsprojects.com/)

## 🤝 Внесок

1. Fork проекту
2. Створіть feature branch
3. Commit зміни
4. Push до branch
5. Створіть Pull Request

## 📄 Ліцензія

MIT License - дивіться LICENSE файл для деталей.