#!/usr/bin/env python3
"""
One-file tournament runner + live web UI (background-capable).

Features:
- Runs the existing headless tournament engine (scripts/tournament.py)
- Optional lightweight Flask web UI with live tournament table and pattern infographics
- Background (daemon) mode to run alongside other Python programs
- Works with both round-robin and single-elimination modes

Usage examples:
  # Round-robin Bo3, serve dashboard on 8080
  python tournament_onefile.py --run --serve --port 8080 --mode rr --bo 3 \
      --agents DynamicBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,RandomBot

  # Single-elimination Bo5 with 1|0 clock, run headless in background
  python tournament_onefile.py --run --daemon --mode se --format bo5 --clock 1|0 \
      --agents DynamicBot,NeuralBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,TrapBot

  # Only serve UI for the latest tournament outputs on 9000
  python tournament_onefile.py --serve --port 9000

Notes:
- The underlying engine writes outputs to output/tournaments/<timestamp>/
- UI reads bracket.json and match_logs.jsonl + patterns/patterns.jsonl from the latest subdirectory
- To run entirely in the background: add --daemon, or use shell backgrounding (&/nohup)
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess

# Flask is optional for headless runs
try:
    from flask import Flask, jsonify, request, Response
    from flask import render_template_string
    HAVE_FLASK = True
except Exception:
    HAVE_FLASK = False

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT_ROOT = ROOT / "output" / "tournaments"


# ------------------------- CLI parsing -------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="One-file tournament runner + UI")
    # High-level actions
    p.add_argument("--run", action="store_true", help="Run the tournament engine")
    p.add_argument("--serve", action="store_true", help="Serve live dashboard (Flask)")
    p.add_argument("--daemon", action="store_true", help="Run in background (detach)")

    # UI options
    p.add_argument("--port", type=int, default=8080, help="Web UI port (default 8080)")

    # Tournament options (forwarded to scripts/tournament.py)
    p.add_argument("--mode", choices=["rr", "se"], default="rr", help="Tournament mode: rr or se")
    p.add_argument("--agents", type=str, default="DynamicBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,RandomBot",
                   help="Comma-separated list of agents")
    p.add_argument("--games", type=int, default=None, help="Exact games per pairing (overrides --bo)")
    p.add_argument("--bo", type=int, default=3, choices=[1,3,5,7], help="Best-of-N for each pairing")
    p.add_argument("--format", type=str, choices=["bo3","bo5","bo7"], help="Series format label")
    p.add_argument("--max-plies", type=int, default=600, help="Max plies per game (safety cap)")
    p.add_argument("--time", type=int, default=60, help="Per-move timeout seconds (disabled if --clock)")
    p.add_argument("--clock", type=str, default=None, help="Per-player chess clock M|inc (minutes|increment)")
    p.add_argument("--tiebreaks", type=str, choices=["on","off"], default="on", help="Tie-breaks on/off")
    p.add_argument("--tag", type=str, default=None, help="Optional tag for metadata")
    p.add_argument("--out-root", type=str, default=str(DEFAULT_OUT_ROOT), help="Output root directory")

    # Advanced: allow specifying a particular tournament directory to serve
    p.add_argument("--out-dir", type=str, default=None, help="Specific tournament directory to serve")

    return p.parse_args(argv)


# ------------------------- Engine orchestration -------------------------

@dataclass
class EngineProcess:
    popen: subprocess.Popen
    outdir: Optional[Path]


def _build_engine_cmd(args: argparse.Namespace) -> List[str]:
    """Build command to run the existing tournament engine as a subprocess."""
    cmd = [sys.executable, "-u", str((ROOT / "scripts" / "tournament.py").resolve())]
    cmd += ["--mode", args.mode]
    cmd += ["--agents", args.agents]
    if args.games is not None:
        cmd += ["--games", str(args.games)]
    else:
        # Respect explicit format if provided, otherwise fallback to --bo
        if args.format:
            cmd += ["--format", args.format]
        else:
            cmd += ["--bo", str(args.bo)]
    cmd += ["--max-plies", str(args.max_plies)]
    if args.clock:
        cmd += ["--clock", args.clock]
    else:
        if args.time and args.time > 0:
            cmd += ["--time", str(args.time)]
    cmd += ["--tiebreaks", args.tiebreaks]
    cmd += ["--out-root", args.out_root]
    if args.tag:
        cmd += ["--tag", args.tag]
    return cmd


def _start_engine_subprocess(args: argparse.Namespace, *, detach: bool) -> EngineProcess:
    """Start the tournament engine as a child process. Returns process and (initial) outdir.

    The engine creates a timestamped directory under out-root; we discover it later for serving.
    """
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    cmd = _build_engine_cmd(args)

    log_dir = out_root / "_onefile_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    stdout_path = log_dir / f"engine_{ts}.out.log"
    stderr_path = log_dir / f"engine_{ts}.err.log"

    stdout_f = open(stdout_path, "a", buffering=1, encoding="utf-8")
    stderr_f = open(stderr_path, "a", buffering=1, encoding="utf-8")

    popen = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=stdout_f,
        stderr=stderr_f,
        preexec_fn=os.setsid if detach else None,
    )
    return EngineProcess(popen=popen, outdir=None)


def _latest_tournament_dir(out_root: Path) -> Optional[Path]:
    try:
        if not out_root.exists():
            return None
        subdirs = [p for p in out_root.iterdir() if p.is_dir() and (p / "bracket.json").exists()]
        if not subdirs:
            # fallback: any dir
            subdirs = [p for p in out_root.iterdir() if p.is_dir()]
        if not subdirs:
            return None
        subdirs.sort(key=lambda p: p.stat().st_mtime)
        return subdirs[-1]
    except Exception:
        return None


# ------------------------- Live Web UI -------------------------

def _create_app(args: argparse.Namespace) -> Flask:
    if not HAVE_FLASK:
        raise RuntimeError("Flask is not installed. Install with: pip install flask")

    app = Flask(__name__)

    OUT_ROOT = Path(args.out_root)
    SPECIFIC_OUT = Path(args.out_dir).resolve() if args.out_dir else None

    def resolve_outdir() -> Optional[Path]:
        if SPECIFIC_OUT:
            return SPECIFIC_OUT if SPECIFIC_OUT.exists() else None
        return _latest_tournament_dir(OUT_ROOT)

    def read_json(path: Path) -> Optional[Dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def tail_jsonl(path: Path, limit: int = 200) -> List[Dict]:
        try:
            if not path.exists():
                return []
            lines: List[str] = []
            with open(path, "r", encoding="utf-8") as f:
                # Efficient tail for reasonably sized files
                for line in f:
                    lines.append(line)
                    if len(lines) > limit:
                        lines.pop(0)
            result: List[Dict] = []
            for line in lines[-limit:]:
                try:
                    result.append(json.loads(line))
                except Exception:
                    continue
            return result
        except Exception:
            return []

    @app.get("/api/outdir")
    def api_outdir() -> Response:
        d = resolve_outdir()
        return jsonify({"outdir": str(d) if d else None})

    @app.get("/api/bracket")
    def api_bracket() -> Response:
        d = resolve_outdir()
        if not d:
            return jsonify({"error": "no tournament directory yet"}), 404
        payload = read_json(d / "bracket.json") or {}
        return jsonify(payload)

    @app.get("/api/logs")
    def api_logs() -> Response:
        d = resolve_outdir()
        limit = int(request.args.get("limit", 100))
        if not d:
            return jsonify([])
        entries = tail_jsonl(d / "match_logs.jsonl", limit=limit)
        return jsonify(entries)

    @app.get("/api/patterns/summary")
    def api_patterns_summary() -> Response:
        d = resolve_outdir()
        if not d:
            return jsonify({"counts": {}, "total": 0})
        patt_path = d / "patterns" / "patterns.jsonl"
        counts: Dict[str, int] = {}
        total = 0
        for row in tail_jsonl(patt_path, limit=100000):
            pat = row.get("pattern") or {}
            types = pat.get("pattern_types") or []
            if isinstance(types, list) and types:
                for t in types:
                    counts[t] = counts.get(t, 0) + 1
                    total += 1
        # Top-N list
        top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        return jsonify({"counts": counts, "total": total, "top": top})

    @app.get("/api/standings")
    def api_standings() -> Response:
        """Compute standings for round-robin from bracket.json pairs."""
        d = resolve_outdir()
        if not d:
            return jsonify({"players": [], "table": []})
        bracket = read_json(d / "bracket.json") or {}
        if bracket.get("type") != "round_robin":
            return jsonify({"players": [], "table": [], "note": "not round_robin"})
        agents: List[str] = bracket.get("agents", [])
        pairs: List[Dict] = bracket.get("pairs", [])
        stats: Dict[str, Dict[str, float]] = {a: {"points": 0.0, "wins": 0, "draws": 0, "losses": 0, "played": 0} for a in agents}
        for p in pairs:
            a = p.get("a"); b = p.get("b")
            pts_a = float(p.get("points_a", 0.0))
            pts_b = float(p.get("points_b", 0.0))
            results = p.get("results", [])
            if a in stats: stats[a]["points"] += pts_a
            if b in stats: stats[b]["points"] += pts_b
            # derive W/D/L per game based on color rotation
            for i, res in enumerate(results):
                white = a if (i % 2 == 0) else b
                black = b if (i % 2 == 0) else a
                if res == "1-0":
                    stats[white]["wins"] += 1; stats[black]["losses"] += 1
                elif res == "0-1":
                    stats[black]["wins"] += 1; stats[white]["losses"] += 1
                else:
                    stats[white]["draws"] += 1; stats[black]["draws"] += 1
                stats[white]["played"] += 1; stats[black]["played"] += 1
        ordered = sorted(((name, s) for name, s in stats.items()), key=lambda x: (-x[1]["points"], -x[1]["wins"], x[0]))
        table = [
            {
                "rank": i+1,
                "name": name,
                "points": round(s["points"], 1),
                "wins": int(s["wins"]),
                "draws": int(s["draws"]),
                "losses": int(s["losses"]),
                "played": int(s["played"]),
            }
            for i, (name, s) in enumerate(ordered)
        ]
        return jsonify({"players": [t[0] for t in ordered], "table": table})

    INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Chess AI Tournament Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background:#f7f7f7; }
    header { background: #222; color: #fff; padding: 12px 16px; }
    main { padding: 16px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 12px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { padding: 8px; border-bottom: 1px solid #eee; text-align: left; }
    th { background: #fafafa; }
    .muted { color: #666; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
    canvas { max-width: 100%; height: 320px; }
    @media (max-width: 960px) { .grid { grid-template-columns: 1fr; } }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <header>
    <h2>Chess AI Tournament Dashboard</h2>
    <div id="outdir" class="muted mono"></div>
  </header>
  <main>
    <div class="grid">
      <div class="card">
        <h3>Round-robin Standings</h3>
        <table id="standings">
          <thead><tr><th>#</th><th>Bot</th><th>Pts</th><th>W</th><th>D</th><th>L</th><th>G</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="card">
        <h3>Points by Bot</h3>
        <canvas id="pointsChart"></canvas>
      </div>
      <div class="card">
        <h3>Pattern Types (counts)</h3>
        <canvas id="patternsChart"></canvas>
      </div>
      <div class="card">
        <h3>Recent Games</h3>
        <pre id="logs" class="mono" style="white-space: pre-wrap; max-height: 340px; overflow: auto;"></pre>
      </div>
    </div>
  </main>
<script>
async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) return null;
  return await res.json();
}

let pointsChart, patternsChart;

async function refreshOutdir() {
  const j = await fetchJSON('/api/outdir');
  const el = document.getElementById('outdir');
  el.textContent = j && j.outdir ? ('Latest directory: ' + j.outdir) : 'Waiting for tournament outputs...';
}

async function refreshStandings() {
  const s = await fetchJSON('/api/standings');
  const tbody = document.querySelector('#standings tbody');
  tbody.innerHTML = '';
  if (!s || !s.table || s.table.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="muted">No round-robin standings yet.</td></tr>';
    return;
  }
  for (const row of s.table) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row.rank}</td><td>${row.name}</td><td>${row.points}</td>`+
                   `<td>${row.wins}</td><td>${row.draws}</td><td>${row.losses}</td><td>${row.played}</td>`;
    tbody.appendChild(tr);
  }
  const labels = s.table.map(r => r.name);
  const pts = s.table.map(r => r.points);
  const ctx = document.getElementById('pointsChart').getContext('2d');
  const data = { labels, datasets: [{ label: 'Points', data: pts, backgroundColor: '#4e79a7' }] };
  if (pointsChart) pointsChart.destroy();
  pointsChart = new Chart(ctx, { type: 'bar', data, options: { responsive: true, plugins: { legend: { display: false } } } });
}

async function refreshPatterns() {
  const p = await fetchJSON('/api/patterns/summary');
  const ctx = document.getElementById('patternsChart').getContext('2d');
  const labels = p && p.counts ? Object.keys(p.counts) : [];
  const vals = p && p.counts ? Object.values(p.counts) : [];
  const data = { labels, datasets: [{ label: 'Patterns', data: vals, backgroundColor: '#f28e2c' }] };
  if (patternsChart) patternsChart.destroy();
  patternsChart = new Chart(ctx, { type: 'bar', data, options: { responsive: true, plugins: { legend: { display: false } } } });
}

async function refreshLogs() {
  const rows = await fetchJSON('/api/logs?limit=50');
  const el = document.getElementById('logs');
  if (!rows || rows.length === 0) { el.textContent = 'No games yet.'; return; }
  const lines = rows.map(r => `${r.pair.a} vs ${r.pair.b}  G${r.game_index}  ${r.white} vs ${r.black}  → ${r.result}${r.tiebreak ? ' (TB)' : ''}`);
  el.textContent = lines.join('\n');
}

async function tick() {
  await refreshOutdir();
  await refreshStandings();
  await refreshPatterns();
  await refreshLogs();
}

setInterval(tick, 5000);
window.addEventListener('load', tick);
</script>
</body>
</html>
    """

    @app.get("/")
    def index() -> Response:
        return render_template_string(INDEX_HTML)

    return app


# ------------------------- Daemonization helpers -------------------------

def _daemonize(argv: List[str]) -> int:
    """Re-exec self in background, returning child PID; parent exits 0.

    Implementation: spawn a subprocess with detached session (setsid), redirect stdio to files.
    """
    out_root = Path(parse_args(argv).out_root)
    log_dir = out_root / "_onefile_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    stdout_path = log_dir / f"daemon_{ts}.out.log"
    stderr_path = log_dir / f"daemon_{ts}.err.log"

    stdout_f = open(stdout_path, "a", buffering=1, encoding="utf-8")
    stderr_f = open(stderr_path, "a", buffering=1, encoding="utf-8")

    # Remove --daemon from argv for the child
    child_argv = [a for a in argv if a != "--daemon"]

    proc = subprocess.Popen(
        [sys.executable, "-u", str(Path(__file__).resolve())] + child_argv,
        cwd=str(ROOT),
        stdout=stdout_f,
        stderr=stderr_f,
        preexec_fn=os.setsid,
    )
    print(f"Started background process PID={proc.pid}")
    return 0


# ------------------------- Main -------------------------

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    if args.daemon:
        # Re-exec in background, then exit parent
        return _daemonize(sys.argv[1:])

    engine_proc: Optional[EngineProcess] = None

    # Optionally start tournament engine
    if args.run:
        engine_proc = _start_engine_subprocess(args, detach=False)
        print(f"Tournament engine started (PID={engine_proc.popen.pid})")

    # Optionally start UI
    if args.serve:
        if not HAVE_FLASK:
            print("Flask not installed. Install with: pip install flask", file=sys.stderr)
            return 2
        app = _create_app(args)
        try:
            app.run(host="0.0.0.0", port=args.port, debug=False)
        finally:
            # If we started the engine in this process, shut it down on server exit
            if engine_proc is not None and engine_proc.popen.poll() is None:
                try:
                    os.killpg(os.getpgid(engine_proc.popen.pid), signal.SIGTERM)
                except Exception:
                    try:
                        engine_proc.popen.terminate()
                    except Exception:
                        pass
        return 0

    # If only --run was requested (no UI), optionally wait for completion so foreground users see logs
    if args.run:
        # Stream until process exits
        while True:
            ret = engine_proc.popen.poll() if engine_proc else 0
            if ret is not None:
                return int(ret)
            time.sleep(1.0)
        # unreachable

    # If neither run nor serve requested, just print help
    print("Nothing to do. Use --run, --serve, or both. Add --daemon to background.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
