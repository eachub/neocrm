"""
卡券相关model
"""
from .base import *
from peewee import TimeField


class CouponInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_info"
        auto_id_base = 50000
        indexes = (
            (('crm_id', 'source', 'create_time'), False),
            (('begin_time', 'end_time'), False),
        )

    coupon_id = AutoField(help_text="自增编号，可以辅助生成card_id")
    crm_id = CharField(32, help_text="crm实例ID")
    card_id = CharField(max_length=64, unique=True, help_text="卡券编码：外部或uuid生成")
    source = SmallIntegerField(default=1, help_text='来源：1制作券  2微信商家券')
    card_type = SmallIntegerField(help_text="优惠券类型(0:代金券；1:折扣券；2:兑换券；3:包邮券；4:赠品券)")
    biz_type = CharField(max_length=32, null=True, default="normal", help_text="卡券业务类型 有使用方自定义，需支持筛选")
    # bind_mode = CharField(max_length=16, default='all', help_text="CouponBind模式：whitelist|blacklist|all")
    # use_with_other_offer = BooleanField(default=1, help_text="1：可与其他促销同时使用")
    # use_with_other_coupon = BooleanField(default=1, help_text="1：可与其他卡券同时使用")
    can_give_friend = BooleanField(default=0, help_text="1：可转赠给朋友")
    title = CharField(max_length=64, help_text="卡券标题")
    subtitle = CharField(max_length=128, help_text="卡券小标题")
    scene = JSONField(help_text="适用场景")
    notice = CharField(max_length=32, null=True, help_text="使用说明：字数上限为15个")
    rule = TextField(null=True, help_text="使用须知：64K")
    description = TextField(null=True, help_text="详情描述")
    date_type = SmallIntegerField(default=0, help_text="时间类型：1:固定时间范围；2:动态时间；3:永久有效")
    begin_time = DateTimeField(null=True, help_text="生效时间")
    end_time = DateTimeField(null=True, help_text="过期时间")
    start_day_count = IntegerField(default=0, help_text="领取后几天生效(date_type=2时有值)")
    expire_day_count = IntegerField(default=0, help_text="领取后几天有效(date_type=2时有值)")
    weekdays = JSONField(null=True, help_text="一周内可以使用的天数，0代表周日，1代表周一，以此类推。示例值：1, 2")
    monthdays = JSONField(null=True, help_text="一月内可以使用的天数")
    day_begin_time = TimeField(default="00:00:00", help_text="当天可用开始时间，单位：秒，1代表当天0点0分1秒。示例值：3600")
    day_end_time = TimeField(default="23:59:59", help_text="当天可用结束时间，单位：秒，86399代表当天23点59分59秒。示例值：86399")
    total_quantity = IntegerField(help_text="发券量")
    active_quantity = IntegerField(help_text="激活全量")
    generate_type = IntegerField(default=1, help_text="生成方式 1系统生成  2外部导入")
    # generate_file = CharField(null=True, help_text="外部导入文件路径")
    get_limit = IntegerField(default=1, help_text="卡券领取限制， 0不限")
    # use_limit = IntegerField(default=0, help_text="卡券数量使用限制， 0不限")
    cash_amount = FloatField(default=0, help_text="代金券：减免金额")
    cash_condition = FloatField(default=0, help_text="起用金额")
    qty_condition = IntegerField(default=0, help_text="购满M件")
    discount = FloatField(default=0, help_text="折扣券：折扣率（八折取值0.8）")
    icon = CharField(max_length=128, null=True, help_text='展示缩略图')
    cover_img = CharField(max_length=512, help_text="卡券封面图")
    extra_info = JSONField(null=True, help_text="附加信息：比如赠品配置")
    store_codes = JSONField(null=True, help_text="适用门店列表，空则不限 list")
    redeem_count = IntegerField(default=0, help_text="卡券核销总数")
    # cost_type = SmallIntegerField(default=0, help_text="成本费用类型  1固定金额  2百分比")
    # cost_value = FloatField(default=0, help_text="成本费用(>=0) cost_type=2时，如百分之八十取值0.8")

    interests_type = SmallIntegerField(default=0, help_text="权益类型：1:额度卡；2:频次卡")
    interests_amount = FloatField(default=0, help_text="权益总数")
    interests_period_type = SmallIntegerField(default=0, help_text="周期类型：1，天，2，周，3，月，4，年")
    interests_period_amount = FloatField(default=0, help_text="周期权益限制")
    discount_limit = IntegerField(default=0, help_text="优惠商品数量")

    removed = BooleanField(default=0, help_text="是否已删除")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class CouponCodeGenInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_code_gen_info"
        auto_id_base = 50000
        indexes = (
            (('crm_id', 'card_id', 'create_time'), False),
        )

    """
    卡券券码生成记录表
    """
    coupon_gen_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text="crm实例ID")
    card_id = CharField(max_length=64, index=True, help_text="卡券编码")
    gen_status = IntegerField(default=0, help_text="0.等待生成券码，1.生成中，2.已完成")
    quantity = IntegerField(help_text="批次生成数量")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class UserCouponCodeInfo(Model):
    """
    用户卡券关系表
    """

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_user_info"
        auto_id_base = 1
        indexes = (
            (('crm_id', 'card_id', 'member_no', 'card_code', 'received_time'), True),
            # (('begin_time', 'end_time'), False),
        )

    member_coupon_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text="crm实例ID")
    card_id = CharField(max_length=64, index=True, help_text="卡券编码：外部或uuid生成")
    member_no = CharField(max_length=32, index=True, help_text="会员号")
    receive_id = CharField(index=True, max_length=64, help_text='领取Id，用与幂等性控制')
    card_code = CharField(max_length=64, index=True, help_text="券码")
    start_time = DateTimeField(null=True, help_text="卡券生效时间，领取生效模式 必填")
    end_time = DateTimeField(null=True, help_text="卡券过期时间，领取生效模式 必填")
    code_status = IntegerField(help_text="卡券状态，1.可用，2.转赠中，3.已核销，4.已过期，5.转赠已领取，6.已作废, 7.领取冲正【作废】")
    outer_str = CharField(default="default", index=True, help_text="领取渠道，默认default, 转赠领取.present_received")
    cost_center = CharField(null=True, max_length=128, help_text="领取成本中心编号")
    received_info = JSONField(null=True, help_text='领取信息')
    received_time = DateTimeField(constraints=[auto_create], help_text="领取时间")
    redeem_time = DateTimeField(null=True, help_text="核销时间")
    present_time = DateTimeField(null=True, help_text="转赠时间")
    obsoleted_time = DateTimeField(null=True, help_text="作废时间")
    receive_reverse_time = DateTimeField(null=True, help_text="冲正时间")
    expired_time = DateTimeField(null=True, help_text="过期时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class UserCouponRedeemInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_user_redeem_info"
        auto_id_base = 1000
        indexes = (
            # (('crm_id', 'card_id', 'member_no', 'card_code', 'received_time'), True),
            # (('begin_time', 'end_time'), False),
        )

    redeem_coupon_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text="crm实例ID")
    card_id = CharField(max_length=64, index=True, help_text="卡券编码：外部或uuid生成")
    member_no = CharField(max_length=32, index=True, help_text="会员号")
    card_code = CharField(max_length=64, index=True, help_text="券码")
    redeem_channel = CharField(default="default", index=True, max_length=128, help_text='核销渠道')
    outer_redeem_id = CharField(max_length=128, unique=True, help_text="核销ID，幂等控制")
    store_code = CharField(null=True, help_text="核销门店")
    redeem_count = IntegerField(default=1, help_text="核销次数")
    redeem_cost_center = CharField(null=True, max_length=128, help_text="核销成本中心编号")
    redeem_info = JSONField(null=True, help_text="额外信息")
    rollback_status = IntegerField(default=0, help_text="0.正常，1.回滚")
    redeem_time = DateTimeField(constraints=[auto_create])
    rollback_time = DateTimeField(null=True, help_text="回滚时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class UserPresentCouponInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_user_present_info"
        auto_id_base = 1000

    present_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text="crm实例ID")
    from_member_no = CharField(max_length=32, index=True, help_text="会员号")
    to_member_no = CharField(max_length=32, null=True, index=True, help_text="会员号")
    card_id = CharField(max_length=64, index=True, help_text="卡券编码：外部或uuid生成")
    card_code = CharField(max_length=64, help_text="券码")
    present_gen_id = CharField(max_length=128, unique=True, help_text='发起转赠时生成的ID')
    present_type = IntegerField(default=1, help_text="1.转赠需领取，2.转赠直塞（不用单独领取）")
    present_status = IntegerField(default=1, help_text="1.转赠中，2.已领取，3.已退回，4.自动退回")
    received_time = DateTimeField(null=True, help_text="接受转赠时间")
    go_back_time = DateTimeField(null=True, help_text="退回时间")
    present_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class CouponCodeInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_code_info"
        auto_id_base = 1000
        indexes = (
            (('crm_id', 'card_id', 'card_code'), True),
            # (('begin_time', 'end_time'), False),
        )

    # 是否需要反查用户ID
    auto_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, index=True, help_text="crm实例ID")
    card_id = CharField(max_length=64, help_text="卡券编码：外部或uuid生成")
    card_code = CharField(max_length=64, help_text='券码')
    coupon_gen_id = IntegerField(help_text="券码生成批次号")
    card_code_status = IntegerField(default=0, help_text='0.未激活，1.激活预存，2.已领取，3.已作废')


class UserCouponReceivedDetail(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_user_receive_detail"
        auto_id_base = 1000
        indexes = (
            (('crm_id', 'member_no', 'card_id'), True),
            # (('begin_time', 'end_time'), False),
        )

    auto_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, index=True, help_text="crm实例ID")
    member_no = CharField(max_length=64, index=True, help_text='用户ID')
    card_id = CharField(max_length=64, help_text='卡券ID')
    count = IntegerField(default=1, help_text="领取次数")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class UserReceivedRecord(Model):
    class Meta:
        database = db_eros_crm
        db_table = "t_crm_coupon_user_receive_record"

    indexes = (
        (('crm_id', 'member_no', 'receive_id'), True),
    )

    auto_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text="crm实例ID")
    member_no = CharField(max_length=64, help_text='用户ID')
    receive_id = CharField(max_length=64, help_text='领取Id，第三方领取ID，用与幂等性控制')
    create_time = DateTimeField(constraints=[auto_create])


class StatisticalCoupon(Model):
    """卡劵分析-趋势"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_stas_cards"
        indexes = (
            (('crm_id', 'card_id', 'tdate', 'thour'), True),
            (('tdate', 'thour'), False),
        )

    auto_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text='crm_id')
    card_id = CharField(max_length=64, null=True, help_text="card_id")
    tdate = DateField(help_text='日期')
    thour = IntegerField(default=99, help_text='0~23，99表示整天')
    receive_cards = IntegerField(default=0, help_text='领取卡券')
    receive_cards_user = IntegerField(default=0, help_text='领取卡券人数')
    redeem_cards = IntegerField(default=0, help_text='核销卡券')
    redeem_cards_user = IntegerField(default=0, help_text='核销卡券人数')
    present_cards = IntegerField(default=0, help_text='转赠卡券')
    present_cards_user = IntegerField(default=0, help_text='转赠卡券人数')
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class UserInterestsCostInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_user_interests_cost_info"
        indexes = (
            (('card_code', 'member_no', 'crm_id', 'card_id', 'interests_period_value',
              'interests_period_type'), True),
            # (('begin_time', 'end_time'), False),
        )

    redeem_coupon_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text="crm实例ID")
    card_id = CharField(max_length=64, index=True, help_text="卡券编码：外部或uuid生成")
    member_no = CharField(max_length=32, index=True, help_text="会员号")
    card_code = CharField(max_length=64, index=True, help_text="券码")
    interests_period_type = IntegerField(default=0, help_text="周期类型")
    interests_period_value = IntegerField(default=0, help_text="周期值")
    redeem_amount = FloatField(default=0, help_text="核销额度")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class UserInterestsCostRecord(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_coupon_user_interests_cost_record"
        indexes = (
            # (('crm_id', 'card_id', 'member_no', 'card_code', 'received_time'), True),
            # (('begin_time', 'end_time'), False),
        )

    redeem_coupon_id = AutoField(help_text="自增编号")
    crm_id = CharField(max_length=32, help_text="crm实例ID")
    card_id = CharField(max_length=64, index=True, help_text="卡券编码：外部或uuid生成")
    member_no = CharField(max_length=32, index=True, help_text="会员号")
    card_code = CharField(max_length=64, index=True, help_text="券码")
    redeem_channel = CharField(default="default", index=True, max_length=128, help_text='核销渠道')
    outer_redeem_id = CharField(max_length=128, unique=True, help_text="核销ID，幂等控制")
    store_code = CharField(null=True, help_text="核销门店")
    redeem_amount = FloatField(default=0, help_text="核销额度")
    redeem_cost_center = CharField(null=True, max_length=128, help_text="核销成本中心编号")
    redeem_info = JSONField(null=True, help_text="额外信息")
    rollback_status = IntegerField(default=0, help_text="0.正常，1.回滚")
    redeem_time = DateTimeField(constraints=[auto_create])
    rollback_time = DateTimeField(null=True, help_text="回滚时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update])
    create_time = DateTimeField(index=True, constraints=[auto_create])

