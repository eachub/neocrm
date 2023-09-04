# -*- coding: utf-8 -*-

from mtkext.base import *
from sanic.log import logger
from copy import deepcopy
from peewee import MySQLDatabase


db_neocam = Proxy()


class CampaignInfo(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_campaign_info"
        auto_id_base = 60000
        indexes = (
            (('create_time', 'instance_id'), False),
        )
    campaign_id = AutoField(help_text="活动ID")
    campaign_name = CharField(max_length=64, help_text="活动名称")
    instance_id = CharField(max_length=64, help_text='账号实例ID')
    campaign_code = CharField(max_length=32, help_text='活动编码')
    campaign_type = IntegerField(help_text="活动类型 101：资源包签到活动,102：资源包抽奖活动,103：资源包发券页活动, 104：后台任务商品任务, 105：后台任务会员生日")
    begin_time = DateTimeField(help_text="开始时间")
    end_time = DateTimeField(help_text="结束时间")
    detail = JSONField(help_text="活动详细配置")
    campaign_path = CharField(max_length=256, null=True, help_text="资源包路径")
    desc = CharField(max_length=128, null=True, help_text="描述")
    status = IntegerField(default=0, help_text="活动状态，0，暂停，1，运行中，2，删除，3，活动尚未开始或者已经结束(实时判断)")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class LotteryRecord(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_lottery_record"
    """
    抽奖记录表
    """
    @staticmethod
    def get_table_name(cid):
        return f"LotteryRecord_{cid}", f"t_cam_lottery_record_{cid}"

    auto_id = AutoField()
    campaign_id = IntegerField(index=True, help_text="campaign id")
    instance_id = CharField(index=True, max_length=64, help_text="uid")
    member_no = CharField(index=True, max_length=64, help_text="会员号")
    lottery_config = JSONField(help_text="奖项配置")
    lottery_info = JSONField(help_text="中奖信息")
    lottery_type = IntegerField(help_text="中奖类型，可能为实物，需填地址 1.卡券（类型）、2.积分等  3. 未中奖, 4.实物,")
    extra = CharField(null=True, max_length=256, help_text="备用")
    prize_no = BigIntegerField(index=True, help_text="奖项id")
    is_received = SmallIntegerField(default=0, help_text="0:未领取 1：已领取")
    utm_source = CharField(max_length=64, null=True, help_text="活动推广来源")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")

class Signin(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_signin"
    """
    签到记录表
    """
    @staticmethod
    def get_table_name(cid):
        return f"Signin_{cid}", f"t_cam_signin_{cid}"

    auto_id = AutoField()
    campaign_id = IntegerField(help_text="campaign id")
    instance_id = CharField(index=True, max_length=64, help_text="uid")
    member_no = CharField(index=True, max_length=64, help_text="会员号")
    receive_prize = IntegerField(default=0, help_text="0:未领取 1：已领取, 暂不使用")
    prize_conf = JSONField(default={}, help_text="奖励信息")
    is_received = SmallIntegerField(default=0, help_text="0:未领取 1：已领取")
    utm_source = CharField(max_length=64, null=True, help_text="活动推广来源")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class CardRecord(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_card_received"
    """
    活动领券记录表
    """
    @staticmethod
    def get_table_name(cid):
        return f"Card_{cid}", f"t_cam_card_received_{cid}"

    auto_id = AutoField()
    campaign_id = IntegerField(help_text="campaign id")
    instance_id = CharField(index=True, max_length=64, help_text="uid")
    member_no = CharField(unique=True, max_length=64, help_text="会员号")
    card_conf = JSONField(default={}, help_text="领券信息")
    is_received = SmallIntegerField(default=0, help_text="0:未领取 1：已领取")
    utm_source = CharField(max_length=64, null=True, help_text="活动推广来源")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class UserWhiteList(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_user_white_list"
    """
     用户会员号白名单
    """
    @staticmethod
    def get_table_name(people_id):
        return f"UserWhiteList_{people_id}", f"t_cam_user_white_list_{people_id}"

    auto_id = AutoField()
    instance_id = CharField(max_length=64, help_text="instance id")
    # campaign_id = IntegerField(help_text="campaign id")
    member_no = CharField(unique=True, max_length=64, help_text="会员号")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class PeopleFile(Model):
    """目标人群文件"""

    class Meta:
        database = db_neocam
        table_name = "t_cam_people_file"

    auto_id = AutoField()
    instance_id = CharField(index=True, max_length=64, help_text="instance id")
    apply_type = SmallIntegerField(default=1, help_text="文件来源，暂时废弃")
    from_type = SmallIntegerField(default=1, help_text="文件类型1会员号")
    file_path = CharField(max_length=128, help_text="文件地址")
    file_name = CharField(max_length=64, index=True, help_text="文件名称")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")

class CampaignRecord(Model):
    class Meta:
        database = db_neocam
        table_name = "t_cam_campaign_record"

    @staticmethod
    def get_table_name(_date):
        return f"CampaignRecord_{_date}", f"t_cam_campaign_record_{_date}"

    auto_id = AutoField(help_text="自增ID")
    campaign_id = IntegerField(help_text="活动ID")
    instance_id = CharField(max_length=64, help_text='账号实例ID')
    # campaign_code = CharField(max_length=32, help_text='活动编码')
    campaign_type = IntegerField(help_text="活动类型 101：资源包签到活动,102：资源包抽奖活动,103：资源包发券页活动, 104：后台任务商品任务, 105：后台任务会员生日")
    member_no = CharField(index=True, max_length=64, help_text="会员号")
    event_type = CharField(default={}, help_text="1。参与活动（包括签到、购买商品任务、抽奖未中奖），2。领取奖励（签到领取奖励、领券、商品任务领取奖励、抽奖中奖）")
    prize_conf = JSONField(default={}, help_text="奖励信息")
    utm_source = CharField(max_length=64, null=True, help_text="活动推广来源")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class StatCalData(Model):
    """分析计算表"""
    class Meta:
        database = db_neocam
        table_name = 't_cam_stat_cal_data'
        primary_key = CompositeKey('cid', 'tdate', 'thour')
        indexes = (
            (('tdate', 'thour'), False),
        )

    cid = CharField(max_length=16, index=True, help_text="cid")
    tdate = DateField(index=True, help_text="统计日期")
    thour = IntegerField(default=99, help_text='0~23，99表示整天')

    expose_times = IntegerField(default=0, help_text="曝光数")
    close_times = IntegerField(default=0, help_text="关闭数")
    pick_num = IntegerField(default=0, help_text="领券数")
    expose_people = IntegerField(default=0, help_text="曝光人数 活动访客")
    click_people = IntegerField(default=0, help_text="点击人数 参与活动人数")
    pick_people = IntegerField(default=0, help_text="领券人数")
    share_gift_people = IntegerField(default=0, help_text="活动分享人数")
    register_member_people = IntegerField(default=0, help_text="注册会员人数")
    create_time = DateTimeField(null=False, index=True, constraints=[auto_create], help_text='创建时间')
    update_time = DateTimeField(null=True, constraints=[auto_update], help_text='更新时间')


class StatRegionData(Model):
    class Meta:
        database = db_neocam
        table_name = 't_cam_stat_region_data'
        primary_key = CompositeKey('cid', 'tdate', 'thour')
        indexes = (
            (('tdate', 'thour'), False),
        )

    cid = CharField(max_length=16, index=True, help_text="cid")
    tdate = DateField(index=True, help_text="统计日期")
    thour = IntegerField(default=99, help_text='0~23，99表示整天')
    province = CharField(max_length=16, null=True, help_text="省")
    city = CharField(max_length=16, null=True, help_text="市")
    numbers = IntegerField(default=0, help_text="人数")
    create_time = DateTimeField(null=False, index=True, constraints=[auto_create], help_text='创建时间')
    update_time = DateTimeField(null=True, index=True, constraints=[auto_update], help_text='更新时间')
