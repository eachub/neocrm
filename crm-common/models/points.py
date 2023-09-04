#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from .base import *


class PointsSummary(Model):
    """积分总览表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_summay"
        indexes = (
            (('member_no', 'crm_id'), True),
        )

    detail_id = BigAutoField(help_text="主键ID")
    crm_id = CharField(32, help_text="crm实例ID")
    member_no = CharField(32, help_text="会员号")
    total_points = DecimalField(20, 4, default=0, help_text="累计积分")
    freeze_points = DecimalField(20, 4, default=0, help_text="冻结积分")
    expired_points = DecimalField(20, 4, default=0, help_text="过期积分")
    active_points = DecimalField(20, 4, default=0, help_text="可用积分")
    used_points = DecimalField(20, 4, default=0, help_text="已使用的积分")  # 转赠也放在这里面了
    future_expired = DecimalField(20, 4, default=0, help_text="快过期积分(7天)")

    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class PointsHistory(Model):
    """积分事件明细记录"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_history"
        indexes = (
            (('member_no', 'event_no'), True),
        )

    auto_id = BigAutoField(help_text="主键ID")
    crm_id = CharField(32, help_text="crm实例ID")
    member_no = CharField(32, help_text="会员号")
    event_no = CharField(32, unique=True, help_text="事件唯一编码")
    origin_event_no = CharField(32, null=True, help_text="冲正对应事件唯一编码,不支持冲正冲正事件")
    redo_use_event = CharField(32, null=True, help_text="积分冲正使用的事件")
    from_transfer_no = CharField(32, null=True, help_text="转赠来源ID")
    action_scene = CharField(16, help_text="积分场景编码")
    event_type = CharField(32, help_text="事件类型 produce累加 consume消耗 reverse_produce \
                           reverse_consume expire过期  present 转赠 accept领取")
    reverse_status = SmallIntegerField(default=0, help_text="冲正状态 0-正常状态 1-已冲正")
    amount = FloatField(null=True, help_text="涉及金额")
    points = DecimalField(20, 4, null=True, help_text="涉及的积分")
    expire_time = DateTimeField(null=True, help_text="积分过期时间")
    unfreeze_time = DateTimeField(null=True, help_text="积分解冻时间")
    store_code = CharField(32, null=True, help_text="来源店铺")
    cost_center = CharField(64, null=True, help_text="成本中心")
    campaign_code = CharField(32, null=True, help_text="活动id")
    operator = CharField(64, null=True, help_text="操作员")
    event_desc = CharField(128, null=True, help_text="事件描述")
    # todo order_items 是否存到另外一个extend表里面
    order_items = JSONField(null=True, help_text="订单信息")
    event_at = DateTimeField(constraints=[auto_create], index=True, help_text="事件发生的时间")
    create_time = DateTimeField(constraints=[auto_create], index=True, help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class PointsAvailable(Model):
    """可用积分表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_available"
        indexes = (
            (('member_no', 'event_no'), False),
        )

    auto_id = BigAutoField(help_text="主键ID")
    crm_id = CharField(32, help_text="crm实例ID")
    member_no = CharField(32, help_text="会员号")
    event_no = CharField(32, unique=True, help_text="事件唯一编码")

    points = DecimalField(20, 4, null=True, help_text="可用积分")
    expire_time = DateTimeField(null=True, help_text="积分过期时间")
    unfreeze_time = DateTimeField(null=True, help_text="积分解冻时间")
    transfer_expire = DateTimeField(null=True, help_text="转赠的窗口期")

    event_at = DateTimeField(constraints=[auto_create], index=True, help_text="事件发生的时间")
    create_time = DateTimeField(constraints=[auto_create], index=True, help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class PointsConsumeRecord(Model):
    """积分消费记录表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_consume_record"
        indexes = (
            (('member_no', 'event_no'), False),
        )

    auto_id = BigAutoField(help_text="主键ID")
    crm_id = CharField(32, help_text="crm实例ID")
    member_no = CharField(32, help_text="会员号")
    event_no = CharField(32, help_text="积分消耗事件")
    points = DecimalField(20, 4, null=True, help_text="消耗的积分")
    store_code = CharField(32, null=True, help_text="来源店铺")
    cost_center = CharField(64, null=True, help_text="成本中心")
    consuemd_event = CharField(32, help_text="被消耗的积分事件id")
    points_used = DecimalField(20, 4, default=0, help_text="使用被消耗事件的积分")
    points_remain = DecimalField(20, 4, default=0, help_text="被消耗积分事件剩余积分")

    create_time = DateTimeField(constraints=[auto_create], index=True, help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class PointsProduceRules(Model):
    """积分累积场景规则"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_produce_rules"
        indexes = (
            (('crm_id', 'action_scene'), False),
        )

    rule_id = AutoField(help_text="规则")
    crm_id = CharField(32, help_text="crm实例ID")
    rule_name = CharField(128, help_text="规则的名称")
    action_scene = CharField(32, help_text="积分场景编码")
    points_type = CharField(16, help_text="积分类型 事件event或订单order")
    ratio_points = IntegerField(null=True, help_text="订单为积分倍率 事件为积分值")
    per_money = FloatField(null=True, help_text="每增加X元")
    change_points = DecimalField(20, 4, null=True, help_text="积分的变更值")
    max_times = IntegerField(null=True, help_text="最大次数")
    max_points = IntegerField(null=True, help_text="最多积分")
    range_days = IntegerField(null=True, help_text="时间周期单位day 多长时间范围内最大次数 最多积分")

    freeze_term = IntegerField(null=True, help_text="积分冻结时长 单位day")
    expire_term = IntegerField(null=True, help_text="积分过期时长 单位day")
    disabled = BooleanField(default=False, help_text="启用状态")
    is_deleted = BooleanField(default=False, help_text="逻辑删除")

    create_time = DateTimeField(constraints=[auto_create], index=True, help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class PointsConsumeRules(Model):
    """积分消耗场景规则"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_consume_rules"
        indexes = (
            (('crm_id', 'action_scene'), False),
        )

    rule_id = AutoField(help_text="规则")
    crm_id = CharField(32, help_text="crm实例ID")
    rule_name = CharField(128, help_text="规则的名称")
    action_scene = CharField(32, help_text="积分场景编码")
    points_type = CharField(16, null=True, help_text="积分类型 冗余比场景更大的分类:积分抵扣")
    base_points = DecimalField(20, 4, null=True, help_text="X积分")
    convert_money = FloatField(null=True, help_text="兑换成Y元")
    consume_level = SmallIntegerField(default=0, help_text="阶梯消费 1234 越小越优先消费")
    disabled = BooleanField(default=False, help_text="启用状态")
    is_deleted = BooleanField(default=False, help_text="逻辑删除")

    create_time = DateTimeField(constraints=[auto_create], index=True, help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class RuleGoodsWhite(Model):
    """规则的商品白名单"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_rules_goods_white"

    auto_id = AutoField(help_text="主键递增")
    crm_id = CharField(32, help_text="crm实例ID")
    rule_id = IntegerField(help_text="规则id")
    rule_type = CharField(16, help_text="规则的类型 produce consume")
    sku_id = CharField(32, null=True, help_text="商品的sku信息")
    goods_id = CharField(32, null=True, help_text="商品的goods信息")

    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class PointsTransfer(Model):
    """积分转赠记录"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_transfer"
        indexes = (
            (('crm_id', 'transfer_no'), False),
        )

    auto_id = AutoField(help_text="主键")
    transfer_no = CharField(32, unique=True, help_text="转赠事件no")
    crm_id = CharField(32, help_text="crm实例ID")
    from_user = CharField(32, help_text="发送积分用户")
    to_user = CharField(32, null=True, help_text="领取积分用户")
    trans_type = CharField(16, help_text="转赠的类型 转赠积分 by_points 转赠事件 by_event")
    points = DecimalField(20, 4, help_text="转赠的积分")
    accept_time = DateTimeField(null=True, help_text="积分领取时间,截止未领取,积分退回")
    transfer_expire = DateTimeField(null=True, help_text="窗口过期时间")
    done = SmallIntegerField(default=0, help_text="任务完成的标识 -1自动过期")
    points_detail = JSONField(
        null=True, help_text="积分转赠的详情 1.用户指定转哪几笔 2给定积分计算用户哪几笔事件")

    event_at = DateTimeField(constraints=[auto_create], index=True, help_text="事件发生的时间")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], index=True, help_text="更新时间")


class TaskRecord(Model):
    """脚本任务执行记录"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_points_task"

    record_id = BigAutoField()
    types = CharField(16, default='hourly, by_day')
    code = CharField(64, default='任务标识')
    task_time = DateTimeField(index=True, default='日期')
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")


class OrderInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_order_info"
        indexes = (
            (('member_no', 'crm_id'), False),
            (('record_time', 'mall_id', 'biz_status', 'platform'), False),
            (('create_time', 'mall_id', 'biz_status', 'platform'), False),
            (('order_sn', 'mall_id', 'biz_status', 'platform'), True),
        )

    auto_id = BigAutoField()
    member_no = CharField(max_length=32, help_text="会员号")
    crm_id = CharField(max_length=32, help_text="CRM实例id")
    order_sn = CharField(max_length=64, help_text="订单序列号")
    mall_id = CharField(max_length=32, help_text="商城编号")
    platform = CharField(max_length=16, help_text="冗余字段：平台编号")
    shop_code = CharField(max_length=32, null=True, help_text="线上店铺编号")
    pay_status = SmallIntegerField(default=0, help_text="支付状态 (0-未支付,1-部分支付,2-已支付)")
    order_status = SmallIntegerField(default=0, help_text="发货状态：1待发货，2已发货待签收，3已签收")
    refund_status = SmallIntegerField(default=0, help_text="售后及退款状态：1无售后或售后关闭，2售后处理中，3退款中，4 退款成功")
    biz_status = SmallIntegerField(default=0, help_text="推导的业务状态：1创建；2取消；3签收；4退货")
    goods_amount = FloatField(null=True, help_text="商品金额")
    deliver_amount = FloatField(null=True, help_text="运费")
    pay_amount = FloatField(null=True, help_text="支付金额；商品金额+运费-订单级的折扣")
    pay_no = CharField(max_length=64, null=True, help_text="支付号")
    pay_type = CharField(max_length=32, null=True, help_text="支付类型")
    deliver_type = SmallIntegerField(default=0, help_text="配送方式: 1-物流配送，2-同城限时达，3-到店自提，4-门店交易，5-无需物流")
    refund_mode = SmallIntegerField(default=0, help_text="退款方式: 1-设置CRO.EXT5=F")
    buyer_words = TextField(null=True, help_text="买家留言")
    seller_words = TextField(null=True, help_text="卖家备注")
    receiver_name = CharField(max_length=32, null=True, help_text="收件人名字")
    receiver_phone = CharField(max_length=16, null=True, index=True, help_text="收件人手机号")
    receiver_address = TextField(default="", help_text="收件人地址")
    province = CharField(max_length=16, null=True, help_text="省份")
    province_code = CharField(max_length=16, null=True, help_text="省份行政区域代码")
    city = CharField(max_length=16, null=True, help_text="所属城市")
    city_code = CharField(max_length=16, null=True, help_text="所属城市行政区域代码")
    area = CharField(max_length=32, null=True, help_text="所属区")
    area_code = CharField(max_length=16, null=True, help_text="所属区行政区域代码")
    longitude = FloatField(null=True, help_text="经度，范围为 -180~180，负数表示西经")
    latitude = FloatField(null=True, help_text="纬度，范围为 -90~90，负数表示南纬")
    logistics = JSONField(null=True, help_text="快递信息：冗余字段，详见DeliverInfo")
    create_time = DateTimeField(null=True, help_text="创建的业务时间")
    pay_time = DateTimeField(null=True, help_text="支付时间")
    deliver_time = DateTimeField(null=True, help_text="发货时间")
    receive_time = DateTimeField(null=True, help_text="确认收货")
    author_info = JSONField(null=True, help_text="主播信息")
    extra = JSONField(null=True, help_text="扩充字段，保存补充信息")
    item_list = JSONField(null=True, help_text="商品信息")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="记录更新的时间")
    record_time = DateTimeField(constraints=[auto_create], help_text="记录创建的时间")


class OrderItem(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_order_item"
        indexes = (
            (('member_no', 'crm_id'), False),
            (('order_sn', 'sku_id', 'child_id'), True),
            (('create_time', 'mall_id'), False),
        )

    item_id = BigAutoField(help_text="Item顺序ID")
    crm_id = CharField(max_length=32, help_text="CRM实例id")
    member_no = CharField(max_length=32, help_text="会员号")
    userid = CharField(max_length=32, null=True, index=True, help_text="微信unionid，或其他平台id")
    mall_id = CharField(max_length=32, help_text="冗余：商城编号")
    item_code = CharField(max_length=32, null=True, help_text="渠道Item编码")
    child_id = IntegerField(default=1, help_text="行拆单后，ChildItem编号")
    order_sn = CharField(max_length=64, help_text="所属渠道订单号")
    sub_order_id = CharField(max_length=64, index=True, help_text="子订单号")
    warehouse_id = BigIntegerField(null=True, help_text="零售圈ID")
    goods_id = CharField(null=True, max_length=64, help_text="商品编号")
    sku_id = CharField(null=True, max_length=64, help_text="商品规格编码")
    erp_goods_id = CharField(max_length=32, null=True, help_text="商品ERP编号")
    erp_sku_code = CharField(max_length=32, null=True, help_text="规格ERP编码")
    goods_name = TextField(null=True, help_text="商品名称")
    goods_spec = TextField(null=True, help_text="商品规格")
    goods_count = IntegerField(null=True, help_text="商品数量")
    goods_price = FloatField(null=True, help_text="商品销售价格")
    goods_pic = TextField(null=True, help_text="图片")
    total_amount = FloatField(null=True, constraints=[SQL('default 0')], help_text="商品总金额+其他费用")
    pay_amount = FloatField(default=0, help_text="商品支付金额=总金额-商品级的总折扣")
    pmt_seller = FloatField(null=True, constraints=[SQL('default 0')], help_text="商品级的商家折扣金额（含均摊）")
    allocated = BooleanField(default=False, help_text="是否已经：拆单并单到ERP")
    refunded = BooleanField(default=False, help_text="是否已经生成退货单")
    erp_order_no = CharField(max_length=64, null=True, index=True, help_text="关联的ERP订单编号")
    rights_status = IntegerField(default=0, help_text="维权状态 (0-未维权,1-维权中,2-已退款)")
    refund_no = CharField(max_length=64, null=True, index=True, help_text="退单号，NULL表示未退单")
    pre_sale_id = BigIntegerField(null=True, index=True, help_text='预售活动id')
    author_id = BigIntegerField(null=True, help_text="主播id")
    author_name = CharField(max_length=32, null=True, help_text="主播名称")
    create_time = DateTimeField(null=False, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class RefundInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_refund_info"
        indexes = (
            (('create_time', 'mall_id'), False),
            (('update_time', 'mall_id'), False),
        )

    auto_id = BigAutoField()
    crm_id = CharField(max_length=32, help_text="CRM实例id")
    refund_id = CharField(max_length=64, null=True, help_text="Refund自增编号")
    user_id = CharField(max_length=32, index=True, help_text="微信unionid，或其他平台id")
    member_no = CharField(max_length=32, null=True, index=True, help_text="会员号：冗余")
    mall_id = IntegerField(help_text="商城编号")
    order_sn = CharField(max_length=64, index=True, help_text="渠道订单号")
    pay_no = CharField(max_length=64, null=True, help_text="支付号")
    after_sales_type = SmallIntegerField(default=0, help_text="售后类型 1-仅退款，2-退货退款，3-换货，4-补寄，5-维修调试")
    after_sales_status = SmallIntegerField(default=0,
                                           help_text="售后状态：1-已申请,等待处理 2-申请通过,等待买家填写快递信息 3-快递信息已录入,等待寄回 4-收到买家退货,5-系统退款中,6-退款完成,7-用户取消售后,8-商家拒绝,9-退款失败")
    after_sales_reason = TextField(null=True, help_text="售后原因")
    is_received = BooleanField(null=True, help_text="是否已收到货物")
    evidence = JSONField(null=True, help_text="证据截图，path数组")
    pay_amount = FloatField(null=True, help_text="item已支付金额（元）")
    refund_amount = FloatField(null=True, help_text="退款金额（元）")
    deliver_type = SmallIntegerField(default=0, help_text="配送方式: 1-物流配送,2-同城限时达,3-到店自提")
    logistics_no = CharField(max_length=32, null=True, help_text="快递单号")
    company_code = CharField(max_length=16, null=True, help_text="快递公司编码")
    company_name = CharField(max_length=64, null=True, help_text="快递公司名称")
    create_time = DateTimeField(constraints=[auto_create], help_text="记录创建的时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="记录更新的时间")


class RefundItem(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_refund_item"
        indexes = (
            (('refund_id', 'sku_id'), True),
            (('order_sn', 'sku_id'), False),
        )

    auto_id = BigAutoField(help_text="顺序ID")
    crm_id = CharField(max_length=32, help_text="CRM实例id")
    mall_id = IntegerField(help_text="商城编号")
    order_sn = CharField(max_length=64, help_text="渠道订单号")
    refund_id = CharField(max_length=64, null=True, help_text="关联到的退单号，来自RefundInfo")
    origin_item_id = BigIntegerField(index=True, help_text="关联到的OrderItem")
    sku_id = BigIntegerField(default=0, help_text="冗余：商品规格编码")
    goods_count = IntegerField(default=0, help_text="商品数量")
    total_amount = FloatField(default=0, help_text="分摊的总额：实价x数量")
    pay_amount = FloatField(default=0, help_text="分摊的支付金额（元）")
    refund_amount = FloatField(default=0, help_text="分摊的退款金额（元）")
    rights_status = IntegerField(default=0, help_text="维权状态 (0-未维权,1-维权中,2-已退款)")
    refunded = SmallIntegerField(default=0, help_text="退货状态：0未退，其他=after_sales_type")
    create_time = DateTimeField(null=False, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
