# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NTEPilot is a game automation tool for a mobile game, automating tasks like fishing and combat via ADB-connected Android emulators. Python backend (FastAPI + Uvicorn) with a React/TypeScript frontend. All frontend-backend communication is over a single WebSocket at `/ws`.

## Commands

### Backend
```powershell
# Install dependencies (from project root)
uv sync

# Run the server (default: 127.0.0.1:9150)
uv run main.py

# With custom host/port
uv run main.py --host 127.0.0.1 --port 9150
```

### Frontend
```powershell
cd frontend
npm install

# Dev server (127.0.0.1:5173) — connects to backend via ?ws= query param
npm run dev

# Production build (outputs to frontend/.static, served by backend)
npm run build

# Mock WebSocket server for frontend-only development
npm run mock:server
```

The frontend dev server needs the backend running. Pass the backend WebSocket URL:
`http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150/ws`

No test runner or linter is configured.

## Architecture

### Data Flow
```
Frontend (React/Vite) ←→ WebSocket (/ws) ←→ api/server.py ←→ NTEPilot/* (business logic) ←→ ADB Device
```

### Key Layers

**`api/`** — WebSocket API server. `server.py` is the single entry point handling all message types. `task_runner.py` executes tasks in daemon threads with hard abort via `PyThreadState_SetAsyncExc`. `scheduler.py` manages daily plans and uses the same task slot as manual runs.

**`NTEPilot/`** — Core business logic package:
- `config/` — Hierarchical JSON config with path-style keys (e.g. `tools.fish.buy_bait`). `framework.py` is the only place to add config fields, defaults, task catalogs, and runner paths.
- `device/` — ADB device layer. `Device` class composes `Screenshot` + `Control` via multiple inheritance. Uses DroidCast APK for screenshots, minitouch for input. Connection retry logic in `connection.py`.
- `tools/` — Tool implementations. Tool and schedule registration lives in `NTEPilot/config/framework.py`. Currently: `fish` (fishing automation).
- `team/` — Character/team management with skill rotation.
- `ui/` — Screen automation. Template matching via OpenCV. `Page` class has A* pathfinding for navigating between game screens.

**`template/`** — PNG image assets for OpenCV template matching. `Template` class in `__init__.py` handles matching. Run `template/update.py` after adding/removing PNGs to regenerate the module's `__init__.py`.

**`frontend/`** — React 19 + Vite 7 + Material Web Components. Three-column layout: instance list, config/tools workspace, log console. Config forms render dynamically from backend schema — no frontend changes needed for new config fields.

**`utils/`** — Shared utilities: `CustomLogger` (Rich-based), image processing (`image.py`), custom exceptions, decorators.

### WebSocket Protocol

All messages are JSON. Key message types:
- `hello` — server sends on connect (instances, status)
- `config.schema` — server sends config field definitions
- `config.update` — client saves config
- `task.start` / `task.stop` — task lifecycle
- `scheduler.catalog` / `scheduler.state` / `scheduler.*` — daily plan catalog, state, and mutations
- `status` — broadcasts active task changes
- `log` — broadcasts log events (with ANSI color from Rich)

### Adding a New Tool

1. Create `NTEPilot/tools/<name>/<name>.py` with the tool class
2. Register the tool in `NTEPilot/config/framework.py` under `CONFIG["tools"]`
3. Add fields/defaults in that same framework entry
4. Frontend auto-discovers tools from the backend schema — no frontend changes needed

Tools are stopped via hard thread abort (`TaskAbort` exception). If a tool holds external resources (ADB forwards, temp files, network), clean them up in a `finally` block.

### Adding a New Config Field

1. Add the field spec and default to `NTEPilot/config/framework.py`
2. Frontend auto-renders it based on type (text → input, integer/float → number input with range, boolean → Switch, select → Select)

### Conventions

- Config keys are lowercase, dot-separated paths: `tools.fish.buy_bait`
- Frontend never hardcodes config fields — always driven by backend `config.schema`
- Tool threads must not touch frontend connection objects directly — use `broadcast_threadsafe()`
- `frontend/.static` is build output — do not edit manually
- The `bin/` directory contains binary dependencies (DroidCast APK, minitouch) — do not modify
