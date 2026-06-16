# DEV.md — 项目开发文档

本文件记录项目的模块、功能、架构变更，维护开发上下文。每次新增模块或功能时必须同步更新。

---

## 当前架构总览

```
前端 (React/Vite) ←→ WebSocket (/ws) ←→ api/server.py ←→ NTEPilot/*（业务逻辑）←→ ADB 设备
```

## 模块清单

### api/ — WebSocket 服务端

| 文件 | 职责 |
|------|------|
| `server.py` | 唯一入口，处理所有 WebSocket 消息类型 |
| `task_runner.py` | 守护线程执行任务，支持 `PyThreadState_SetAsyncExc` 强制中断 |
| `scheduler.py` | 管理每日计划，与手动任务共用同一任务槽位 |

### NTEPilot/ — 核心业务逻辑

| 子模块 | 职责 | 核心文件 |
|--------|------|----------|
| `config/` | 层级 JSON 配置，路径式键名 | `framework.py`（字段、默认值、任务注册） |
| `device/` | ADB 设备层，截图 + 触控 | `Device` 类（多重继承），`connection.py`（重试） |
| `tools/` | 工具实现 | `fish/`（钓鱼自动化） |
| `team/` | 角色/队伍管理与技能循环 | — |
| `ui/` | 屏幕自动化，OpenCV 模板匹配 | `Page` 类（A* 寻路） |

### template/ — 模板图片资源

- PNG 图片用于 OpenCV 模板匹配
- `Template` 类在 `__init__.py` 中处理匹配
- 添加/删除 PNG 后运行 `template/update.py` 重新生成 `__init__.py`

### frontend/ — 前端

- React 19 + Vite 7 + Material Web Components
- 三栏布局：实例列表、配置/工具工作区、日志控制台
- 配置表单由后端 schema 动态渲染，新增字段无需改前端

### utils/ — 公共工具

- `CustomLogger` — 基于 Rich 的日志
- `image.py` — 图像处理
- 自定义异常、装饰器

### bin/ — 二进制依赖

- DroidCast APK（截图）
- minitouch（触控）
- 不要修改

---

## WebSocket 协议

所有消息均为 JSON。主要类型：

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `hello` | 服务端→客户端 | 连接时发送，包含实例列表和状态 |
| `config.schema` | 服务端→客户端 | 配置字段定义 |
| `config.update` | 客户端→服务端 | 保存配置 |
| `task.start` / `task.stop` | 双向 | 任务生命周期 |
| `scheduler.*` | 双向 | 每日计划目录、状态及变更 |
| `status` | 服务端→客户端 | 广播活跃任务变化 |
| `log` | 服务端→客户端 | 广播日志（带 ANSI 颜色） |

---

## 变更记录

<!-- 每次新增模块、功能、架构变更时在此处添加记录 -->

| 日期 | 变更类型 | 说明 |
|------|----------|------|
| 2026-06-16 | 初始化 | 创建 DEV.md，记录当前架构 |
