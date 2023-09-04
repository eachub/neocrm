#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

from sanic import Blueprint
from datetime import datetime
from biz.campaign import get_month_activity
from sanic.log import logger
from sanic.response import json
from common.utils.const import *

bp = Blueprint('bp_calendar', url_prefix='/calendar')


@bp.get('/<instance_id>/month')
async def month_calendar(request, instance_id):
    mgr = request.app.mgr
    args = request.args
    year = args.get('year')
    assert year, 'year必传'
    month = args.get('month')
    assert month, 'month必传'
    assert int(month) in range(1, 13), 'month非法'
    campaign_list = await get_month_activity(mgr, instance_id, int(year), int(month))
    _campaign_list = []
    for x in campaign_list:
        x["create_time"] = x["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        _campaign_list.append(x)
    campaign_list = _campaign_list
    logger.info(f"campaign_list: {campaign_list}")

    #  判断营销活动是否属于企微活动
    for item in campaign_list:
        source_type = 1
        _detail = item.get("detail") or {}
        if _detail.get("children",[]):
            children = _detail.get("children",[])
            for child in children:
                wsm_improve = child.get("wsm_improve",{})
                if wsm_improve.get("guider") or \
                        wsm_improve.get("fans") or \
                        wsm_improve.get("sop"):
                    source_type = 3
        item['source_type'] = source_type
        item.update({
            "activity_id": item["campaign_id"],
            "activity_name": item["campaign_name"],
            "activity_begin_time": item["begin_time"],
            "activity_end_time": item["end_time"],
            "activity_type": item["campaign_type"],
        })

    return json(dict(code=RC.OK, msg="ok", data=campaign_list))
