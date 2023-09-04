#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from common.biz.const import RC
from common.biz.heads import *
from biz.analyze import *
from common.biz.wrapper import safe_crm_instance, except_decorator

bp = Blueprint("bp_analyze_crm", url_prefix="/analyze")


def get_args(request):
    # crm_id = request.args.get("crm_id")
    # assert crm_id, "缺少crm_id参数"
    dr = request.args.get("dr")
    assert dr and dr.find("~") > 0, "dr必须是~分割的两个日期"
    from_date, to_date = map(dateFromString, dr.split("~"))
    logger.info(f"{from_date}~{to_date}")
    assert from_date <= to_date, "开始日期不能大于结束日期"
    types = request.args.get("types")
    return from_date, to_date, types


@bp.get('/<crm_id>/points/total')
async def fetch_points_total(request, crm_id):
    """获取积分汇总数据"""
    try:
        from_date, to_date, types = get_args(request)
        result = await handle_points_total(request.app, crm_id, from_date, to_date=to_date)
        return json(dict(code=RC.OK, msg="OK", data=result))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get('/<crm_id>/points/trend')
async def fetch_points_trends(request, crm_id):
    """获取积分趋势图数据"""
    try:
        from_date, to_date, types = get_args(request)
        result = await handle_points_trends(request.app, crm_id, from_date, to_date=to_date)
        return json(dict(code=RC.OK, msg="OK", data=result))
        pass
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get('/<crm_id>/points/distr')
async def fetch_points_distributed(request, crm_id):
    """积分的分布数据"""
    try:
        from_date, to_date, types = get_args(request)
        assert types in ("source", "redu_source"), "types参数错误"
        result = await handle_points_distributed(request.app, crm_id, from_date, to_date=to_date, types=types)
        return json(dict(code=RC.OK, msg="OK", data=result))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/points/export")
async def points_export_api(request, crm_id):
    """数据导出"""
    try:
        from_date, to_date, _ = get_args(request)
        return await handle_points_export(request.app, crm_id, from_date, to_date=to_date)
        # return json(dict(code=RC.OK, msg="OK", **result))
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/member/total")
@safe_crm_instance
async def api_member_total(request, crm_id):
    from_date, to_date, _ = get_args(request)
    result = await handle_member_total(request.app, crm_id, from_date, to_date=to_date)
    return json(dict(code=RC.OK, msg="OK", data=result))


@bp.get("/<crm_id>/member/trend")
@safe_crm_instance
async def api_member_trend(request, crm_id):
    from_date, to_date, _ = get_args(request)
    result = await handle_member_trend(request.app, crm_id, from_date, to_date=to_date)
    return json(dict(code=RC.OK, msg="OK", data=result))


@bp.get("/<crm_id>/member/distr")
@safe_crm_instance
async def api_member_distr(request, crm_id):
    from_date, to_date, types = get_args(request)
    assert types in ('channel', 'mp_source', "scene"), "types参数错误"
    result = await handel_member_dist(request.app, crm_id, from_date, to_date=to_date, types=types)
    return json(dict(code=RC.OK, msg="OK", data=result))


@bp.get("/<crm_id>/member/top")
@safe_crm_instance
async def api_member_top(request, crm_id):
    from_date, to_date, _ = get_args(request)
    result = await handle_invite_top(request.app, crm_id, from_date, to_date=to_date, item_count=10)
    return json(dict(code=RC.OK, msg="OK", data=result))


@bp.get("/<crm_id>/member/export")
@safe_crm_instance
async def api_member_export(request, crm_id):
    from_date, to_date, _ = get_args(request)
    return await handle_member_export(request.app, crm_id, from_date, to_date=to_date)


@bp.post('/<crm_id>/tags_qty_his')
@except_decorator
async def api_tags_dims_history(request, crm_id):
    """标签人数历史数据"""
    app = request.app
    params_dict = request.json
    model = StatTagsQty
    dr = params_dict.get("dr")
    assert dr and dr.find("~") > 0, "dr必须是~分割的两个日期"
    from_date, to_date = map(dateFromString, dr.split("~"))
    logger.info(f"{from_date}~{to_date}")
    assert from_date <= to_date, "开始日期不能大于结束日期"
    tag_id = params_dict.get('tag_id')
    assert type(tag_id) is int, "tag_id参数缺失或错误"
    level_ids = params_dict.get('level_ids') or []
    assert type(level_ids) is list, "level_ids格式错误"
    ###
    where = [model.crm_id == crm_id, model.tag_id == tag_id, model.tdate.between(from_date, to_date),]
    if level_ids:
        where.append(model.level_id.in_(level_ids))
    items = await app.mgr.execute(StatTagsQty.select().where(*where))
    # 格式化数据
    # {date: {level_id: qty}}
    date_levels = defaultdict(dict)
    desc_levels = defaultdict()
    key_list = []
    for item in items:
        tdate = item.tdate
        tdate = datetime.strftime(tdate, '%Y-%m-%d')
        level_id = item.level_id
        desc = item.desc
        logger.info(f"desc is {desc}")
        qty = item.qty
        date_levels[level_id][tdate] = qty
        if desc:
            desc_levels[tdate] = desc
        key_list.append(level_id)
    ###
    # 列 level_id
    if level_ids:
        lie_levels = level_ids
    else:
        lie_levels = key_list
    # 构造成前端需要的数据
    t, tdate = from_date, []
    items1 = []
    while t <= to_date:  # 没有数据点的填0
        rows = dict()
        tdate_ = f"{t}"
        rows["tdate"] = tdate_
        rows['desc'] = desc_levels.get(tdate_)
        for level_id in lie_levels:
            _key = f"level_{level_id}"
            rows[_key] = date_levels.get(level_id, {}).get(tdate_) or 0
        items1.append(rows)
        t += timedelta(days=1)
    # 格式化

    data = dict(items=items1, mode="by_day")

    return json(dict(code=RC.OK, msg="OK", data=data))