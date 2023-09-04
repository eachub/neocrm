# -*- coding: utf-8 -*-
from urllib.parse import urlencode

from sanic import Blueprint
from sanic.log import logger
from sanic.response import json

from common.utils.const import *
from common.utils.common import get_campaign_path, logical_remove_record
from common.models.cam import *
from biz.campaign import CAMPAIGN_PLUGIN
from mtkext.db import FlexModel
from datetime import datetime, timedelta
from mtkext.dt import datetimeToString, datetimeFromString

bp = Blueprint('bp_campaign', url_prefix="/campaign")


@bp.get("/<instance_id>/search")
async def campaign_search(request, instance_id):
    try:
        logger.info(request.args)
        keyword = request.args.get("keyword") or None
        campaign_types = get_or_sep_list(request.args, "campaign_type", conv_type=int)
        dtr = request.args.get("dtr") or None
        ###
        page_id = int(request.args.get("page_id", 1))
        assert page_id > 0, "page_id从1开始"
        page_size = int(request.args.get("page_size", 20))
        assert 1 < page_size <= 500, "page_size不能小于2或超过500"

        # 追加排序
        order_by = request.args.get('order_by') or None
        assert order_by in (None, 'begin_time', 'end_time'), '错误参数：order_by'

        # 排序方式 0降序 1升序 (-1和order_by按时间降序)
        asc = int(request.args.get('asc', 0))

        ###
        where = [
            CampaignInfo.instance_id == instance_id,
        ]
        logger.info(request.args)
        campaign_ids = request.args.getlist("campaign_ids")
        logger.info(f"campaign_ids: {campaign_ids}")
        if campaign_ids:
            if type(campaign_ids) != list: campaign_ids = [campaign_ids]
            where.append(CampaignInfo.campaign_id.in_(campaign_ids))
        else:
            where.append(CampaignInfo.status != 2)
        if keyword:
            where.append(CampaignInfo.campaign_name.contains(keyword))
        if campaign_types:
            where.append(CampaignInfo.campaign_type.in_(campaign_types))
        if dtr:
            parts = dtr.split("~")
            assert len(parts) == 2, "错误参数dtr"
            begin_time, end_time = int(parts[0]), int(parts[1])
            if begin_time > 0: where.append(CampaignInfo.begin_time >= begin_time)
            if end_time > 0: where.append(CampaignInfo.end_time < end_time)

        sql = CampaignInfo.select().where(*where)
        if order_by and asc in (0, 1):
            order_by_field = getattr(CampaignInfo, order_by)
        else:
            order_by_field = CampaignInfo.update_time
            asc = 0
        sql = sql.order_by(order_by_field.asc() if asc else order_by_field.desc())
        logger.info(f"sql: {sql.sql()}")
        items = await request.app.mgr.execute(sql.paginate(page_id, page_size))
        total = await request.app.mgr.count(CampaignInfo.select(1).where(*where))
        excluded = [CampaignInfo.instance_id]
        results = [model_to_dict(i, exclude=excluded) for i in items]

        # 追加活动累计人数和当日累计人数
#        campaign_ids = set(x['campaign_id'] for x in results)
#        uv_info = await get_uv_cal(request.app, instance_id, campaign_ids)
#        for item in results:
#            uv_item = uv_info.get(str(item['campaign_id']), {})
#            item['uv_total'] = uv_item.get('uv_total', 0)
#            item['uv_today'] = uv_item.get('uv_today', 0)
#            nft_file = item.get('pkg')

            # 如果是压缩包 追加预览
 #           item['campaign_path'] = await get_campaign_path(request.app, instance_id, nft_file, item['campaign_id'])

        got = dict(total=total, campaign_list=results)
        return json(dict(code=RC.OK, msg="ok", data=got))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.get("/<instance_id>/fetch")
async def campaign_fetch(request, instance_id):
    campaign_id = int(request.args.get("campaign_id") or 0)
    try:
        app = request.app
        assert campaign_id, "缺少campaign_id参数"
        one = await app.mgr.get(CampaignInfo, campaign_id=campaign_id, instance_id=instance_id)
        excluded = [CampaignInfo.instance_id, CampaignInfo.status]
        one = model_to_dict(one, exclude=excluded)
#        nft_file = one.get('pkg')

        # 如果是压缩包 追加预览
#        one['preview_path'] = await get_preview_path(app, instance_id, nft_file, campaign_id)
        return json(dict(code=RC.OK, msg="ok", data=one))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"找不到活动：{campaign_id}"))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post("/<instance_id>/create")
async def campaign_create(request, instance_id):
    try:
        obj = request.json
        obj["instance_id"] = instance_id
        rec = {
            "instance_id":instance_id,
            "status":0,
            "campaign_name": obj.get("campaign_name"),
            "campaign_type": obj.get("campaign_type"),
            "begin_time": obj.get("begin_time"),
            "end_time": obj.get("end_time"),
            "desc": obj.get("desc")
        }
        #rec = peewee_normalize_dict(CampaignInfo, obj, excludes=["campaign_id", "create_time"])
        #rec["status"] = 0
        logger.info(f"rec: {rec}")
        async with request.app.mgr.atomic():
            got = await request.app.mgr.create(CampaignInfo, **rec)
            logger.info(f"got: {got}")
            await request.app.mgr.execute(
                CampaignInfo.update(campaign_code=f"cam_crm_{got.campaign_id}")
                    .where(CampaignInfo.campaign_id == got.campaign_id))
        return json(dict(code=RC.OK, msg="ok", data=dict(campaign_id=got.campaign_id)))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post('/<instance_id>/update')
async def campaign_update(request, instance_id):
    obj = request.json
    campaign_id = obj.get("campaign_id")
    logger.info(f"campaign_update: {campaign_id}")
    logger.info(f"campaign_update: {obj}")
    try:
        mgr = request.app.mgr
        campaign_type = obj.pop("campaign_type", None)
        assert campaign_type is None, "不支持修改活动类型"
        rec = peewee_normalize_dict(CampaignInfo, obj)
        assert rec, "无有效的修改字段"

        status = obj.get("status")
        only_intro = obj.get("only_intro",0)
        detail = obj.get("detail")
        got = await mgr.get(CampaignInfo, campaign_id = campaign_id,\
                instance_id = instance_id,
            )
        assert got.status != 2, "活动已删除，更新失败"
        campaign_type = got.campaign_type
        # 修改状态操作
        if not detail:
            detail = got.detail
        elif detail:
            rec["status"] = 0
        assert detail or only_intro, "活动详情未配置"
        cam_check_func = CAMPAIGN_PLUGIN.get(str(campaign_type))
        logger.info(f"cam_check_func: {cam_check_func}")
        if cam_check_func and detail and not only_intro:
            cam_check_func(request, detail)
        else:
            rec.pop("detail", None)
        logger.info(f"update campaign: {rec}")
        got = await mgr.execute(CampaignInfo.update(rec).where(
            CampaignInfo.campaign_id == campaign_id,
            CampaignInfo.instance_id == instance_id,
        ))
        logger.info(f"成功更新活动信息：{got}")

        return json(dict(code=RC.OK, msg="保存成功"))
    except DoesNotExist as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"更新失败：找不到活动{campaign_id}"))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post('/<instance_id>/remove')
async def campaign_remove(request, instance_id):
    try:
        obj = request.json
        mgr = request.app.mgr

        all_campaign_ids = []

        # 原有单个campaign_id
        campaign_id = obj.get("campaign_id")
        if campaign_id is not None:
            assert type(campaign_id) is int, "错误的campaign_id类型"
            all_campaign_ids.append(campaign_id)

        # 新增批量删除 campaign_ids 同时传递 屏蔽掉单个campaign_id
        campaign_ids = obj.get('campaign_ids')
        if campaign_ids and isinstance(campaign_ids, list): all_campaign_ids = [int(x) for x in campaign_ids]
        rec = dict(status=2)
        got = await request.app.mgr.execute(CampaignInfo.update(rec).where(
            CampaignInfo.campaign_id.in_(all_campaign_ids),
            CampaignInfo.instance_id == instance_id,
        ))
        logger.info(f"remove got: {got}")
        #if got and obj.get("detail"):
        #    try:
        #        item = await mgr.get(CampaignInfo, instance_id=instance_id, campaign_id=campaign_id)
        #        campaign_type = item.campaign_type
        #        await update_campaign_stocks(mgr, campaign_id, campaign_type, obj.get("detail"))
        #    except DoesNotExist:
        #        return json(dict(code=RC.PARSER_FAILED, msg='获取活动信息失败'))
        return json(dict(code=RC.OK, msg="删除成功"))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))

@bp.post('/<instance_id>/list')
async def api_campaign_list(request, instance_id):
    #
    app = request.app
    params_dict = request.json
    member_no = params_dict.get("member_no")
    create_start = params_dict.get("create_start")
    create_end = params_dict.get("create_end")
    order_by = params_dict.get("order_by", 'create_time')
    order_asc = params_dict.get("order_asc", 0)
    page_id = params_dict.get("page_id", 1)
    page_size = params_dict.get("page_size", 10)
    update_start = params_dict.get("update_start")
    update_end = params_dict.get("update_end")

    min_date, max_date = None,None
    if create_start or update_start :
        _list = [ x for x in  [create_start, update_start] if x ]
        min_date = datetime.strptime( min(_list), "%Y-%m-%d %H:%M:%S")
        min_date = datetime.strptime( min_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
    if create_end or update_end:
        _list = [ x for x in  [create_end, update_end] if x ]
        max_date = datetime.strptime( max(_list), "%Y-%m-%d %H:%M:%S")
        max_date = datetime.strptime( max_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
    all_tables = []
    if not min_date:
        min_date = datetime.now()
    if not max_date:
        max_date = min_date
    for x in range(0, (max_date - min_date).days + 1):
        _now = (min_date + timedelta(days=x)).strftime("%Y%m%d")
        all_tables.append(FlexModel.get(CampaignRecord, _now))

    all_sub_query = []
    for table_cls in all_tables:
        where = []
        if instance_id != "common":
            table_cls.instance_id == instance_id
        if member_no:
            where.append(table_cls.member_no == member_no)
        if create_start:
            from_dt = datetimeFromString(create_start)
            where.append(table_cls.create_time > from_dt)
        if create_end:
            to_dt = datetimeFromString(create_end)
            where.append(table_cls.create_time < to_dt)
        if update_start:
            from_update = datetimeFromString(update_start)
            where.append(table_cls.update_time > from_update)
        if update_end:
            to_update = datetimeFromString(update_end)
            where.append(table_cls.update_time < to_update)
        sql = table_cls.select().where(*where)
        all_sub_query.append(sql)

    logger.info(f"all sub query: {all_sub_query}")
    def _union_all(idx):
        if idx >= len(all_sub_query) - 1:
            return all_sub_query[idx]
        else:
            return all_sub_query[idx].union_all(_union_all(idx + 1))

    sql = _union_all(0)
    logger.info(f"sql: {sql.sql()}")
    if len(all_sub_query) > 1:
        sql = sql.select_from(sql.c.auto_id,sql.c.campaign_id,sql.c.member_no,\
                   sql.c.instance_id,sql.c.campaign_type,\
                   sql.c.event_type,sql.c.prize_conf,sql.c.utm_source,sql.c.create_time,sql.c.update_time)
    total = await app.mgr.count(sql)

    if order_by:
        logger.info(f"sql dir: {dir(sql)}")
#        logger.info(f"sql dir: {dir(sql.clou)}")
        logger.info(f"sql.c dir: {dir(sql.c)}")
        #order_field = getattr(sql, order_by)
        order_field = f" {order_by} "
        if order_asc == 0:
            sql = sql.order_by( SQL( f" {order_field} desc " ) ).paginate(int(page_id), int(page_size))
        else:
            sql = sql.order_by( SQL( f" {order_field} asc " ) ).paginate(int(page_id), int(page_size))
    logger.info(f" sql: {sql.sql()}")
    items = await app.mgr.execute(sql.dicts())
    logger.info(f"total {total}, data: {len(items)}")
    return json(dict(code=RC.OK, msg="OK", data=dict(items=items, total=total)))

