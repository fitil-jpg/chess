// Utility to render a chess board from a FEN string with overlay support.
// The module exports a single function `renderFenBoard` that accepts a
// DOM element (or its id), a FEN string and an optional 8x8 overlay grid.
// Each overlay entry is a list of `{type, color}` objects.  The colour is
// applied as a semi-transparent background to the cell.  ``renderFenBoard``
// additionally supports optional *heatmap* overlays and scenario markers.

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

function valueToColor(val) {
  const v = Math.max(0, Math.min(1, Number(val)));
  const r = Math.round(v * 255);
  const g = Math.round((1 - v) * 255);
  return `#${r.toString(16).padStart(2, '0')}${g
    .toString(16)
    .padStart(2, '0')}00`;
}

export function renderFenBoard(target, fen, overlays = [], options = {}) {
  const el = typeof target === 'string' ? document.getElementById(target) : target;
  if (!el) return;
  const { heatmaps = {}, piece = null, scenarios = [] } = options;

  const board = parseFEN(fen);
  el.innerHTML = '';
  el.style.display = 'grid';
  el.style.gridTemplateColumns = 'repeat(8, 60px)';
  el.style.gridTemplateRows = 'repeat(8, 60px)';

  const scenarioMap = {};
  for (const sc of scenarios) {
    if (!scenarioMap[sc.row]) scenarioMap[sc.row] = {};
    scenarioMap[sc.row][sc.col] = sc;
  }

  const heatmapGrid = piece && heatmaps[piece] ? heatmaps[piece] : null;

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
      cell.style.position = 'relative';

      const pieceCh = board[r][c];
      if (pieceCh) cell.textContent = PIECE_UNICODE[pieceCh] || '';

      if (heatmapGrid) {
        const val = heatmapGrid[r] && heatmapGrid[r][c];
        if (val !== null && val !== undefined) {
          cell.style.backgroundColor = valueToColor(val);
          cell.style.opacity = '0.7';
        }
      }

      const overlayItems = overlays[r] && overlays[r][c];
      if (overlayItems && overlayItems.length) {
        // Prefer gradient overlays for background colouring; avoid solid fills for alerts.
        const getType = (item) => (item && typeof item === 'object' && 'type' in item) ? item.type : (Array.isArray(item) ? item[0] : undefined);
        const getColor = (item) => (item && typeof item === 'object' && 'color' in item) ? item.color : (Array.isArray(item) ? item[1] : undefined);

        const gradientItem = overlayItems.find((it) => getType(it) === 'gradient');
        if (gradientItem) {
          const color = getColor(gradientItem);
          if (color) {
            cell.style.backgroundColor = color;
            cell.style.opacity = '0.7';
          }
        }

        // Render non-gradient overlays (e.g., king_attacked) as small markers, not full-cell fills.
        const attackedItem = overlayItems.find((it) => getType(it) === 'king_attacked');
        if (attackedItem) {
          const marker = document.createElement('div');
          marker.style.position = 'absolute';
          marker.style.width = '12px';
          marker.style.height = '12px';
          marker.style.borderRadius = '50%';
          marker.style.backgroundColor = getColor(attackedItem) || 'red';
          marker.style.top = '50%';
          marker.style.left = '50%';
          marker.style.transform = 'translate(-50%, -50%)';
          cell.appendChild(marker);
        }
      }

      if (scenarioMap[r] && scenarioMap[r][c]) {
        const sc = scenarioMap[r][c];
        const marker = document.createElement('div');
        marker.style.position = 'absolute';
        marker.style.width = '12px';
        marker.style.height = '12px';
        marker.style.borderRadius = '50%';
        marker.style.backgroundColor = sc.color || 'red';
        marker.style.top = '50%';
        marker.style.left = '50%';
        marker.style.transform = 'translate(-50%, -50%)';
        cell.appendChild(marker);
      }

      el.appendChild(cell);
    }
  }
}

export function renderAgentMetrics(target, metrics) {
  const el = typeof target === 'string' ? document.getElementById(target) : target;
  if (!el || !metrics) return;
  el.innerHTML = '';

  // Support both a nested ``{white: {}, black: {}}`` structure and a flat
  // ``{metric: value}`` mapping as used by analysis/agent_metrics.json.
  if ('white' in metrics || 'black' in metrics) {
    for (const side of ['white', 'black']) {
      const box = document.createElement('div');
      box.innerHTML = `<h3>${side}</h3>`;
      const data = metrics[side] || {};
      for (const [key, value] of Object.entries(data)) {
        box.innerHTML += `<div>${key}: ${value}</div>`;
      }
      el.appendChild(box);
    }
  } else {
    for (const [key, value] of Object.entries(metrics)) {
      const div = document.createElement('div');
      div.textContent = `${key}: ${value}`;
      el.appendChild(div);
    }
  }
}

export default {
  renderFenBoard,
  renderAgentMetrics
};
