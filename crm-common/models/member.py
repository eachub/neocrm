from .base import *
from datetime import datetime, timedelta


def get_model_by_platform(platform):
    if platform == 'wechat':
        return WechatUserInfo
    elif platform == 'alipay':
        return AlipayUserInfo
    elif platform == "douyin":
        return DouyinUserInfo
    elif platform == 'tmall':
        return TmallUserInfo
    elif platform == "jd":
        return JDUserInfo
    return None


def getUsertags(date_str=None):
    """获取usertags model"""
    # date_str格式 %Y%m%d
    if not date_str:
        now = datetime.now()
        yestaday = now - timedelta(days=1)
        date_str = datetime.strftime(yestaday, "%Y%m%d")
    model = FlexModel.get(UserTags, date_str)
    logger.info(f'table name is {model._meta.table_name}')
    return model


# 角色1自己2父亲3母亲4配偶5孩子6其他人
relationship_maping = {
    1: "自己",
    2: "父亲",
    3: "母亲",
    4: "配偶",
    5: "孩子",
    6: "其他人",
}


class MemberStatus:
    NORMAL = 0  # 普通状态
    # UNBIND_MOBILE = 1  # 解绑手机号
    CANCEL = 2  # 注销状态
    ABNORMAL = 3  # 异常状态
    BLACK = 4  # 黑名单
    FAMILY = 5  # 家庭组

    MEMBER_EXIST = [NORMAL, BLACK]
    ACTIVE = [NORMAL, FAMILY]  # 正常用户


class GENDER:
    MALE = 1
    FEMALE = 2
    OTHER = 0

    GENDER_LI = [MALE, FEMALE, OTHER]


class UserInfoStatus:
    NORMAL = 0
    CANCEL = 1


class MemberInfo(Model):
    """会员信息表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_info"
        indexes = (
            (('member_no', 'crm_id'), True),
            (('enc_mobile', 'crm_id'), False),
            (('create_time', 'crm_id'), False),
        )

    info_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, null=True, help_text="会员号")
    mobile = CharField(32, help_text="手机号 脱敏展示")
    enc_mobile = CharField(64, help_text="手机号加密数据")
    platform = CharField(8, help_text="会员注册渠道")  # 渠道来源详情信息抽出来 来源信息可能很复杂
    nickname = CharField(64, null=True, help_text="会员名")
    level = IntegerField(default=1, help_text="等级")
    score = IntegerField(default=0, help_text="成长值")
    avatar = TextField(null=True, help_text="头像")
    province = CharField(16, null=True, help_text="省份")
    city = CharField(32, null=True, help_text="城市")
    birthday = DateField(null=True, help_text="生日")
    gender = SmallIntegerField(null=True, help_text="性别 1男 2女 0其他")
    member_status = SmallIntegerField(
        default=MemberStatus.NORMAL, help_text="用户状态 会员分类会员分类（普通会员、注销用户、家庭组、内部人员会员")
    invite_code = CharField(32, null=True, help_text="邀请码")
    create_time = DateTimeField(
        constraints=[auto_create], help_text="创建时间 注册时间")
    update_time = DateTimeField(
        constraints=[auto_create, auto_update], help_text="更新时间")


class MemberExtendInfo(Model):
    """会员的扩展信息表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_extend_info"
        indexes = (
            (("member_no", "crm_id"), True),
        )

    extend_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, help_text="会员号")
    score = IntegerField(default=0, help_text="成长值分")
    ip = CharField(32, null=True, help_text="ip信息")
    order_amount = DecimalField(12, 2, default=0, help_text="订单总金额累计")
    inviter = CharField(32, null=True, help_text="受邀码 邀请者")

    address = TextField(null=True, help_text="详细地址信息")
    email = CharField(64, null=True, help_text="邮箱地址")
    occupation = CharField(32, null=True, help_text="职业")
    hobby = TextField(null=True, help_text="兴趣爱好")
    tags = JSONField(null=True, help_text="标签列表")
    extra = JSONField(null=True, help_text="扩充信息")

    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(
        constraints=[auto_create, auto_update], help_text="更新时间")


class ChannelInfo(Model):
    """渠道信息表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_channel_code"
        indexes = (
            (('crm_id', 'channel_code'), False),
        )
        auto_id_base = 100000

    channel_id = AutoField()
    crm_id = CharField(32, help_text="产品实例id")
    channel_name = CharField(64, help_text="渠道名称")
    channel_code = CharField(16, null=True, help_text="渠道编码 R+层级1(2)+层级2(2)+层级3(2)+4位channel_id")
    channel_type = JSONField(null=True, help_text="渠道类型")
    desc = TextField(null=True, help_text="备注")
    is_deleted = BooleanField(default=False, help_text="逻辑删除")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class BlackMemberInfo(Model):
    """会员黑名单"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_black"
        indexes = (
            (('crm_id', 'member_no'), True),
        )

    auto_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, help_text="会员号")
    block_days = IntegerField(default=0, help_text="封禁时间(单位days) 0:需要手动解封 非0:计算拉黑结束时间")
    start_time = DateTimeField(constraints=[auto_create], help_text="黑名单开始时间")
    end_time = DateTimeField(null=True, help_text="黑名单结束时间, null表示手动解封")
    status = IntegerField(help_text="黑名单状态, 0表示正常状态, 1代表黑名单  2冻结积分 3冻结账户 4限制活动")
    desc = TextField(null=True, help_text="黑名单描述")
    operator = CharField(32, null=True, help_text="操作者")
    extra = TextField(null=True, help_text="额外信息")
    register_time = DateTimeField(null=True, help_text="会员注册时间 冗余 筛选条件使用")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(
        constraints=[auto_create, auto_update], help_text="更新时间")


class MemberFamily(Model):
    """会员家庭组信息表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_family"
        indexes = (
            (('member_no', 'crm_id'), False),
        )

    family_uid = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, help_text="会员号")
    nickname = CharField(128, help_text="家庭成员名称")
    gender = SmallIntegerField(null=True, help_text="性别 1男 2女 0其他")
    avatar = CharField(255, null=True, help_text="成员头像")
    birthday = DateField(null=True, help_text="生日")
    province = CharField(32, null=True, help_text="省份")
    city = CharField(32, null=True, help_text="城市")
    relationship = SmallIntegerField(null=True, help_text="角色1自己2父亲3母亲4配偶5孩子6其他人")
    occupation = CharField(64, null=True, help_text="职业")
    height = CharField(32, null=True, help_text="身高")
    weight = CharField(32, null=True, help_text="体重")
    extra = JSONField(null=True, help_text="额外信息")
    status = SmallIntegerField(default=0, help_text=" 0 正常 1 删除")
    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(
        constraints=[auto_create, auto_update], help_text="更新时间")


class CancelMemberInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_cancel"
        indexes = ((('crm_id', 'member_no'), True),)

    info_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    mobile = CharField(16, help_text="手机号")
    member_no = CharField(32, help_text="会员号")
    cancel_time = DateTimeField(constraints=[auto_create], help_text="注销时间")
    status = IntegerField(help_text="0代表手机号可以重新注册1代表手机号不能重新注册")
    extra = TextField(null=True, help_text="额外信息")

    update_time = DateTimeField(constraints=[auto_create, auto_update])


class MemberCodeRule(Model):
    """会员编码规则"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_code_rule"

    auto_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    prefix = CharField(16, null=True, help_text="会员号前缀")
    suffix = CharField(16, null=True, help_text="会员号后缀")
    update_time = DateTimeField(
        constraints=[auto_create, auto_update], help_text="更新时间")


class MemberCardRule(Model):
    """会员卡配置规则"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_card_rule"

    auto_id = BigAutoField(help_text="主键递增")
    crm_id = CharField(32, help_text="产品实例id")
    card_name = CharField(32, help_text="会员卡名称")
    card_prefix = CharField(16, null=True, help_text="前缀")
    middle_type = CharField(16, null=True, help_text="中间规则 使用手机号 会员号")
    card_suffix = CharField(16, null=True, help_text="后缀")
    qr_type = SmallIntegerField(default=0, help_text="二维码1 静态 2 动态")
    member_notice = TextField(null=True, help_text="会员须知")
    payee = CharField(16, null=True, help_text="收款方 开卡门店 统一到商家")

    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(
        constraints=[auto_create, auto_update], help_text="更新时间")


class MemberSourceInfo(Model):
    """会员渠道来源记录表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_source_info"
        indexes = ((("member_no", "crm_id"), True),)

    auto_id = BigAutoField()
    crm_id = CharField(max_length=32, help_text="产品实例id")
    member_no = CharField(max_length=32, help_text="会员号")
    channel_code = CharField(max_length=64, null=True, help_text="utm_source")
    platform = CharField(max_length=16, null=True, help_text="平台")
    campaign_code = CharField(max_length=64, null=True, help_text="utm_campaign")
    appid = CharField(max_length=32, null=True, help_text="appid")
    path = CharField(max_length=64, null=True, help_text="来源路径")
    scene = CharField(max_length=16, null=True, help_text="场景值")
    invite_code = CharField(max_length=32, null=True, help_text="受邀码")
    extra = JSONField(null=True, help_text="额外信息")

    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


# 各个渠道的用户信息
class WechatUserInfo(Model):
    """微信用户信息表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_wechat_uinfo"
        indexes = ((('crm_id', 'unionid',), False),
                   (('crm_id', 'openid', 'appid'), True),
                   (('member_no', 'crm_id'), True))

    auto_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, help_text="会员号")
    appid = CharField(32, help_text="appid")
    unionid = CharField(32, null=True, help_text="unionid")
    openid = CharField(32, help_text="openid")
    card_code = CharField(64, null=True, help_text="微信会员卡卡号")
    nickname = CharField(32, help_text="昵称")
    country = CharField(16, null=True, help_text="国家")
    province = CharField(32, null=True, help_text="省份")
    city = CharField(32, null=True, help_text="城市")
    avatar = TextField(help_text="用户头像")
    gender = SmallIntegerField(help_text="性别")

    status = SmallIntegerField(default=MemberStatus.NORMAL, help_text="平台状态")
    extra = JSONField(null=True, help_text="额外字段")

    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class DouyinUserInfo(Model):
    """抖音用户信息表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_douyin_uinfo"
        indexes = ((('openid', 'appid'), True),
                   (('member_no', 'crm_id'), True))

    info_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, help_text="会员号")
    appid = CharField(32, help_text="小程序appid")
    openid = CharField(64, help_text="openid")
    card_code = CharField(64, null=True, help_text="抖音会员卡卡号")
    nickname = CharField(32, help_text="昵称")
    country = CharField(16, help_text="国家")
    province = CharField(32, help_text="省份")
    city = CharField(32, help_text="城市")
    gender = SmallIntegerField(help_text="性别")
    avatar = TextField(help_text="用户头像")
    status = SmallIntegerField(default=MemberStatus.NORMAL, help_text="平台状态")
    extra = JSONField(null=True, help_text="额外字段")

    create_time = DateTimeField(constraints=[auto_create], help_text="创建时间")
    update_time = DateTimeField(constraints=[auto_create, auto_update], help_text="更新时间")


class TmallUserInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_tmall_uinfo"
        indexes = ((('ouid',), True),
                   (('member_no', 'mix_mobile', 'crm_id'), True))

    auto_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, help_text="特殊前缀:TM 会员号")
    ouid = CharField(32, help_text="ouid淘宝买家在当前店铺的唯一标识")
    omid = CharField(32, null=True, help_text="omid淘宝买家在当前品牌/企业的唯一标识，需做品牌认领")
    mix_mobile = CharField(128, help_text="默认密文手机号码")
    status = SmallIntegerField(default=MemberStatus.NORMAL, help_text="平台状态")

    nickname = CharField(max_length=32, null=True, help_text="extend->name")
    birthday = DateTimeField(null=True, help_text="extend->birthDate")
    gender = SmallIntegerField(null=True, help_text="extend->sex")
    extra = JSONField(null=True, help_text="会员的扩展额外字段")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class JDUserInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_jd_uinfo"
        indexes = (
            (("pin",), True),
            (("crm_id", "member_no", "phone_no"), True)
        )

    auto_id = AutoField()
    crm_id = CharField(32)
    member_no = CharField(32, help_text="特殊前缀： JD")
    pin = CharField(64, help_text="京东用户pin")
    phone_no = CharField(128, help_text="京东加密手机号")
    status = SmallIntegerField(default=MemberStatus.NORMAL, help_text="平台状态")
    extend = JSONField(null=True, help_text="会员扩展信息")
    name = CharField(32, null=True, help_text="extend->v_name")
    birthday = DateTimeField(null=True)
    gender = SmallIntegerField(null=True, help_text="0-女 1-男")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class AlipayUserInfo(Model):
    """支付宝用户信息表"""

    class Meta:
        database = db_eros_crm
        table_name = "t_crm_alipay_uinfo"
        indexes = ((('user_id', 'appid'), True),
                   (('member_no', 'crm_id'), True))

    info_id = BigAutoField()
    crm_id = CharField(32, help_text="产品实例id")
    member_no = CharField(32, help_text="会员号")
    appid = CharField(32, help_text="appid")
    user_id = CharField(32, help_text="user_id")
    biz_card_no = CharField(64, null=True, help_text="支付宝会员卡卡号")
    nickname = CharField(32, help_text="昵称")
    country_code = CharField(16, help_text="国家码")
    province = CharField(32, help_text="省份")
    city = CharField(32, help_text="城市")
    gender = SmallIntegerField(null=True, help_text="性别")
    avatar = TextField(help_text="用户头像")
    status = SmallIntegerField(default=MemberStatus.NORMAL, help_text="平台状态")
    extra = JSONField(null=True, help_text="额外字段")

    create_time = DateTimeField(constraints=[auto_create])
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
    level_name = CharField(max_length=128, help_text="要展示的level名称")
    change_tag = CharField(max_length=64, null=True, help_text="标签初始化更新的时候判断是否更新")
    tag_id = IntegerField(help_text="归属：标签编码")
    crm_id = CharField(max_length=32, help_text="所属实例")
    seqid = IntegerField(help_text="标签下的排序id")
    rules = JSONField(null=True, help_text="标签规则数组")
    rule_count = IntegerField(default=0, help_text="规则条数")
    qty = JSONField(null=True, help_text='预估规模: {"super_id":1123,"mobile":245,"unionid":523,"member_no":245}')
    removed = BooleanField(default=False, help_text="是否删除")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class DatasetInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_dataset_info"
        indexes = (
            (('crm_id', 'dataset_id'), True),
            (('parent_dataset_id', 'removed'), False),
        )

    auto_id = AutoField(help_text="顺序编码")
    crm_id = CharField(max_length=32, help_text="所属实例")
    dataset_id = CharField(max_length=32, index=True, help_text="数据源ID")
    platform = CharField(max_length=16, help_text='平台：woa/wmp/wsm/bmp/crm/mall/dyxd/ksxd/tmall')
    title = CharField(max_length=64, help_text="平台名称")
    dataset_key = CharField(max_length=16, null=True, help_text="dataset_id字段名")
    main_id_type = CharField(max_length=16, null=True, help_text="main_id字段名")
    name = CharField(max_length=128, help_text='数据源名称')
    icon = CharField(max_length=512, null=True, help_text='数据源头像')
    children = JSONField(null=True, help_text='子级别的数据源信息')
    parent_dataset_id = CharField(max_length=32, null=True, help_text="父级数据源ID")
    realtime = JSONField(null=True, help_text='实时指标')
    removed = BooleanField(default=False, help_text="删除标记")
    auth_status = BooleanField(default=True, help_text="授权标记")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


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


# 会员权益、规则表、等级
class MemberLevelInfo(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_level"
        auto_id_base = 300000
        indexes = (
            (('level_no', 'crm_id'), True),
        )

    level_id = AutoField(help_text="业务主键id")
    crm_id = CharField(max_length=32, help_text="所属实例")
    level_no = IntegerField(help_text="等级数字编码")
    name = CharField(max_length=128, help_text="等级名称 等级1 or 普通会员 or 黄金")
    min_score = IntegerField(null=True, help_text="最小成长值 达到这个等级的限制")
    desc = JSONField(null=True, help_text="等级描述")
    degraded_type = CharField(null=True, help_text="level 个等级分别设置 common 统一规则(查找实例对应的配置) 冗余存在实例配置里")
    down_able = BooleanField(default=False, help_text="能否降级 0 不能降级 1可降级 ")
    min_ship_times = IntegerField(null=True, help_text="如果是可降级 需要配置年最小购物次数 ")
    background = TextField(null=True, help_text="卡背景 预留")

    level_benefit = JSONField(null=True, help_text="等级权益 [{benefit_id title benefit_rule_ids=[]}]")
    level_bonus = JSONField(null=True, help_text="升级奖励 json points:积分 score:成长值 coupon优惠券 score成长值")
    deleted = BooleanField(default=False, help_text="逻辑删除")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class MemberBenefit(Model):
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_member_benefit"
        auto_id_base = 400000

    benefit_id = AutoField(help_text="权益id")
    crm_id = CharField(max_length=32, help_text="所属实例")
    benefit_type = CharField(max_length=32, help_text="权益类型 ")
    title = CharField(max_length=128, help_text="权益名称")
    icon = TextField(null=True, help_text="权益的图标")
    describe = TextField(null=True, help_text="权益的文字描述或协议")
    enable = BooleanField(default=False, help_text="是否启用")
    custom_config = JSONField(null=True, help_text="权益的配置信息 [{benefit_id: rules={}}]")
    # rules = JSONField(default=[], help_text="规则")

    deleted = BooleanField(default=False, help_text="逻辑删除")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class BenefitRuleInfo(Model):
    class Meta:
        database = db_eros_crm
        auto_id_base = 500000
        table_name = "t_crm_benefit_rule"

    benefit_rule_id = AutoField(help_text="业务主键id")
    crm_id = CharField(max_length=32, help_text="实例id")
    benefit_id = IntegerField(help_text="基础权益id")
    benefit_type = CharField(max_length=32, help_text="权益类型 冗余字段")
    name = CharField(max_length=32, help_text="规则的名称")
    son_rules = JSONField(default=[], help_text="基础规则id列表")
    # 积分倍率：{ 积分倍数 ratio_points produce_scene:{rule_id: rule_name}}
    # 晋级礼券：{ 优惠券coupon_list=[{coupon_id,coupon_name}] 发放次数:times send_time:'06:23'}
    # 会员包邮：{ free_shipping_type:1,  region:[province_id]}
    # 自定义组合权益 选中配置好的权益 选择这个权益下的规则(多选)
    content = JSONField(null=True, help_text="权益每一条规则的配置")

    deleted = BooleanField(default=False, help_text="逻辑删除")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class BenefitRulesMap(Model):
    """tree数据需要"""
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_benefit_rule_map"
        indexes = (
            (('benefit_id', 'benefit_rule_id'), True),
        )

    auto_id = AutoField()
    crm_id = CharField(max_length=32, help_text="实例id")
    benefit_id = IntegerField(help_text="权益id")
    benefit_rule_id = IntegerField(help_text="权益规则id")
    base_benefit_id = IntegerField(help_text="基础权益id")
    base_rule_id = IntegerField(help_text="基础规则id")
    rule_name = CharField(null=True, help_text="基础权益规则名称")
    create_time = DateTimeField(index=True, constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])


class LevelUpRecord(Model):
    """升级记录"""
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_level_up_record"
        indexes = (
            (('member_no', 'crm_id'), False),
        )

    auto_id = AutoField()
    crm_id = CharField(max_length=32, help_text="实例id")
    link_id = CharField(max_length=128, help_text="唯一标识")
    member_no = CharField(32, null=True, help_text="会员号")
    level_no = IntegerField(default=0, help_text="已有的等级")
    create_time = DateTimeField(constraints=[auto_create])


class MobileLinkId(Model):
    """手机号指向一个唯一标识 更换手机号之后，指向同一个id"""
    class Meta:
        database = db_eros_crm
        table_name = "t_crm_mobile_linkid"
        indexes = (
            (('link_id', 'enc_mobile'), True),
        )

    auto_id = AutoField()
    link_id = CharField(max_length=128, help_text="第一次领取手机号的唯一标识")
    enc_mobile = CharField(max_length=64, help_text="加密手机号")
    create_time = DateTimeField(constraints=[auto_create])





class ScoreChangeHis(Model):

    class Meta:
        database = db_eros_crm
        db_table = "t_crm_score_history"

    auto_id = BigAutoField()
    member_no = CharField(32, help_text="会员号")
    action = CharField(32, help_text="动作")
    source_evnet_id = CharField(32, null=True, help_text="数据源的event_id")
    change_score = IntegerField(help_text="变更成长值")
    event_date = DateField(index=True, help_text="事件发生的日期")
    create_time = DateTimeField(constraints=[auto_create])


class MemberOrderSummary(Model):
    """用户消费和售后的金额 更改成长值使用"""
    class Meta:
        database = db_eros_crm
        db_table = "t_crm_member_amount"

    auto_id = BigAutoField()
    member_no = CharField(32, unique=True, help_text="会员号")
    pay_amount = FloatField(default=0, help_text="订单金额")
    score_used_pay = FloatField(default=0, help_text="兑换过成长值的")
    refund_amount = FloatField(default=0, help_text="退单金额")
    score_used_refund = FloatField(default=0, help_text="兑换过成长值")
    create_time = DateTimeField(constraints=[auto_create])
    update_time = DateTimeField(constraints=[auto_create, auto_update])
