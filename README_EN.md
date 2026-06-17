# NTEPilot

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a> · <a href="README_JA.md">日本語</a> · <a href="README_TW.md">繁體中文</a>
</p>
<p>
  <img src="https://count.getloli.com/@NTEPilot?name=NTEPilot&theme=gelbooru-h" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-19.2-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/FastAPI-0.136-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vite-7.2-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-green?style=flat-square" alt="License">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/ADB-Supported-4CAF50?style=flat-square" alt="ADB">
  <img src="https://img.shields.io/badge/OpenCV-4.13-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/ONNX-Inference-005CED?style=flat-square" alt="ONNX">
  <img src="https://img.shields.io/badge/WebSocket-Realtime-FF6F00?style=flat-square" alt="WebSocket">
</p>

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEPilot&theme=dark)](https://github.com/NTEPilot/NTEPilot)

---

## About

NTEPilot is an automation tool designed for *Ering* (异环), connecting to Android emulators via ADB to automate various in-game operations. The project uses a frontend-backend separated architecture: Python + FastAPI handles core logic on the backend, while React + TypeScript builds a modern control panel on the frontend, communicating in real-time via WebSocket.

## Features

<table>
  <tr>
    <td width="50%">
      <h3>Fishing Automation</h3>
      <ul>
        <li>Real-time green progress bar tracking</li>
        <li>Automatic cursor control</li>
        <li>Auto-purchase bait</li>
        <li>Auto-sell fish</li>
        <li>Configurable safe proportion threshold</li>
      </ul>
    </td>
    <td width="50%">
      <h3>Team Management</h3>
      <ul>
        <li>17 characters supported</li>
        <li>Auto E/Q skill cooldown management</li>
        <li>Configurable skill rotation order</li>
        <li>4-member party formation</li>
        <li>Automatic character recognition</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>Combat System</h3>
      <ul>
        <li>Auto combat control</li>
        <li>Skill release management</li>
        <li>Battle state recognition</li>
        <li>Auto-retry mechanism</li>
      </ul>
    </td>
    <td width="50%">
      <h3>Daily Tasks</h3>
      <ul>
        <li>Daily task automation</li>
        <li>Café interactions</li>
        <li>Bond system handling</li>
        <li>House management</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>Screen Recognition</h3>
      <ul>
        <li>OpenCV template matching</li>
        <li>Auto-detect game UI elements</li>
        <li>OCR text recognition (ONNX)</li>
        <li>High-precision image processing</li>
      </ul>
    </td>
    <td width="50%">
      <h3>Page Navigation</h3>
      <ul>
        <li>A* pathfinding algorithm</li>
        <li>Automatic UI switching</li>
        <li>Map location teleport</li>
        <li>Smart route planning</li>
      </ul>
    </td>
  </tr>
</table>

## System Requirements

<table>
  <tr>
    <td><strong>OS</strong></td>
    <td>Windows 10/11</td>
  </tr>
  <tr>
    <td><strong>Python</strong></td>
    <td>3.14 or higher</td>
  </tr>
  <tr>
    <td><strong>Node.js</strong></td>
    <td>18 or higher (development only)</td>
  </tr>
  <tr>
    <td><strong>ADB</strong></td>
    <td>Android Debug Bridge</td>
  </tr>
  <tr>
    <td><strong>Emulator</strong></td>
    <td>LDPlayer, MuMu, BlueStacks, or other Android emulators</td>
  </tr>
</table>

> **Why use an emulator?** If you run the script on the desktop client, the game window must stay in the foreground — meaning you can't touch your mouse or keyboard while it runs. Use an emulator instead.

## Quick Start

Or use the one-click launcher:

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEP-Launcher)](https://github.com/NTEPilot/NTEP-Launcher)

### 1. Clone the Repository

```powershell
git clone https://github.com/NTEPilot/NTEPilot.git
cd NTEPilot
```

### 2. Install Backend Dependencies

```powershell
uv sync
```

### 3. Install Frontend Dependencies

```powershell
cd frontend
npm install
cd ..
```

### 4. Build Frontend

```powershell
cd frontend
npm run build
cd ..
```

Build output goes to `frontend/.static`, automatically served by the backend.

### 5. Start the Service

```powershell
uv run main.py
```

Visit http://127.0.0.1:9150/ to open the control panel.

### 6. Configure the Emulator

Fill in the ADB device serial number in "General Settings" on the control panel, e.g. `127.0.0.1:16448` (port varies by emulator).

## Architecture

<table>
  <tr>
    <th width="20%">Layer</th>
    <th width="40%">Tech Stack</th>
    <th width="40%">Description</th>
  </tr>
  <tr>
    <td><strong>Frontend</strong></td>
    <td>React 19 + TypeScript + Vite 7</td>
    <td>Material Design 3, dynamic config form rendering</td>
  </tr>
  <tr>
    <td><strong>Backend</strong></td>
    <td>Python 3.14 + FastAPI + Uvicorn</td>
    <td>Async WebSocket service, plugin-based tool system</td>
  </tr>
  <tr>
    <td><strong>Communication</strong></td>
    <td>WebSocket JSON Protocol</td>
    <td>Real-time bidirectional, log streaming & status push</td>
  </tr>
  <tr>
    <td><strong>Image</strong></td>
    <td>OpenCV 4.13 + ONNX Runtime</td>
    <td>Template matching, OCR inference, image preprocessing</td>
  </tr>
  <tr>
    <td><strong>Device</strong></td>
    <td>ADB + DroidCast + minitouch</td>
    <td>Device connection, screenshot capture, touch input</td>
  </tr>
</table>

## Development Mode

Run Vite dev server and backend simultaneously:

```powershell
# Terminal 1: Start backend
uv run main.py

# Terminal 2: Start frontend dev server
cd frontend
npm run dev
```

Visit http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150/ws

For frontend-only development, use the built-in mock WebSocket server:

```powershell
# Terminal 1: Start mock server
cd frontend
npm run mock:server

# Terminal 2: Start frontend
npm run dev
```

## Project Structure

```
NTEPilot/
├── main.py                     # Application entry point
├── pyproject.toml              # Python project config
│
├── api/                        # WebSocket API service
│   ├── server.py               # FastAPI app & WebSocket endpoints
│   ├── scheduler.py            # Daily schedule planner
│   └── task_runner.py          # Threaded task executor
│
├── NTEPilot/                   # Core business logic
│   ├── config/                 # Configuration system
│   ├── device/                 # Android device interaction layer
│   ├── tools/                  # Tool implementations (fish/combat/bond/cafe/daily/house)
│   ├── team/                   # Character / team management
│   ├── ui/                     # Screen automation layer
│   ├── map/                    # Map navigation
│   ├── ocr.py                  # OCR text recognition
│   └── instance.py             # Instance management
│
├── template/                   # Template image assets
│   ├── fish/                   # Fishing templates
│   ├── control/                # Combat control templates
│   └── ui/                     # General UI templates
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.tsx             # Main interface
│   │   ├── components/         # UI components
│   │   ├── lib/                # Hooks
│   │   └── types/              # TypeScript types
│   └── vite.config.ts          # Vite config
│
├── bin/                        # Binary dependencies
│   ├── DroidCast/              # Screenshot APK
│   └── Minitouch/              # Touch tool
│
├── instances/                  # Runtime instance configs
└── logs/                       # Runtime logs
```

## Configuration System

Uses path-style keys with nested JSON:

```json
{
  "general": {
    "name": "NTE",
    "serial": "127.0.0.1:16448"
  },
  "tools": {
    "fish": {
      "sell_fish": true,
      "buy_bait": true
    }
  }
}
```

Access in code via `config["tools.fish.buy_bait"]`.

## Supported Characters

| Chinese | English | E Cooldown | Q Cooldown |
|---------|---------|-----------|-----------|
| 零 | Zero | 16s | 15s |
| 早雾 | Sakiri | 16s | 20s |
| 九原 | Jiuyuan | 16s | 15s |
| 哈索尔 | Hathor | 16s | 15s |
| 法帝娅 | Fadia | 16s | 20s |
| 达芙蒂尔 | Daffodill | 16s | 20s |
| 白藏 | Baicang | 14s | 20s |
| 小吱 | Chiz | 3s | 15s |
| 阿德勒 | Adler | 16s | 20s |
| 海月 | Aurelia | 15s | 15s |
| 埃德嘉 | Edgar | 16s | 20s |
| 哈尼娅 | Haniel | 20s | 20s |
| 薄荷 | Mint | 6s | 15s |
| 翳 | Skia | 15s | 15s |
| 娜娜莉 | Nanally | 16s | 15s |
| 浔 | Hotori | 16s | 0s |
| 安魂曲 | Lacrimosa | 16s | 20s |

## Configuration Parameters

### General

| Parameter | Type | Description |
|-----------|------|-------------|
| `general.name` | text | Instance name |
| `general.serial` | text | ADB device serial number |
| `general.client` | select | Client type: Ering / Cloud Ering |

### Fishing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools.fish.sell_fish` | boolean | true | Auto-sell fish when inventory full |
| `tools.fish.buy_bait` | boolean | true | Auto-purchase bait when depleted |
| `tools.fish.buy_bait_stack_count` | number | 5 | Bait stacks per purchase (1-20) |
| `tools.fish.green_bar_safe_proportion` | number | 0.4 | Green bar safe proportion (0-1) |

### Team

| Parameter | Type | Description |
|-----------|------|-------------|
| `team.chara_1` ~ `team.chara_4` | text | Character names in party |
| `team.skill_order` | text | Skill rotation order, e.g. `1E>2E>3E>4E>1A` |

Skill rotation format: `<character_number><skill_type>`, character 1-4, skill type E/Q/A.

## Development Guide

### Adding a New Tool

1. Create the corresponding runner class with task logic
2. Register the task, runner, fields, and defaults in `NTEPilot/config/framework.py`

The frontend auto-discovers and renders new tools — no frontend changes needed.

### Adding a New Character

In `NTEPilot/team/character.py`:

```python
class NewChara(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)

CHINESE_TO_CHARA['新角色'] = NewChara
```

### Updating Template Images

After adding or removing PNG files in `template/`, regenerate the module index:

```powershell
python template/update.py
```

## Related Documentation

- [DEV.md](DEV.md) — Project development docs & module index
- [dev_doc/](dev_doc/) — Detailed development documentation

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE).

## Contributors

<a href="https://github.com/NTEPilot/NTEPilot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=NTEPilot/NTEPilot" />
</a>
