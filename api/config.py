from NTEPilot.config.config_field import ConfigField
from NTEPilot.tools.registry import get_task_catalog, get_tool_config_fields


GENERAL_CONFIG_FIELDS = [
    ConfigField("general.serial", "设备序列号", "text", "general", "ADB 设备或模拟器序列号"),
    ConfigField("general.package_name", "应用包名", "text", "general", "目标 Android 应用包名"),
    ConfigField("general.activity_name", "启动 Activity", "text", "general", "目标 Android Activity"),
    ConfigField("general.websocket_host", "监听地址", "text", "general", "前端和 WebSocket 共用监听地址"),
    ConfigField("general.websocket_port", "监听端口", "number", "general", "前端和 WebSocket 共用监听端口", min=1, max=65535, step=1),
]


CONFIG_FIELDS = [*GENERAL_CONFIG_FIELDS, *get_tool_config_fields()]


TASKS = get_task_catalog()
