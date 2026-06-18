# 语义宏模块

`NTEPilot/macro/` 提供路线宏的通用执行能力，把路线里的语义动作转换为 ADB/minitouch 触控。

---

## semantic.py

`SemanticController` 维护当前按住的语义键状态。

- 方向键：`forward`、`back`、`left`、`right`
- 动作键：`attack`、`interact`、`jump`、`dodge`、`lock`
- 技能键：`skill_e`、`skill_q`、`skill_g`、`skill_r`
- 切人键：`switch_1`、`switch_2`、`switch_3`、`switch_4`
- 界面键：`escape`、`city_tycoon_menu`

方向键会合成摇杆角度，例如 `forward + right` 会推到右前 45 度。动作键走现有 `template/control` 和 `template/ui` 模板坐标；`switch_4` 暂使用固定坐标，因为项目当前没有四号位切人模板。

---

## route.py

`SourceRoute` 从 JSON 文件读取转换后的 Python 方法源码，绑定到运行时对象后执行入口方法。

路线 JSON 需要包含：

- `version`
- `route_id`
- `source`
- `entry`
- `methods`
- `semantic_keys`

执行前可运行：

```bash
uv run python scripts/check_pinkpaw_routes.py
```

该校验会检查 JSON 是否可解析、入口是否存在、语义键是否有效、运行时调用是否都有实现，并阻止 MaaNTE 桌面按键或旧框架残留进入路线。
