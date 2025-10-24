import React, { useState, useEffect, useCallback } from 'react';
import { Chess } from 'chess.js';

/**
 * React компонент шахової дошки з відстеженням ходів
 * Підтримує інтеграцію з Flask API та відображення аналітики
 */
const ChessBoard = ({ 
  onMove = () => {}, 
  onGameEnd = () => {},
  showMoveHistory = true,
  showAnalytics = true,
  apiEndpoint = '/api/game',
  autoPlay = false,
  whiteBot = 'StockfishBot',
  blackBot = 'DynamicBot',
  infiniteMode = false
}) => {
  // Стан гри
  const [game, setGame] = useState(new Chess());
  const [moveHistory, setMoveHistory] = useState([]);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [possibleMoves, setPossibleMoves] = useState([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [gameStatus, setGameStatus] = useState('Готовий до початку гри');
  const [analytics, setAnalytics] = useState({
    whiteModules: [],
    blackModules: [],
    moveTimes: [],
    positionEvals: []
  });

  // Ініціалізація дошки
  const initializeBoard = useCallback(() => {
    const board = [];
    for (let row = 0; row < 8; row++) {
      const boardRow = [];
      for (let col = 0; col < 8; col++) {
        const square = String.fromCharCode(97 + col) + (8 - row);
        const piece = game.get(square);
        boardRow.push({
          square,
          piece,
          color: (row + col) % 2 === 0 ? 'white' : 'black',
          row,
          col
        });
      }
      board.push(boardRow);
    }
    return board;
  }, [game]);

  // Отримання символу фігури
  const getPieceSymbol = (piece) => {
    if (!piece) return '';
    const symbols = {
      'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
      'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
    };
    return symbols[piece.color + piece.type.toUpperCase()] || '';
  };

  // Обробка кліку по клітинці
  const handleSquareClick = useCallback(async (square) => {
    if (isPlaying || game.isGameOver()) return;

    const piece = game.get(square);
    
    // Якщо клікнули на фігуру того ж кольору, що ходить
    if (piece && piece.color === game.turn()) {
      setSelectedSquare(square);
      const moves = game.moves({ square, verbose: true });
      setPossibleMoves(moves.map(move => move.to));
    }
    // Якщо клікнули на можливий хід
    else if (selectedSquare && possibleMoves.includes(square)) {
      try {
        const move = game.move({
          from: selectedSquare,
          to: square,
          promotion: 'q'
        });

        if (move) {
          const moveData = {
            move,
            fen: game.fen(),
            turn: game.turn(),
            isGameOver: game.isGameOver(),
            result: game.isGameOver() ? game.result() : null,
            timestamp: new Date().toISOString()
          };

          setMoveHistory(prev => [...prev, moveData]);
          setSelectedSquare(null);
          setPossibleMoves([]);
          
          onMove(moveData);

          // Перевіряємо чи гра закінчена
          if (game.isGameOver()) {
            setIsPlaying(false);
            setGameStatus(`Гра закінчена: ${getGameResultText(game.result())}`);
            onGameEnd(moveData);
            
            // В безкінечному режимі автоматично перезапускаємо гру
            if (infiniteMode) {
              setTimeout(() => {
                startGame();
              }, 1000);
            }
          } else {
            setGameStatus(`Хід ${game.turn() === 'w' ? 'білих' : 'чорних'}`);
          }

          // Автоматична гра з ботами
          if (autoPlay && !game.isGameOver()) {
            await makeBotMove();
          }
        }
      } catch (error) {
        console.error('Помилка виконання ходу:', error);
      }
    }
  }, [game, selectedSquare, possibleMoves, isPlaying, autoPlay, onMove, onGameEnd]);

  // Зробити хід ботом
  const makeBotMove = useCallback(async () => {
    try {
      const response = await fetch(`${apiEndpoint}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fen: game.fen(),
          turn: game.turn()
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.move) {
          const move = game.move(data.move);
          if (move) {
            const moveData = {
              move,
              fen: game.fen(),
              turn: game.turn(),
              isGameOver: game.isGameOver(),
              result: game.isGameOver() ? game.result() : null,
              timestamp: new Date().toISOString(),
              bot: data.bot,
              confidence: data.confidence
            };

            setMoveHistory(prev => [...prev, moveData]);
            onMove(moveData);

            if (game.isGameOver()) {
              setIsPlaying(false);
              setGameStatus(`Гра закінчена: ${getGameResultText(game.result())}`);
              onGameEnd(moveData);
              
              // В безкінечному режимі автоматично перезапускаємо гру
              if (infiniteMode) {
                setTimeout(() => {
                  startGame();
                }, 1000);
              }
            } else {
              setGameStatus(`Хід ${game.turn() === 'w' ? 'білих' : 'чорних'}`);
            }
          }
        }
      }
    } catch (error) {
      console.error('Помилка ходу бота:', error);
    }
  }, [game, apiEndpoint, onMove, onGameEnd]);

  // Почати гру
  const startGame = useCallback(async () => {
    try {
      const response = await fetch(`${apiEndpoint}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          white_bot: whiteBot,
          black_bot: blackBot,
          infinite_mode: infiniteMode
        })
      });

      if (response.ok) {
        const data = await response.json();
        setGame(new Chess());
        setMoveHistory([]);
        setSelectedSquare(null);
        setPossibleMoves([]);
        setIsPlaying(true);
        setGameStatus(infiniteMode ? 'Безкінечна гра розпочата' : 'Гра розпочата');
        
        if (autoPlay) {
          await makeBotMove();
        }
      }
    } catch (error) {
      console.error('Помилка початку гри:', error);
    }
  }, [apiEndpoint, whiteBot, blackBot, autoPlay, makeBotMove, infiniteMode]);

  // Скинути гру
  const resetGame = useCallback(async () => {
    try {
      await fetch(`${apiEndpoint}/reset`, { method: 'POST' });
      setGame(new Chess());
      setMoveHistory([]);
      setSelectedSquare(null);
      setPossibleMoves([]);
      setIsPlaying(false);
      setGameStatus('Готовий до початку гри');
    } catch (error) {
      console.error('Помилка скидання гри:', error);
    }
  }, [apiEndpoint]);

  // Отримати текст результату гри
  const getGameResultText = (result) => {
    switch (result) {
      case '1-0': return 'Білі виграли';
      case '0-1': return 'Чорні виграли';
      case '1/2-1/2': return 'Нічия';
      default: return 'Невідомий результат';
    }
  };

  // Завантаження аналітики
  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const response = await fetch(`${apiEndpoint}/analytics`);
        if (response.ok) {
          const data = await response.json();
          setAnalytics(data);
        }
      } catch (error) {
        console.error('Помилка завантаження аналітики:', error);
      }
    };

    if (showAnalytics) {
      loadAnalytics();
    }
  }, [apiEndpoint, showAnalytics]);

  const board = initializeBoard();

  return (
    <div className="chess-board-container">
      <div className="chess-board-wrapper">
        <div className="chess-board">
          {board.map((row, rowIndex) =>
            row.map((cell, colIndex) => (
              <div
                key={`${rowIndex}-${colIndex}`}
                className={`chess-square ${cell.color} ${
                  selectedSquare === cell.square ? 'selected' : ''
                } ${
                  possibleMoves.includes(cell.square) ? 'possible-move' : ''
                }`}
                onClick={() => handleSquareClick(cell.square)}
              >
                {cell.piece && (
                  <span className="chess-piece">
                    {getPieceSymbol(cell.piece)}
                  </span>
                )}
                {possibleMoves.includes(cell.square) && (
                  <div className="move-indicator" />
                )}
              </div>
            ))
          )}
        </div>
        
        <div className="game-controls">
          <button 
            onClick={startGame} 
            disabled={isPlaying}
            className="btn btn-primary"
          >
            ▶️ Почати гру
          </button>
          <button 
            onClick={resetGame}
            className="btn btn-secondary"
          >
            🔄 Скинути
          </button>
        </div>
        
        <div className="game-status">
          {gameStatus}
        </div>
      </div>

      {showMoveHistory && (
        <div className="move-history">
          <h3>Історія ходів</h3>
          <div className="moves-list">
            {moveHistory.map((moveData, index) => (
              <div key={index} className="move-item">
                <span className="move-number">{index + 1}.</span>
                <span className="move-notation">{moveData.move.san}</span>
                {moveData.bot && (
                  <span className="move-bot">({moveData.bot})</span>
                )}
                {moveData.confidence && (
                  <span className="move-confidence">
                    {Math.round(moveData.confidence * 100)}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {showAnalytics && (
        <div className="analytics-panel">
          <h3>Аналітика</h3>
          <div className="analytics-content">
            <div className="module-usage">
              <h4>Використання модулів</h4>
              <div className="module-stats">
                <div className="white-modules">
                  <h5>Білі:</h5>
                  {analytics.whiteModules.map((module, index) => (
                    <div key={index} className="module-item">
                      {module.name}: {module.count}
                    </div>
                  ))}
                </div>
                <div className="black-modules">
                  <h5>Чорні:</h5>
                  {analytics.blackModules.map((module, index) => (
                    <div key={index} className="module-item">
                      {module.name}: {module.count}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChessBoard;