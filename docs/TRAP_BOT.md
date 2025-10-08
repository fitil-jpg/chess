# Trap Bot — Tasks and Executable Spec

This document outlines the implementation plan for interactive trap annotation in the PlayViewer and a dedicated TrapViewer for reviewing and acting on saved trap positions. It also defines the executable entrypoint name and usage.

## Scope Overview

- In-game trap placement in the existing PySide viewer (PlayViewer)
- Separate TrapViewer for filtering, inspecting, and performing actions on saved traps
- Backend-lite persistence (file/SQLite) with optional realtime (WS) updates
- CLI launcher `trap-bot` with subcommands `play` and `review`

---

## Data Model

Trap entity fields (minimum viable):

- `id` (uuid)
- `matchId` (string)
- `round` (int or string)
- `side` ("white" | "black")
- `map` (string) — board variant if applicable
- `fen` (string) — exact position snapshot
- `position` { `file`: 0-7, `rank`: 0-7 } — UI coordinate; can be derived from FEN + clicked square
- `timestamp` (ISO string)
- `trapType` (enum/string)
- `status` ("active" | "cleared")
- `note` (string)

Storage options:

- MVP: JSONL file in `runs/traps.jsonl`
- Next: SQLite DB `runs/traps.db` with indexes on `(matchId, round, side, status, trapType)`

---

## Tasks Breakdown (Epics → Key Tasks)

### 1) Foundations
- Define `Trap` dataclass and validators
- Implement FEN↔UI square helpers; unify coordinate system
- Create persistence layer (JSONL writer/reader); interface abstracted for future SQLite
- Add config entries and paths under `configs/traps.json` where appropriate

### 2) PlayViewer — In-game Trap Placement
- Add a toggled "Trap placing" mode in `pyside_viewer.py`
  - Cursor highlight and cancel (Esc)
  - Click a square → open mini-form (trapType, note, status)
- Implement hotkeys: add/remove last, undo/redo
- Render markers over board cells with icon/color by status/type
- Save trap to storage immediately (optimistic), queue sync
- Optional: debounce batching, retry on write errors

### 3) Backend/API (optional/MVP-light)
- Define REST endpoints (stub/local):
  - `POST /traps`, `GET /traps`, `PATCH /traps/{id}`, `DELETE /traps/{id}`
- WebSocket pub/sub events: `trap_created/updated/deleted`
- Add auth hooks if needed (no-op by default)

### 4) TrapViewer — Review & Actions
- New UI that loads saved traps and supports:
  - Dual modes: Map view (overlay markers) and List view (virtualized table)
  - Filters: match/round/side/type/status/time range
  - Actions: Activate/Deactivate, Edit, Move, Delete, Add note (batch operations)
  - Details side panel with change history
- Realtime updates via WS or polling; optimistic UI
- Export/Import: JSON/CSV with validation and preview

### 5) Quality & Performance
- Marker clustering on zoomed-out views
- Keyboard navigation and accessibility
- Unit tests for model/IO; smoke tests for UI flows
- Ruff lint rules and CI check updates

### 6) Packaging & Release
- Build `trap-bot` launcher (entrypoint)
- Distributable artifacts for Linux; archive with `trap-bot` binary
- User documentation and examples

---

## Executable Spec

- Name: `trap-bot`
- Location (dev): `./dist/trap-bot` after build; (prod): install to `/usr/local/bin/trap-bot`
- Modes (subcommands):
  - `trap-bot play` — launch PlayViewer with trap placing overlay enabled
  - `trap-bot review` — launch TrapViewer for browsing and acting on traps
- Common flags:
  - `--server-url=<url>` (optional) — REST/WS backend
  - `--match-id=<id>` — current match context
  - `--map=<name>` — board/map identifier if applicable
  - `--readonly` — prevent modifications
  - `--dev` — verbose logging/dev tools

### Entry Point Implementation (MVP)

- Add `scripts/trap_bot_cli.py` that parses args and dispatches to:
  - `pyside_viewer.py` with placing mode enabled for `play`
  - `run_viewer.py` or new `trap_viewer.py` for `review`
- Provide a setup shim or a simple `bash` launcher in `scripts/`

---

## README Additions (Trap Bot quickstart)

Include in top-level `README.md` a link to this document and quick commands:

```bash
# Play mode — annotate traps during a session
trap-bot play --match-id demo-001

# Review mode — filter and manage saved traps
trap-bot review --match-id demo-001 --readonly
```

---

## Future Enhancements

- Conflict resolution (optimistic locking; last-write-wins with audit trail)
- Multi-user permissions and roles
- Rich analytics panels and heatmaps derived from traps

