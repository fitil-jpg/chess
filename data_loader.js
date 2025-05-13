
const pieceMap = {
  'pawn':   { white: '♙', black: '♟' },
  'rook':   { white: '♖', black: '♜' },
  'knight': { white: '♘', black: '♞' },
  'bishop': { white: '♗', black: '♝' },
  'queen':  { white: '♕', black: '♛' },
  'king':   { white: '♔', black: '♚' }
};

function renderBoard(board) {
  const boardEl = document.getElementById('board');
  boardEl.innerHTML = '';
  for (let row = 0; row < 8; row++) {
    for (let col = 0; col < 8; col++) {
      const cell = document.createElement('div');
      const piece = board[row][col];
      const isWhite = (row + col) % 2 === 0;
      cell.className = 'cell ' + (isWhite ? 'white' : 'black');
      if (piece) {
        const [color, type] = piece.split('-');
        cell.textContent = pieceMap[type]?.[color] || '';
      }
      boardEl.appendChild(cell);
    }
  }
}

function renderMetrics(data) {
  const whiteBox = document.getElementById('white_metrics');
  const blackBox = document.getElementById('black_metrics');
  whiteBox.innerHTML = '<h3>White Metrics</h3>';
  blackBox.innerHTML = '<h3>Black Metrics</h3>';
  for (const key in data.metrics.white) {
    whiteBox.innerHTML += `<div>${key}: ${data.metrics.white[key]}</div>`;
  }
  for (const key in data.metrics.black) {
    blackBox.innerHTML += `<div>${key}: ${data.metrics.black[key]}</div>`;
  }
}

// ✅ fetch with same-directory relative path
fetch("output/position_01.json")
  .then(res => res.json())
  .then(data => {
    renderBoard(data.board);
    renderMetrics(data);
  });
