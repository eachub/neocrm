import asyncio
import logging

import ujson
from mtkext.db import safe_string, sql_printf
from peewee import fn
from playhouse.shortcuts import model_to_dict
from collections import defaultdict

from common.biz.utils import chrec_to_dict
from stats.task import *
from common.models.member import MemberInfo, TagLevel, getUsertags

logger = logging.getLogger(__name__)


async def get_tag_qty(app, crm_id, tag_fields):
    # tag_fields: tag_id: bind_filed
    ret_list = []
    model = getUsertags()
    for tag_id, bind_filed in tag_fields.items():
        if not bind_filed:
            logger.info(f"tag_id={tag_id} no bind_filed")
            continue
        await asyncio.sleep(0.02)
        qty = await app.mgr.count(model.select().where(model.crm_id == crm_id, getattr(model, bind_filed) != ""))
        tmp_dict = dict(tag_id=tag_id, member_no=qty)
        ret_list.append(tmp_dict)
    return ret_list


async def fill_those_qty(app, crm_id, ThatModel, key, results):
    for one in results:
        tid = one.get(key)
        await app.mgr.execute(ThatModel.update(qty=one).where(
            getattr(ThatModel, key) == tid,
            ThatModel.crm_id == crm_id,
        ))


async def get_level_qty(app, crm_id, tag_fields):
    # 构建tag_id对应的level_id 列表
    # ret_list = defaultdict(list)
    tag_level_id_mp = dict()
    tag_levels = await app.mgr.execute(TagLevel.select().where(TagLevel.crm_id==crm_id))
    for tag_level in tag_levels:
        tag_id = tag_level.tag_id
        level_id = tag_level.level_id
        tag_level_id_mp[level_id] = tag_id
    ###
    ret_list = []
    tmp_qty_dict = {}
    model = getUsertags()
    for tag_id, bind_field in tag_fields.items():
        logger.info(bind_field)
        if not bind_field:
            logger.info(f"tag_id={tag_id} no bind_filed")
            continue
        b_field = getattr(model, bind_field)
        items = await app.mgr.execute(model.select(b_field, fn.count(1).alias("count")).where(model.crm_id==crm_id, b_field is not None).
                                      group_by(b_field).dicts())
        # sql = f"""SELECT {bind_field} ,count(1) as count from db_neocrm.t_crm_tags where crm_id={crm_id} and {bind_field} is not NULL  group by {bind_field}"""
        # logger.info(f"find level counts group by {bind_field} {sql}")
        # items = await app.mgr.execute(MemberInfo.raw(sql).dicts())
        for item in items:
            qty = item.get('count')
            level_ids = item.get(bind_field)
            logger.info(f"{bind_field} level_ids {level_ids} ")
            if not level_ids:
                continue
            for level_id in level_ids.split(','):
                origin_level_qty = tmp_qty_dict.get(level_id) or 0
                tmp_qty_dict[level_id] = origin_level_qty + qty
        await asyncio.sleep(0.02)
    ret_list = [dict(level_id=k, member_no=v, tag_id=tag_level_id_mp.get(k)) for k,v in tmp_qty_dict.items()]
    return ret_list

