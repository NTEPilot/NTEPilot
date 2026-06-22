# 工具模块

所有任务 runner 的实现。每个工具继承 `UI` 或 `Map`，实现 `run()` 方法。

---

## Instance 基类 (`instance.py`)

所有任务 runner 的基类，持有 `config` 和 `device`。

```python
class Instance:
    def __init__(self, config: Config, device: Any | None = None):
```

---

## fish — 钓鱼自动化

**文件**: `NTEPilot/fish/fish.py`
**继承**: `UI`
**Runner**: `NTEPilot.fish.fish:Fish`

### 常量

- `FISH_BAR_RECT = (404, 44, 880, 55)` — 钓鱼条区域
- `GREEN_BAR_RGB = (58, 240, 177)` — 绿条颜色
- `YELLOW_CURSOR_RGB = (255, 253, 160)` — 黄色光标颜色

### 主流程 (`run`)

1. 进入钓鱼界面
2. 循环点击鱼钩开始钓鱼
3. 鱼满时自动卖鱼（如果启用）
4. 鱼饵用完自动购买（如果启用）

### 钓鱼核心 (`fish`)

- 启动异步控制线程 `_control_loop()`
- 主线程截图检测绿条和光标位置
- 共享状态变量通过 `threading.Lock` 同步

### 控制线程 (`_control_loop`)

- 预测未来 0.25s 光标和绿条位置
- 以 0.15s 最小间隔发送左/右/释放指令
- 根据 `green_bar_safe_proportion` 判断安全区域

### 辅助方法

- `buy_bait()` — 导航到鱼饵商店，购买指定组数
- `sell_fish()` — 导航到鱼仓，全部出售

---

## display_density_calibrator — DPI 校准工具

**文件**: `NTEPilot/tools/display_density.py`
**继承**: `UI`
**Runner**: `NTEPilot.tools.display_density:DisplayDensityCalibrator`

手动工具，不接入普通任务的进游戏前置流程。启动后会：

1. 记录当前设备 DPI 状态
2. 按 10-999 逐个执行 `wm density`
3. 每次设置后重启游戏
4. 等待进入主界面并检测 `F1` / `F2` / `F3`
5. 命中后保留当前 DPI；失败或中断时尽量恢复原 DPI

---

## combat — 战斗自动化

**文件**: `NTEPilot/combat/combat.py`
**继承**: `Map`, `Team`, `Ocr`（多重继承）
**Runner**: `NTEPilot.combat.combat:Combat`

### 副本定义 (`CHINESE_INFO`)

4 大副本类型：
- **经验本** — 传送点 15，体力消耗 40
- **卡牌本** — 传送点 16，体力消耗 40
- **罐头本** — 传送点 17，体力消耗 40
- **兔子洞** — 传送点 18，体力消耗 40

### 主流程 (`run`)

1. OCR 读取体力像素
2. 计算可刷次数
3. 循环调用 `combat()`

### 战斗流程 (`combat`)

1. 传送到目标副本
2. 初始化队伍
3. 前进交互找到副本入口
4. 选择副本难度
5. 进入战斗
6. 调用 `start_combat()` 战斗
7. 调用 `claim_reward()` 领奖

### 战斗逻辑 (`start_combat`)

1. 前进找到焦点
2. 平 A 拉近
3. 循环使用技能直到出现 SUCCESS

### 领奖逻辑 (`claim_reward`)

寻找宝箱标记，调整视角居中，交互领取（支持双倍/单倍）。

---

## bond — 社交系统

### gift.py — 送礼物

**继承**: `UI`, `CharaOcr`
**Runner**: `NTEPilot.bond.gift:Gift`

流程：
1. 遍历角色列表
2. OCR 识别角色名
3. 找到目标角色后送指定礼物
4. 支持滚动查找更多角色

### movie.py — 看电影

**继承**: `Map`, `CharaOcr`
**Runner**: `NTEPilot.bond.movie:Movie`

流程：
1. `goto_movie()` — 传送到传送点 44，通过移动指令到达电影院
2. `_movie()` — 匹配所有 DATE_TELEPHONE 模板，OCR 识别角色名，找到后邀请看电影

### ocr.py — 角色名 OCR 纠错

继承 `Ocr`，覆盖 `ocr()` 方法，纠正常见 OCR 错误：
- "驱" → "翳"
- "得" → "浔"
- "小" → "小吱"

---

## cafe — 咖啡厅

**文件**: `NTEPilot/cafe/claim_rewards.py`
**继承**: `UI`
**Runner**: `NTEPilot.cafe.claim_rewards:ClaimRewards`

流程：导航到 CAFE_PAGE → 点击领取 → 等待 GET_ITEM 弹窗后关闭。

---

## daily — 每日任务

### claim_daily.py — 领取日常任务

**继承**: `UI`
**Runner**: `NTEPilot.daily.claim_daily:ClaimDaily`

流程：
1. 导航到 DAILY_TASK_PAGE
2. 领取日常积分
3. 领取日常奖励（5 个奖励等级，使用 avg_color 匹配判断是否可领取）

### claim_big_monthcard.py — 领取大月卡

**继承**: `UI`
**Runner**: `NTEPilot.daily.claim_big_monthcard:ClaimBigMonthcard`

流程：
1. 导航到 BIG_MONTHCARD_TASK_PAGE 领取任务奖励
2. 导航到 BIG_MONTHCARD_PAGE 领取月卡奖励

---

## house — 家园系统

**文件**: `NTEPilot/house/claim_house.py`
**继承**: `Map`
**Runner**: `NTEPilot.house.claim_house:ClaimHouse`

流程：
1. 传送到指定房产
2. 与家具交互
3. 进入家具概览
4. 滚动到底部
5. 领取指定编号的资源

### chinese_to_teleport.py

6 个房产名到传送点 ID 的映射（28-33）。

---

## pinkpaw — 粉爪大劫案

**文件**: `NTEPilot/pinkpaw/pinkpaw.py`
**继承**: `UI`
**Runner**: `NTEPilot.pinkpaw.pinkpaw:PinkPawHeist`

### 路线文件

路线位于 `NTEPilot/pinkpaw/routes/`：

- `core1.json`
- `core2.json`
- `core3_dash.json`
- `core3_attack.json`
- `entrance_recovery.json`

这些 JSON 由 `scripts/convert_pinkpaw_macro.py` 从 MaaNTE 的粉爪 Python 路线生成，保留原路线中的按下、松开、点击、等待、循环、分支和撤离重试。转换时会把桌面按键改成语义键，例如 `W` 变成 `forward`，`F` 变成 `interact`，鼠标左键变成 `attack`。

### 运行时

`NTEPilot/pinkpaw/runtime.py` 负责承接路线调用：

1. 用 `SemanticController` 把语义键转为 minitouch 触控。
2. 用现有 OCR、颜色检测和模板匹配实现交互点、撬锁、撤离、怪物血条等检测。
3. 停止或异常时释放摇杆和动作触点。

粉爪专用模板目录是 `template/pinkpaw/assets/`。当前专用模板允许为空；缺少 `INTERACTABLE.png`、`HEIST_INTERAC_LOCK_PICK.png`、`HEIST_LOCK_PICK.png` 时，对应模板检测会返回未命中，不会伪造成功。

### 配置项

注册位置：`NTEPilot/config/framework.py` 的 `CONFIG["tools"]["pinkpaw"]`。

- `scheme` — 方案一、方案二、方案三
- `core3_branch` — 方案三分支
- `loop_count` — 循环次数
- `timing_scale` — 方案三路线时间倍率
- `interaction_pause` — 交互前松开方向后的停顿
- `early_extract_exit1` — 出口 1 提前撤离
- `early_extract_exit2` — 出口 2 提前撤离

---

## 新增工具的步骤

1. 在 `NTEPilot/tools/<名称>/<名称>.py` 中创建工具类，继承 `UI` 或 `Map`
2. 实现 `run()` 方法
3. 在 `NTEPilot/config/framework.py` 的 `CONFIG["tools"]` 或 `CONFIG["schedule"]` 中注册
4. 添加 runner 路径（格式 `"module.path:ClassName"`）和配置字段
5. 前端会从后端 schema 自动发现工具，无需修改前端代码

### 注意事项

- 工具通过硬线程中断（`TaskAbort` 异常）停止
- 如果工具持有外部资源（ADB 端口转发、临时文件、网络连接），务必在 `finally` 块中清理
- 每个实例同一时间只能运行一个任务
