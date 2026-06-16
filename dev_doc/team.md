# 队伍与角色系统

角色管理、技能冷却和战斗技能循环。

---

## character.py — 角色基类与子类

### Character 基类

属性：
- `id` — 角色 ID
- `device` — 设备实例
- `e_cd` / `q_cd` — E/Q 技能冷却时间（秒）
- `e_timer` / `q_timer` — 技能冷却计时器

方法：
- `use_e()` — 点击 SKILL_E，重置 CD，等待 0.8-1s
- `use_q()` — 点击 SKILL_Q，重置 CD，等待 5.9-6.1s
- `use_a()` — 点击 BA（普通攻击），等待 0.1-0.2s
- `is_e_ready` / `is_q_ready` / `is_a_ready` — CD 检查属性

### 17 个角色子类

| 中文名 | 类名 | E CD | Q CD | 备注 |
|--------|------|------|------|------|
| 零 | Zero | 16s | 15s | |
| 早雾 | Sakiri | 16s | 20s | |
| 九原 | Jiuyuan | 16s | 15s | |
| 哈索尔 | Hathor | 16s | 15s | |
| 法帝娅 | Fadia | 16s | 20s | |
| 达芙蒂尔 | Daffodill | 16s | 20s | |
| 白藏 | Baicang | 14s | 20s | |
| 小吱 | Chiz | 3s | 15s | |
| 阿德勒 | Adler | 16s | 20s | |
| 海月 | Aurelia | 15s | 15s | |
| 埃德嘉 | Edgar | 16s | 20s | |
| 哈尼娅 | Haniel | 20s | 20s | |
| 薄荷 | Mint | 6s | 15s | |
| 翳 | Skia | 15s | 15s | |
| 娜娜莉 | Nanally | 16s | 15s | |
| 浔 | Hotori | 16s | 0s | Q 后持续平 A 8 秒 |
| 安魂曲 | Lacrimosa | 16s | 20s | |

### CHINESE_TO_CHARA

中文名到角色类的映射字典，用于配置系统和 OCR 识别。

---

## team.py — Team 类

继承 `Instance`。

### 初始化

从配置读取 4 个角色选择和技能顺序，创建角色实例。

### 方法

- `switch_chara(target)` — 切换角色（使用 SWITCH_1/2/3 按钮），带 1.1s 冷却
- `init_team()` — 初始化队伍（先切换到 2 号再切回 1 号）
- `combat_once()` — 按技能顺序遍历，找到第一个 CD 好的技能使用

### 技能循环格式

`<角色编号><技能类型>`，如 `1E>2E>3E>4E>1A`

- 角色编号：1-4
- 技能类型：E（元素技能）、Q（大招）、A（平 A）
