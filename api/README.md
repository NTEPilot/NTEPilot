# NTEPilot API 开发指南

`api/server.py` 是前端和后端之间的唯一实时通信入口。服务启动后，同一个端口同时提供：

- 前端静态页面：`http://127.0.0.1:9150/`
- WebSocket API：`ws://127.0.0.1:9150/ws`

默认监听地址为 `127.0.0.1`，默认端口为 `9150`，可通过 `main.py` 的启动参数修改。

## 启动方式

在项目根目录运行：

```powershell
.venv\Scripts\python.exe main.py
```

也可以显式指定监听地址和端口：

```powershell
.venv\Scripts\python.exe main.py --host 127.0.0.1 --port 9150
```

`main.py` 会创建默认实例、读取实例配置，然后启动 FastAPI + Uvicorn。前端静态文件来自 `frontend/.static`。

## 配置模型

配置定义位于：

```text
NTEPilot/config/framework.py
```

实例配置保存在：

```text
instances/<实例名>.json
```

如果 `instances` 下没有任何实例配置，后端会根据 `framework.py` 的默认值创建：

```text
instances/NTE.json
```

实例配置是嵌套结构：

```json
{
  "general": {
    "name": "NTE",
    "serial": "127.0.0.1:16448",
    "client": "异环"
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
- `tools.fish.buy_bait`
- `tools.fish.green_bar_safe_proportion`

代码内部通过 `Config.__getitem__` 使用同样的路径式 key 访问：

```python
config["general.serial"]
config["general.client"]
config["tools.fish.buy_bait"]
config["tools.fish.green_bar_safe_proportion"]
```


## 新增配置项

新增配置项只需要修改 `NTEPilot/config/framework.py`。例如给钓鱼工具新增一个布尔开关：

```python
CONFIG["tools"]["fish"]["config"]["enable_debug_marker"] = {
    "label": "显示调试标记",
    "type": "boolean",
    "description": "钓鱼识别时显示调试标记",
    "default": False,
}
```

字段参数说明：

- 字段路径由所在分组自动生成，例如上例为 `tools.fish.enable_debug_marker`。
- `label`：前端显示名。
- `type`：支持 `text`、`integer`、`float`、`boolean`、`select`。
- `description`：前端辅助说明，可为空。
- `range`：数字项的输入范围和步长，格式为 `(min, max, step)`。
- `options`：`select` 类型的选项列表。

第三步，在业务代码中读取：

```python
if self.config["tools.fish.enable_debug_marker"]:
    ...
```

如果新增的是数字项或字符串项，`Config.update()` 会根据 `framework.py` 中的字段类型自动做基础类型转换。

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
    "activeTask": "idle",
    "scheduler": "disabled"
  }
}
```

随后还会下发实例列表、配置 schema、工具目录、计划任务目录和计划器状态。

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

第二步，在 `NTEPilot/config/framework.py` 中登记工具：

```python
CONFIG["tools"]["example"] = {
    "label": "示例工具",
    "description": "运行示例工具",
    "runner": "NTEPilot.tools.example.example:Example",
    "config": {
        "enabled": {
            "label": "启用示例工具",
            "type": "boolean",
            "default": True,
        },
        "interval": {
            "label": "执行间隔",
            "type": "float",
            "range": (0.1, 60, 0.1),
            "default": 1.0,
        },
    },
}
```

后端会从 `framework.py` 生成工具目录、配置字段和默认值并下发给前端。不需要修改 `api/server.py`、`api/task_runner.py` 或前端代码。

停止逻辑由 `TaskRunner.stop()` 统一处理。新增工具不需要接收停止事件，也不需要在工具内部实现停止检查。工具线程被硬中止时，`TaskRunner` 会捕获内部 `TaskAbort` 并广播任务取消状态。

如果新增工具持有外部资源，例如按键按下状态、ADB 转发、临时文件或网络连接，应在工具自身的 `finally` 中清理资源，确保硬中止时仍能释放。

## 注意事项

- API 层通过 `ConfigStore` 管理配置对象；同一个实例只保留一个 `Config` 对象。
- 配置 key 必须小写。
- 新工具配置必须在 `framework.py` 字段 spec 中提供默认值；后端会将这些默认值合并进实例配置并用于保存校验。
- 前端和 WebSocket 共用端口，`/ws` 只能用于 WebSocket，静态文件走 `/`。
- 工具线程不能直接操作前端连接对象，应通过 `broadcast_threadsafe()` 广播状态、任务和日志。
