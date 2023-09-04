from copy import deepcopy
from datetime import datetime, timedelta

from async_lru import alru_cache
from mtkext.db import pop_matched_dict
from openpyxl import Workbook
from playhouse.shortcuts import model_to_dict
from sanic.log import logger
from sanic.kjson import json_loads, json_dumps
from sanic.response import file, json

from common.biz.const import RC
from common.biz.utils import gen_excel_fileinfo
from common.models.member import TagInfo, TagLevel, CRMChannelTypes


@alru_cache(maxsize=1000)
async def cache_get_campaign_info(client, cid):
    try:
        flag, cam_info = await client.campaign.fetch(
            dict(campaign_id=cid), instance_id=client._instance_id)
    except Exception as ex:
        logger.exception(ex)
        return dict()
    logger.info(cam_info)
    if flag:
        return cam_info
    else:
        return {}


def init_db_manager(loop, proxy, write_params=None, read_params=None, database=None):
    from peewee_async import PooledMySQLDatabase, Manager
    mgw = None
    if write_params:
        tmp_write_params = deepcopy(write_params)
        db = write_params.pop('database', None)
        db_write = PooledMySQLDatabase(**write_params, database=database or db)
        proxy.initialize(db_write)
        mgw = Manager(proxy, loop=loop)
    mgr = mgw  # TODO 暂时禁用读写分离
    if read_params:
       db = read_params.pop('database', None)
       db_read = PooledMySQLDatabase(**read_params, database=database or db)
       mgr = Manager(db_read, loop=loop)
    return mgw, mgr


def get_format_total(data_dict, key_dict):
    total = []
    for key, vl_dict in key_dict.items():
        val = data_dict.get(key, 0)
        vl_dict.update(dict(value=val, indicator=key))
        total.append(vl_dict)

    return dict(items=total)


async def fill_user_tags(redis, super_id, tag_dict):
    x = await redis.hgetall(super_id, encoding="utf-8")
    logger.info((super_id, x))
    for k, v in x.items():
        """ tag_dict = defaultdict(set) """
        tag_dict[k].update(json_loads(v))
    return tag_dict


async def get_tag_dict(app, instance_id, key="tag_name"):
    items = await app.mgr.execute(TagInfo.select(
            TagInfo.tag_id, getattr(TagInfo, key),
        ).where(
            TagInfo.instance_id == instance_id,
            TagInfo.removed == 0,
            getattr(TagInfo, key).is_null(False),
        ))
    return {i.tag_id: getattr(i, key) for i in items}


async def get_channel_dict(app, crm_id, key='name'):
    model = CRMChannelTypes
    items = await app.mgr.execute(model.select(
        model.type_id, getattr(model, key),
    ).where(
        model.crm_id == crm_id,
        getattr(model, key).is_null(False),
    ))
    return {i.type_id: getattr(i, key) for i in items}


async def get_level_dict(app, instance_id, key="level_name"):
    items = await app.mgr.execute(TagLevel.select(
            TagLevel.level_id, getattr(TagLevel, key),
        ).where(
            TagLevel.instance_id == instance_id,
            TagLevel.removed == 0,
            getattr(TagLevel, key).is_null(False),
        ))
    return {i.level_id: getattr(i, key) for i in items}



def levels_from_dict_info(dict_info, name, parents=[]):
    if type(dict_info) is list:
        if dict_info[0].find("::") < 0:
            return [dict(level_name=v, rules=[
                dict(name=name, value=v, text=v, parents=parents)]) for v in dict_info]
        else:
            ones = [v.split("::") for v in dict_info]
            return [dict(level_name=v, rules=[
                dict(name=name, value=k, text=v, parents=parents)]) for k, v in ones]
    elif type(dict_info) is dict:
        results = []
        for key, val in dict_info.items():
            results += levels_from_dict_info(val, name, parents + [key])
        return results
    else:
        raise AssertionError("错误的dict_info类型")


async def fetch_model_increment_list(app, crm_id, model, params_dict, exclude=[], base_where=[]):
    """增量数据获取通用参数处理"""
    ###
    page_id = int(params_dict.get("page_id", 1))
    assert page_id > 0, "page_id从1开始"
    page_size = int(params_dict.get("page_size", 20))
    assert 1 < page_size <= 500, "page_size不能小于2或超过500"
    ###
    time_start = int(params_dict.get("time_start", 0))
    assert time_start >= 0, "缺少合法的time_start参数"
    time_end = int(params_dict.get("time_end", 0))
    assert time_end >= 0, "缺少合法的time_end参数"
    assert time_start <= time_end, "time_end必须大于time_start"
    ###
    order_by = params_dict.get("order_by") or "update_time"
    assert order_by in ("create_time", "update_time"), "错误参数：order_by"
    order_field = getattr(model, order_by)

    if crm_id != "common":
        base_where.append(model.crm_id == crm_id)
    if 0 <= time_start < time_end:
        base_where.append(order_field.between(datetime.fromtimestamp(time_start), datetime.fromtimestamp(time_end)))

    sql = model.select().where(*base_where)
    order_asc = int(params_dict.get("order_asc", 0))
    total = await app.mgr.count(sql)
    if order_asc == 0:
        sql = sql.order_by(order_field.desc()).paginate(int(page_id), int(page_size))
    else:
        sql = sql.order_by(order_field.asc()).paginate(int(page_id), int(page_size))
    if not total:
        data = dict(crm_id=crm_id, page_id=page_id, page_size=page_size, total=0, items=[])
        return dict(code=RC.OK, msg="OK", data=data)
    items = await app.mgr.execute(sql)
    result = [model_to_dict(one, exclude=exclude) for one in items]
    data = dict(crm_id=crm_id, page_id=page_id, page_size=page_size, total=total, items=result)
    return dict(code=RC.OK, msg="OK", data=data)


async def get_channle_type_dict(app, crm_id):
    model = CRMChannelTypes
    items = await app.mgr.execute(model.select().where(
            model.crm_id == crm_id,
        ))
    return {i.type_id: model_to_dict(i) for i in items}


def plus_some_day(start_time, days=0, hours=0):
    # 计算过期时间和冻结时间
    if not days and not hours:
        return None
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    new_day = start_time + timedelta(days=days, hours=hours)
    # 过期时间和冷冻时间精度,是否取整到整天 23:59:59
    return new_day
    # return new_day.strftime("%Y-%m-%d %H:%M:%S")


async def translate_campaign_code(app, camp_code):
    """"翻译活动名称"""
    outer_str = camp_code
    if camp_code:
        cid = camp_code.split("_")[-1]
        camp_info = await cache_get_campaign_info(app.cam_app_client, cid)
        campaign_name = camp_info.get("campaign_name")
        if campaign_name:
            outer_str = campaign_name
    return outer_str


def get_by_list_or_comma(args, key):
    items = args.getlist(key, [])
    return items if len(items) != 1 else [i.strip() for i in items[0].split(",")]


async def export_list(app, crm_id, params_dict, header, file_name, fields, get_list_func, **kwargs):
    file_name, file_path = gen_excel_fileinfo(prefix=file_name)
    page_id = 1
    page_size = 10000
    data = []
    while True:
        params_dict['page_id'] = page_id
        params_dict['page_size'] = page_size
        items = await get_list_func(app, crm_id, params_dict, is_download=True)
        data.extend([[func(i.get(field)) if func else i.get(field) for field, func in fields] for i in items])
        if len(items) < page_size:
            break
        if items:
            page_size += 1
    if not data:
        return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，没有数据！"))
    wb = Workbook()
    ws = wb[wb.sheetnames[0]]
    ws.append(header)
    for i in data:
        ws.append(i)
    wb.save(file_path)
    return await file(file_path, filename=file_name)