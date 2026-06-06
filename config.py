# 临时配置
SERIAL = '127.0.0.1:16448'
PACKAGE_NAME = 'com.pwrd.cloud.yh.laohu'
ACTIVITY_NAME = 'com.pwrd.cloudgame.client_core.ui.HomeActivity'

# fish
'''
鱼仓满时是否自动卖鱼，关闭此选项后，鱼仓满时会停止脚本
'''
SELL_FISH = True

'''
缺少鱼饵时是否自动购买鱼饵，关闭此选项后，缺少鱼饵时会停止脚本
'''
BUY_BAIT = True

'''
每次购买几组鱼饵（每组99个）
'''
BUY_BAIT_STACK_COUNT = 5

'''
钓鱼时绿条中间多少比例的范围内不移动黄色光标（范围0~1）
'''
GREEN_BAR_SAFE_PROPORTION = 0.4