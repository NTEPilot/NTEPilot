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
  <img src="https://img.shields.io/badge/ADB-支持-4CAF50?style=flat-square" alt="ADB">
  <img src="https://img.shields.io/badge/OpenCV-4.13-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/ONNX-推理-005CED?style=flat-square" alt="ONNX">
  <img src="https://img.shields.io/badge/WebSocket-实时通信-FF6F00?style=flat-square" alt="WebSocket">
</p>

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEPilot)](https://github.com/NTEPilot/NTEPilot)

---

## 项目简介

NTEPilot 是一款专为《异环》设计的自动化工具，通过 ADB 连接 Android 模拟器，自动执行各类游戏操作。项目采用前后端分离架构，后端使用 Python + FastAPI 处理核心逻辑，前端使用 React + TypeScript 构建现代化控制台，通过 WebSocket 实现实时双向通信。

## 功能模块

<table>
  <tr>
    <td width="50%">
      <h3>钓鱼自动化</h3>
      <ul>
        <li>实时追踪绿色进度条</li>
        <li>自动控制光标位置</li>
        <li>支持自动购买鱼饵</li>
        <li>支持自动出售鱼类</li>
        <li>可配置安全比例阈值</li>
      </ul>
    </td>
    <td width="50%">
      <h3>队伍管理</h3>
      <ul>
        <li>支持 17 个角色</li>
        <li>自动管理 E/Q 技能冷却</li>
        <li>可配置技能循环顺序</li>
        <li>支持 4 人队伍编成</li>
        <li>角色自动识别映射</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>战斗系统</h3>
      <ul>
        <li>自动战斗控制</li>
        <li>技能释放管理</li>
        <li>战斗状态识别</li>
        <li>自动重试机制</li>
      </ul>
    </td>
    <td width="50%">
      <h3>日常任务</h3>
      <ul>
        <li>每日任务自动化</li>
        <li>咖啡厅互动</li>
        <li>羁绊系统处理</li>
        <li>房屋管理</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>屏幕识别</h3>
      <ul>
        <li>基于 OpenCV 模板匹配</li>
        <li>自动识别游戏界面元素</li>
        <li>OCR 文字识别（ONNX）</li>
        <li>高精度图像处理</li>
      </ul>
    </td>
    <td width="50%">
      <h3>页面导航</h3>
      <ul>
        <li>A* 寻路算法</li>
        <li>自动界面切换</li>
        <li>地图定位传送</li>
        <li>智能路径规划</li>
      </ul>
    </td>
  </tr>
</table>

## 系统要求

<table>
  <tr>
    <td><strong>运行环境</strong></td>
    <td>Windows 10/11</td>
  </tr>
  <tr>
    <td><strong>Python 版本</strong></td>
    <td>3.14 或更高</td>
  </tr>
  <tr>
    <td><strong>Node.js 版本</strong></td>
    <td>18 或更高（仅开发需要）</td>
  </tr>
  <tr>
    <td><strong>ADB 工具</strong></td>
    <td>Android Debug Bridge</td>
  </tr>
  <tr>
    <td><strong>模拟器</strong></td>
    <td>雷电、MuMu、BlueStacks 等 Android 模拟器</td>
  </tr>
</table>

> **为什么使用模拟器？** 如果你用桌面端来运行脚本的话，游戏窗口必须保持在前台，我猜你也不想运行脚本的时候不能动鼠标键盘像个傻宝一样坐在那吧，所以用模拟器

## 快速开始

或者使用启动器一键启动

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NTEPilot&repo=NTEP-Launcher)](https://github.com/NTEPilot/NTEP-Launcher)

### 1. 克隆项目

```powershell
git clone https://github.com/NTEPilot/NTEPilot.git
cd NTEPilot
```

### 2. 安装后端依赖

```powershell
# 使用 uv 安装依赖并同步虚拟环境
uv sync
```

### 3. 安装前端依赖

```powershell
cd frontend
npm install
cd ..
```

### 4. 构建前端

```powershell
cd frontend
npm run build
cd ..
```

构建产物输出到 `frontend/.static`，后端启动后自动托管。

### 5. 启动服务

```powershell
uv run main.py
```

访问 http://127.0.0.1:9150/ 打开控制台。

### 6. 配置模拟器

在控制台的"通用配置"中填写 ADB 设备序列号，格式如 `127.0.0.1:16448`（不同模拟器端口不同）。

## 技术架构

<table>
  <tr>
    <th width="20%">层级</th>
    <th width="40%">技术栈</th>
    <th width="40%">说明</th>
  </tr>
  <tr>
    <td><strong>前端</strong></td>
    <td>React 19 + TypeScript + Vite 7</td>
    <td>Material Design 3 设计语言，动态配置表单渲染</td>
  </tr>
  <tr>
    <td><strong>后端</strong></td>
    <td>Python 3.14 + FastAPI + Uvicorn</td>
    <td>异步 WebSocket 服务，插件化工具系统</td>
  </tr>
  <tr>
    <td><strong>通信</strong></td>
    <td>WebSocket JSON 协议</td>
    <td>实时双向通信，支持日志流、状态推送</td>
  </tr>
  <tr>
    <td><strong>图像</strong></td>
    <td>OpenCV 4.13 + ONNX Runtime</td>
    <td>模板匹配、OCR 推理、图像预处理</td>
  </tr>
  <tr>
    <td><strong>设备</strong></td>
    <td>ADB + DroidCast + minitouch</td>
    <td>设备连接、截图捕获、触控输入</td>
  </tr>
</table>

## 开发模式

前后端分离开发时，可同时运行 Vite 开发服务器和后端：

```powershell
# 终端 1：启动后端
uv run main.py

# 终端 2：启动前端开发服务器
cd frontend
npm run dev
```

访问 http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150/ws

如需仅开发前端，可使用内置的 mock WebSocket 服务器：

```powershell
# 终端 1：启动 mock 服务器
cd frontend
npm run mock:server

# 终端 2：启动前端
npm run dev
```

## 项目结构

```
NTEPilot/
├── main.py                     # 应用入口
├── pyproject.toml              # Python 项目配置
│
├── api/                        # WebSocket API 服务
│   ├── server.py               # FastAPI 应用及 WebSocket 端点
│   ├── scheduler.py            # 每日计划调度器
│   └── task_runner.py          # 线程化任务执行器
│
├── NTEPilot/                   # 核心业务逻辑
│   ├── config/                 # 配置系统
│   ├── device/                 # Android 设备交互层
│   ├── tools/                  # 工具实现（fish/combat/bond/cafe/daily/house）
│   ├── team/                   # 角色/队伍管理
│   ├── ui/                     # 屏幕自动化层
│   ├── map/                    # 地图导航
│   ├── ocr.py                  # OCR 文字识别
│   └── instance.py             # 实例管理
│
├── template/                   # 模板图片资源
│   ├── fish/                   # 钓鱼相关模板
│   ├── control/                # 战斗控制模板
│   └── ui/                     # 通用 UI 模板
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.tsx             # 主界面
│   │   ├── components/         # UI 组件
│   │   ├── lib/                # Hooks
│   │   └── types/              # TypeScript 类型
│   └── vite.config.ts          # Vite 配置
│
├── bin/                        # 二进制依赖
│   ├── DroidCast/              # 截图 APK
│   └── Minitouch/              # 触控工具
│
├── instances/                  # 运行时实例配置
└── logs/                       # 运行时日志
```

## 配置系统

配置使用路径式 key，嵌套 JSON 结构：

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

代码中通过 `config["tools.fish.buy_bait"]` 访问。

## 支持的角色

| 中文名 | 英文名 | E 技能冷却 | Q 技能冷却 |
|--------|--------|-----------|-----------|
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

## 配置参数

### 通用配置

| 参数 | 类型 | 说明 |
|------|------|------|
| `general.name` | text | 实例名称 |
| `general.serial` | text | ADB 设备序列号 |
| `general.client` | select | 客户端类型：异环 / 云·异环 |

### 钓鱼配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tools.fish.sell_fish` | boolean | true | 钓满后自动卖鱼 |
| `tools.fish.buy_bait` | boolean | true | 鱼饵用完自动购买 |
| `tools.fish.buy_bait_stack_count` | number | 5 | 每次购买鱼饵组数（1-20） |
| `tools.fish.green_bar_safe_proportion` | number | 0.4 | 绿条安全比例（0-1） |

### 队伍配置

| 参数 | 类型 | 说明 |
|------|------|------|
| `team.chara_1` ~ `team.chara_4` | text | 队伍中的角色名称 |
| `team.skill_order` | text | 技能循环顺序，如 `1E>2E>3E>4E>1A` |

技能循环格式：`<角色编号><技能类型>`，角色编号 1-4，技能类型 E/Q/A。

## 开发指南

### 添加新工具

1. 创建对应 runner 类，实现任务逻辑
2. 在 `NTEPilot/config/framework.py` 中注册任务、runner、字段和默认值

前端会自动发现并渲染新工具，无需修改前端代码。

### 添加新角色

在 `NTEPilot/team/character.py` 中：

```python
class NewChara(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)

CHINESE_TO_CHARA['新角色'] = NewChara
```

### 更新模板图片

添加或删除 `template/` 目录下的 PNG 文件后，需重新生成模块索引：

```powershell
python template/update.py
```

## 相关文档

- [DEV.md](DEV.md) - 项目开发文档及模块索引
- [dev_doc/](dev_doc/) - 详细开发文档目录

## 许可证

本项目使用 [GNU Affero General Public License v3.0](LICENSE) 许可。

## 感谢以下贡献者

<a href="https://github.com/NTEPilot/NTEPilot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=NTEPilot/NTEPilot" />
</a>
