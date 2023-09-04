# -*- coding: utf-8 -*-
from copy import deepcopy

from mtkext.base import *
from peewee_async import MySQLDatabase
from sanic.log import logger
from mtkext.db import FlexModel

db_eros_crm = Proxy()


class CRMModel(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_info"

    auto_id = AutoField()
    crm_id = CharField(max_length=32, help_text="实例id", unique=True)
    salt = CharField(max_length=128, null=True,
                     help_text="盐 tmall 加密信息 md5(md5(tmall{mobile}{instance.salt}).hexdigest()).hexdigest()")
    jd_salt = JSONField(
        null=True,
        help_text="京东加密信息 品牌密钥 secret 商家应用标志 customerId 需要用来加密得出京东加密手机号 加密手机号=MD5(MD5(品牌秘钥+会员体系id[商家应用标志]+用户手机号+品牌秘钥)) MD5加密第一次加密后，需要转化为大写再进行第二次加密。")
    member_code_rule = JSONField(null=True, help_text="会员号编码规则 {prefix shuffix}")
    points_config = JSONField(null=True, help_text="积分相关的配置 consume_scene produce_scene")
    level_config = JSONField(null=True, help_text="等级的全局配置")
    benefit_config = JSONField(null=True, help_text="权益配置 权益类型 ")
    coupon_present_validity = IntegerField(default=1, help_text="转赠退回有效期 默认1天")
    black_cfg = JSONField(null=True, help_text="黑名单阈值配置")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class CRMChannelTypes(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_channel_types"

    type_id = AutoField()
    crm_id = CharField(32, help_text="实例id")
    name = CharField(16, help_text="渠道名称")
    type_no = CharField(8, help_text="渠道层级编号")
    parent_id = IntegerField(default=0, help_text="父级id")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
