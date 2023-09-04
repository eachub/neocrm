#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from copy import deepcopy
from common.biz.const import RC
from common.biz.crm import cache_get_crm_scene, cache_get_crm_channel_map, cache_get_wmp_name
from common.biz.utils import *
from common.biz.heads import *
from stats.points import *
from stats.member import *
from common.models.points import PointsHistory
from common.models.analyze import *
from biz.utils import get_format_total

dims = ["prod_points", "total_prod", "consume_points", "total_consume", "total_active",
        "total_transfer", "total_accept", "expire_points", "total_expire",
        "prod_points_user", "total_prod_user", "consume_points_user", "total_consume_user",
        "total_active_user", "total_transfer_user", "total_accept_user", "expire_points_user", "total_expire_user"        
]

dim_mapping = {
    "prod_points": {"label": "新增积分", "description": "时间范围内新增加的人员数"},
    "prod_points_user": {"label": "新增积分人数", "description": "结束时间累计的人员数"},
    "total_prod": {"label": "累积新增积分", "description": "结束时间累计的人员数"},
    "total_prod_user": {"label": "累积新增积分人数", "description": "结束时间累计的人员数"},
    "consume_points": {"label": "消耗积分", "description": "结束时间累计的人员数"},
    "consume_points_user": {"label": "消耗积分人数", "description": "结束时间累计的人员数"},
    "total_consume": {"label": "累积消耗积分", "description": "结束时间累计的人员数"},
    "total_consume_user": {"label": "累积消耗积分人数", "description": "结束时间累计的人员数"},
    "total_active": {"label": "累积可用积分", "description": "结束时间累计的人员数"},
    "total_active_user": {"label": "累积可用积分人数", "description": "结束时间累计的人员数"},
    "total_transfer": {"label": "累积转赠积分", "description": "结束时间累计的人员数"},
    "total_transfer_user": {"label": "累积转赠积分人数", "description": "结束时间累计的人员数"},
    "total_accept": {"label": "累积接受转赠积分", "description": "结束时间累计的人员数"},
    "total_accept_user": {"label": "累积接受转赠积分人数", "description": "结束时间累计的人员数"},
    "expire_points": {"label": "过期积分", "description": "结束时间累计的人员数"},
    "expire_points_user": {"label": "过期积分人数", "description": "结束时间累计的人员数"},
    "total_expire": {"label": "累积过期积分", "description": "结束时间累计的人员数"},
    "total_expire_user": {"label": "累积过期积分人数", "description": "结束时间累计的人员数"},
}


member_dim_mapping = {
    "new_member": {"label": "新增会员", "description": "时间范围内新增加的会员数"},
    "total_member": {"label": "累积会员", "description": "结束时间累积的会员数"},
    "new_family": {"label": "新增家庭成员", "description": "时间范围内新增的家庭成员数"},
    "total_family": {"label": "累积家庭成员", "description": "结束时间累积的家庭成员数"},
}

async def mysql_gen_points_total(mgv, from_date, to_date, crm_id=None, dims=[]):
    # 查询多个sql 然后把指标汇总在一块
    extra_conds = safe_string(f" crm_id='{crm_id}' ")
    from_time, to_time = make_time_range(from_date, to_date)
    result_dict = {}
    for tmp_sql in [q_points_total1, q_points_total2, q_points_total3, q_points_total4,
                    q_points_total5, q_points_total6,q_points_total7, q_points_total8, q_points_total9]:
        sql = sql_printf(tmp_sql, tdate=from_date, thour=99,
                        from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        logger.info(f'积分分析-汇总-sql:{sql}')
        items = await mgv.execute(PointsHistory.raw(sql).dicts())
        logger.info(items)
        if len(items):
            item = items[0]
            # item = model_to_dict(items[0])
            logger.info(item)
            crm_id = item.get("crm_id")
            zhibiaos =  result_dict.get(crm_id) or {}
            zhibiaos.update(item)
            result_dict[crm_id] = zhibiaos
    return result_dict

@cache_to_date(ttl=180)
async def handle_points_total(app, crm_id, from_date, to_date):
    # 累计值 是小于当前时间范围结束点的值
    points_dims = deepcopy(dim_mapping)
    
    result_dict = await mysql_gen_points_total(app.mgv, from_date, to_date, crm_id=crm_id)
    result = result_dict.get(crm_id) or {}
    result = get_format_total(result, points_dims)
    return result


@cache_to_date(ttl=180)
async def handle_points_trends(app, crm_id, from_date, to_date):
    points_dims = deepcopy(dim_mapping)
    key_list = list(points_dims.keys())
    if (to_date - from_date).days < 2:
        items = await app.mgv.execute(StatPoints.select().where(
            StatPoints.crm_id == crm_id,
            StatPoints.tdate.between(from_date, to_date),
            StatPoints.thour.between(0, 23),
        ))
        data = result_by_hour(items, from_date, to_date, key_list)

    else:
        items = await app.mgv.execute(StatPoints.select().where(
            StatPoints.crm_id == crm_id,
            StatPoints.tdate.between(from_date, to_date),
            StatPoints.thour == 99,
        ))
        data = result_by_day(items, from_date, to_date, key_list)

    return data


@cache_to_date(ttl=180)
async def handle_points_distributed(app, crm_id, from_date, to_date, types):
    from_time, to_time = make_time_range(from_date, to_date)
    extra_conds = safe_string(f" crm_id='{crm_id}' ")
    if types == 'source':  # 积分来源
        sql = sql_printf(q_points_by_scene, tdate=from_date, thour=99,
                         from_time=from_time, to_time=to_time, extra_conds=extra_conds)
    elif types == 'redu_source':  # 消耗来源
        sql = sql_printf(q_reduce_by_scene, from_time=from_time, to_time=to_time, extra_conds=extra_conds)
    else:
        return False, {}
    logger.info(f"积分: {types} 获取分布-sql：{sql}")
    #  从mysql数据库计算
    result = await app.mgv.execute(PointsHistory.raw(sql).dicts())
    # result中label替换
    point_scene_mp = await cache_get_crm_scene(app.mgr, app.redis, crm_id)
    for i in result:
        code = i.get("item")
        i['label'] = point_scene_mp.get(code)
    data = dict(result=result, crm_id=crm_id, from_date=from_date, to_date=to_date)
    return data


async def handle_points_export(app, crm_id, from_date, to_date):
    ### 汇总数据
    indice = [val.get("label") for val in dim_mapping.values()]
    dim_li = list(dim_mapping.keys())
    total = await handle_points_total(app, crm_id, from_date, to_date=to_date)
    total_li = total.get('items')
    tmp_dict = {}
    for item in total_li:
        tmp_dict[item['indicator']] = item['value']
    sheet1 = ("分析汇总", ["开始日期", "结束日期"] + indice,
              [
                  [from_date, to_date ] + [tmp_dict.get(i) for i in dim_li]
              ])
    ### 趋势数据
    data = await handle_points_trends(app, crm_id, from_date, to_date=to_date)
    mode = data.get('mode')
    if mode == 'by_hour':
        dim_ = ['tdate', 'thour'] + dim_li
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet2 = ("趋势分析", ["日期", "小时"] + indice,
                  rows
                  )
    else:
        dim_ = ['tdate'] + dim_li
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet2 = ("趋势分析", ["日期"] + indice,
                  rows
                  )
    ### 分布数据  积分来源 source  消耗来源 redu_source
    dist_source = await handle_points_distributed(app, crm_id, from_date, to_date=to_date, types='source')
    sheet3 = (
        "积分来源场景", ["开始日期", "结束日期", "指标名称", "数值"],
        [[from_date, to_date , row['label'], row['counts']] for row in dist_source["result"]]
    )
    dist_redu_source = await handle_points_distributed(app, crm_id, from_date, to_date=to_date, types='redu_source')
    sheet4 = (
        "消耗来源场景", ["开始日期", "结束日期", "指标名称", "数值"],
        [[from_date, to_date , row['label'], row['counts']] for row in dist_redu_source["result"]]
    )
    fname, fpath = gen_excel_fileinfo(prefix="积分统计")

    write_to_excel(fpath, [sheet1, sheet2, sheet3, sheet4])
    return await file(fpath, filename=fname)



async def mysql_gen_member_total(mgv, from_date, to_date, crm_id=None, dims=[]):
    # 查询多个sql 然后把指标汇总在一块
    extra_conds = safe_string(f" crm_id='{crm_id}' ")
    from_time, to_time = make_time_range(from_date, to_date)
    result_dict = {}
    for tmp_sql in [q_member_dim1,q_member_dim2, q_member_dim3, q_member_dim4]:
        sql = sql_printf(tmp_sql, tdate=from_date, thour=99,
                        from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        logger.info(f'积分分析-汇总-sql:{sql}')
        items = await mgv.execute(PointsHistory.raw(sql).dicts())
        logger.info(items)
        if len(items):
            item = items[0]
            # item = model_to_dict(items[0])
            logger.info(item)
            crm_id = item.get("crm_id")
            zhibiaos =  result_dict.get(crm_id) or {}
            zhibiaos.update(item)
            result_dict[crm_id] = zhibiaos
    return result_dict


@cache_to_date(ttl=180)
async def handle_member_total(app, crm_id, from_date, to_date):
    dims = deepcopy(member_dim_mapping)
    
    result_dict = await mysql_gen_member_total(app.mgv, from_date, to_date, crm_id=crm_id)
    result = result_dict.get(crm_id) or {}
    result = get_format_total(result, dims)
    return result


@cache_to_date(ttl=180)
async def handle_member_trend(app, crm_id, from_date, to_date):
    """会员注册的趋势数据"""
    member_dims = deepcopy(member_dim_mapping)
    key_list = list(member_dims.keys())
    if (to_date - from_date).days < 2:
        items = await app.mgr.execute(StatUser.select().where(
            StatUser.crm_id == crm_id,
            StatUser.tdate.between(from_date, to_date),
            StatUser.thour.between(0, 23),
        ))
        data = result_by_hour(items, from_date, to_date, key_list)
    else:
        items = await app.mgr.execute(StatUser.select().where(
            StatUser.crm_id == crm_id,
            StatUser.tdate.between(from_date, to_date),
            StatUser.thour == 99,
        ))
        data = result_by_day(items, from_date, to_date, key_list)
    return data


@cache_to_date(ttl=180)
async def handel_member_dist(app, crm_id, from_date, to_date, types):
    """分布"""
    from_time, to_time = make_time_range(from_date, to_date)
    extra_conds = safe_string(f" crm_id='{crm_id}' ")
    if types == 'channel':
        sql = sql_printf(q_member_by_source, tdate=from_date, thour=99,
                         from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        result = await app.mgv.execute(PointsHistory.raw(sql).dicts())
        # 中文字段映射
        channel_map = await cache_get_crm_channel_map(app.mgr, app.redis, crm_id)
        for one in result:
            item = one.get("item")
            cn_label = channel_map.get(item, {}).get("channel_name")
            if cn_label:
                one["label"] = cn_label
    elif types == 'mp_source':
        sql = sql_printf(q_member_by_minip, tdate=from_date, thour=99,
                         from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        result = await app.mgv.execute(PointsHistory.raw(sql).dicts())
        # 中文描述
        appid_name_map = await cache_get_wmp_name(app, app.redis, crm_id)
        logger.info(appid_name_map)
        for one in result:
            item = one.get("item")
            cn_label = appid_name_map.get(item)
            if cn_label: one['label'] = cn_label
    else:
        sql = sql_printf(q_member_by_scene, tdate=from_date, thour=99,
                         from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        result = await app.mgv.execute(PointsHistory.raw(sql).dicts())
        # 中文映射
        with open('data/scene2.json', 'r', encoding='utf-8') as fp:
            scene_data = ujson.load(fp)
        for one in result:
            item = one.get("item")
            cn_label = scene_data.get(item)
            if cn_label: one['label'] = cn_label.get("name")
    data = dict(result=result, crm_id=crm_id, from_date=from_date, to_date=to_date)
    return data


@cache_to_date(ttl=180)
async def handle_invite_top(app, crm_id, from_date, to_date, item_count):
    """邀请top10 时间范围内的数据"""
    from_time, to_time = make_time_range(from_date, to_date)
    extra_conds = safe_string(f" crm_id='{crm_id}' ")
    sql = sql_printf(q_user_by_invite_code, tdate=from_date, thour=99,
                     from_time=from_time, to_time=to_time, extra_conds=extra_conds, tops=int(item_count))
    logger.info(f"top10 的sql {sql}")
    result = await app.mgv.execute(PointsHistory.raw(sql).dicts())
    data = dict(result=result, crm_id=crm_id, from_date=from_date, to_date=to_date)
    return data


async def handle_member_export(app, crm_id, from_date, to_date):
    ### 汇总数据
    indice = [val.get("label") for val in member_dim_mapping.values()]
    dim_li = list(member_dim_mapping.keys())
    total = await handle_member_total(app, crm_id, from_date, to_date=to_date)
    total_li = total.get('items')
    tmp_dict = {}
    for item in total_li:
        tmp_dict[item['indicator']] = item['value']
    sheet1 = ("分析汇总", ["开始日期", "结束日期"] + indice,
              [
                  [from_date, to_date ] + [tmp_dict.get(i) for i in dim_li]
              ])
    ### 趋势数据
    data = await handle_member_trend(app, crm_id, from_date, to_date=to_date)
    mode = data.get('mode')
    logger.info(f"trends_data={data}")
    if mode == 'by_hour':
        dim_ = ['tdate', 'thour'] + dim_li
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet2 = ("趋势分析", ["日期", "小时"] + indice,
                  rows
                  )
    else:
        dim_ = ['tdate'] + dim_li
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet2 = ("趋势分析", ["日期"] + indice,
                  rows
                  )
    ### 分布数据  积分来源 source  消耗来源 redu_source
    dist_source = await handel_member_dist(app, crm_id, from_date, to_date=to_date, types='channel')
    sheet3 = (
        "注册渠道", ["开始日期", "结束日期", "渠道", "数值"],
        [[from_date, to_date , row['label'], row['counts']] for row in dist_source["result"]]
    )
    
    dist_redu_source = await handel_member_dist(app, crm_id, from_date, to_date=to_date, types='mp_source')
    sheet4 = (
        "来源小程序", ["开始日期", "结束日期", "小程序", "数值"],
        [[from_date, to_date , row['label'], row['counts']] for row in dist_redu_source["result"]]
    )
    
    dist_redu_source = await handel_member_dist(app, crm_id, from_date, to_date=to_date, types='scene')
    sheet5 = (
        "来源场景", ["开始日期", "结束日期", "场景", "数值"],
        [[from_date, to_date , row['label'], row['counts']] for row in dist_redu_source["result"]]
    )
    # 排行
    rank_data = await handle_invite_top(app, crm_id, from_date, to_date=to_date, item_count=10)
    rank_li = rank_data.get('result', [])
    sheet6 = (
        "注册top10", ["开始日期", "结束日期", "邀请码", "数值"],
        [[from_date, to_date, row['label'], row['counts']] for row in rank_li]
    )
    fname, fpath = gen_excel_fileinfo(prefix="会员统计")

    write_to_excel(fpath, [sheet1, sheet2, sheet3, sheet4, sheet5, sheet6])
    return await file(fpath, filename=fname)
