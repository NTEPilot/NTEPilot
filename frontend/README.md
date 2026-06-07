# NTEPilot 前端开发指南

前端使用 React + Vite 构建，源码位于 `frontend/src`，构建产物输出到：

```text
frontend/.static
```

后端启动后会直接托管 `frontend/.static`，并在同一个端口提供 WebSocket：

```text
http://127.0.0.1:9150/
ws://127.0.0.1:9150/ws
```

前端默认从浏览器地址栏推导 WebSocket 地址：

- `http://127.0.0.1:9150/` -> `ws://127.0.0.1:9150/ws`
- `https://example.com/` -> `wss://example.com/ws`

开发调试时也可以用查询参数覆盖：

```text
http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150/ws
```

## 安装和构建

进入前端目录：

```powershell
cd frontend
npm install
```

开发模式：

```powershell
npm run dev
```

生产构建：

```powershell
npm run build
```

构建命令会执行 TypeScript 检查并把结果写入 `frontend/.static`。

## 目录结构

```text
frontend/
  src/
    App.tsx                         主界面布局
    styles.css                      全局暗色主题和组件样式
    components/
      ConfigPanel.tsx               配置表单渲染器
      ConsolePanel.tsx              同步控制台日志
      InstanceTabs.tsx              左侧实例标签
      Switch.tsx                    通用开关组件
    lib/
      useWebSocketBridge.ts         WebSocket 通信和状态管理
    types/
      protocol.ts                   前后端消息类型
  scripts/
    mock-ws-server.mjs              本地 mock WebSocket 服务
  vite.config.ts                    Vite 配置，产物目录为 .static
```

## 界面结构

当前界面分三列：

- 左侧：实例列表，纵向标签页。
- 中间：配置和工具工作区。
- 右侧：同步控制台日志。

中间区域有二级标签：

- `通用配置`：显示 `group === "general"` 的配置项。
- `工具`：显示工具入口，目前包含 `钓鱼`。

工具页中，钓鱼项包含：

- `启动/停止` 按钮。
- 默认收起的 `钓鱼配置` 下拉区。
- 下拉区内显示 `group === "fish"` 的配置项。

## WebSocket 状态管理

`src/lib/useWebSocketBridge.ts` 负责：

- 建立 WebSocket 连接。
- 保存当前实例。
- 接收实例列表。
- 接收配置 schema。
- 保存配置。
- 启动和停止工具。
- 接收任务状态。
- 接收日志。

常用返回值：

```ts
const bridge = useWebSocketBridge();

bridge.instances           // 实例列表
bridge.selectedInstance    // 当前实例
bridge.groupedFields       // 按 group 分组后的配置项
bridge.values              // 当前表单值
bridge.backendStatus       // 后端状态，包括 activeTask
bridge.logs                // 控制台日志
bridge.saveConfig()        // 保存配置
bridge.startTask('fish')   // 启动钓鱼
bridge.stopTask('fish')    // 硬中止钓鱼线程
```

## 配置渲染规则

后端通过 `config.schema` 下发配置字段：

```json
{
  "key": "tools.fish.buy_bait",
  "label": "自动买鱼饵",
  "type": "boolean",
  "group": "fish",
  "value": true
}
```

前端渲染规则在 `ConfigPanel.tsx`：

- `type: "text"` -> 文本输入框。
- `type: "number"` -> 数字输入框，支持 `min/max/step`。
- `type: "boolean"` -> `Switch` 开关组件。

因此新增配置项时，前端一般不需要改表单代码，只要后端把字段加入 `CONFIG_FIELDS` 并设置正确的 `group`。

## 新增通用配置

第一步，后端模板新增字段：

```json
{
  "general": {
    "adb_timeout": 10
  }
}
```

第二步，后端 `api/server.py` 的 `CONFIG_FIELDS` 注册：

```python
ConfigField("general.adb_timeout", "ADB 超时", "number", "general", "ADB 命令超时时间", min=1, max=120, step=1)
```

第三步，前端无需改动。字段会自动出现在“通用配置”页。

## 新增钓鱼配置

第一步，后端模板新增字段：

```json
{
  "tools": {
    "fish": {
      "enable_debug_marker": false
    }
  }
}
```

第二步，后端注册字段：

```python
ConfigField("tools.fish.enable_debug_marker", "显示调试标记", "boolean", "fish", "钓鱼识别时显示调试标记")
```

第三步，前端无需改动。字段会自动出现在“工具 -> 钓鱼配置”下拉区，并使用开关组件显示。

## 新增工具页面

如果只是在后端新增配置字段，前端无需改动。如果要新增一个和“钓鱼”并列的工具，需要修改 `App.tsx`。

示例：新增 `example` 工具。

第一步，后端 `TASKS` 下发：

```json
{
  "id": "example",
  "title": "示例工具",
  "description": "运行示例工具"
}
```

第二步，后端配置字段使用新的 group：

```python
ConfigField("tools.example.enabled", "启用示例工具", "boolean", "example")
```

第三步，在 `App.tsx` 的工具页中新增一个工具项：

```tsx
const exampleTask = bridge.tasks.find((task) => task.id === 'example');
const exampleRunning = bridge.backendStatus.activeTask === 'example';
```

渲染时使用：

```tsx
<ConfigPanel
  fields={bridge.groupedFields.example ?? []}
  values={bridge.values}
  onChange={bridge.updateValue}
/>
```

按钮逻辑：

```tsx
if (exampleRunning) bridge.stopTask('example');
else bridge.startTask('example');
```

`stopTask()` 对应后端 `task.stop`，当前实现是硬中止任务线程，不依赖工具内部的停止事件。

## 开关组件

开关组件位于：

```text
frontend/src/components/Switch.tsx
```

使用方式：

```tsx
<Switch checked={enabled} onChange={setEnabled} label="启用功能" />
```

`ConfigPanel` 已经自动对 boolean 配置使用 `Switch`，普通业务界面也可以复用这个组件。

## 日志控制台

`ConsolePanel.tsx` 负责显示后端日志。

日志来源是后端广播的 `log` 消息：

```json
{
  "type": "log",
  "event": {
    "level": "info",
    "source": "NTEPilot",
    "message": "普通文本",
    "ansi": "\u001b[38;2;69;196;154m带颜色文本\u001b[0m"
  }
}
```

前端优先解析 `ansi`，没有 `ansi` 时显示 `message`。控制台支持 Rich 生成的基础 ANSI 样式，包括 truecolor 前景色、粗体、淡化和重置。

控制台标题栏有“自动滚动”开关：

- 开启：新日志到达时自动滚动到底部。
- 关闭：保留当前滚动位置，便于查看历史日志。

前端不会再把 `call.result` 的 JSON 返回包直接渲染到日志区域下方，只会显示简短的操作结果日志。

## 本地 mock 后端

如果只开发前端，可以运行 mock WebSocket 服务：

```powershell
cd frontend
node scripts/mock-ws-server.mjs
```

然后启动 Vite：

```powershell
npm run dev
```

打开：

```text
http://127.0.0.1:5173/?ws=ws://127.0.0.1:9150
```

mock 服务支持：

- 实例列表。
- 创建实例。
- 获取和保存配置。
- 启动钓鱼。
- 停止钓鱼。
- 模拟日志。

## 开发注意事项

- 前端不要硬编码配置项，优先依赖后端 `config.schema`。
- 配置 key 使用路径式小写 key，例如 `tools.fish.buy_bait`。
- 新配置必须先加入 `NTEPilot/config/template.json`，否则后端会拒绝保存。
- 新工具如果要出现在工具页，需要后端 `TASKS` 注册，并在前端 `App.tsx` 添加对应工具项。
- `frontend/.static` 是构建产物，不应手动编辑。
- 改完前端后至少运行一次 `npm run build`。
