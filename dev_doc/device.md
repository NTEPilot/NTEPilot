# 设备层

ADB 设备交互层，通过 DroidCast 截图 + minitouch 触控实现 Android 设备自动化。

---

## 继承链

```
Connection -> DroidCast -> Screenshot -> Minitouch -> Control -> Device
```

---

## connection.py — ADB 连接管理

### 客户端映射

```python
CLIENT = {
    '异环': ('com.hottagames.yh.laohu', 'com.epicgames.ue.LaunchActivity'),
    '云·异环': ('com.pwrd.cloud.yh.laohu', 'com.pwrd.cloudgame.client_core.LaunchActivity'),
}
```

### 缓存属性

`adb_client`, `adb`, `port`, `is_emulator`, `is_mumu12_family`, `is_mumu_family`, `is_network_device`, `cpu_abi`, `sdk_ver`

### ADB 操作

- `adb_shell` — 执行 shell 命令
- `adb_getprop` — 获取系统属性
- `adb_find_pids` / `adb_kill_processes` — 查找/杀死进程
- `adb_forward` / `adb_reverse` — 端口转发
- `adb_push` — 推送文件到设备

### 连接管理

- `adb_connect` / `adb_disconnect` / `adb_reconnect` / `adb_restart`

### 应用管理

- `app_current_adb` — 获取当前前台应用
- `app_is_running` — 检查应用是否运行
- `app_start_adb` / `app_stop_adb` — 启停应用

### 重试机制

`retry` 装饰器：最多重试 `RETRY_TRIES=5` 次，处理 `ConnectionResetError`, `AdbError`, `PackageNotInstalled` 等。

---

## droidcast.py — 截图方案

使用 DroidCast_raw APK，通过 `app_process` 方式运行（非真正安装）。

- 本地路径: `./bin/DroidCast/DroidCast_raw-release-1.1.apk`
- 远程路径: `/data/local/tmp/DroidCast_raw.apk`
- 通过 ADB forward 端口 (`tcp:53516`) 提供 HTTP 服务
- `/screenshot` 接口返回 RGB565 原始位图

### 关键函数

- `decode_droidcast_raw(image, shape, rotate)` — 将 RGB565 bytes 转为 RGB numpy 数组
- `droidcast_init()` — 推送 APK、启动服务、等待就绪

### MuMu 模拟器特殊处理

MuMu > 3.5.6 版本需要动态获取分辨率和方向。

---

## screenshot.py — 截图管理

### 截图流程

1. 等待间隔 (0.1s)
2. 调用 `screenshot_droidcast()`
3. 处理方向（非 1280x720 时根据 orientation 旋转）
4. 检查分辨率和黑屏

### 方法

- `screenshot()` — 完整截图流程
- `_handle_orientated_image(image)` — 方向处理
- `check_screen_size()` — 验证分辨率为 1280x720
- `check_screen_black()` — 检测纯黑截图（模拟器未就绪）
- `save_screenshot(interval)` — 保存截图到 `./debug/screenshots/`

---

## minitouch.py — 触控方案

使用 minitouch 二进制文件，通过 ADB push 并运行。

- 本地路径: `./bin/Minitouch/{abi}/minitouch`
- 远程路径: `/data/local/tmp/minitouch`
- 通过 ADB forward `localabstract:minitouch` 建立 socket 连接

### Command 类

封装 minitouch 命令（c/r/d/m/u/w），支持 `to_minitouch()` 和 `to_maatouch_sync()` 格式。

### CommandBuilder 类

- `convert(x, y)` — 根据设备方向转换坐标，映射到设备实际 max_x/max_y
- `down(x, y, contact, pressure)` / `move(...)` / `up(contact)` / `commit()` / `wait(ms)` / `reset(mode)`
- `send()` — 通过 `minitouch_send` 发送
- `DEFAULT_DELAY = 0.05`

### Minitouch 类方法

- `click_minitouch(x, y)` — 点击
- `long_click_minitouch(x, y, duration)` — 长按
- `swipe_minitouch(p1, p2)` — 滑动
- `drag_minitouch(p1, p2, disturbance)` — 拖拽
- `press_minitouch(x, y)` / `release_minitouch()` — 持续按住（保持线程定期发送 move 命令）
- `release_all_minitouch()` — 释放所有已记录为按下的触点，用于任务中断、服务关闭和 minitouch 停止兜底
- `keep_drag_minitouch(p1, p2)` — 拖拽后保持按住

### 滑动路径生成

`insert_swipe(p0, p3, speed=15, min_distance=10)` — 使用三次贝塞尔曲线生成自然滑动路径，带随机控制点。

---

## control.py — 高级控制

### 常量

- `JOYSTICK_CENTER = (198, 565)` — 虚拟摇杆中心
- `JOYSTICK_OFFSET = 100` — 摇杆偏移量

### 方法

- `click(target)` — 支持 tuple 和 Template 类型
- `long_click(target, duration)` — 长按
- `multi_click(button, n, interval)` — 连续点击
- `swipe(p1, p2)` — 滑动
- `drag(p1, p2, disturbance)` — 拖拽
- `press(target)` / `release()` — 按住/释放
- `move(angle, until)` — 虚拟摇杆移动，`until` 可以是秒数或回调函数
- `move_forward/backward/left/right(until)` — 八方向移动
- `move_forward_right/backward_right/backward_left/forward_left(until)`

---

## device.py — 设备主类

继承 `Screenshot` 和 `Control`。

### 初始化

最多重试 4 次连接（捕获 `EmulatorNotRunningError`）。

### 卡死检测

- `screenshot()` — 调用父类截图 + `_check_image_stuck()`
- `_check_image_stuck()` — 将截图缩放到 16x16 计算 hash，如果连续 30s 未变化则抛出 `GameStuckError` 或 `GameNotRunningError`
- `stuck_timer_reset()` — 重置卡死检测状态

---

## utils.py — 设备工具

- `RETRY_TRIES = 5`, `RETRY_DELAY = 3`
- `retry_sleep(trial)` — 指数退避: 0, 0, 1, 3, 3...
- `handle_adb_error(e)` — 分析 ADB 错误文本决定是否重试
- `handle_image_truncated(obj, exc)` — 图像截断计数器，达到阈值(3)后尝试重启 DroidCast/重连 ADB
- `recv_all(stream)` — 接收完整 socket 数据
- `random_port(port_range)` — 从范围 (20000, 21000) 中选择可用端口
