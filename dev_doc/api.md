# API 层

WebSocket 服务端，负责前后端通信、任务执行和调度管理。

---

## server.py — WebSocket 服务器

### 核心类

**`NTEPilotWebSocketApp`** — 应用主类，管理所有 WebSocket 连接和业务逻辑。

属性：
- `clients: set[WebSocket]` — 连接的客户端集合
- `config_store: ConfigStore` — 多实例配置管理
- `task_runner: TaskRunner` — 任务执行器
- `scheduler: Scheduler` — 调度器
- `loop: asyncio.AbstractEventLoop` — 事件循环引用（用于 `broadcast_threadsafe`）

方法：
- `asgi_app()` — 创建 FastAPI 应用，注册 startup/shutdown 事件和 `/ws` 端点
- `websocket_handler(websocket)` — WebSocket 连接处理循环
- `send_initial_state(websocket)` — 连接建立后发送初始状态（hello、instance.list、config.schema、task.catalog、scheduler.catalog、scheduler.state）
- `handle_message(websocket, raw)` — 消息路由分发

### 辅助类

**`ConfigStore`** — 管理多实例配置，维护 `_configs` 字典，提供 `list_instances()`, `get(instance)`, `create(instance)`, `schema(instance)`, `update(instance, values)` 方法。

**`BroadcastLogHandler(logging.Handler)`** — 拦截 Python logging 日志，通过 Rich Console 渲染为 ANSI 字符串，广播到所有 WebSocket 客户端。

**`HTTPMount(Mount)`** — Starlette 路由挂载，仅匹配 HTTP 类型请求，用于静态文件服务。

### 消息类型（前端 → 后端）

| 消息类型 | 功能 | 响应 |
|---|---|---|
| `hello` | 忽略 | 无 |
| `instance.list` | 列出所有实例 | `instance.list` |
| `instance.create` | 创建新实例 | `instance.list` 广播 + `config.schema` + `scheduler.state` + `call.result` |
| `config.get` | 获取配置 schema | `config.schema` |
| `config.update` | 更新配置 | `config.schema` + `status` 广播 + `call.result` |
| `task.list` | 获取任务目录 | `task.catalog` |
| `task.start` | 启动手动任务 | `call.result` |
| `task.stop` | 停止任务 | `call.result` |
| `scheduler.catalog` | 获取调度器任务目录 | `scheduler.catalog` |
| `scheduler.get` | 获取调度器状态 | `scheduler.state` |
| `scheduler.set_enabled` | 启用/禁用调度器 | `call.result` |
| `scheduler.plan.add` | 添加计划 | `config.schema` + `call.result` |
| `scheduler.plan.update` | 更新计划 | `config.schema` + `call.result` |
| `scheduler.plan.remove` | 删除计划 | `call.result` |
| `scheduler.plan.run` | 强制运行计划 | `call.result` |

### 广播消息（后端 → 前端）

- `log` — 日志事件，含 ANSI 渲染
- `task` — 任务状态变更（running/done/error/cancelled）
- `status` — 实例状态（device/activeTask/scheduler）
- `scheduler.state` — 调度器状态

### 工厂函数

`create_app() -> FastAPI` — 创建并返回 ASGI 应用。

---

## task_runner.py — 任务执行器

### 异常类

- `TaskAbort(BaseException)` — 用于强制中断线程（通过 `PyThreadState_SetAsyncExc` 注入）
- `TaskBusyError(RuntimeError)` — 实例已有任务在运行

### 关键函数

`raise_thread_exception(thread, exception)` — 使用 `ctypes.pythonapi.PyThreadState_SetAsyncExc` 向目标线程注入异常。

### TaskHandle 数据类

- `instance`, `section` (TaskSection), `task_id`, `title`
- `source`: "manual" | "scheduler"
- `plan_id`: 调度器计划 ID（仅调度器启动时有值）
- `done: threading.Event` — 完成信号
- `thread: threading.Thread`
- `status`: "queued" | "running" | "done" | "error" | "cancelled"
- `detail: str`

### TaskRunner 类

属性：
- `max_attempts = 3` — 最大重试次数
- `retry_delay = 3.0` — 重试间隔（秒）
- `_tasks: dict[str, TaskHandle]` — 每个实例最多一个活跃任务
- `_devices: dict[str, Any]` — 设备实例缓存

方法：
- `start(instance, task_id, values)` — 手动启动任务
- `start_scheduled(instance, task_id, plan_id)` — 调度器启动任务
- `stop(instance, task_id)` — 先释放设备按下触点，再通过 `raise_thread_exception` 强制中止
- `stop_all()` — 服务关闭时停止全部运行中任务，并释放所有已缓存设备的按下输入
- `_run_task(handle)` — 线程入口，调用 `_execute_with_retry`
- `_execute_with_retry(handle)` — 创建 runner（通过 `create_runner` 动态导入），调用 `ensure_in_game()` + `run()`
- `_device(instance)` — 懒加载 Device 实例

### 重试策略

- `TaskAbort` / `RequestHumanTakeover` — 直接抛出，不重试
- `GameStuckError` / `GameBugError` / `GameNotRunningError` — 先停止应用再重试
- 其他异常 — 直接重试

---

## scheduler.py — 调度器

### Scheduler 类

属性：
- `poll_seconds = 5.0` — 轮询间隔
- `_stop_event: threading.Event` — 停止信号
- `_thread: threading.Thread` — 后台轮询线程
- `_active_plan: dict[str, str]` — 实例 → 当前运行的计划 ID
- `_last_error: dict[str, str]` — 实例 → 最后错误

方法：
- `start()` / `shutdown()` — 启停轮询线程
- `set_enabled(instance, enabled)` — 启用/禁用调度器，禁用时自动停止当前调度任务
- `add_plan(instance, task_id, run_time, priority, values)` — 添加计划，UUID 生成 ID，时间格式 HH:MM
- `update_plan(...)` / `remove_plan(...)` / `run_plan(...)` — 计划 CRUD 和强制运行
- `_loop()` — 主循环：遍历所有实例，调用 `_run_due_plans`
- `_run_due_plans(instance)` — 检查到期计划并依次执行，所有计划完成后关闭应用
- `_due_plans(instance)` — 筛选今日未执行且时间已到的计划，按优先级降序、时间升序排序
- `_start_plan(instance, plan)` — 启动计划任务
- `_finish_plan(instance, plan_id, handle)` — 等待任务完成，支持调度器禁用时自动停止
- `_mark_plan_success(instance, plan_id)` — 记录 `last_run_date`

### 计划数据结构

```json
{
  "id": "uuid",
  "taskId": "combat",
  "time": "09:00",
  "priority": 0,
  "values": {"selection": "经验本", "number": 100},
  "last_run_date": "2026-06-16"
}
```

### 执行流程

1. 轮询线程每 5s 遍历所有实例
2. 筛选今日未执行且时间已到的计划
3. 按优先级降序、时间升序排序
4. 依次执行，每个计划完成后标记 `last_run_date`
5. 所有计划完成后调用 `app.shutdown()` 关闭应用
