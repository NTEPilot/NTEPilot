# 工具库

公共工具模块，提供日志、图像处理、异常、装饰器等基础功能。

---

## exceptions.py — 自定义异常

| 异常类 | 说明 |
|--------|------|
| `ScriptError` | 开发代码错误（不应发生） |
| `ScriptEnd` | 脚本正常结束 |
| `GameStuckError` | 游戏卡死（30s 画面无变化） |
| `GameBugError` | 游戏客户端错误（重启可恢复） |
| `EmulatorNotRunningError` | 模拟器未运行 |
| `GameNotRunningError` | 游戏未运行 |
| `GamePageUnknownError` | 未知游戏页面 |
| `RequestHumanTakeover` | 请求人工接管（配置错误等无法自动恢复） |

### 重试策略（task_runner.py 中使用）

- `TaskAbort` / `RequestHumanTakeover` — 直接抛出，不重试
- `GameStuckError` / `GameBugError` / `GameNotRunningError` — 先停止应用再重试
- 其他异常 — 直接重试

---

## image.py — 图像处理

### 函数

- `limit_in(x, lower, upper)` — 值限制
- `xywh2xyxy` / `xyxy2xywh` — 坐标格式转换
- `load_image(file, area)` — PIL 加载转 RGB numpy
- `save_image(image, file)` — PIL 保存
- `copy_image(src)` — 快速图像复制
- `crop(image, area, copy)` — 裁剪，支持越界填充黑色
- `image_size(image)` — 返回 (width, height)
- `get_color(image, area)` — 区域平均颜色
- `color_similar(color1, color2, threshold)` — Photoshop 风格容差比较
- `extract_letters(image, letter, threshold)` — 颜色提取为灰度图
- `crop_to_text(image, threshold, padding)` — 紧密裁剪文字区域

---

## logger.py — 日志系统

### CustomLogger

继承 `logging.Logger`，扩展方法：
- `rule()` — 分隔线
- `hr(title, level)` — 标题
- `attr(name, text)` — 属性

### 输出

- 控制台：`rich.logging.RichHandler`（带颜色和格式）
- 文件：`logs/NTEPilot_{date}.log`

---

## timer.py — 计时器

### Timer 类

- `Timer(duration)` — 创建指定时长的计时器
- `reset()` — 重置
- `force_reached()` — 强制标记为已到时
- `reached` — 属性，是否已到时
- `wait()` — 阻塞等待到时

---

## decorators.py — 装饰器

- `cached_property` — 带类型的缓存属性装饰器
- `del_cached_property` / `has_cached_property` / `set_cached_property` — 缓存属性操作
- `run_once` — 确保函数只执行一次
