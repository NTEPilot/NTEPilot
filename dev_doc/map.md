# 地图模块

地图导航系统，包含地图数据加载、小地图定位和传送功能。

---

## 继承链

```
Instance -> InfoHandler -> UI -> Map
```

---

## map_data.py — 地图数据

### MapData 类

加载大地图 `bigmap_total_hires.png` 和传送点数据 `DT_TeleportPoint.json`。

### 世界坐标系

- `CENTER_X = -40532.004`
- `CENTER_Y = 131446.33`
- `EDGE_X = EDGE_Y = 687134.0`

### 方法

- `world_to_map(x, y)` — 世界坐标转地图像素坐标
- `get_teleport(number)` — 按编号获取传送点

---

## map_locator.py — 小地图定位

### 常量

- `SCALE = 0.1736` — 小地图缩放比例
- `MIN_SCORE = 0.2` — 最低匹配分数
- `EARLY_SCORE = 0.6` — 早停分数

### 定位流程

1. 裁剪小地图区域 `(128, 88, 1154, 638)`
2. 预处理：灰度 + Canny 边缘 + HSV 饱和度/明度过滤（去除彩色图标，保留灰色道路结构）
3. 模板匹配大地图
4. 返回 `MapView`

---

## utils.py — 数据类

### TeleportPoint

```python
TeleportPoint(number, name, level, kind, world_x, world_y, map_x, map_y)
```

### MapView

```python
MapView(origin_x, origin_y, scale, score, crop, screen_size)
```

方法：
- `map_to_screen(x, y)` — 地图坐标转屏幕坐标
- `screen_to_map(x, y)` — 屏幕坐标转地图坐标
- `is_on_screen(x, y)` — 判断坐标是否在屏幕内

### 常量

- `CROP = (128, 88, 1154, 638)` — 小地图裁剪区域

---

## map.py — Map 主类

继承 `UI`，提供传送功能。

### 方法

- `teleport_to(number, max_attempts=10)` — 传送到指定传送点
- `_drag_points(target_x, target_y)` — 计算拖拽起止点

### 传送流程

1. 打开地图
2. 最小化地图（确保全图可见）
3. 循环定位当前位置
4. 拖拽使目标进入安全区域
5. 点击传送

---

## mark.py — 调试工具

在大地图上标注所有传送点编号，用于调试和验证传送点数据。
