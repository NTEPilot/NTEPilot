from NTEPilot.config.config_field import ConfigField
from NTEPilot.tools.base import ToolSpec


TOOL_SPEC = ToolSpec(
    id="fish",
    title="钓鱼",
    description="运行钓鱼工具",
    runner="NTEPilot.tools.fish.fish:Fish",
    config_fields=(
        ConfigField("tools.fish.sell_fish", "自动卖鱼", "boolean", "fish", default=True),
        ConfigField("tools.fish.buy_bait", "自动买鱼饵", "boolean", "fish", default=True),
        ConfigField("tools.fish.buy_bait_stack_count", "鱼饵购买组数", "number", "fish", min=1, max=20, step=1, default=5),
        ConfigField("tools.fish.green_bar_safe_proportion", "绿条安全比例", "number", "fish", min=0, max=1, step=0.05, default=0.4),
    ),
)
