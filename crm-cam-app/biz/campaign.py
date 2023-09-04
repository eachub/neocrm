# -*- coding: utf-8 -*-
from urllib.parse import urlencode

from peewee import DoesNotExist
from common.models.cam import CampaignInfo,CampaignRecord
from common.models.crm import TagInfo
from mtkext.db import sql_printf, sql_execute, safe_string
from datetime import datetime, timedelta
from common.utils.const import *
from sanic.log import logger
from mtkext.db import FlexModel

CAMPAIGN_PRIZE_PLUGIN = {}

async def get_all_campaign(app):
    query = CampaignInfo.select().where(CampaignInfo.status == 1)
    _ans = await app.mgr.execute(query)
    return _ans


async def get_all_tag_info(app):
    query = TagInfo.select()
    _ans = await app.crm_mgr.execute(query)
    return _ans


async def get_recent_update_campaign(app, time_range=10 * 60):
    sql =  f'SELECT * from t_cam_campaign_info where update_time >= DATE_SUB(now(), interval {time_range} SECOND)'
    query = CampaignInfo.raw(sql)
    _ans = await app.mgr.execute(query)
    return _ans


async def campaign_101_prize(request, campaign_id, member_no, page_id=1, page_size=10):
    app = request.app
    cam_ins = app.campaign_instance.get(f"cam_{campaign_id}")
    if not cam_ins:
        logger.error(f"查询失败，没有找到活动缓存 {campaign_id}")
        return False, dict(code=RC.STATUS_ERROR, msg=f"查询失败，活动不在有效期内：{campaign_id}")
    records = await cam_ins.get_prize_record(member_no, page_id, page_size)
    result = []
    for record in records:
        prize_conf = record.get("prize_conf", [])
        logger.info(f"record: {record}")
        for x in prize_conf:
            _goods_info = x.get("goods_info")
            _type = x.get("type",3)
            if _type == 1:
                coupon_len = len(_goods_info.get("coupon_list"))
                _name = f"{coupon_len}张优惠券"
                result.append({
                    "prize_type": _type,
                    "prize_name": _name,
                    "create_time": x.get("create_time"),
                })
            elif _type == 2:
                _points = _goods_info.get("points")
                _name = f"{_points}积分"
                result.append({
                    "prize_type": _type,
                    "prize_name": _name,
                    "create_time": x.get("create_time"),
                })
    return result

CAMPAIGN_PRIZE_PLUGIN["101"] = campaign_101_prize

async def campaign_102_prize(request, campaign_id, member_no, page_id=1, page_size=10):
    app = request.app
    cam_ins = app.campaign_instance.get(f"cam_{campaign_id}")
    if not cam_ins:
        logger.error(f"查询失败，没有找到活动缓存 {campaign_id}")
        return False, dict(code=RC.STATUS_ERROR, msg=f"查询失败，活动不在有效期内：{campaign_id}")
    records = await cam_ins.get_lottery_record(member_no, page_id, page_size)
    result = []
    for x in records:
        _name = x.get("lottery_info",{}).get("name", "未中奖")
        _type = x.get("lottery_type",3)
        if _type != 3:
#        if _type == 1: #积分
#            _points =  x.get("lottery_info",{}).get("name", "谢谢惠顾")
#            _name = f"{}{name}"
            result.append({
                "prize_type": _type,
                "prize_name": _name,
                "create_time": x.get("create_time"),
            })
    return result

CAMPAIGN_PRIZE_PLUGIN["102"] = campaign_102_prize

async def campaign_prize_default(request, campaign_info, result):
    return []


async def record_campaign(mgr, record):
    _now = datetime.now().strftime("%Y%m%d")
    record_cls = FlexModel.get(CampaignRecord, _now)
    created = await mgr.create(record_cls, **record)
    return created



