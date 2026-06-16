# 前端

React + TypeScript + Material Web Components 实现的 Web 控制台。

---

## 技术栈

- React 19 + TypeScript 5.9 + Vite 7.2
- Material Web Components (`@material/web`)
- Material Color Utilities（动态主题）
- `@formkit/auto-animate`（动画）
- Material Symbols Outlined（图标）

---

## 协议类型 (`types/protocol.ts`)

### BackendMessage（后端 → 前端）

联合类型：`hello`, `instance.list`, `config.schema`, `task.catalog`, `scheduler.catalog`, `scheduler.state`, `status`, `log`, `task`, `call.result`

### FrontendMessage（前端 → 后端）

15 种消息类型，覆盖实例管理、配置、任务控制、调度器操作。

---

## useWebSocketBridge — 核心 Hook

**文件**: `lib/useWebSocketBridge.ts`

功能：
- 自动重连（2.5s 间隔）
- localStorage 持久化选中实例
- 状态管理

### 状态

`instances`, `backendStatus`, `fields`, `values`, `tasks`, `scheduleTasks`, `scheduler`, `taskEvents`, `logs`

### 操作方法

`connect`, `disconnect`, `setSelectedInstance`, `createInstance`, `updateValue`, `startTask`, `stopTask`, `setSchedulerEnabled`, `addSchedulePlan`, `updateSchedulePlan`, `removeSchedulePlan`, `runSchedulePlan`

---

## App.tsx — 主应用组件

### 页面标签

- `general` — 通用配置
- `team` — 队伍
- `tools` — 工具
- `plan` — 计划

### 布局

三栏布局：左侧实例导航栏 + 中间工作区 + 右侧日志面板（可调宽度）。顶部状态栏显示连接状态、当前任务、调度器状态。

### 对话框

- 新建实例对话框
- 计划管理对话框（添加/编辑计划，支持任务级配置覆盖）

---

## 组件

### ConfigPanel

根据字段类型动态渲染：
- boolean → `Switch`
- select → `OutlinedSelect`
- text/integer/float → `OutlinedTextField`

**前端绝不硬编码配置字段，始终由后端 `config.schema` 驱动。**

### ConsolePanel

日志面板，功能：
- 完整 ANSI 转义序列解析器（支持 256 色、RGB 真彩色、粗体/斜体/下划线）
- 自动滚动
- 可拖拽调整宽度

### InstanceTabs

实例列表导航。

### Switch / MaterialIcon

Material Web Switch 和 Material Symbols 图标的封装组件。

---

## Hooks

### useThemeMode

Material You 动态主题，源色 `#006CFF`，支持 light/dark，自定义 surface tones。

### useMotionParent

基于 `@formkit/auto-animate` 的动画 Hook。

---

## 构建与开发

- `npm run build` — 构建到 `frontend/.static`（后端自动托管）
- `npm run dev` — Vite 开发服务器（需同时运行后端）
- `npm run mock:server` — 独立开发用的模拟 WebSocket 服务器

**`frontend/.static` 是构建输出目录，不要手动编辑。**
