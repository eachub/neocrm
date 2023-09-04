from .base import *


class StatPoints(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_stat_points"
        primary_key = CompositeKey('crm_id', 'tdate', 'thour')
        indexes = (
            (('tdate', 'thour'), False),
        )

    crm_id = CharField(max_length=32, help_text='实例crm_id')
    tdate = DateField(help_text='日期')
    thour = IntegerField(default=99, help_text='0~23，99表示整天')
    # store_code = CharField(max_length=32, default="ALL", help_text="门店")
    # cost_center = CharField(max_length=64, default='ALL', help_text="成本中心")
    prod_points = DecimalField(20, 4, default=0, help_text='新增积分')
    total_prod = DecimalField(20, 4, default=0, help_text='累积新增积分')
    consume_points = DecimalField(20, 4, default=0, help_text='消耗积分')
    total_consume = DecimalField(20, 4, default=0, help_text='累积消耗积分')
    total_active = DecimalField(20, 4, default=0, help_text='累积可用积分')
    total_transfer = DecimalField(20, 4, default=0, help_text="累积转赠积分")
    total_accept = DecimalField(20, 4, default=0, help_text="累积领取转赠积分")
    expire_points = DecimalField(20, 4, default=0, help_text="过期积分")
    total_expire = DecimalField(20, 4, default=0, help_text="累积过期积分")

    prod_points_user = IntegerField(default=0, help_text='新增积分人数')
    total_prod_user = IntegerField(default=0, help_text='累积新增积分人数')
    consume_points_user = IntegerField(default=0, help_text='消耗积分人数')
    total_consume_user = IntegerField(default=0, help_text='累积消耗积分人数')
    total_active_user = IntegerField(default=0, help_text='累积可用积分人数')
    total_transfer_user = IntegerField(default=0, help_text="累积转赠积分人数")
    total_accept_user = IntegerField(default=0, help_text="累积领取转赠积分人数")
    expire_points_user = IntegerField(default=0, help_text="过期积分人数")
    total_expire_user = IntegerField(default=0, help_text="累积过期积分人数")

    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class StatUser(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_stat_user"
        primary_key = CompositeKey('crm_id', 'tdate', 'thour')
        indexes = (
            (('tdate', 'thour'), False),
        )

    crm_id = CharField(max_length=32, help_text='实例crm_id')
    tdate = DateField(help_text='日期')
    thour = IntegerField(default=99, help_text='0~23, 99表示整天')
    new_member = IntegerField(default=0, help_text='新增会员')
    total_member = IntegerField(default=0, help_text='累计会员')
    tmall_member = IntegerField(default=0, help_text="天猫会员")
    jd_member = IntegerField(default=0, help_text="京东会员")
    dy_member = IntegerField(default=0, help_text="抖音会员")
    new_family = IntegerField(default=0, help_text='新增家庭组成员')
    total_family = IntegerField(default=0, help_text='累积家庭组成员')
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class StatTagsQty(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_stat_tags_qty"
        primary_key = CompositeKey('level_id', 'tdate')
        indexes = (
            (('crm_id', 'tag_id', 'tdate'), False),
        )

    crm_id = CharField(max_length=32, help_text='实例crm_id')
    tag_id = IntegerField(help_text="标签id")
    level_id = IntegerField(help_text="标签的level_id")
    level_name = CharField(32, null=True, help_text="levelname 冗余字段")
    tdate = DateField(help_text='日期')
    qty = IntegerField(default=0, help_text="标签会员数量")
    desc = JSONField(null=True, help_text="当时的计算规则的描述")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
