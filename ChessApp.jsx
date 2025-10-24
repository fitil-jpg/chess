import React, { useState, useEffect } from 'react';
import ChessBoard from './ChessBoard';
import './ChessBoard.css';

/**
 * Головний React додаток для шахової гри з аналітикою
 */
const ChessApp = () => {
  const [gameData, setGameData] = useState({
    currentGame: 0,
    totalGames: 0,
    whiteWins: 0,
    blackWins: 0,
    draws: 0
  });
  const [availableBots, setAvailableBots] = useState([]);
  const [selectedBots, setSelectedBots] = useState({
    white: 'StockfishBot',
    black: 'DynamicBot'
  });
  const [gameHistory, setGameHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [infiniteMode, setInfiniteMode] = useState(true);
  const [currentGameNumber, setCurrentGameNumber] = useState(0);

  // Завантаження доступних ботів
  useEffect(() => {
    const loadBots = async () => {
      try {
        const response = await fetch('/api/bots');
        if (response.ok) {
          const bots = await response.json();
          setAvailableBots(bots);
        }
      } catch (error) {
        console.error('Помилка завантаження ботів:', error);
      }
    };

    loadBots();
  }, []);

  // Завантаження статистики ігор
  useEffect(() => {
    const loadGameStats = async () => {
      try {
        const response = await fetch('/api/games');
        if (response.ok) {
          const games = await response.json();
          const stats = {
            currentGame: currentGameNumber,
            totalGames: games.length,
            whiteWins: games.filter(g => g.result === '1-0').length,
            blackWins: games.filter(g => g.result === '0-1').length,
            draws: games.filter(g => g.result === '1/2-1/2').length
          };
          setGameData(stats);
        }
      } catch (error) {
        console.error('Помилка завантаження статистики:', error);
      }
    };

    loadGameStats();
  }, []);

  // Обробка ходу
  const handleMove = (moveData) => {
    console.log('Хід виконано:', moveData);
    // Тут можна додати додаткову логіку обробки ходу
  };

  // Обробка завершення гри
  const handleGameEnd = (gameEndData) => {
    console.log('Гра закінчена:', gameEndData);
    setGameHistory(prev => [...prev, gameEndData]);
    
    // Оновлюємо статистику
    setGameData(prev => ({
      ...prev,
      totalGames: prev.totalGames + 1,
      whiteWins: gameEndData.result === '1-0' ? prev.whiteWins + 1 : prev.whiteWins,
      blackWins: gameEndData.result === '0-1' ? prev.blackWins + 1 : prev.blackWins,
      draws: gameEndData.result === '1/2-1/2' ? prev.draws + 1 : prev.draws
    }));
    
    // В безкінечному режимі автоматично перезапускаємо гру
    if (infiniteMode) {
      setCurrentGameNumber(prev => prev + 1);
      setTimeout(() => {
        // Автоматичний перезапуск буде оброблений в ChessBoard компоненті
      }, 1000);
    }
  };

  // Зміна ботів
  const handleBotChange = (color, bot) => {
    setSelectedBots(prev => ({
      ...prev,
      [color]: bot
    }));
  };

  return (
    <div className="chess-app">
      <header className="app-header">
        <h1>♟️ Chess AI Analytics Dashboard</h1>
        <p>Інтерактивна аналітика шахових ботів з реальним часом</p>
      </header>

      <div className="app-content">
        {/* Статистика */}
        <div className="stats-panel">
          <h3>📊 Статистика ігор</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{gameData.currentGame}</div>
              <div className="stat-label">Поточна гра</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{gameData.totalGames}</div>
              <div className="stat-label">Всього ігор</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{gameData.whiteWins}</div>
              <div className="stat-label">Перемоги білих</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{gameData.blackWins}</div>
              <div className="stat-label">Перемоги чорних</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{gameData.draws}</div>
              <div className="stat-label">Нічиї</div>
            </div>
          </div>
        </div>

        {/* Налаштування ботів */}
        <div className="bot-settings">
          <h3>🤖 Налаштування ботів</h3>
          <div className="bot-selectors">
            <div className="bot-selector">
              <label>Білі:</label>
              <select 
                value={selectedBots.white} 
                onChange={(e) => handleBotChange('white', e.target.value)}
              >
                {availableBots.map(bot => (
                  <option key={bot} value={bot}>{bot}</option>
                ))}
              </select>
            </div>
            <div className="bot-selector">
              <label>Чорні:</label>
              <select 
                value={selectedBots.black} 
                onChange={(e) => handleBotChange('black', e.target.value)}
              >
                {availableBots.map(bot => (
                  <option key={bot} value={bot}>{bot}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="mode-selector">
            <label>
              <input 
                type="checkbox" 
                checked={infiniteMode}
                onChange={(e) => setInfiniteMode(e.target.checked)}
              />
              ♾️ Безкінечний режим
            </label>
          </div>
        </div>

        {/* Шахова доска */}
        <ChessBoard
          onMove={handleMove}
          onGameEnd={handleGameEnd}
          showMoveHistory={true}
          showAnalytics={true}
          apiEndpoint="/api/game"
          autoPlay={true}
          whiteBot={selectedBots.white}
          blackBot={selectedBots.black}
          infiniteMode={infiniteMode}
        />

        {/* Історія ігор */}
        {gameHistory.length > 0 && (
          <div className="game-history-panel">
            <h3>📋 Останні ігри</h3>
            <div className="history-list">
              {gameHistory.slice(-5).reverse().map((game, index) => (
                <div key={index} className="history-item">
                  <div className="game-info">
                    <span>Гра #{gameHistory.length - index}</span>
                    <span className={`result ${game.result?.replace('/', '-')}`}>
                      {game.result}
                    </span>
                  </div>
                  <div className="game-details">
                    {game.bot && <span>Бот: {game.bot}</span>}
                    {game.confidence && (
                      <span>Впевненість: {Math.round(game.confidence * 100)}%</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChessApp;