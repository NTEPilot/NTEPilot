# UI 层

屏幕自动化层，通过 OpenCV 模板匹配识别游戏界面，使用 A* 寻路算法在页面间导航。

---

## 继承链

```
Instance -> InfoHandler -> UI
```

---

## info_handler.py — 模板匹配操作

继承 `Instance`，提供基础的模板检测和交互方法。

### 方法

- `appear(template, offset, similarity=0.85)` — 模板匹配检测，返回匹配位置或 None
- `appear_then_click(template)` — 检测到则点击，返回是否成功
- `wait_until_appear(template)` — 阻塞等待模板出现
- `wait_until_disappear(template)` — 阻塞等待模板消失
- `handle_enter_game()` — 处理进入游戏的各种弹窗（月卡、领取物品、开始界面等）
- `restart_app()` — 停止 → 等待 3s → 启动 → 等待进入游戏
- `ensure_in_game()` — 确保游戏在前台运行

---

## page.py — 页面导航

### Page 类

每个 Page 代表一个游戏界面，通过 `links` 定义可达的相邻页面。

属性：
- `all_pages: dict[str, Page]` — 全局页面注册表
- `check_template` — 用于检测当前是否在该页面的模板
- `links: dict[Page, Template]` — 导航链接（点击哪个模板可以到达哪个页面）

### 导航算法

`init_connection(destination)` — BFS 反向遍历构建 parent 指针树，从目标页面出发反向搜索到当前页面，得到最短路径。

### 页面导航图

```
MAIN_PAGE <-> PHONE_PAGE
MAIN_PAGE <-> FISH_MAIN_PAGE <-> FISH_SHOP
FISH_MARKET_PAGE <-> FISH_STORAGE_PAGE
MAIN_PAGE <-> MAP_PAGE
PHONE_PAGE <-> BOND_PAGE
MAIN_PAGE <-> DAILY_PAGE <-> DAILY_TASK_PAGE
MAIN_PAGE <-> BIG_MONTHCARD_PAGE <-> BIG_MONTHCARD_TASK_PAGE
MAIN_PAGE <-> TYCOON_PAGE <-> CAFE_PAGE
```

---

## ui.py — UI 主类

继承 `InfoHandler`，组合页面导航功能。

### 方法

- `ui_page_appear(page, offset)` — 检测指定页面是否到达
- `ui_goto(destination, offset, skip_first_screenshot)` — A* 路径导航到目标页面

---

## template/ — 模板匹配系统

### Template 类 (`template/__init__.py`)

属性：
- `name` — 模板名称
- `image` — 灰度图片数据
- `rect` — 预期匹配区域 `(x, y, w, h)`
- `method` — 匹配方法

方法：
- `pos` — 返回匹配区域内随机点（避免总是点击同一位置）
- `match_template_gray(screenshot, offset, similarity)` — 灰度模板匹配，在 rect ± offset 区域内搜索
- `match_all_template_gray(screenshot, rect, offset, similarity)` — 多实例匹配，带非极大值抑制 (NMS)
- `match_avg_color(screenshot, threshold)` — 平均颜色匹配
- `match()` / `match_all()` — 根据 method 分发

### 模板加载 (`template/load_template.py`)

`load_template(filename, rect, method)` — 加载图片 → `get_bbox` 自动裁剪空白 → 创建 Template 实例。默认 method 为 `'template_gray'`。

### 模板更新工具 (`template/update.py`)

`update(path)` — 遍历 `template/{genre}/assets/` 目录下的图片，生成对应的 `__init__.py` 文件。支持 `override.json` 自定义 rect 和 method。

**添加或删除 PNG 后必须运行 `python template/update.py` 重新生成 `__init__.py`。**

### 模板分类

| 分组 | 数量 | 说明 |
|------|------|------|
| control | 11 | BA, DODGE, JUMP, LOCK, SKILL_E/G/Q/R, SWITCH_1/2/3 |
| ui | 20+ | BOND, BUTTON_CROSS, CHAT, EXIT, F1-F5, GET_ITEM, INTERACT, MAP, PHONE 等 |
| fish | 21 | 鱼钩、商店、鱼饵、卖鱼等 |
| combat | 14 | 宝箱、领取、选择、成功等 |
| bond | 16 | 角色、礼物、约会等 |
| daily | 15 | 日常、月卡奖励等 |
| house | 6 | 家具、领取等 |
| tycoon | 5 | 咖舍等 |
| map | 6 | 传送按钮、地图设置等 |

### override.json

各模板子目录下的 `override.json` 可覆盖模板匹配的默认参数（如置信度阈值、匹配区域）。
