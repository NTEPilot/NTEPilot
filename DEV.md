# DEV.md — 项目开发文档

项目架构总览和模块索引。详细文档在 `dev_doc/` 目录下。

---

## 架构

```
前端 (React/Vite) ←→ WebSocket (/ws) ←→ api/server.py ←→ NTEPilot/* ←→ ADB 设备
```

任务执行：每实例单任务，`PyThreadState_SetAsyncExc` 强制中断，最多重试 3 次。调度器 5s 轮询，按优先级执行到期计划。

---

## 模块索引

| 模块 | 职责 | 详细文档 |
|------|------|----------|
| `api/` | WebSocket 服务端、任务执行器、调度器 | [api.md](dev_doc/api.md) |
| `NTEPilot/config/` | 配置系统（路径式键名、schema 驱动前端） | [config.md](dev_doc/config.md) |
| `NTEPilot/device/` | ADB 设备层（DroidCast 截图 + minitouch 触控） | [device.md](dev_doc/device.md) |
| `NTEPilot/ui/` | 屏幕自动化（模板匹配、A* 页面导航） | [ui.md](dev_doc/ui.md) |
| `NTEPilot/macro/` | 语义宏执行层（方向/动作语义键到 minitouch 触控） | [macro.md](dev_doc/macro.md) |
| `NTEPilot/tools/` | 工具实现（fish、combat、bond、cafe、daily、house） | [tools.md](dev_doc/tools.md) |
| `NTEPilot/pinkpaw/` | 粉爪大劫案路线运行时和工具入口 | [tools.md](dev_doc/tools.md) |
| `NTEPilot/map/` | 地图导航（定位、传送） | [map.md](dev_doc/map.md) |
| `NTEPilot/team/` | 队伍与角色系统（17 角色、技能循环） | [team.md](dev_doc/team.md) |
| `NTEPilot/ocr.py` | OCR 系统（ONNX 推理） | [ocr.md](dev_doc/ocr.md) |
| `template/` | 模板匹配 PNG 资源（改 PNG 后跑 `python template/update.py`） | [ui.md](dev_doc/ui.md) |
| `frontend/` | React 前端（MD3、schema 动态渲染） | [frontend.md](dev_doc/frontend.md) |
| `utils/` | 公共工具（日志、图像、异常、装饰器） | [utils.md](dev_doc/utils.md) |

---

## 关键约定

- **配置入口唯一** — 所有字段、默认值、runner 路径都在 `NTEPilot/config/framework.py` 注册
- **前端 schema 驱动** — 新增配置字段无需改前端
- **工具自注册** — 新增工具只需在 `framework.py` 注册，前端自动发现
- **模板更新** — 添加/删除 PNG 后必须运行 `python template/update.py`
- **线程安全** — 工具线程不得直接操作前端连接，必须用 `broadcast_threadsafe()`

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-06-16 | 初始化，创建 DEV.md 和 dev_doc/ 详细文档 |
