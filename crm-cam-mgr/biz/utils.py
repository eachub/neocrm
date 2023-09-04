import functools
import time
from sanic.log import logger
from copy import deepcopy
from datetime import timedelta, date
from inspect import getabsfile, isawaitable
from sanic.kjson import json_dumps, json_loads

from mtkext.dt import dateFromString


def init_db_manager(loop, proxy, write_params=None, read_params=None, database=None):
    from peewee_async import PooledMySQLDatabase, Manager
    mgw = None
    if write_params:
        tmp_write_params = deepcopy(write_params)
        db = write_params.pop('database', None)
        db_write = PooledMySQLDatabase(**write_params, database=database or db)
        proxy.initialize(db_write)
        mgw = Manager(proxy, loop=loop)
    mgr = mgw  # TODO 暂时禁用读写分离
    if read_params:
       db = read_params.pop('database', None)
       db_read = PooledMySQLDatabase(**read_params, database=database or db)
       mgr = Manager(db_read, loop=loop)
    return mgw, mgr


def make_time_range(from_date, to_date, use_timestamp=0):
    if use_timestamp:
        from_time = int(time.mktime(from_date.timetuple()))
        to_time = int(time.mktime(to_date.timetuple())) + 86400
    else:
        if type(from_date) is str:
            from_date = dateFromString(from_date)
        if type(to_date) is str:
            to_date = dateFromString(to_date)
        from_time = f"{from_date:%Y-%m-%d} 00:00:00"
        tdate = to_date + timedelta(days=1)
        to_time = f"{tdate:%Y-%m-%d} 00:00:00"
    return from_time, to_time


"""
要求：被装饰的函数的第一个参数必须是app（已准备好redis），
其中还有一个keyword-only argument：to_date（date类型）
"""


def cache_to_date(ttl=120):
    def warpper_(func):
        @functools.wraps(func)
        async def handler(app, *args, to_date, **kwargs):
            if type(to_date) is str:
                tmp_to_date = dateFromString(to_date)
            else:
                tmp_to_date = to_date
            key, use_cache = "", (tmp_to_date < date.today())
            if use_cache:
                key = f"{func.__name__}@{getabsfile(func)}={':'.join(map(str, args))}:{to_date}:{kwargs}"
                got = await app.redis.get(key)
                if got:
                    logger.info(f"cache-hit: {key}")
                    return json_loads(got)
            result = func(app, *args, to_date=to_date, **kwargs)
            got = await result if isawaitable(result) else result
            if use_cache:
                logger.info(f"cache-new: {key}")
                await app.redis.setex(key, ttl, json_dumps(got))
            return got

        return handler

    return warpper_


scene_map = {
    "1000": "其他",
    "1001": "发现栏小程序主入口，「最近使用」列表",
    "1005": "微信首页顶部搜索框的搜索结果页",
    "1006": "发现栏小程序主入口搜索框的搜索结果页",
    "1007": "单人聊天会话中的小程序消息卡片",
    "1008": "群聊会话中的小程序消息卡片",
    "1010": "收藏夹",
    "1011": "扫描二维码",
    "1012": "长按图片识别二维码",
    "1013": "扫描手机相册中选取的二维码",
    "1014": "小程序订阅消息",
    "1017": "前往小程序体验版的入口页",
    "1019": "微信钱包",
    "1020": "公众号 profile 页相关小程序列表",
    "1022": "聊天顶部置顶小程序入口",
    "1023": "安卓系统桌面图标",
    "1024": "小程序 profile 页",
    "1025": "扫描一维码",
    "1026": "发现栏小程序主入口，「附近的小程序」列表",
    "1027": "微信首页顶部搜索框搜索结果页「使用过的小程序」列表",
    "1028": "我的卡包",
    "1029": "小程序中的卡券详情页",
    "1030": "自动化测试下打开小程序",
    "1031": "长按图片识别一维码",
    "1032": "扫描手机相册中选取的一维码",
    "1034": "微信支付完成页",
    "1035": "公众号自定义菜单",
    "1036": "App分享消息卡片<",
    "1037": "小程序打开小程序",
    "1038": "从另一个小程序返回",
    "1039": "摇电视",
    "1042": "添加好友搜索框的搜索结果页",
    "1043": "公众号模板消息",
    "1044": "带 shareTicket 的小程序消息卡片",
    "1045": "朋友圈广告",
    "1046": "朋友圈广告详情页",
    "1047": "扫描小程序码",
    "1048": "长按图片识别小程序码",
    "1049": "扫描手机相册中选取的小程序码",
    "1052": "卡券的适用门店列表",
    "1053": "搜一搜的结果页",
    "1054": "顶部搜索框小程序快捷入口",
    "1056": "聊天顶部音乐播放器右上角菜单",
    "1057": "钱包中的银行卡详情页",
    "1058": "公众号文章",
    "1059": "体验版小程序绑定邀请页",
    "1060": "微信支付完成页",
    "1064": "微信首页连Wi-Fi状态栏",
    "1065": "URL scheme",
    "1067": "公众号文章广告",
    "1068": "附近小程序列表广告",
    "1069": "移动应用通过openSDK进入微信，打开小程序",
    "1071": "钱包中的银行卡列表页",
    "1072": "二维码收款页面",
    "1073": "客服消息列表下发的小程序消息卡片",
    "1074": "公众号会话下发的小程序消息卡片",
    "1077": "摇周边",
    "1078": "微信连Wi-Fi成功提示页",
    "1079": "微信游戏中心",
    "1081": "客服消息下发的文字链",
    "1082": "公众号会话下发的文字链",
    "1084": "朋友圈广告原生页",
    "1088": "会话中查看系统消息，打开小程序",
    "1089": "微信聊天主界面下拉，「最近使用」栏",
    "1090": "长按小程序右上角菜单唤出最近使用历史",
    "1091": "公众号文章商品卡片",
    "1092": "公众号文章商品卡片",
    "1095": "小程序广告组件",
    "1096": "聊天记录，打开小程序",
    "1097": "微信支付签约原生页，打开小程序",
    "1099": "页面内嵌插件",
    "1100": "红包封面详情页打开小程序",
    "1101": "远程调试热更新",
    "1102": "公众号 profile 页服务预览",
    "1103": "发现栏小程序主入口，「我的小程序」列表",
    "1104": "微信聊天主界面下拉，「我的小程序」栏",
    "1106": "聊天主界面下拉，从顶部搜索结果页，打开小程序",
    "1107": "订阅消息，打开小程序",
    "1113": "安卓手机负一屏，打开小程序（三星）",
    "1114": "安卓手机侧边栏，打开小程序（三星）",
    "1119": "【企业微信】工作台内打开小程序",
    "1120": "【企业微信】个人资料页内打开小程序",
    "1121": "【企业微信】聊天加号附件框内打开小程序",
    "1124": "扫“一物一码”打开小程序",
    "1125": "长按图片识别“一物一码”",
    "1126": "扫描手机相册中选取的“一物一码”",
    "1129": "微信爬虫访问",
    "1131": "浮窗",
    "1133": "硬件设备打开小程序",
    "1135": "小程序profile页相关小程序列表，打开小程序",
    "1144": "公众号文章 - 视频贴片",
    "1145": "发现栏 - 发现小程序",
    "1146": "地理位置信息打开出行类小程序",
    "1148": "卡包-交通卡，打开小程序",
    "1150": "扫一扫商品条码结果页打开小程序",
    "1151": "发现栏 - 我的订单",
    "1152": "订阅号视频打开小程序",
    "1153": "“识物”结果页打开小程序",
    "1154": "朋友圈内打开“单页模式”",
    "1155": "“单页模式”打开小程序",
    "1157": "服务号会话页打开小程序",
    "1158": "群工具打开小程序",
    "1160": "群待办",
    "1167": "H5通过开放标签打开小程序",
    "1168": "移动应用直接运行小程序",
    "1169": "发现栏小程序主入口，各个生活服务入口",
    "1171": "微信运动记录（仅安卓）",
    "1173": "聊天素材用小程序打开",
    "1175": "视频号主页商店入口",
    "1176": "视频号直播间主播打开小程序",
    "1177": "视频号直播商品<",
    "1178": "在电脑打开手机上打开的小程序",
    "1179": "话题页打开小程序",
    "1181": "网站应用打开PC小程序",
    "1183": "PC微信 - 小程序面板 - 发现小程序 - 搜索",
    "1185": "群公告",
    "1186": "收藏 - 笔记",
    "1187": "浮窗",
    "1189": "表情雨广告",
    "1191": "视频号活动",
    "1192": "企业微信联系人profile页",
    "1194": "URL Link",
    "1195": "视频号主页商品tab",
    "1197": "视频号主播从直播间返回小游戏",
    "1198": "视频号开播界面打开小游戏",
    "1203": "微信小程序压测工具的请求",
}
