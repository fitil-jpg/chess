// Utility to render a chess board from a FEN string with overlay support.
// The module exports a single function `renderFenBoard` that accepts a
// DOM element (or its id), a FEN string and an optional 8x8 overlay grid.
// Each overlay entry is a list of `{type, color}` objects.  The colour is
// applied as a semi-transparent background to the cell.

const PIECE_UNICODE = {
  'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚',
  'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔'
};

function parseFEN(fen) {
  const [placement] = fen.split(' ');
  const rows = placement.split('/');
  const board = [];
  for (const row of rows) {
    const cells = [];
    for (const ch of row) {
      if (/\d/.test(ch)) {
        const empties = parseInt(ch, 10);
        for (let i = 0; i < empties; i++) cells.push(null);
      } else {
        cells.push(ch);
      }
    }
    board.push(cells);
  }
  return board;
}

export function renderFenBoard(target, fen, overlays = []) {
  const el = typeof target === 'string' ? document.getElementById(target) : target;
  if (!el) return;
  const board = parseFEN(fen);
  el.innerHTML = '';
  el.style.display = 'grid';
  el.style.gridTemplateColumns = 'repeat(8, 60px)';
  el.style.gridTemplateRows = 'repeat(8, 60px)';
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const cell = document.createElement('div');
      cell.className = 'cell ' + ((r + c) % 2 === 0 ? 'white' : 'black');
      cell.style.width = '60px';
      cell.style.height = '60px';
      cell.style.display = 'flex';
      cell.style.alignItems = 'center';
      cell.style.justifyContent = 'center';
      cell.style.fontSize = '36px';
      const piece = board[r][c];
      if (piece) cell.textContent = PIECE_UNICODE[piece] || '';
      const overlay = overlays[r] && overlays[r][c];
      if (overlay) {
        // Apply the colour of the last overlay entry.
        const last = overlay[overlay.length - 1];
        cell.style.backgroundColor = last.color;
        cell.style.opacity = '0.7';
      }
      el.appendChild(cell);
    }
  }
}

export function renderAgentMetrics(target, metrics) {
  const el = typeof target === 'string' ? document.getElementById(target) : target;
  if (!el || !metrics) return;
  el.innerHTML = '';
  for (const side of ['white', 'black']) {
    const box = document.createElement('div');
    box.innerHTML = `<h3>${side}</h3>`;
    const data = metrics[side] || {};
    for (const [key, value] of Object.entries(data)) {
      box.innerHTML += `<div>${key}: ${value}</div>`;
    }
    el.appendChild(box);
  }
}

export default {
  renderFenBoard,
  renderAgentMetrics
};
