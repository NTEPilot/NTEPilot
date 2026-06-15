import traceback

from template.fish import *
from template.ui import *
from template.map import *
from template.bond import *
from template.daily import *
from template.tycoon import *

SAFE_AREA = (640, 500)

class Page:
    # 键: str, 页面名称如 "page_main"
    # 值: Page, 页面实例
    all_pages = {}

    @classmethod
    def clear_connection(cls):
        for page in cls.all_pages.values():
            page.parent = None

    @classmethod
    def init_connection(cls, destination):
        """初始化页面间的 A* 寻路连接。

        Args:
            destination (Page): 目标页面。
        """
        cls.clear_connection()

        visited = [destination]
        visited = set(visited)
        while True:
            new = visited.copy()
            for page in visited:
                for link in cls.iter_pages():
                    if link in visited:
                        continue
                    if page in link.links:
                        link.parent = page
                        new.add(link)
            if len(new) == len(visited):
                break
            visited = new

    @classmethod
    def iter_pages(cls):
        return cls.all_pages.values()

    @classmethod
    def iter_check_templates(cls):
        for page in cls.all_pages.values():
            yield page.check_template

    def __init__(self, check_template):
        self.check_template = check_template
        self.links = {}
        (filename, line_number, function_name, text) = traceback.extract_stack()[-2]
        self.name = text[:text.find('=')].strip()
        self.parent = None
        Page.all_pages[self.name] = self

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def link(self, template, destination):
        self.links[destination] = template

MAIN_PAGE = Page(CHAT)

# phone
PHONE_PAGE = Page(BOND)
MAIN_PAGE.link(PHONE, PHONE_PAGE)
PHONE_PAGE.link(SAFE_AREA, MAIN_PAGE)

# fish
FISH_MAIN_PAGE = Page(HOOK)
FISH_SHOP = Page(BAIT)
FISH_MAIN_PAGE.link(BUTTON_SHOP, FISH_SHOP)
FISH_SHOP.link(BUTTON_CROSS, FISH_MAIN_PAGE)
FISH_MARKET_PAGE = Page(MARKET)
FISH_STORAGE_PAGE = Page(SELL_ALL)
FISH_MAIN_PAGE.link(BUTTON_MARKET, FISH_MARKET_PAGE)
FISH_MARKET_PAGE.link(BUTTON_CROSS, FISH_MAIN_PAGE)
FISH_MARKET_PAGE.link(FISH_STORAGE, FISH_STORAGE_PAGE)
FISH_STORAGE_PAGE.link(BUTTON_CROSS, FISH_MAIN_PAGE)

# map
MAP_PAGE = Page(MAP_SETTING)
MAIN_PAGE.link(MAP, MAP_PAGE)
MAP_PAGE.link(BUTTON_CROSS, MAIN_PAGE)

# bond
BOND_PAGE = Page(BOND_ICON)
PHONE_PAGE.link(BOND, BOND_PAGE)
BOND_PAGE.link(BUTTON_CROSS, PHONE_PAGE)

# daily
DAILY_PAGE = Page(DAILY)
MAIN_PAGE.link(F1, DAILY_PAGE)
DAILY_PAGE.link(BUTTON_CROSS, MAIN_PAGE)
DAILY_TASK_PAGE = Page(DAILY_TASK)
DAILY_TASK_PAGE.link(BUTTON_CROSS, MAIN_PAGE)
DAILY_PAGE.link(GOTO_DAILY_TASK, DAILY_TASK_PAGE)

# big monthcard
BIG_MONTHCARD_PAGE = Page(BIG_MONTHCARD)
MAIN_PAGE.link(F2, BIG_MONTHCARD_PAGE)
BIG_MONTHCARD_PAGE.link(BUTTON_CROSS, MAIN_PAGE)
BIG_MONTHCARD_TASK_PAGE = Page(BIG_MONTHCARD_TASK)
BIG_MONTHCARD_TASK_PAGE.link(BUTTON_CROSS, MAIN_PAGE)
BIG_MONTHCARD_PAGE.link(GOTO_BIG_MONTHCARD_TASK, BIG_MONTHCARD_TASK_PAGE)
BIG_MONTHCARD_TASK_PAGE.link(GOTO_BIG_MONTH_CARD_REWARDS, BIG_MONTHCARD_PAGE)

# tycoon
TYCOON_PAGE = Page(GOTO_CAFE)
MAIN_PAGE.link(F5, TYCOON_PAGE)
TYCOON_PAGE.link(BUTTON_CROSS, MAIN_PAGE)
CAFE_PAGE = Page(CLAIM_CAFE)
TYCOON_PAGE.link(GOTO_CAFE, CAFE_PAGE)
CAFE_PAGE.link(CAFE_CROSS, TYCOON_PAGE)