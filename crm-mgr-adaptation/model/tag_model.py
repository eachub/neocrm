from copy import deepcopy

import logging
from datetime import datetime, timedelta

from mtkext.base import *
from mtkext.db import FlexModel

logger = logging.getLogger(__name__)

db_eros_crm = Proxy()


def getUsertags(date_str=None):
    """获取usertags model"""
    # date_str格式 %Y%m%d
    if not date_str:
        now = datetime.now()
        yestaday = now - timedelta(days=1)
        date_str = datetime.strftime(yestaday, "%Y%m%d")
    model: UserTags = FlexModel.get(UserTags, date_str)
    return model


class UserTags(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_user_tags_%s"
        indexes = (
            (('member_no', 'crm_id'), True),
        )

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
    parent_id = IntegerField(null=True, help_text="父级标签ID")
    tag_name = CharField(max_length=32, help_text="标签名称")
    only_folder = BooleanField(default=False, help_text="仅作为标签目录")
    seqid = IntegerField(help_text="排序id")
    bind_field = CharField(max_length=32, null=True, help_text="绑定宽表字段")
    renew_mode = SmallIntegerField(default=0, help_text="更新模式：1-hourly, 2-daily")
    define_mode = SmallIntegerField(default=0, help_text="定义方式：1-自定义分档, 2-单指标映射，3-单指标区间化，10-产品库导入，11-企业微信导入")
    desc = MediumJSONField(null=True, help_text='tag定义描述')
    active = BooleanField(default=False, help_text="是否已激活")
    activate_at = DateTimeField(null=True, help_text="激活时间")
    qty = JSONField(null=True, help_text='预估规模: {"super_id":1123,"mobile":245,"unionid":523,"member_no":245}')
    build_in = SmallIntegerField(default=0, help_text="是否系统内置。1系统内置，可以编辑；2系统内置，不可以编辑；0或空，非系统内置")
    removed = BooleanField(default=False, help_text="是否删除")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class TagLevel(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_tag_level"
        auto_id_base = 6000000
        indexes = (
            (('tag_id', 'crm_id'), False),
        )

    level_id = AutoField(help_text="顺序编码")
    level_name = CharField(max_length=32, help_text="冗余：所属实例")
    tag_id = IntegerField(help_text="归属：标签编码")
    crm_id = CharField(max_length=32, help_text="所属实例")
    seqid = IntegerField(help_text="标签下的排序id")
    rules = JSONField(null=True, help_text="标签规则数组")
    rule_count = IntegerField(default=0, help_text="规则条数")
    qty = JSONField(null=True, help_text='预估规模: {"super_id":1123,"mobile":245,"unionid":523,"member_no":245}')
    removed = BooleanField(default=False, help_text="是否删除")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
