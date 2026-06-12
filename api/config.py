from NTEPilot.config.config_field import ConfigField
from NTEPilot.team.character import CHINESE_TO_CHARA
from NTEPilot.tools.registry import get_task_catalog, get_tool_config_fields

CHARACTER_OPTIONS = tuple(CHINESE_TO_CHARA.keys())

GENERAL_CONFIG_FIELDS = [
    ConfigField("general.serial", "设备序列号", "text", "general", "ADB 设备或模拟器序列号"),
    ConfigField("general.client", "客户端", "select", "general", "游戏客户端类型", options=("异环", "云·异环")),
]

TEAM_CONFIG_FIELDS = [
    ConfigField("team.chara_1", "一号角色", "select", "team", "队伍一号位角色", options=CHARACTER_OPTIONS),
    ConfigField("team.chara_2", "二号角色", "select", "team", "队伍二号位角色", options=CHARACTER_OPTIONS),
    ConfigField("team.chara_3", "三号角色", "select", "team", "队伍三号位角色", options=CHARACTER_OPTIONS),
    ConfigField("team.chara_4", "四号角色", "select", "team", "队伍四号位角色", options=CHARACTER_OPTIONS),
    ConfigField("team.skill_order", "技能顺序", "text", "team", "按 1E>2E>3E>4E>1A 格式填写队伍技能循环"),
]

CONFIG_FIELDS = [*GENERAL_CONFIG_FIELDS, *TEAM_CONFIG_FIELDS, *get_tool_config_fields()]


TASKS = get_task_catalog()
