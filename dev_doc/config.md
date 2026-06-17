# 配置系统

路径式键名的层级 JSON 配置，支持多实例、类型校验和前端 schema 驱动。

---

## config.py — Config 类

### 常量

- `PROJECT_ROOT` — 项目根目录
- `INSTANCES_DIR = PROJECT_ROOT / "instances"` — 实例配置存储目录
- `DEFAULT_INSTANCE_NAME = "NTE"` — 默认实例名

### Config 类

支持点分路径访问：`config["general.serial"]`、`config["tools.fish.buy_bait"]`

方法：
- `__getitem__` / `__setitem__` — 支持嵌套键的点分路径访问
- `update(values, save)` — 更新配置，校验字段白名单，调用 `normalize_config_value` 类型归一化
- `save()` — 写入 JSON 文件到 `instances/` 目录
- `load(name)` — 从文件加载，自动合并默认值
- `create(name, values)` — 创建新实例配置
- `list_instances()` — 列出所有实例 JSON 文件
- `ensure_default_instance()` — 确保至少存在一个默认实例

### 静态方法

- `get_from_data(data, path)` — 从嵌套字典中按点分路径取值
- `set_path(data, path, value)` — 按点分路径设置值

---

## framework.py — 配置框架定义

**所有配置字段、默认值、任务目录和运行器路径都在此文件注册。新增工具或配置字段只改这个文件。**

### CONFIG 字典结构

#### general 区

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `serial` | text | `"127.0.0.1:16384"` | ADB 设备序列号 |
| `client` | select | `"异环"` | 客户端类型，选项：`("异环", "云·异环")` |

#### team 区

| 字段 | 类型 | 说明 |
|------|------|------|
| `chara_1` ~ `chara_4` | select | 角色选择，选项来自 `CHINESE_TO_CHARA`（17个角色） |
| `skill_order` | text | 技能顺序，默认 `"1E>2E>3E>4E>1A"` |

#### tools 区（手动工具）

**fish** — 钓鱼工具，runner: `NTEPilot.fish.fish:Fish`

| 字段 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| `sell_fish` | boolean | — | true | 钓满后自动卖鱼 |
| `buy_bait` | boolean | — | true | 鱼饵用完自动购买 |
| `buy_bait_stack_count` | integer | 1-20 | 5 | 每次购买鱼饵组数 |
| `green_bar_safe_proportion` | float | 0-1 | 0.4 | 绿条安全比例 |

#### schedule 区（可调度任务）

| 任务 ID | Runner | 配置字段 |
|---------|--------|----------|
| `combat` | `NTEPilot.combat.combat:Combat` | `selection` (select), `number` (int, 1-100, 默认100) |
| `gift` | `NTEPilot.bond.gift:Gift` | `character` (select), `gift` (int, 1-10), `number` (int, 1-3) |
| `cafe` | `NTEPilot.cafe.claim_rewards:ClaimRewards` | 无 |
| `daily` | `NTEPilot.daily.claim_daily:ClaimDaily` | 无 |
| `big_monthcard` | `NTEPilot.daily.claim_big_monthcard:ClaimBigMonthcard` | 无 |
| `movie` | `NTEPilot.bond.movie:Movie` | `character` (select) |
| `house` | `NTEPilot.house.claim_house:ClaimHouse` | `house` (select), `index` (int, 1-4) |

### 辅助常量

- `CHARA_OPTIONS` — 17 个角色中文名元组
- `CHARA_OPTIONS_WITHOUT_ZERO` — 去掉"零"的 16 个角色
- `HOUSE_OPTIONS` — 6 个房产名称元组
- `COMBAT_SELECTIONS` — 19 个副本选项元组

---

## schema.py — 配置 Schema 工具

### 核心函数

- `iter_config_fields()` — 遍历所有配置字段，yield `(path, section, field)` 三元组
- `get_default_config()` — 生成包含所有默认值的配置字典，包含 `scheduler: {enabled: false, plans: []}`
- `merge_defaults(data)` — 将用户数据与默认值合并
- `get_user_config_fields()` — 返回 `{path: field}` 字典
- `get_config_schema(config)` — 生成前端需要的配置 schema 列表
- `get_task_catalog(section)` — 获取任务目录（"tools" 或 "schedule"）
- `create_runner(section, task_id, config, device)` — 动态导入 runner 类并实例化（格式 `"module.path:ClassName"`）
- `normalize_config_value(path, value)` — 类型归一化（bool/int/float/select），校验 range 和 options
- `field_to_json(path, group, field, config)` — 字段序列化为 JSON schema

### 配置字段定义格式

```python
"option": {
    "label": "选项名称",
    "type": "boolean",          # boolean | integer | float | text | select
    "description": "选项说明",
    "default": True,
    "range": (min, max),        # 可选，integer/float 有效
    "options": ("选项1", "选项2"),  # 可选，select 有效
}
```

### 新增配置字段的步骤

1. 在 `framework.py` 中给对应分组添加字段定义和默认值
2. 前端根据类型自动渲染（text → 输入框，integer/float → 带范围的数字输入，boolean → 开关，select → 下拉选择）

### 新增工具的步骤

1. 在 `NTEPilot/tools/<名称>/<名称>.py` 中创建工具类
2. 在 `framework.py` 的 `CONFIG["tools"]` 中注册工具（添加 runner 路径和配置字段）
3. 前端会从后端 schema 自动发现工具，无需修改前端代码
