from mtkext.base import *
from models import db_neocrm_adapt



class GoodsInfo(Model):
    class Meta:
        database = db_neocrm_adapt
        table_name = "t_crm_goods_info"
        indexes = (
            (('create_time', 'mall_id'), False),
            (('begin_time', 'end_time'), False),
        )
    goods_id = BigAutoField(help_text="商品编码")
    mall_id = IntegerField(help_text="商城编号")
    cat_id_1 = SmallIntegerField(null=True, help_text="第1级类目")
    cat_id_2 = SmallIntegerField(null=True, help_text="第2级类目")
    rv = IntegerField(default=50, help_text="推荐值，取值0~100")
    goods_name = CharField(max_length=128, help_text="商品全名")
    goods_alias = CharField(max_length=64, null=True, help_text="商品别名")
    goods_type = IntegerField(default=1, help_text="1-普通商品，2-进口商品，3-海淘商品，4-优惠券，5-套装，6-赠品，7-试用品，9服务型")
    outer_goods_id = CharField(max_length=64, null=True, index=True, help_text="商品外部编码")
    extra = JSONField(null=True, help_text="商品补充说明：用作卡券等特殊商品")
    shelf_only = BooleanField(default=0, help_text="仅出现在货架，商城列表或搜索不可见")
    is_onsale = BooleanField(default=True, help_text="是否上架：0-下架，1-上架")
    begin_time = IntegerField(null=True, help_text="定时上架的时间：unix-timestamp")
    end_time = IntegerField(null=True, help_text="定时下架的时间：unix-timestamp")
    thumb_icon = CharField(max_length=128, null=True, help_text='缩略图')
    poster_image = CharField(max_length=128, null=True, help_text='海报图（通常750宽）')
    share_image = CharField(max_length=128, null=True, help_text='分享微信群icon（长宽比5:4）')
    share_words = TextField(null=True, help_text='分享提示文本')
    share_moments = CharField(max_length=128, null=True, help_text='分享朋友圈image')
    swiper_list = JSONField(null=True, help_text='轮播图-数组')
    intro_list = JSONField(null=True, help_text='详情图-数组')
    spec_name_1 = CharField(max_length=8, help_text="规格名称1：颜色、型号、尺寸...")
    spec_name_2 = CharField(max_length=8, null=True, help_text="规格名称2")
    freight_id = SmallIntegerField(null=True, help_text="运费模板ID")
    attrs = JSONField(null=True, help_text="商品属性表")
    services = JSONField(null=True, help_text="服务承诺")
    price_type = SmallIntegerField(default=1, help_text="定价类型：1-CNY, 2-score, 3-CNY和score组合购")
    min_price = FloatField(help_text='SKU最小价格，比如：99元起')
    max_price = FloatField(help_text='SKU最高价格，多规格有意义')
    min_score = FloatField(help_text='SKU最小积分：2000积分起')
    total_quantity = IntegerField(default=0, help_text='汇总sku的库存数')
    sales_base = IntegerField(default=0, help_text='销售量基数')
    sales_actual = IntegerField(default=0, help_text='实际销售量')
    weight = IntegerField(null=True, help_text='商品重量 (单位:克)，快递可能用到')
    removed = BooleanField(default=0, help_text="是否已删除")
    sku_list = JSONField(null=True, help_text="sku list 信息")

    version = CharField(max_length=32)
    create_time = DateTimeField(index=True, constraints=[auto_create], help_text="记录创建的时间")
    update_time = DateTimeField(index=True, constraints=[auto_create, auto_update], help_text="记录更新的时间")


class SkuInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_sku_info"

    sku_id = BigAutoField(help_text="sku编码")
    mall_id = IntegerField(help_text="商城编号")
    outer_sku_code = CharField(max_length=64, null=True, index=True, help_text="外部sku编码")
    is_combo = BooleanField(default=0, help_text="套装标记：goods_type=5时有效,非套装取值0")
    goods_id = BigIntegerField(index=True, help_text="商品编码")
    outer_goods_id = CharField(max_length=64, null=True, help_text="冗余：商品外部编码")
    spec_value_1 = CharField(max_length=16, help_text="规格取值1：红色")
    spec_value_2 = CharField(max_length=16, null=True, help_text="规格取值2")
    thumb_icon = TextField(null=True, help_text='缩略图')
    is_onsale = BooleanField(default=1, help_text="是否上架，0-下架，1-上架")
    origin_price = FloatField(null=True, help_text='原单价（吊牌价）')
    sale_price = FloatField(default=0, help_text='现单价')
    cost_score = FloatField(default=0, help_text='所需积分数')
    quantity = IntegerField(default=0, help_text="库存数")
    reserve_quantity = IntegerField(default=0, help_text="预扣库存数")

    removed = BooleanField(default=0, help_text="是否已删除：仅控制可见性")
    version = CharField(max_length=32)
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
