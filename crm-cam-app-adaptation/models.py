# -*- coding: utf-8 -*-

from mtkext.base import *
db_neocam_adapt = Proxy()




class Instance(Model):
    class Meta:
        database = db_neocam_adapt
        table_name = "t_cam_instance"
        auto_id_base = 200000

    auto_id = BigAutoField()
    instance_id = CharField(max_length=32, unique=True, help_text="实例id")
    crm_id = BigIntegerField(null=True, help_text="crm id")
    mchid = CharField(max_length=64, help_text="mchid")
    appid = CharField(max_length=64, help_text="appId")
    woa_appid = CharField(max_length=64, help_text="绑定的公众号appId")
    instance_status = SmallIntegerField(default=0, help_text="实例状态 0已创建未绑定appid 1可用")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])

# class CampaignRecord(Model):
#     class Meta:
#         database = db_neocam
#         table_name = "t_cam_campaign_record"
#         indexes = (
#             (('create_time', 'member_no', 'campaign_id'), False),
#         )
#     auto_id = BigAutoField()
#     member_no = CharField(max_length=32, help_text="会员号")
#     campaign_id = IntegerField(help_text="活动ID")
#     create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
#     update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


