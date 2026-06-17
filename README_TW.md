# NTEPilot

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a> · <a href="README_JA.md">日本語</a> · <a href="README_TW.md">繁體中文</a>
</p>

<p>
  <img src="https://count.getloli.com/@NTEPilot?name=NTEPilot&theme=moebooru" />
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
  <img src="https://img.shields.io/badge/平台-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/ADB-支援-4CAF50?style=flat-square" alt="ADB">
  <img src="https://img.shields.io/badge/OpenCV-4.13-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/ONNX-推論-005CED?style=flat-square" alt="ONNX">
  <img src="https://img.shields.io/badge/WebSocket-即時通訊-FF6F00?style=flat-square" alt="WebSocket">
</p>

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEPilot&theme=dark)](https://github.com/NTEPilot/NTEPilot)

---

## 專案簡介

NTEPilot 是一款專為《異環》設計的自動化工具，透過 ADB 連接 Android 模擬器，自動執行各類遊戲操作。專案採用前後端分離架構，後端使用 Python + FastAPI 處理核心邏輯，前端使用 React + TypeScript 建構現代化控制台，透過 WebSocket 實現即時雙向通訊。

## 功能模組

<table>
  <tr>
    <td width="50%">
      <h3>釣魚自動化</h3>
      <ul>
        <li>即時追蹤綠色進度條</li>
        <li>自動控制游標位置</li>
        <li>支援自動購買魚餌</li>
        <li>支援自動出售魚類</li>
        <li>可配置安全比例閾值</li>
      </ul>
    </td>
    <td width="50%">
      <h3>隊伍管理</h3>
      <ul>
        <li>支援 17 個角色</li>
        <li>自動管理 E/Q 技能冷卻</li>
        <li>可配置技能循環順序</li>
        <li>支援 4 人隊伍編成</li>
        <li>角色自動識別映射</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>戰鬥系統</h3>
      <ul>
        <li>自動戰鬥控制</li>
        <li>技能釋放管理</li>
        <li>戰鬥狀態識別</li>
        <li>自動重試機制</li>
      </ul>
    </td>
    <td width="50%">
      <h3>每日任務</h3>
      <ul>
        <li>每日任務自動化</li>
        <li>咖啡廳互動</li>
        <li>羈絆系統處理</li>
        <li>房屋管理</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>螢幕識別</h3>
      <ul>
        <li>基於 OpenCV 範本匹配</li>
        <li>自動識別遊戲介面元素</li>
        <li>OCR 文字辨識（ONNX）</li>
        <li>高精度影像處理</li>
      </ul>
    </td>
    <td width="50%">
      <h3>頁面導航</h3>
      <ul>
        <li>A* 尋路演算法</li>
        <li>自動介面切換</li>
        <li>地圖定位傳送</li>
        <li>智慧路徑規劃</li>
      </ul>
    </td>
  </tr>
</table>

## 系統需求

<table>
  <tr>
    <td><strong>運行環境</strong></td>
    <td>Windows 10/11</td>
  </tr>
  <tr>
    <td><strong>Python 版本</strong></td>
    <td>3.14 或更高</td>
  </tr>
  <tr>
    <td><strong>Node.js 版本</strong></td>
    <td>18 或更高（僅開發需要）</td>
  </tr>
  <tr>
    <td><strong>ADB 工具</strong></td>
    <td>Android Debug Bridge</td>
  </tr>
  <tr>
    <td><strong>模擬器</strong></td>
    <td>雷電、MuMu、BlueStacks 等 Android 模擬器</td>
  </tr>
</table>

> **為什麼使用模擬器？** 如果你用桌面端來運行腳本的話，遊戲視窗必須保持在前台，我猜你也不想運行腳本的時候不能動滑鼠鍵盤像個傻寶一樣坐在那吧，所以用模擬器

## 快速開始

或者使用啟動器一鍵啟動

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEP-Launcher)](https://github.com/NTEPilot/NTEP-Launcher)

### 1. 克隆專案

```powershell
git clone https://github.com/NTEPilot/NTEPilot.git
cd NTEPilot
```

### 2. 安裝後端依賴

```powershell
# 使用 uv 安裝依賴並同步虛擬環境
uv sync
```

### 3. 安裝前端依賴

```powershell
cd frontend
npm install
cd ..
```

### 4. 建構前端

```powershell
cd frontend
npm run build
cd ..
```

建構產物輸出到 `frontend/.static`，後端啟動後自動託管。

### 5. 啟動服務

```powershell
uv run main.py
```

訪問 http://127.0.0.1:9150/ 開啟控制台。

### 6. 配置模擬器

在控制台的「通用配置」中填寫 ADB 裝置序號，格式如 `127.0.0.1:16448`（不同模擬器連接埠不同）。

## 技術架構

<table>
  <tr>
    <th width="20%">層級</th>
    <th width="40%">技術棧</th>
    <th width="40%">說明</th>
  </tr>
  <tr>
    <td><strong>前端</strong></td>
    <td>React 19 + TypeScript + Vite 7</td>
    <td>Material Design 3 設計語言，動態配置表單渲染</td>
  </tr>
  <tr>
    <td><strong>後端</strong></td>
    <td>Python 3.14 + FastAPI + Uvicorn</td>
    <td>非同步 WebSocket 服務，插件化工具系統</td>
  </tr>
  <tr>
    <td><strong>通訊</strong></td>
    <td>WebSocket JSON 協定</td>
    <td>即時雙向通訊，支援日誌流、狀態推送</td>
  </tr>
  <tr>
    <td><strong>影像</strong></td>
    <td>OpenCV 4.13 + ONNX Runtime</td>
    <td>範本匹配、OCR 推論、影像前處理</td>
  </tr>
  <tr>
    <td><strong>裝置</strong></td>
    <td>ADB + DroidCast + minitouch</td>
    <td>裝置連接、截圖擷取、觸控輸入</td>
  </tr>
</table>

## 開發模式

前後端分離開發時，可同時運行 Vite 開發伺服器和後端：

```powershell
# 終端 1：啟動後端
uv run main.py

# 終端 2：啟動前端開發伺服器
cd frontend
npm run dev
```

訪問 http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150/ws

如需僅開發前端，可使用內建的 mock WebSocket 伺服器：

```powershell
# 終端 1：啟動 mock 伺服器
cd frontend
npm run mock:server

# 終端 2：啟動前端
npm run dev
```

## 專案結構

```
NTEPilot/
├── main.py                     # 應用程式入口
├── pyproject.toml              # Python 專案配置
│
├── api/                        # WebSocket API 服務
│   ├── server.py               # FastAPI 應用及 WebSocket 端點
│   ├── scheduler.py            # 每日計劃排程器
│   └── task_runner.py          # 執行緒化任務執行器
│
├── NTEPilot/                   # 核心業務邏輯
│   ├── config/                 # 配置系統
│   ├── device/                 # Android 裝置互動層
│   ├── tools/                  # 工具實現（fish/combat/bond/cafe/daily/house）
│   ├── team/                   # 角色/隊伍管理
│   ├── ui/                     # 螢幕自動化層
│   ├── map/                    # 地圖導航
│   ├── ocr.py                  # OCR 文字辨識
│   └── instance.py             # 實例管理
│
├── template/                   # 範本圖片資源
│   ├── fish/                   # 釣魚相關範本
│   ├── control/                # 戰鬥控制範本
│   └── ui/                     # 通用 UI 範本
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.tsx             # 主介面
│   │   ├── components/         # UI 元件
│   │   ├── lib/                # Hooks
│   │   └── types/              # TypeScript 型別
│   └── vite.config.ts          # Vite 配置
│
├── bin/                        # 二進位依賴
│   ├── DroidCast/              # 截圖 APK
│   └── Minitouch/              # 觸控工具
│
├── instances/                  # 運行時實例配置
└── logs/                       # 運行時日誌
```

## 配置系統

配置使用路徑式 key，巢狀 JSON 結構：

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

程式碼中透過 `config["tools.fish.buy_bait"]` 存取。

## 支援的角色

| 中文名 | 英文名 | E 技能冷卻 | Q 技能冷卻 |
|--------|--------|-----------|-----------|
| 零 | Zero | 16s | 15s |
| 早雾 | Sakiri | 16s | 20s |
| 九原 | Jiuyuan | 16s | 15s |
| 哈索爾 | Hathor | 16s | 15s |
| 法帝婭 | Fadia | 16s | 20s |
| 達芙蒂爾 | Daffodill | 16s | 20s |
| 白藏 | Baicang | 14s | 20s |
| 小吱 | Chiz | 3s | 15s |
| 阿德勒 | Adler | 16s | 20s |
| 海月 | Aurelia | 15s | 15s |
| 埃德嘉 | Edgar | 16s | 20s |
| 哈尼婭 | Haniel | 20s | 20s |
| 薄荷 | Mint | 6s | 15s |
| 翳 | Skia | 15s | 15s |
| 娜娜莉 | Nanally | 16s | 15s |
| 潯 | Hotori | 16s | 0s |
| 安魂曲 | Lacrimosa | 16s | 20s |

## 配置參數

### 通用配置

| 參數 | 型別 | 說明 |
|------|------|------|
| `general.name` | text | 實例名稱 |
| `general.serial` | text | ADB 裝置序號 |
| `general.client` | select | 用戶端類型：異環 / 雲·異環 |

### 釣魚配置

| 參數 | 型別 | 預設值 | 說明 |
|------|------|--------|------|
| `tools.fish.sell_fish` | boolean | true | 釣滿後自動賣魚 |
| `tools.fish.buy_bait` | boolean | true | 魚餌用完自動購買 |
| `tools.fish.buy_bait_stack_count` | number | 5 | 每次購買魚餌組數（1-20） |
| `tools.fish.green_bar_safe_proportion` | number | 0.4 | 綠條安全比例（0-1） |

### 隊伍配置

| 參數 | 型別 | 說明 |
|------|------|------|
| `team.chara_1` ~ `team.chara_4` | text | 隊伍中的角色名稱 |
| `team.skill_order` | text | 技能循環順序，如 `1E>2E>3E>4E>1A` |

技能循環格式：`<角色編號><技能類型>`，角色編號 1-4，技能類型 E/Q/A。

## 開發指南

### 新增工具

1. 建立對應 runner 類別，實作任務邏輯
2. 在 `NTEPilot/config/framework.py` 中註冊任務、runner、欄位和預設值

前端會自動發現並渲染新工具，無需修改前端程式碼。

### 新增角色

在 `NTEPilot/team/character.py` 中：

```python
class NewChara(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)

CHINESE_TO_CHARA['新角色'] = NewChara
```

### 更新範本圖片

新增或刪除 `template/` 目錄下的 PNG 檔案後，需重新產生模組索引：

```powershell
python template/update.py
```

## 相關文件

- [DEV.md](DEV.md) — 專案開發文件及模組索引
- [dev_doc/](dev_doc/) — 詳細開發文件目錄

## 授權條款

本專案使用 [GNU Affero General Public License v3.0](LICENSE) 授權。

## 感謝以下貢獻者

<a href="https://github.com/NTEPilot/NTEPilot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=NTEPilot/NTEPilot" />
</a>
