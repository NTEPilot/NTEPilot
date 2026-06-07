# NTEPilot API 开发指南

`api/server.py` 是前端和后端之间的唯一实时通信入口。服务启动后，同一个端口同时提供：

- 前端静态页面：`http://127.0.0.1:9150/`
- WebSocket API：`ws://127.0.0.1:9150/ws`

默认端口来自实例配置中的 `general.websocket_port`，默认监听地址来自 `general.websocket_host`。

## 启动方式

在项目根目录运行：

```powershell
.venv\Scripts\python.exe main.py
```

`main.py` 会创建默认实例、读取实例配置，然后启动 FastAPI + Uvicorn。前端静态文件来自 `frontend/.static`。

## 配置模型

配置模板位于：

```text
NTEPilot/config/template.json
```

实例配置保存在：

```text
instances/<实例名>.json
```

如果 `instances` 下没有任何实例配置，后端会复制模板创建：

```text
instances/NTE.json
```

当前模板是嵌套结构：

```json
{
  "general": {
    "name": "NTE",
    "serial": "127.0.0.1:16448",
    "package_name": "com.pwrd.cloud.yh.laohu",
    "activity_name": "com.pwrd.cloudgame.client_core.ui.HomeActivity",
    "websocket_host": "127.0.0.1",
    "websocket_port": 9150
  },
  "tools": {
    "fish": {
      "sell_fish": true,
      "buy_bait": true,
      "buy_bait_stack_count": 5,
      "green_bar_safe_proportion": 0.4
    }
  }
}
```

后端通信使用路径式 key，例如：

- `general.serial`
- `general.websocket_port`
- `tools.fish.buy_bait`
- `tools.fish.green_bar_safe_proportion`

代码内部仍然可以通过短 key 访问：

```python
config.serial
config.package_name
config.buy_bait
config.green_bar_safe_proportion
```

短 key 到嵌套路径的映射由 `NTEPilot/config/config.py` 中的 `Config.alias_paths()` 自动生成。要求模板里不同分支不要出现重复叶子 key，否则短 key 只会映射到第一个路径。

## 新增配置项

新增配置项需要三步。

第一步，修改 `NTEPilot/config/template.json`。例如给钓鱼工具新增一个布尔开关：

```json
{
  "tools": {
    "fish": {
      "enable_debug_marker": false
    }
  }
}
```

第二步，在 `api/server.py` 的 `CONFIG_FIELDS` 中注册前端字段：

```python
ConfigField(
    "tools.fish.enable_debug_marker",
    "显示调试标记",
    "boolean",
    "fish",
    "钓鱼识别时显示调试标记"
)
```

字段参数说明：

- `key`：路径式配置 key，必须能在模板中找到。
- `label`：前端显示名。
- `type`：支持 `text`、`number`、`boolean`。
- `group`：前端分组。通用配置使用 `general`，钓鱼工具使用 `fish`。
- `description`：前端辅助说明，可为空。
- `min/max/step`：数字项的输入范围和步长。

第三步，在业务代码中读取：

```python
if self.config.enable_debug_marker:
    ...
```

如果新增的是数字项或字符串项，`Config.update()` 会根据模板中的默认值类型自动做基础类型转换。

## WebSocket 协议

所有消息都是 JSON 文本。

### 初始化

前端连接 `/ws` 后，后端会主动下发：

```json
{
  "type": "hello",
  "app": "NTEPilot",
  "version": "0.4.0",
  "currentInstance": "NTE",
  "instances": [{ "name": "NTE" }],
  "status": {
    "device": "127.0.0.1:16448",
    "packageName": "com.pwrd.cloud.yh.laohu",
    "activeTask": "idle"
  }
}
```

随后还会下发实例列表、配置 schema 和工具目录。

### 获取实例列表

请求：

```json
{ "type": "instance.list" }
```

响应：

```json
{
  "type": "instance.list",
  "instances": [{ "name": "NTE", "path": "E:\\github\\NTEPilot\\instances\\NTE.json" }]
}
```

### 创建实例

请求：

```json
{
  "type": "instance.create",
  "requestId": "uuid",
  "name": "Test"
}
```

后端会复制模板创建 `instances/Test.json`，并广播新的实例列表。

### 获取配置

请求：

```json
{
  "type": "config.get",
  "instance": "NTE"
}
```

响应：

```json
{
  "type": "config.schema",
  "instance": "NTE",
  "fields": [
    {
      "key": "general.serial",
      "label": "设备序列号",
      "type": "text",
      "group": "general",
      "description": "ADB 设备或模拟器序列号",
      "value": "127.0.0.1:16448"
    }
  ]
}
```

### 保存配置

请求：

```json
{
  "type": "config.update",
  "requestId": "uuid",
  "instance": "NTE",
  "values": {
    "general.serial": "127.0.0.1:16448",
    "tools.fish.buy_bait": true,
    "tools.fish.buy_bait_stack_count": 5
  }
}
```

后端会验证 key 是否在模板中存在，然后写回当前实例配置文件。

### 获取工具目录

请求：

```json
{ "type": "task.list" }
```

响应：

```json
{
  "type": "task.catalog",
  "tasks": [
    {
      "id": "fish",
      "title": "钓鱼",
      "description": "运行钓鱼工具"
    }
  ]
}
```

### 启动工具

请求：

```json
{
  "type": "task.start",
  "requestId": "uuid",
  "instance": "NTE",
  "taskId": "fish",
  "values": {
    "tools.fish.buy_bait": true
  }
}
```

`task.start` 会先保存传入配置，再异步启动工具线程。后端会广播：

```json
{
  "type": "status",
  "instance": "NTE",
  "status": {
    "activeTask": "fish"
  }
}
```

### 停止工具

请求：

```json
{
  "type": "task.stop",
  "requestId": "uuid",
  "instance": "NTE",
  "taskId": "fish"
}
```

停止是硬中止。后端会通过 `PyThreadState_SetAsyncExc` 向任务线程抛出内部 `TaskAbort` 异常，任务线程收到异常后进入 `finally` 清理状态并广播 `cancelled`。

这个方式不要求工具代码主动检查停止标记，也不要把停止事件挂到配置对象上。需要注意的是，如果任务线程正卡在底层 C 扩展、设备 I/O 或系统调用里，异常会在 Python 线程重新获得执行机会后生效。

### 日志

后端通过 `BroadcastLogHandler` 捕获 `utils.logger` 输出，并广播：

```json
{
  "type": "log",
  "event": {
    "level": "info",
    "source": "NTEPilot",
    "message": "日志文本",
    "ansi": "\u001b[38;2;69;196;154m日志文本\u001b[0m",
    "time": "2026-06-07T23:00:00"
  }
}
```

`ansi` 字段由 Rich 渲染生成，前端会解析并显示颜色。

## 新增工具

新增工具建议按下面流程做。

第一步，在业务目录实现工具类，例如：

```text
NTEPilot/tools/example/example.py
```

第二步，在 `NTEPilot/config/template.json` 下新增配置：

```json
{
  "tools": {
    "example": {
      "enabled": true,
      "interval": 1.0
    }
  }
}
```

第三步，在 `api/server.py` 注册配置字段：

```python
ConfigField("tools.example.enabled", "启用示例工具", "boolean", "example"),
ConfigField("tools.example.interval", "执行间隔", "number", "example", min=0.1, max=60, step=0.1)
```

第四步，在 `TASKS` 中注册工具：

```python
{
    "id": "example",
    "title": "示例工具",
    "description": "运行示例工具",
}
```

第五步，扩展 `TaskRunner.start()`、`TaskRunner.stop()` 和任务线程函数，让 `taskId == "example"` 时运行你的工具。

停止逻辑由 `TaskRunner.stop()` 统一处理。新增工具不需要接收停止事件，也不需要在工具内部实现停止检查。工具线程被硬中止时，`TaskRunner` 会捕获内部 `TaskAbort` 并广播任务取消状态。

如果新增工具持有外部资源，例如按键按下状态、ADB 转发、临时文件或网络连接，应在工具自身的 `finally` 中清理资源，确保硬中止时仍能释放。

## 注意事项

- 不要直接在 API 层创建 `Config`，统一通过 `Instance(...).config` 或 `Instance.create()`。
- 配置 key 必须小写。
- 新配置必须先进入 `template.json`，否则 `config.update` 会拒绝保存。
- 前端和 WebSocket 共用端口，`/ws` 只能用于 WebSocket，静态文件走 `/`。
- 工具线程不能直接操作前端连接对象，应通过 `broadcast_threadsafe()` 广播状态、任务和日志。
