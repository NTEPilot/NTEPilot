from NTEPilot.team.character import CHINESE_TO_CHARA


CHARA_OPTIONS = tuple(CHINESE_TO_CHARA.keys())
CHARA_OPTIONS_WITHOUT_ZERO = tuple([c for c in CHARA_OPTIONS if c != '零'])
COMBAT_SELECTIONS = (
    "经验本 - 合订本",
    "经验本 - 万花筒",
    "经验本 - 硬币记",
    "卡牌本 - 小心鸽子",
    "卡牌本 - 扑克茶会",
    "卡牌本 - 惊喜派对",
    "卡牌本 - 心电感应",
    "卡牌本 - 越狱艺术",
    "罐头本 - 泡影罐头·苹果核",
    "罐头本 - 泡影罐头·螺旋乐",
    "罐头本 - 泡影罐头·液态梦",
    "罐头本 - 泡影罐头·冷甜点",
    "罐头本 - 泡影罐头·戏剧芯",
    "兔子洞 - 钟表把戏",
    "兔子洞 - 雕塑展馆",
    "兔子洞 - 纬线织机",
    "兔子洞 - 守卫萝卜",
    "兔子洞 - 精神图谱",
    "兔子洞 - 轨道之夜",
)


CONFIG = {
    "general": {
        "serial": {
            "label": "设备序列号",
            "type": "text",
            "description": "ADB 设备或模拟器序列号",
            "default": "127.0.0.1:16384",
        },
        "client": {
            "label": "客户端",
            "type": "select",
            "description": "游戏客户端类型",
            "options": ("异环", "云·异环"),
            "default": "异环",
        },
    },
    "team": {
        "chara_1": {
            "label": "一号角色",
            "type": "select",
            "description": None,
            "options": CHARA_OPTIONS,
            "default": "零",
        },
        "chara_2": {
            "label": "二号角色",
            "type": "select",
            "description": None,
            "options": CHARA_OPTIONS,
            "default": "早雾",
        },
        "chara_3": {
            "label": "三号角色",
            "type": "select",
            "description": None,
            "options": CHARA_OPTIONS,
            "default": "九原",
        },
        "chara_4": {
            "label": "四号角色",
            "type": "select",
            "description": None,
            "options": CHARA_OPTIONS,
            "default": "哈索尔",
        },
        "skill_order": {
            "label": "技能顺序",
            "type": "text",
            "description": "技能顺序，由数字加字母组成。数字代表几号位；字母在'Q'、'E'、'A'中选，代表攻击方式",
            "default": "1E>2E>3E>4E>1A",
        },
    },
    "tools": {
        "fish": {
            "label": "钓鱼",
            "description": "自动钓鱼工具，在钓鱼界面运行该工具",
            "runner": "NTEPilot.fish.fish:Fish",
            "config": {
                "sell_fish": {
                    "label": "自动卖鱼",
                    "type": "boolean",
                    "description": "是否自动卖鱼，关掉此选项将在鱼仓满时结束任务",
                    "default": True,
                },
                "buy_bait": {
                    "label": "自动买鱼饵",
                    "type": "boolean",
                    "description": "是否自动购买鱼饵，关掉此选项将在鱼饵不足时结束任务",
                    "default": True,
                },
                "buy_bait_stack_count": {
                    "label": "鱼饵购买组数",
                    "type": "integer",
                    "description": "购买鱼饵的组数，每组99个",
                    "range": (1, 20, 1),
                    "default": 5,
                },
                "green_bar_safe_proportion": {
                    "label": "绿条安全比例",
                    "type": "float",
                    "description": "绿条安全比例，尽量将光标保持在绿条中间的比例",
                    "range": (0, 1, 0.05),
                    "default": 0.4,
                },
            },
        },
    },
    "schedule": {
        "combat": {
            "label": "刷副本",
            "description": "自动刷副本",
            "runner": "NTEPilot.combat.combat:Combat",
            "config": {
                "selection": {
                    "label": "副本选择",
                    "type": "select",
                    "description": None,
                    "options": COMBAT_SELECTIONS,
                    "default": "经验本 - 合订本",
                },
            },
        },
        "gift": {
            "label": "送礼物",
            "description": "给一位角色送礼物",
            "runner": "NTEPilot.bond.gift:Gift",
            "config": {
                "character": {
                    "label": "选择角色",
                    "type": "select",
                    "description": None,
                    "options": CHARA_OPTIONS_WITHOUT_ZERO,
                    "default": "早雾",
                },
                "gift": {
                    "label": "礼物编号",
                    "type": "integer",
                    "description": "送礼物的编号，送礼界面第一页从1开始，先从左往右再从上往下数（1-10）",
                    "range": (1, 10, 1),
                    "default": 1,
                },
                "number": {
                    "label": "礼物数量",
                    "type": "integer",
                    "description": "送礼物的数量",
                    "range": (1, 3, 1),
                    "default": 1,
                },
            },
        },
        "cafe": {
            "label": "领一咖舍",
            "description": None,
            "runner": "NTEPilot.cafe.claim_rewards:ClaimRewards",
            "config": {},
        },
        "daily": {
            "label": "领日常任务",
            "description": None,
            "runner": "NTEPilot.daily.claim_daily:ClaimDaily",
            "config": {},
        },
        "big_monthcard": {
            "label": "领大月卡",
            "description": None,
            "runner": "NTEPilot.daily.claim_big_monthcard:ClaimBigMonthcard",
            "config": {},
        },
        "movie": {
            "label": "看电影",
            "description": None,
            "runner": "NTEPilot.bond.movie:Movie",
            "config": {
                "character": {
                    "label": "选择角色",
                    "type": "select",
                    "description": None,
                    "options": CHARA_OPTIONS_WITHOUT_ZERO,
                    "default": "早雾",
                },
            },
        }
    },
}