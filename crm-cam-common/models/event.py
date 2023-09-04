from mtkext.dt import getCurrentDatetime
from .cam import db_neocam
from mtkext.base import *


class WebTrafficEvent(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_web_traffic_event"

    event_id = BigAutoField(help_text='行为流水ID')
    uuid = CharField(max_length=64, index=True, help_text='CookieId或设备Id')
    member_no = CharField(max_length=32, null=True, help_text='会员号')
    user_id = CharField(max_length=32, null=True, help_text='unionid/openid/支付宝user_id')
    account_id = IntegerField(help_text='品牌数字编码')
    site_id = IntegerField(help_text='网站数字编码')
    page_id = CharField(max_length=32, null=True, help_text='页面编码')
    page_type = CharField(max_length=32, null=True, help_text='页面类型')
    session_id = CharField(max_length=64, help_text='用户会话ID')
    keyword = CharField(max_length=32, null=True, help_text='搜索词')
    referer = TextField(null=True, help_text='第一方referer')
    title = CharField(max_length=96, null=True, help_text='标题')
    ip = CharField(max_length=16, help_text='IP地址')
    province = CharField(max_length=32, null=True, help_text='IP：省份')
    city = CharField(max_length=16, null=True, help_text='IP：城市')
    host = CharField(max_length=32, null=True, help_text='URL：host')
    path = CharField(max_length=128, null=True, help_text='URL：path')
    qs = JSONField(null=True, help_text='URL：query_string')
    cid = IntegerField(null=True, help_text="活动cid")
    utm_source = CharField(max_length=32, null=True, help_text='UTM参数1')
    utm_campaign = CharField(max_length=32, null=True, help_text='UTM参数2')
    utm_medium = CharField(max_length=32, null=True, help_text='UTM参数3')
    create_time = DateTimeField(index=True, default=getCurrentDatetime, constraints=[auto_create, auto_update])


class WxmpShareEvent(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_wmp_share_event"

    event_id = BigAutoField(help_text='事件流水ID')
    event_time = IntegerField(default=0, help_text='事件时间', index=True)
    ip = CharField(max_length=16, null=True, help_text='IP-V4')
    uuid = CharField(max_length=32, help_text='UUID')
    appid = CharField(max_length=32, help_text='公众号ID')
    appver = CharField(max_length=8, null=True)
    sdkver = CharField(max_length=8, null=True)
    create_time = DateTimeField(default=getCurrentDatetime)
    openid = CharField(max_length=64, null=True, help_text='微信openid')
    unionid = CharField(max_length=64, null=True, help_text='微信unionid')
    title = CharField(max_length=64, null=True)
    path = CharField(max_length=256, null=True)
    cid = IntegerField(null=True, help_text="活动cid")
    desc = TextField(null=True)
    image_url = CharField(max_length=256, null=True)