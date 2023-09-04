from mtkext.base import *

db_neocrm_adapt = Proxy()


class CRMModel(Model):
    class Meta:
        database = db_neocrm_adapt
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
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class InstanceInfo(Model):
    class Meta:
        database = db_neocrm_adapt
        table_name = "t_instance_info"

    # todo 带完善扩充
    auto_id = AutoField()
    instance_id = CharField(max_length=32, help_text="实例id", unique=True)
    crm_id = CharField(max_length=32, help_text="crmID")
    app_id = CharField(max_length=32, help_text="小程序APPID")
    account_id = CharField(max_length=32, help_text="活动H5埋点上报账户ID")
    woa_app_id = CharField(max_length=32, help_text="公众号APPID")
    mch_id = CharField(max_length=32, help_text="商户号ID")
    corp_id = CharField(max_length=32, help_text="企微ID")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class WxpayImage(Model):
    class Meta:
        # 适配层微信支付卡券图片管理
        database = db_neocrm_adapt
        db_table = "t_wxpay_image"

    auto_id = AutoField()
    instance_id = CharField(max_length=32, help_text="实例id")
    hashcode = CharField(max_length=64, unique=True, help_text="唯一码：sha256")
    origin_url = CharField(max_length=256, null=False, help_text="原始链接")
    info = JSONField(null=True, help_text="微信信息")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class MaterialApply(Model):
    class Meta:
        # 适配层微信支付卡券图片管理
        database = db_neocrm_adapt
        db_table = "t_crm_material_apply"

    auto_id = AutoField()
    instance_id = CharField(max_length=32, help_text="实例id")
    material_no = CharField(max_length=64, unique=True, help_text="素材编码")
    third_no = CharField(max_length=64, null=True, help_text="审批任务编码")
    apply_status = IntegerField(default=0, help_text="审批状态：#0，待审批, 1-审批中；2-已通过；3-已驳回；4-已撤销")
    removed = IntegerField(default=0, help_text="是否删除")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
