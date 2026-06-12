# NTEPilot

NTEPilot 是一个游戏自动化工具，通过 ADB 连接 Android 模拟器，自动执行钓鱼、战斗等游戏操作。后端使用 Python + FastAPI，前端使用 React + TypeScript，通过 WebSocket 实现实时通信。

## 功能特性

- **钓鱼自动化**：实时追踪绿色进度条，自动控制光标，支持自动购买鱼饵和自动卖鱼
- **队伍管理**：支持 16 个角色，自动管理 E/Q 技能冷却和技能循环
- **屏幕识别**：基于 OpenCV 模板匹配，自动识别游戏界面元素
- **页面导航**：A* 寻路算法自动在不同游戏界面间导航
- **插件系统**：工具自注册机制，新增工具无需修改前端代码
- **Web 控制台**：实时日志输出，支持 ANSI 颜色，配置表单动态渲染

## 系统要求

- Python 3.14+
- Node.js 18+
- ADB（Android Debug Bridge）
- Android 模拟器（如雷电、MuMu、BlueStacks）

## 快速开始

### 1. 克隆项目

```powershell
git clone <repository-url>
cd NTEPilot
```

### 2. 安装后端依赖

```powershell
# 使用 uv 安装依赖并创建/同步虚拟环境
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

构建产物会输出到 `frontend/.static`，后端启动后会自动托管。

### 5. 启动服务

```powershell
uv run main.py
```

服务启动后访问 http://127.0.0.1:9150/ 即可打开控制台。

### 6. 配置模拟器

在控制台的"通用配置"中填写 ADB 设备序列号，格式如 `127.0.0.1:16448`（不同模拟器端口不同）。

## 开发模式

前后端分离开发时，可以同时运行 Vite 开发服务器和后端：

```powershell
# 终端 1：启动后端
uv run main.py

# 终端 2：启动前端开发服务器
cd frontend
npm run dev
```

然后访问 http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150/ws

如果只开发前端，可以使用内置的 mock WebSocket 服务器：

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
├── main.py                 # 应用入口（FastAPI + Uvicorn）
├── pyproject.toml          # Python 项目配置及依赖声明
├── uv.lock                 # uv 锁文件
│
├── api/                    # WebSocket API 服务器
│   ├── server.py           # FastAPI 应用，WebSocket 端点
│   ├── config.py           # 配置字段定义和任务目录
│   └── task_runner.py      # 线程化任务执行，支持硬中止
│
├── NTEPilot/               # 核心业务逻辑
│   ├── config/             # 配置系统（Config 类，ConfigField 数据类）
│   ├── device/             # Android 设备交互层
│   │   ├── connection.py   # ADB 连接管理，重试逻辑
│   │   ├── device.py       # Device 类（组合截图 + 控制）
│   │   ├── screenshot.py   # 通过 DroidCast 截图
│   │   ├── droidcast.py    # DroidCast APK 管理
│   │   ├── minitouch.py    # 通过 minitouch 触控输入
│   │   └── control.py      # 高级点击/滑动/移动控制
│   ├── tools/              # 工具插件系统
│   │   ├── base.py         # ToolSpec 数据类
│   │   ├── registry.py     # 自动发现 */manifest.py
│   │   └── fish/           # 钓鱼自动化工具
│   │       ├── manifest.py # 工具注册和配置字段
│   │       └── fish.py     # 钓鱼逻辑（绿条追踪、光标控制）
│   ├── team/               # 角色/队伍管理
│   │   ├── character.py    # 16 个角色类，E/Q 技能冷却
│   │   └── team.py         # 队伍编成和技能循环
│   ├── ui/                 # 屏幕自动化层
│   │   ├── info_handler.py # 模板匹配（appear, click, wait）
│   │   ├── page.py         # 页面导航（A* 寻路）
│   │   └── ui.py           # UI 类（组合 InfoHandler + 导航）
│   └── instance.py         # Instance 类（绑定 Config + Device）
│
├── template/               # 模板图片资源
│   ├── __init__.py         # Template 类（OpenCV 模板匹配）
│   ├── load_template.py    # 加载 PNG 并计算边界框
│   ├── update.py           # 重新生成 __init__.py
│   ├── fish/               # 钓鱼相关模板（19 张）
│   ├── control/            # 战斗控制模板（11 张）
│   └── ui/                 # 通用 UI 模板（3 张）
│
├── utils/                  # 共享工具
│   ├── logger.py           # Rich 格式化日志
│   ├── image.py            # OpenCV 图像处理
│   ├── decorators.py       # cached_property、run_once
│   ├── exceptions.py       # 自定义异常层次
│   └── timer.py            # 计时器类
│
├── frontend/               # React 前端
│   ├── src/
│   │   ├── App.tsx         # 主界面（三列布局）
│   │   ├── components/     # UI 组件
│   │   ├── lib/            # Hooks（WebSocket、主题、动画）
│   │   └── types/          # TypeScript 类型定义
│   ├── scripts/            # Mock WebSocket 服务器
│   └── vite.config.ts      # Vite 配置
│
├── bin/                    # 二进制依赖
│   ├── DroidCast/          # 截图 APK
│   └── Minitouch/          # 触控输入工具
│
├── instances/              # 运行时实例配置 JSON
└── logs/                   # 运行时日志文件
```

## 架构说明

### 数据流

```
前端 (React/Vite) ←→ WebSocket (/ws) ←→ api/server.py ←→ NTEPilot/* ←→ ADB 设备
```

所有前后端通信通过一个 WebSocket 连接完成，消息格式为 JSON。

### WebSocket 协议

主要消息类型：

| 方向 | 类型 | 说明 |
|------|------|------|
| 服务端 → 客户端 | `hello` | 连接建立，发送实例列表和状态 |
| 服务端 → 客户端 | `config.schema` | 配置字段定义 |
| 服务端 → 客户端 | `task.catalog` | 可用工具列表 |
| 服务端 → 客户端 | `status` | 任务状态变更广播 |
| 服务端 → 客户端 | `log` | 日志事件（支持 ANSI 颜色） |
| 客户端 → 服务端 | `config.get` | 请求配置 |
| 客户端 → 服务端 | `config.update` | 保存配置 |
| 客户端 → 服务端 | `task.start` | 启动工具 |
| 客户端 → 服务端 | `task.stop` | 停止工具（硬中止） |

### 配置系统

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

### 工具插件系统

新增工具只需三步：

1. 创建 `NTEPilot/tools/<name>/manifest.py`，定义 `TOOL_SPEC`
2. 创建 `NTEPilot/tools/<name>/<name>.py`，实现工具逻辑
3. 在 `NTEPilot/config/template.json` 中添加默认配置

前端会自动发现并渲染新工具，无需修改前端代码。

### 任务执行与中止

工具在守护线程中运行。停止任务时，后端通过 `PyThreadState_SetAsyncExc` 向线程注入 `TaskAbort` 异常实现硬中止，不要求工具代码主动检查停止标记。如果工具持有外部资源（ADB 转发、临时文件、网络连接），应在 `finally` 块中清理。

### 设备控制层

```
Device (device.py)
├── Screenshot (screenshot.py)  ← DroidCast APK 截图
└── Control (control.py)        ← minitouch 触控输入
```

`Device` 类通过多重继承组合截图和控制功能，内置卡死检测和重试逻辑。

## 添加新配置项

1. 在 `NTEPilot/config/template.json` 中添加默认值
2. 在 `api/config.py` 的 `CONFIG_FIELDS` 中注册字段：

```python
ConfigField("tools.example.option", "选项名称", "boolean", "example", "选项说明", default=True)
```

支持的类型：`text`、`number`（可设置 min/max/step）、`boolean`

前端会根据类型自动渲染对应的表单控件。

## 添加新角色

在 `NTEPilot/team/character.py` 中：

1. 创建角色类，继承 `Character`，设置 E/Q 冷却时间
2. 在 `CHINESE_TO_CHARA` 字典中添加中文名映射

```python
class NewChara(Character):
    def __init__(self, id, device):
        super().__init__(id, device, e_cd=16, q_cd=15)

CHINESE_TO_CHARA['新角色'] = NewChara
```

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

## 配置参数说明

### 通用配置

| 参数 | 类型 | 说明 |
|------|------|------|
| `general.name` | text | 实例名称 |
| `general.serial` | text | ADB 设备序列号 |
| `general.client` | select | 客户端类型，可选 "异环" 或 "云·异环" |

### 钓鱼配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `tools.fish.sell_fish` | boolean | true | 钓满后自动卖鱼 |
| `tools.fish.buy_bait` | boolean | true | 鱼饵用完自动购买 |
| `tools.fish.buy_bait_stack_count` | number | 5 | 每次购买鱼饵组数（1-20） |
| `tools.fish.green_bar_safe_proportion` | number | 0.4 | 绿条安全比例（0-1） |

### 队伍配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `team.chara_1` ~ `team.chara_4` | text | - | 队伍中的角色名称 |
| `team.skill_order` | text | - | 技能循环顺序，如 `1E>2E>3E>4E>1A` |

技能循环格式：`<角色编号><技能类型>`，角色编号 1-4，技能类型 E/Q/A。

## 更新模板图片

如果添加或删除了 `template/` 目录下的 PNG 文件，需要重新生成模块索引：

```powershell
python template/update.py
```

## 许可证

本项目使用 [GNU Affero General Public License v3.0](LICENSE) 许可。
