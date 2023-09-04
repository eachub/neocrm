"""
计算会员标签脚本 定时更新会员标签
"""

import asyncio
import logging
import os
from collections import defaultdict
from copy import deepcopy
from datetime import timedelta, datetime
from mtkext.dt import *
import sys
import ujson
from mtkext.db import sql_printf, safe_string
from mtkext.proc import Processor
from playhouse.shortcuts import model_to_dict

sys.path.insert(0, '..')
from utils.ip2region import Ipv4Finder


from biz.utils import model_build_key_map
from utils.misc import init_logger
from model.tag_model import TagLevel, TagInfo, getUsertags
from tasks.make_tag_sql import level_find_member_cfg, data_find_level_member_cfg, \
    data_find_level_sql_cfg, data_find_member_no, recent_region_sql, save_update_user_tags, active_sql

logger = logging.getLogger(__name__)


# crm_id tag001:tag_id tag_002:tag_id

async def gen_cal_sql_by_rule(crm_id, rules, from_date, to_date, sql):
    rule = rules[0]
    value = rule.get("value")
    dr = rule.get("dr")
    if dr:
        days = dr[0]
        if days:
            from_date = to_date - timedelta(days)
    # 根据dr计算时间范围 如果没有dr使用默认时间范围(防止计算的数据量过大)
    from_date = datetimeToString(from_date)
    to_date = datetimeToString(to_date)
    if type(value) is list:
        v0, v1 = value[0] or 0, value[1]
        this_sql = sql_printf(sql, crm_id=crm_id, value0=v0, value1=v1, from_time=from_date, to_time=to_date)
    else:
        v0 = value
        this_sql = sql_printf(sql, crm_id=crm_id, value0=v0, from_time=from_date, to_time=to_date)
    return this_sql


async def handle_one_level(app, crm_id, tag_info, tag_level, from_date, to_date, sql):
    level_id = tag_level.get("level_id")
    rules = tag_level.get("rules")
    bind_field = tag_info.get('bind_field')
    if not bind_field:
        logger.info(f"no bind_field passing")
        return
    this_sql = await gen_cal_sql_by_rule(crm_id, rules, from_date, to_date, sql)
    # 处理 %% 的问题
    this_sql = re.sub(r"%%'(.*?)'%%", r"%%\1%%", this_sql)
    logger.info(this_sql)
    results = await app.mgr.execute(TagInfo.raw(this_sql).dicts())
    # 更新member_no 的标签
    user_tags_model = getUsertags()

    for i in results:
        member_no = i.get('member_no')
        if member_no:
            crm_id = crm_id
            in_obj = {bind_field: level_id, "member_no":  member_no, "crm_id": crm_id}
            logger.info(f"insert {bind_field}:{level_id} {member_no} {crm_id}")
            await app.mgr.execute(user_tags_model.insert(in_obj).on_conflict(update=in_obj))
    logger.info("end one level")


async def level_cal_member(app, crm_id, from_date, to_date):
    # 遍历level表 查找对应的会员 给会员打标签
    for tag_name, sql in level_find_member_cfg.items():
        tag_info = app.tag_name_info.get(tag_name)
        if not tag_info:
            logger.info(f'tag_name={tag_name}no tag_info please config')
            continue
        tag_id = tag_info.get("tag_id")
        logger.info(f"process tag_id {tag_id} tag_name={tag_name}")

        tag_levels = await app.mgr.execute(TagLevel.select().where(
            TagLevel.crm_id == crm_id, TagLevel.tag_id == tag_id).dicts())
        for tag_level in tag_levels:
            level_name = tag_level.get("level_name")
            logger.info(f"=====process tag_level {level_name}====")
            await handle_one_level(app, crm_id, tag_info, tag_level, from_date, to_date, sql)


async def data_cal_level_member(app, crm_id, from_date, to_date):
    """数据源计算 member_no level"""
    # 商品相关

    for tag_name, one_sql in data_find_level_sql_cfg.items():
        tag_info = app.tag_name_info.get(tag_name)
        logger.info(tag_info)
        if not tag_info:
            logger.warning(f"not found tag_info tag_name={tag_name} please check config")
            continue
        desc = tag_info.get('desc')
        bind_field = tag_info.get('bind_field')
        if desc: desc = desc[0]
        dr = desc.get('dr')  # [60]
        # value_field = desc.get('name')
        value_field = "value"  # sql里面写死
        if dr:
            # 计算时间范围
            days = dr[0]
            if days:
                logger.info(type(days))
                logger.info(days)
                from_date = to_date - timedelta(int(days))
        from_time = datetimeToString(from_date)
        to_time = datetimeToString(to_date)
        tag_id = tag_info.get('tag_id')
        await data_find_member_no(app, crm_id, tag_id, from_time, to_time, bind_field, value_field, one_sql)

        # # 最近最多领取的优惠券
        # tag_level = {}
        # if define_mode == 3:
        #     # 区间范围
        #     pass
        #     await handle_one_level(app, crm_id, tag_level, from_date, to_date)
        # if define_mode == 2:
        #     # 单指标
        #     sql = data_find_level_member_cfg.get(tag_name)
        #     if not sql:
        #         logger.warning(f"not found data_find_level config")
        #         return
        #     this_sql = sql_printf(sql, crm_id=crm_id, from_time=from_date, to_time=to_date)
        #     results = await app.mgr.execute(TagInfo.raw(this_sql).dicts())
        #     logger.info(results)
        #     value_field = tag_level['rules'][0]['value']  # member_no 和 value
        #     in_objs = []
        #     for item in results:
        #         member_no = item.get('member_no')
        #         value = item.get(value_field)
        #         find_level = app.conf.levels_value.get(value)
        #         level_id = find_level.get("level_id")
        #
        #         logger.info(f"value={value} find level_id={level_id}")
        #
        #         in_obj = {
        #             "member_no": member_no,
        #             bind_field: [level_id],
        #             "crm_id": crm_id
        #         }
        #         in_objs.append(in_obj)
        #     # 更新写入
        #     await app.mgr.execute(usertag_model.insert_many(in_objs).on_conflict(update=in_objs))
        #     logger.info(f"tag insert many")


async def handle_data_vistor_region(app, crm_id, from_date, to_date):
    tag_province = "最近一次访问小程序出现的省份"
    tag_city = "最近一次访问小程序出现的城市"
    city_bind_field = app.tag_name_info.get(tag_city).get("bind_field")
    city_tag_id = app.tag_name_info.get(tag_city).get("tag_id")
    # todo 后来要增加 分页获取会员数据，防止数据过大
    sql = """select member_no ,unionid  from db_neocrm.t_crm_wechat_uinfo tcwu where unionid !=''"""
    member_info = await app.mgr.execute(TagInfo.raw(sql).dicts())
    unionid_map = defaultdict()
    unionid_li = []
    for i in member_info:
        member_no = i.get("member_no")
        unionid = i.get("unionid")
        unionid_li.append(unionid)
        unionid_map[unionid] = member_no
    province_bind_field = app.tag_name_info.get(tag_province).get("bind_field")
    province_tag_id = app.tag_name_info.get(tag_province).get("tag_id")
    # 查询数据
    from_date = datetimeToString(from_date)
    to_date = datetimeToString(to_date)
    unionid_li = [f"'{i}'" for i in unionid_li]
    where = f"unionid in ({','.join(unionid_li)})"
    extra_conds = safe_string(where)
    this_sql = sql_printf(recent_region_sql, crm_id=crm_id, from_time=from_date, to_time=to_date, extra_conds=extra_conds)
    logger.info(this_sql)
    results = await app.db_event_mgr.execute(TagInfo.raw(this_sql).dicts())
    # member_no ip 地址
    finder = Ipv4Finder("../utils/ip2region.db")
    p_tmp_dict = defaultdict(list)
    c_tmp_dict = defaultdict(list)
    for item in results:
        unionid = item.get("unionid")
        member_no = unionid_map.get(unionid)
        # unionid_li.append(unionid)
        ip = item.get("value")
        logger.info(f'this ip is {ip}')
        city_id, region = finder.search(ip)
        region_tuple = region.split("|")
        if len(region_tuple):
            province = region_tuple[2]
            city = region_tuple[3]
            # 查找对应的level_id
            p_level = app.conf.levels_value.get(province_tag_id).get(province)
            logger.info(f"{ip} find province_level={p_level}")
            if p_level:
                p_tmp_dict[member_no].append(p_level.get("level_id"))
            c_level = app.conf.levels_value.get(city_tag_id).get(city)
            logger.info(f"{ip} find city_level={c_level}")
            if c_level:
                c_tmp_dict[member_no].append(c_level.get('level_id'))
    # 添加到数据库里面
    for member_no, c_levels in c_tmp_dict.items():
        c_levels = [str(i) for i in c_levels]
        value = ','.join(c_levels)
        await save_update_user_tags(app, crm_id, member_no, city_bind_field, value)

    for member_no, c_levels in p_tmp_dict.items():
        c_levels = [str(i) for i in c_levels]
        value = ','.join(c_levels)
        await save_update_user_tags(app, crm_id, member_no, province_bind_field, value)


async def query_member_no_by_unionids(mgr, unionid_li):
    if not unionid_li:
        return {}
    unionid_li = [f"'{i}'" for i in unionid_li]
    where = f"unionid in ({','.join(unionid_li)})"
    extra_conds = safe_string(where)
    sql = """select member_no, unionid from db_neocrm.t_crm_wechat_uinfo where {where}"""
    this_sql = sql_printf(sql, where=extra_conds)
    items = await mgr.execute(TagInfo.raw(this_sql).dicts())
    unionid_map = defaultdict()
    for i in items:
        member_no = i.get("member_no")
        unionid = i.get("unionid")
        unionid_map[unionid] = member_no
    return unionid_map


async def handle_active_data(app, crm_id, from_date, to_date):
    """活跃状态的计算"""
    tag_name = "活跃状态"
    tag_sql = active_sql
    tag_info = app.tag_name_info.get(tag_name)
    if not tag_info:
        logger.warning(f"config {tag_name}")
        return

    bind_field = tag_info.get("bind_field")
    tag_id = tag_info.get("tag_id")
    tag_levels = await app.mgr.execute(TagLevel.select().where(
        TagLevel.crm_id == crm_id, TagLevel.tag_id == tag_id).dicts())
    for tag_level in tag_levels:
        level_name = tag_level.get("level_name")
        level_id = tag_level.get("level_id")
        rules = tag_level.get("rules")
        one_sql = await gen_cal_sql_by_rule(crm_id, rules, from_date, to_date, tag_sql)
        logger.info(f"{level_name}:{one_sql}")
        items = await app.db_event_mgr.execute(TagInfo.raw(one_sql).dicts())
        unionid_li = [i.get("unionid") for i in items]

        unionid_map = await query_member_no_by_unionids(app.mgr, unionid_li)
        for item in items:
            unionid = item.get("unionid")
            member_no = unionid_map.get(unionid)
            if member_no:
                await save_update_user_tags(app, crm_id, member_no=member_no, bind_field=bind_field, value=level_id)


async def update_key_info(app):
    """初始化常用的关系"""

    def handle_info(info, key, pkey):
        if info is None:
            logger.error(f"failed to get {key}")
        elif getattr(app.conf, key, None) != info:
            setattr(app.conf, key, info)
            info = {t[pkey]: t for t in info}
            setattr(app, key.lower(), info)
            logger.info(f"{key} is updated: {info}")

    items = await app.mgr.execute(TagInfo.select().where(TagInfo.removed == False))
    items = [model_to_dict(item) for item in items]
    handle_info(items, "TAG_INFO", 'tag_id')
    handle_info(items, "TAG_NAME_INFO", 'tag_name')
    logger.info(f"update tag_info {app.conf.TAG_INFO}")
    logger.info(f"update tag_name_info {app.conf.TAG_NAME_INFO}")
    ### 标签

    ###
    crm_ins = await app.mgr.execute(TagInfo.select())
    crm_ids = [i.crm_id for i in crm_ins]
    levels_value = dict()
    tag_infos = await app.mgr.execute(TagInfo.select(TagInfo.tag_id).where(TagInfo.define_mode.in_([2, 4])))
    tag_ids = [i.tag_id for i in tag_infos]
    for tag_id in tag_ids:
        level_infos = await app.mgr.execute(TagLevel.select(TagLevel.level_id, TagLevel.level_name,
                                                            TagLevel.tag_id, TagLevel.rules)
                                            .where(TagLevel.removed == False, TagLevel.tag_id==tag_id).dicts())
        tmp_dict = dict()
        for level in level_infos:
            rules = level.get("rules")
            level_name = level.get("level_name")
            value = rules[0].get('value') if rules else level_name
            if type(value) is list:
                continue
            tmp_dict[value] = deepcopy(level)
        levels_value[tag_id] = deepcopy(tmp_dict)
    setattr(app.conf, f"levels_value", levels_value)
    logger.info(f"update levels_value")


async def cron_job(cls):
    prevStamp = int(time.time())
    while not cls.jobs.closed:
        now = int(time.time())
        if now - prevStamp >= 60:
            try:
                await update_key_info(cls)
                prevStamp = now
            except Exception as ex:
                logger.exception(ex)
        cls.cache.purge(delta=1800, interval=10)
        await asyncio.sleep(0.3)


class TaskProc(Processor):
    async def run(self, i):
        app = self
        to_date = datetime.now()
        from_date = to_date - timedelta(days=365)
        # start_dt = datetimeToString(from_time)
        # end_dt = datetimeToString(to_time)
        # 两种计算方式
        # 1 遍历level_id 从数据源 根据value值或范围 查找会员号
        # 2 从数据源计算计算会员和指标 指标值计算level_id
        # 3 获取到的会员号 和level_id 写更到t_user_tags表
        ###
        crm_ins = await app.mgr.execute(TagInfo.select())
        crm_ids = [i.crm_id for i in crm_ins]

        for crm_id in set(crm_ids):
            #
            await level_cal_member(app, crm_id, from_date, to_date)
            #
            await data_cal_level_member(app, crm_id, from_date, to_date)
            # 最近访问的城市省份处理
            await handle_data_vistor_region(app, crm_id, from_date, to_date)
            # 活跃状态的计算
            await handle_active_data(app, crm_id, from_date, to_date)
        logger.info(f"Coroutine-{i} is stopped.")

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()

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
        from mtkext.mq import MessageQueue
        cls.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        from model.tag_model import db_eros_crm
        db = PooledMySQLDatabase(**args.CRM_PARAM_MYSQL)
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)
        # db_event mgr
        from peewee import Proxy
        event_proxy = Proxy()
        db_event = PooledMySQLDatabase(**args.DB_EVENT_MYSQL)
        event_proxy.initialize(db_event)
        cls.db_event_mgr = Manager(event_proxy, loop=loop)
        # 初始化加载标签的数据 等级数据 crontab更新
        await update_key_info(cls)
        ###
        # import aiojobs
        # cls.jobs = await aiojobs.create_scheduler(close_timeout=0.5)
        # await cls.jobs.spawn(cron_job(cls))

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


if __name__ == "__main__":
    # python3 t_tag_calculate.py --env=local
    init_logger(f"logs/tag_calculate.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test', 'local'))
    cmd_args = parser.parse_args()
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TaskProc.start(loop, cmd_args))
    loop.close()
