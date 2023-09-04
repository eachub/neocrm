# 标签初始化和更新的脚本
# 更新性别数据
import asyncio
import logging
import os
import sys

import ujson

sys.path.insert(0, '..')

from mtkext.proc import Processor

from common.utils.misc import init_logger
from common.models.member import *
from common.models.coupon import *
from common.models.member import GENDER
from common.models.ecom import GoodsInfo, SkuInfo, CategoryNode

logger = logging.getLogger(__name__)


# 生成rules的配置

async def gen_campaign_info_rules(app, crm_id, days=None):
    """获取所有的活动 构建rules"""
    sql = f"""SELECT * FROM db_neocam.t_cam_campaign_info"""
    data_li = await app.mgr.execute(CRMModel.raw(sql).dicts())
    logger.info(data_li)
    rules = []
    for one in data_li:
        name = one.get("campaign_name")
        campaign_code = one.get("campaign_code")
        cid = one.get("campaign_id")
        rules.append(dict(level_name=name, name="cid", value=cid, text=name, code=campaign_code, dr=[days]))
    return rules


async def gen_campaign_info_rules_dr(app, crm_id):
    return await gen_campaign_info_rules(app, crm_id, days=30)


async def member_action002(app, crm_id):
    """注册渠道信息"""
    channels = await app.mgr.execute(ChannelInfo.select().where(ChannelInfo.crm_id == crm_id).dicts())
    rules = []
    for channel in channels:
        name = channel.get("channel_name")
        value = channel.get("channel_code")
        rules.append(dict(level_name=name, name="channel", value=value, text=name))
    return rules


async def gen_gender_rules(app, crm_id):
    level_name = (('未知', GENDER.OTHER), ("男", GENDER.MALE), ("女", GENDER.FEMALE))
    rules = []
    for name, value in level_name:
        rules.append(dict(level_name=name, name="gender", value=value, text=name))
    return rules


async def gen_occupation_rules(app, crm_id):
    level_name = ("专业人士", "服务业人员", "自由职业者", "工人", "公司职员", "商人", "个体户", "公务员", "学生", "家庭主妇", "农民", "失业")
    level_value = ("专业人士", "服务业人员", "自由职业者", "工人", "公司职员", "商人", "个体户", "公务员", "学生", "家庭主妇", "农民", "失业")
    rules = []
    for index, name in enumerate(level_name):
        rules.append(dict(level_name=name, name="occupation", value=level_value[index], text=name))
    return rules


async def gen_birthday_rules(app, crm_id):
    level_name = ('1月', '2月', '3月', '4月', '5月', '6月','7月', '8月', '9月','10月', '11月', '12月',)
    level_value = ('01', '02', '03', '04', '05', '06','07', '08', '09','10', '11', '12',)
    rules = []
    for index,  name in enumerate(level_name):
        rules.append(dict(level_name=name, name="birthday", value=level_value[index], text=name))
    return rules


async def gen_user_level_rules(app, crm_id):
    level_name = ('等级1', '等级2', '等级3', '等级4', '等级5', '等级6', '等级7', '等级8', '等级9', '等级10')
    level_value = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10')
    rules = []
    for index, name in enumerate(level_name):
        rules.append(dict(level_name=name, name="level", value=level_value[index], text=name))
    return rules


async def gen_province_rules(app, crm_id):
    with open('region.json', 'r', encoding='utf-8') as fp:
        region_data = ujson.load(fp)
    rules = []
    for province in region_data:
        name = province.get('name')
        # value = name.strip("省|市")
        code = province.get('code')
        rules.append(dict(level_name=name, name='province', value=name, code=code, text=name))
    return rules


async def gen_city_rules(app, crm_id):
    with open('region.json', 'r', encoding='utf-8') as fp:
        region_data = ujson.load(fp)
    rules = []
    for province in region_data:
        chidren = province.get('chidren')
        for city in chidren:
            name = city.get('name')
            code = city.get('code')
            rules.append(dict(level_name=name, name='province', value=name, code=code, text=name))
    return rules


async def gen_coupon_rules(app, crm_id):
    # 每次计算标签的时候要计算已经删除的优惠券吗
    items = await app.mgr.execute(CouponInfo.select().where(CouponInfo.crm_id==crm_id, CouponInfo.removed==False).dicts())
    rules = []
    for i in items:
        card_id = i.get("card_id")
        title = i.get('title')
        rules.append(dict(level_name=f'{title}({card_id})', name='card_id', value=card_id, title=title,
                          text=f'{title}({card_id})', dr=[60]))
    return rules


async def gen_goods_rules(app, crm_id, days=None):
    """商品信息"""
    # todo 后续这个要更改为商品主数据表
    items = await app.mgr.execute(SkuInfo.select(SkuInfo.goods_id, SkuInfo.outer_sku_code,
                                                 SkuInfo.sku_id, GoodsInfo.goods_name
                    ).join(GoodsInfo, on=(GoodsInfo.goods_id == SkuInfo.goods_id)).dicts())
    rules = []
    for i in items:
        sku_code = i.get("outer_sku_code")
        if sku_code:
            goods_name = i.get("goods_name")
            rules.append(dict(level_name=goods_name, name='sku_code', value=sku_code,
                              title=goods_name, text=f'{goods_name}({sku_code})', dr=[days]))
    return rules


async def gen_goods_rules_dr(app, crm_id):
    """默认60天时间"""
    return await gen_goods_rules(app, crm_id, days=60)


async def gen_goods_category_rules_dr(app, crm_id):
    items = await app.mgr.execute(CategoryNode.select().where(
        CategoryNode.removed==False, CategoryNode.layer >= 1).dicts())
    rules = []
    for i in items:
        name = i.get("name")
        cat_id = i.get("cat_id")
        rules.append(dict(level_name=name, name='cat_id', value=cat_id, title=name,
                          text=f'{name}', dr=[60]))
    return rules


async def add_son_tag_info(app, crm_id, tag_id, tag_name, index, define_mode, rules_li=None, dr=None, bind_field=None):
    """添加性别子标签和level配置"""
    in_obj = dict(
        parent_id=tag_id,
        crm_id=crm_id,
        tag_name=tag_name,
        only_folder=0,
        seqid=index,
        renew_mode=2,
        define_mode=define_mode,
        build_in=2,
        active=1
    )
    if bind_field:
        in_obj.update(dict(bind_field=bind_field))
    if define_mode in (2, 4):
        if not dr:
            dr = [None]
        in_obj['desc'] = [
            {
                "dataset": {
                    "data_type": "attr",
                    "data": [],
                    "combo_mode": "any"
                },
                "text": tag_name,
                "name": tag_name,
                "dr": dr
            }
        ]

    try:
        one = await app.mgr.get(TagInfo, crm_id=crm_id, tag_name=tag_name, parent_id=tag_id)
        son_tag_id = one.tag_id
        # define_mode=2 更新 4 不更新，前端可编辑，会充值掉
        if define_mode == 2:
            await app.mgr.execute(TagInfo.update(in_obj).where(TagInfo.tag_id==son_tag_id))
            logger.info(f"update tag_info tag_id={son_tag_id}")
    except DoesNotExist:
        son_tag_id = await app.mgr.execute(TagInfo.insert(in_obj))
        logger.info(f"insert tag_info tag_id={son_tag_id}")
    # 添加这个tag_id 下面的level
    # 没有规则的 需要生成
    if not rules_li:
        gen_rules_func = rules_func_mping.get(tag_name)
        if not gen_rules_func:
            logger.info('no gen fules function, need config!!!')
            return
        rules_li = await gen_rules_func(app, crm_id)
    # 单指标的要能更新 rules只能通过程序更改
    if define_mode in (2, 4):
        for _, one_rule in enumerate(rules_li):
            # 生成规则 根据类型
            name = one_rule.get("level_name")
            change_tag = one_rule.get("value")
            level_obj = dict(
                change_tag=change_tag,  # 用value的值 做是否更新的标识
                level_name=name,
                tag_id=son_tag_id,
                crm_id=crm_id,
                seqid=_,
                rules=[one_rule]
            )
            try:
                one = await app.mgr.get(TagLevel, crm_id=crm_id, change_tag=change_tag, tag_id=son_tag_id)
                # 更新
                level_id = one.level_id
                await app.mgr.execute(TagLevel.update(level_obj).where(TagLevel.level_id == level_id))
                logger.info(f'update one level {level_id}')
            except DoesNotExist:
                level_id = await app.mgr.execute(TagLevel.insert(level_obj))
                logger.info(f'insert one level {level_id}')
    # rules只能通过前端操作，程序只能写入
    if define_mode == 3:
        # 数据库 rules不存在 写入
        mode3_level_nums = await app.mgr.count(TagLevel.select().where(TagLevel.tag_id == son_tag_id))
        if not mode3_level_nums:
            # 没有写入
            for _, one_rule in enumerate(rules_li):
                if dr:
                    one_rule['dr'] = dr
                name = one_rule.get("level_name")
                level_obj = dict(
                    level_name=name,
                    tag_id=son_tag_id,
                    crm_id=crm_id,
                    seqid=_,
                    rules=[one_rule]
                )
                level_id = await app.mgr.execute(TagLevel.insert(level_obj))
                logger.info(f"insert one {name} level_id={level_id}")

# define_mode 1 自定义分档标签 这种暂时没有

# define_mode 2 单指标映射标签
# define_mode 3 单指标区间化标签 可修改时间范围和指标span范围
# define)mode 4 单指标映射标签 可修改时间范围
# [{"level_name":"老用户","value":[null,"2021-05-01 00:00:00"],"name":"subscribe_time","text":"注册时间"}]
# [{"dr":[7],"param":[],"spans":[{"level_name":"停留低时长","value":[null,"10"],"level_id":601159},{"level_name":"停留高时长","value":["10",null],"level_id":601160}],"aggr_name":"sum","name":"页面停留时长"}]
# [{"level_name":"停留低时长","value":[null,"10"],"name":"sum","text":"页面停留时长","dr":[7]}]

# 属性的不配置rules 从表(配置文件)里面获取 区间范围的配置rules
tag_parent_cfg = {
    "会员行为": [
        {"name": "注册引流活动", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_001"},
        {"name": "注册引流渠道", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_002"},
        {"name": "积分变更行为", "define_mode": 3, "rules": [
            {"level_name": "低频积分获取", "value": [None, 100], "name": "points", "text": "低频积分获取", "dr": [90]},
            {"level_name": "中频积分获取", "value": [100, 500], "name": "points", "text": "中频积分获取", "dr": [90]},
            {"level_name": "高频积分获取", "value": [500, None], "name": "points", "text": "高频积分获取", "dr": [90]},
        ], 'levels': [], "dr":[90], "bind_field": "tag_003"},
    ],
    "人口属性": [
        {"name": "性别", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_004"},
        {"name": "职业", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_005"},
        {"name": "年龄", "define_mode": 3, "rules": [
            {"level_name": "小于10岁", "value": [None, 9], "name": "year", "text": "小于10岁"},
            {"level_name": "10岁到20岁", "value": [9, 20], "name": "year", "text": "10岁到20岁"},
            {"level_name": "20岁到40岁", "value": [20, 40], "name": "year", "text": "20岁到40岁"},
            {"level_name": "40岁以上", "value": [40, None], "name": "year", "text": "40岁以上"},
        ], 'levels': [], "bind_field": "tag_006"},
        {"name": "生日", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_007"},  # 12个月
        {"name": "会员等级", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_008"},  # 1-12
        {"name": "会龄区间", "define_mode": 3, "rules": [
            {"level_name": "入会<1周", "value": [None, 7], "name": "days", "text": "入会<1周"},
            {"level_name": "入会1周-1个月", "value": [7, 30], "name": "days", "text": "入会1周-1个月"},
            {"level_name": "入会1个月-3个月", "value": [30, 90], "name": "days", "text": "入会1个月-3个月"},
            {"level_name": "入会3个月-1年", "value": [90, 365], "name": "days", "text": "入会3个月-1年"},
            {"level_name": "入会>1年", "value": [365, None], "name": "days", "text": "入会>1年"}
        ], 'levels': [], "bind_field": "tag_009"},
        {"name": "活跃状态", "define_mode": 3, "rules": [
            {"level_name": "低度活跃", "value": [None, 7], "name": "active", "text": "低度活跃", "dr": [90]},
            {"level_name": "中度活跃", "value": [7, 50], "name": "active", "text": "中度活跃", "dr": [90]},
            {"level_name": "高度活跃", "value": [50, None], "name": "active", "text": "高度活跃", "dr": [90]}
        ], 'levels': [], "bind_field": "tag_010"},
        {"name": "家庭成员数量", "define_mode": 3, "rules": [
            {"level_name": "少于2人", "value": [None, 2], "name": "sum", "text": "少于2人"},
            {"level_name": "3到5人", "value": [2, 5], "name": "sum", "text": "3到5人"},
            {"level_name": "大于5人", "value": [5, None], "name": "sum", "text": "大于5人"}
        ], 'levels': [], "bind_field": "tag_011"},
        {"name": "最近一次访问小程序出现的省份", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_012"},
        {"name": "最近一次访问小程序出现的城市", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_013"},
        # '性别', '年龄', '生日', '会员等级', '会龄区间', '活跃状态', '家庭成员数量', '最近一次访问小程序出现的城市', '最近一次访问小程序出现的省份',
    ],
    "消费习惯": [
        {"name": "近期购买频次", "define_mode": 3, "rules": [
            {"level_name": "低频购买", "value": [None, 2], "name": "times", "text": "低频购买", "dr": [90]},
            {"level_name": "中频购买", "value": [2, 5], "name": "times", "text": "中频购买", "dr": [90]},
            {"level_name": "高频购买", "value": [5, None], "name": "times", "text": "高频购买", "dr": [90]}
        ], 'levels': [], "dr":[90], "bind_field": "tag_014"},
        {"name": "近期购买支付金额", "define_mode": 3, "rules": [
            {"level_name": "小于200元", "value": [None, 200], "name": "pay_amount", "text": "小于200元", "dr": [90]},
            {"level_name": "200元到1000元", "value": [200, 1000], "name": "pay_amount", "text": "200元到1000元", "dr": [90]},
            {"level_name": "1000元以上", "value": [1000, None], "name": "pay_amount", "text": "1000元以上", "dr": [90]}
        ], 'levels': [], "dr":[90], "bind_field": "tag_015"},
        {"name": "最近一次购买距今天数", "define_mode": 3, "rules": [
            {"level_name": "小于30天", "value": [None, 30], "name": "day", "text": "小于30天", "dr": [90]},
            {"level_name": "30天到90天", "value": [30, 90], "name": "day", "text": "30天到90天", "dr": [90]},
            {"level_name": "90天以上", "value": [90, None], "name": "day", "text": "90天以上", "dr": [90]}
        ], 'levels': [], "dr":[90], "bind_field": "tag_016"},
        {"name": "最近一次购买商品", "define_mode": 2, "rules": [], 'levels': [], "bind_field": "tag_017"},
        # '近期购买频次', '近期购买支付金额', '最近一次购买距今天数', '最近一次购买商品',
    ],
    "商品偏好": [
        {"name": "近期最近一次购买商品", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_018", "dr": [90]},
        {"name": "近期最多购买商品", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_019", "dr": [90]},
        {"name": "近期最近一次购买商品类目", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_020", "dr": [90]},
        {"name": "近期最多购买商品类目", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_021", "dr": [90]},
        # '近期最近一次购买商品', '近期最多购买商品', '近期最近一次购买商品类目', '最近最多购买商品类目',
    ],
    "营销偏好": [
        {"name": "近期最近一次访问活动", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_022", "dr": [90]},
        {"name": "近期最多访问活动", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_023", "dr": [90]},
        {"name": "近期最近一次领取优惠券", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_024", "dr": [90]},
        {"name": "近期最多领取优惠券", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_025", "dr": [90]},
        {"name": "近期最近一次核销优惠券", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_026", "dr": [90]},
        {"name": "近期最多核销优惠券", "define_mode": 4, "rules": [], 'levels': [], "bind_field": "tag_027", "dr": [90]},
        # '近期最近一次访问活动', '近期最多访问活动', '近期最近一次领取优惠券', '近期最多领取优惠券', '近期最近一次核销优惠券', '近期最多核小优惠券',
    ],
}

rules_func_mping = {
    '注册引流活动': gen_campaign_info_rules,
    '注册引流渠道': member_action002,
    '性别': gen_gender_rules,
    '职业': gen_occupation_rules,
    '生日': gen_birthday_rules,
    '会员等级': gen_user_level_rules,
    '最近一次访问小程序出现的城市': gen_city_rules,
    '最近一次访问小程序出现的省份': gen_province_rules,
    '最近一次购买商品': gen_goods_rules,

    '近期最近一次购买商品': gen_goods_rules_dr,
    '近期最多购买商品': gen_goods_rules_dr,
    '近期最近一次购买商品类目': gen_goods_category_rules_dr,
    '近期最多购买商品类目': gen_goods_category_rules_dr,
    '近期最近一次访问活动': gen_campaign_info_rules_dr,
    '近期最多访问活动': gen_campaign_info_rules_dr,
    '近期最近一次领取优惠券': gen_coupon_rules,
    '近期最多领取优惠券': gen_coupon_rules,
    '近期最近一次核销优惠券': gen_coupon_rules,
    '近期最多核销优惠券': gen_coupon_rules,
}


async def add_tag_folder(app, crm_id):
    """创建标签目录"""

    result_dict = dict()
    index = 0
    for key in tag_parent_cfg.keys():
        # TagInfo.build_in
        # TagLevel.seqid
        # build_in 2 内置不能编辑
        in_obj = dict(parent_id=0, only_folder=1, active=1, seqid=index, crm_id=crm_id, tag_name=key, build_in=2)
        # 查看tag_info是否存在
        try:
            one = await app.mgr.get(TagInfo, crm_id=crm_id, tag_name=key, parent_id=0)
            tag_id = one.tag_id
        except DoesNotExist:
            tag_id = await app.mgr.execute(TagInfo.insert(in_obj))
        index += 1
        result_dict[key] = tag_id
    return result_dict


async def rebuild_tags_desc(app, crm_id, folder_tag_id):
    """重新构建desc信息 区间的是多个level信息 指标"""
    # 查找所有的level
    son_tags = await app.mgr.execute(
        TagInfo.select().where(TagInfo.parent_id == folder_tag_id, TagInfo.define_mode == 3).dicts())
    for son_tag in son_tags:
        tag_id = son_tag.get('tag_id')
        logger.info(f"tag_id={tag_id}")
        tag_name = son_tag.get('tag_name')
        await asyncio.sleep(0.01)
        level_infos = await app.mgr.execute(
            TagLevel.select().where(TagLevel.crm_id == crm_id, TagLevel.tag_id == tag_id).dicts())
        spans = []
        dr = [None]
        for level in level_infos:
            level_id = level.get('level_id')
            level_name = level.get('level_name')
            tmp = level.get('rules')[0]  # 目前level都是单规则 level.rules 是 []
            tmp.update(dict(level_id=level_id, level_name=level_name))
            spans.append(tmp)
            dr = tmp.get('dr')

        desc = [{
            "dataset": {
                "data_type": "attr",
                "data": [],
                "combo_mode": "any"
            },
            "text": tag_name,
            "name": tag_name,
            "spans": spans,
            "dr":dr,
        }]
        # 更新
        await app.mgr.execute(TagInfo.update(desc=desc).where(TagInfo.crm_id == crm_id, TagInfo.tag_id == tag_id))
        logger.info(f'update tag_id={tag_id} desc {desc}')


class TaskProc(Processor):

    async def run(self, i):
        # 加载性别标签到 t_tag_info 和 t_tag_level
        crm_id = self.cmd_args.crm_id
        try:
            async with self.mgr.atomic() as t:
                result_dict = await add_tag_folder(self, crm_id)  # {'tag': tag_id}
                for tag_name, tag_id in result_dict.items():
                    son_tag_dict_li = tag_parent_cfg.get(tag_name)
                    for index, son_tag in enumerate(son_tag_dict_li):
                        son_tag_name = son_tag.get('name')
                        define_mode = son_tag.get('define_mode')
                        rules = son_tag.get('rules')
                        dr = son_tag.get('dr')
                        bind_field = son_tag.get('bind_field')
                        # 查找这个tag添加的方法
                        await add_son_tag_info(self, crm_id, tag_id, son_tag_name, index, define_mode,
                                               rules_li=rules, dr=dr, bind_field=bind_field)  # 执行方法

            # 重新构建 tag_info 里面的desc
            for tag_name, tag_id in result_dict.items():
                await rebuild_tags_desc(self, crm_id, tag_id)
        except Exception as ex:
            await t.rollback()
            logger.exception(ex)
            return

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()
        cls.cmd_args = cmd_args

        # 加载配置
        def update_config(args, path):
            if not os.path.exists(path):
                return
            args.update_config(path)

        update_config(args, f"../common/conf/{cmd_args.env}.py")
        update_config(args, f"../conf/{cmd_args.env}.py")

        ###
        from mtkext.cache import LocalCache
        cls.cache = LocalCache()
        from mtkext.hcp import HttpClientPool
        # app.http = HttpClientPool(loop=loop, client=client)
        ###
        import aioredis
        cls.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        from common.models.base import db_eros_crm
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)

    @classmethod
    async def release(cls):
        await cls.mgr.close()
        cls.redis.close()
        await cls.redis.wait_closed()
        await super().release()
        logger.info("finish release-works")

    @classmethod
    async def start(cls, loop, cmd_args):
        await cls.init(loop, cmd_args)
        await cls().run(1)
        await cls.release()


if __name__ == '__main__':
    # python3 t_tag_init_update.py --env=local --crm_id=10080
    init_logger(f"logs/tag_init.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test', 'local'))
    parser.add_argument('--crm_id', dest='crm_id', type=str, required=True)
    cmd_args = parser.parse_args()
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TaskProc.start(loop, cmd_args))
    loop.close()
