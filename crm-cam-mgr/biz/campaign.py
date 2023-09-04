# -*- coding: utf-8 -*-
from urllib.parse import urlencode

from peewee import DoesNotExist, logger
from common.models.cam import  CampaignInfo
from mtkext.guid import fast_guid
from datetime import datetime, timedelta
from calendar import monthrange

CAMPAIGN_PLUGIN = {}

def cam_101_check(request, detail):
    signin_way = detail.get("signin_way")
    assert signin_way in [1,2], "签到活动奖励规则选择错误"
    prize_conf = detail.get("prize_conf")
    assert prize_conf, "奖励规则未配置"
    for x in prize_conf:
        signin_days = x.get("signin_days")
        assert signin_days, "签到天数需要大于0"
        if signin_way == 2:
            assert x.get("schedule") in ["week", "month"], "签到周期配置错误"
        item = x.get("item")
        assert item, "奖品未配置"
        for y in item:
            _type = y.get("type")
            y["prize_no"] = y.get("prize_no") if y.get("prize_no") else fast_guid()
            assert _type in [1,2], "奖品类型错误"
            goods_info = y.get("goods_info")
            assert goods_info, "奖品配置错误"
            if _type == 1:
                assert goods_info.get("coupon_list"), "自制券配置错误"
            elif _type == 2:
                assert goods_info.get("rule_id"), "积分累积场景配置错误"
                assert goods_info.get("points"), "积分值配置错误"

CAMPAIGN_PLUGIN["101"] = cam_101_check

def cam_102_check(request, detail):
    lottery_way = detail.get("lottery_way")
    assert lottery_way in [1,2], "抽奖概率模式配置错误"
    lottery_schedule = detail.get("lottery_schedule")
    assert lottery_schedule, "奖励限制未配置"
    assert lottery_schedule.get("interval", "day") == "day", "只支持每天限制次数"
    lottery_consume = detail.get("lottery_consume")
    assert lottery_consume and lottery_consume.get("points"), "请输入消耗积分值"
    lottery_item = detail.get("lottery_item")
    is_default = []
    for x in lottery_item:
        order = x.get("order")
        assert order, "缺少奖品顺序"
        name = x.get("name")
        assert name, "奖品名称未配置"
        x["prize_no"] = x.get("prize_no") if x.get("prize_no") else fast_guid()
        qty = x.get("qty")
        assert qty, "奖品库存配置错误"
        if lottery_way == 2:
            probability = x.get("probability")
            assert probability, "概率未配置"
        _is_default = x.get("is_default", False)
        if _is_default:
            is_default.append(order)
        _type = x.get("type")
        assert _type in [1, 2, 3], "奖品类型错误"
        if _type == 3: continue # 未中奖，不检查奖品配置
        goods_info = x.get("goods_info")
        assert goods_info, "奖品配置错误"
        if _type == 1:
            assert goods_info.get("coupon_list"), "自制券配置错误"
        elif _type == 2:
            assert goods_info.get("rule_id"), "积分累积场景配置错误"
            assert goods_info.get("points"), "积分值配置错误"

    assert is_default and len(is_default) == 1, "必须配置1个默认奖品"

CAMPAIGN_PLUGIN["102"] = cam_102_check



def cam_103_check(request, detail):
    children = detail.get("children")
    assert children, "至少配置1个子活动"
    for child in children:
        child["campaign_child_no"] = child.get("campaign_child_no") if child.get("campaign_child_no") else fast_guid()
        _now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        start_time = child.get("start_time")
        end_time = child.get("end_time")
        assert start_time and end_time, "活动开始时间或结束时间未配置"
        assert start_time < end_time, "活动结束时间必须大于开始时间"
        assert _now < end_time, "活动结束时间必须大于当前时间"
        campaign_path = child.get("campaign_path")
        assert campaign_path, "资源包配置错误"

        target_type = child.get("target_type")
        if target_type: assert target_type in [1,2], "发送人群配置错误"
        if target_type == 1:
            people_ids = child.get("people_ids")
            assert people_ids, "人群包配置错误"
        elif target_type == 2:
            tag_condition = child.get("tag_condition")
            crm_id = request.headers.get("X-SHARK-CRM")
            assert crm_id, "系统错误：CRM编号错误"
            tag_condition["crm_id"] = crm_id
            #验证标签规则
            includes = tag_condition.get("includes")
            excludes = tag_condition.get("excludes")
            assert includes or excludes, "包含或者不包含至少配置其中1个"
            for _xcludes in [includes, excludes]:
                if _xcludes:
                    op = _xcludes.get("op")
                    assert op and op in ["and", "or"], "标签判断逻辑条件错误"
                    expr = _xcludes.get("expr")
                    assert expr, "未选择标签"
                    for _expr in expr:
                        assert _expr, "未选择标签"
                        tag_type = _expr.get("tag_type")
                        assert tag_type and tag_type in [1,2], "系统错误：标签类型配置错误"
                        tag_id = _expr.get("tag_id")
                        assert tag_id, "系统错误：标签编码配置错误"
                        tag_bind_field = _expr.get("tag_bind_field")
                        #assert tag_bind_field, "系统错误：标签绑定编码配置错误"
                        level_id = _expr.get("level_id")
                        assert level_id, "系统错误：标签级别配置错误"

        goods_info = child.get("goods_info")
        assert goods_info, "奖品配置错误"
        assert goods_info.get("coupon_list"), "卡券配置错误"
        assert goods_info.get("coupon_type") and goods_info.get("coupon_type", 1) in [1,2], "卡券类型配置错误"

CAMPAIGN_PLUGIN["103"] = cam_103_check

def cam_105_check(request, detail):
    before_days = detail.get("before_days")
    assert before_days is not None and before_days >= 0, "发送日期配置错误"
    send_time = detail.get("send_time")
    assert send_time, "发送时间配置错误"
    before_days = detail.get("before_days")
    assert before_days is not None and before_days >= 0, "发送日期配置错误"
    _type = y.get("type")
    assert _type in [1, 2], "奖励类型错误"
    goods_info = x.get("goods_info")
    assert goods_info, "奖励配置错误"
    if _type == 1:
        assert goods_info.get("coupon_list"), "自制券配置错误"
    elif _type == 2:
        assert goods_info.get("rule_id"), "积分累积场景配置错误"
        assert goods_info.get("points"), "积分值配置错误"

def cam_check(request, detail):
    pass

CAMPAIGN_PLUGIN["105"] = cam_105_check


async def get_month_activity(mgr, instance_id, year, month):
    month_start = datetime(year, month, 1).strftime('%Y-%m-%d')
    start, end = month_start, (datetime(year,month,1) + timedelta(days=monthrange(year,month)[1])).strftime("%Y-%m-%d")
    q = CampaignInfo.select(
        CampaignInfo.campaign_id,
        CampaignInfo.campaign_name,
        CampaignInfo.campaign_type,
        CampaignInfo.begin_time,
        CampaignInfo.end_time,
        CampaignInfo.create_time,
        CampaignInfo.detail,
    ).where(
        CampaignInfo.instance_id == instance_id,
        CampaignInfo.status != 2,
        CampaignInfo.begin_time < end,
        CampaignInfo.end_time > start
    ).order_by(
        CampaignInfo.create_time.desc()
    ).dicts()
    return await mgr.execute(q)
