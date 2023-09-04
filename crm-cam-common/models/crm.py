# -*- coding: utf-8 -*-

from mtkext.base import *
from sanic.log import logger
from copy import deepcopy
from peewee import MySQLDatabase


db_eros_crm = Proxy()


class UserTags(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_user_tags"

    auto_id = BigAutoField(help_text="自增主键")
    member_no = CharField(max_length=32, help_text="会员号")
    crm_id = CharField(max_length=32, help_text="所属实例")
    tag_001 = CharField(32, null=True, help_text="标签值 level_id")
    tag_002 = CharField(32, null=True, help_text="标签值 ")
    tag_003 = CharField(32, null=True, help_text="标签值 ")
    tag_004 = CharField(32, null=True, help_text="标签值 ")
    tag_005 = CharField(32, null=True, help_text="标签值 ")
    tag_006 = CharField(32, null=True, help_text="标签值 ")
    tag_007 = CharField(32, null=True, help_text="标签值 ")
    tag_008 = CharField(32, null=True, help_text="标签值 ")
    tag_009 = CharField(32, null=True, help_text="标签值 ")
    tag_010 = CharField(32, null=True, help_text="标签值 ")
    tag_011 = CharField(32, null=True, help_text="标签值 ")
    tag_012 = CharField(32, null=True, help_text="标签值 ")
    tag_013 = CharField(32, null=True, help_text="标签值 ")
    tag_014 = CharField(32, null=True, help_text="标签值 ")
    tag_015 = CharField(32, null=True, help_text="标签值 ")
    tag_016 = CharField(32, null=True, help_text="标签值 ")
    tag_017 = CharField(32, null=True, help_text="标签值 ")
    tag_018 = CharField(128, null=True, help_text="标签值 ")
    tag_019 = CharField(128, null=True, help_text="标签值 ")
    tag_020 = CharField(128, null=True, help_text="标签值 ")
    tag_021 = CharField(128, null=True, help_text="标签值 ")
    tag_022 = CharField(128, null=True, help_text="标签值 ")
    tag_023 = CharField(128, null=True, help_text="标签值 ")
    tag_024 = CharField(128, null=True, help_text="标签值 ")
    tag_025 = CharField(128, null=True, help_text="标签值 ")
    tag_026 = CharField(128, null=True, help_text="标签值 ")
    tag_027 = CharField(128, null=True, help_text="标签值 ")
    tag_028 = CharField(128, null=True, help_text="标签值 ")
    tag_029 = CharField(128, null=True, help_text="标签值 ")
    tag_030 = CharField(128, null=True, help_text="标签值 ")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


# 标签相关
class TagInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_tag_info"
        auto_id_base = 200000
        indexes = (
            (('crm_id', 'tag_name'), False),
        )

    tag_id = AutoField(help_text="标签编码")
    crm_id = CharField(max_length=32, help_text="所属实例")
    bind_field = CharField(max_length=32, null=True, help_text="绑定宽表字段")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
