#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/27
"""
import time
from biz.utils import translate_campaign_code
from common.biz.coupon_const import *
from common.biz.crm import cache_get_crm_channel_map
from common.models.coupon import CouponCodeGenInfo, CouponCodeInfo, CouponInfo, UserCouponCodeInfo
from mtkext.cut import cut2
from peewee import fn
from sanic.log import logger


def verify_create_card_param(data: dict):
    """
    校验创建卡券参数
    """
    assert data, "缺失卡券配置参数"
    card_meta_data = {}  # 存储需要返回的数据
    title = data.get("title")
    assert title and len(title) <= 64, "参数:卡券标题错误"
    card_meta_data["title"] = title
    subtitle = data.get("subtitle")
    assert subtitle, "参数:卡券副标题错误"
    card_meta_data["subtitle"] = subtitle
    # 默认 normal
    card_meta_data["biz_type"] = data.get("biz_type", None) or "normal"

    get_limit = data.get("get_limit", 0)
    assert isinstance(get_limit, int) and get_limit >= 0, "参数:get_limit错误"
    card_meta_data["get_limit"] = get_limit
    # use_limit = data.get("use_limit", 0)
    # assert isinstance(use_limit, int) and use_limit >= 0, "参数:use_limit错误"
    # card_meta_data["use_limit"] = use_limit
    # 默认为False
    # 商家券无此参数
    can_give_friend = data.get("can_give_friend", False)
    # if can_give_friend is not None:
    assert can_give_friend in (True, False), "参数:can_give_friend错误"

    card_meta_data["can_give_friend"] = can_give_friend
    card_meta_data['notice'] = data.get("notice", None)
    card_meta_data['rule'] = data.get("rule", None)
    card_meta_data['description'] = data.get("description", None)

    card_type = data.get("card_type")
    assert card_type in CardType.get_card_type_values(), "参数:card_type错误"  # 1:固定时间范围；2:动态时间；3:永久有效
    card_meta_data["card_type"] = card_type
    cash_condition = float(data.get("cash_condition", 0) or 0)
    qty_condition = int(data.get("qty_condition", 0) or 0)
    if card_type == CardType.CASH_COUPON.value:
        cash_amount = cut2(data["cash_amount"])
        assert cash_condition > 0 or qty_condition > 0, "代金券：起用金额或购满N件参数错误"
        assert cash_amount > 0, "代金券：券参数cash_amount错误"
        card_meta_data["cash_amount"] = cash_amount
    elif card_type == CardType.DISCOUNT_COUPON.value:
        discount_ = data.get("discount")
        discount = cut2(discount_)
        discount_limit = data.get("discount_limit")
        # 折扣数量 或 折扣金额或件数
        if not discount_limit:
            assert cash_condition > 0 or qty_condition > 0, "折扣：起用金额或购满N件参数错误"
        else:
            card_meta_data['discount_limit'] = data.get("discount_limit") or 0
        card_meta_data["discount"] = discount
    elif card_type == CardType.FREE_SHIP_COUPON.value:
        assert cash_condition > 0 or qty_condition > 0, "包邮券：起用金额或购满N件参数错误"
    elif card_type == CardType.GIFT_COUPON.value:
        assert cash_condition > 0 or qty_condition > 0, "赠品券：起用金额或购满N件参数错误"

    card_meta_data["cash_condition"] = cash_condition
    card_meta_data["qty_condition"] = qty_condition
    date_type = data.get("date_type")
    assert date_type in CardDateType.get_card_date_type_values(), "参数:date_type错误"  # 1:固定时间范围；2:动态时间；3:永久有效
    card_meta_data["date_type"] = date_type
    card_meta_data["extra_info"] = data.get("extra_info")
    # if date_type == CardDateType.DURATION.value:
    begin_time = data.get("begin_time")
    assert begin_time, "缺失参数:begin_time"
    # assert begin_time > 0, "参数错误:begin_time"
    end_time = data.get("end_time")
    assert end_time, "缺失参数:end_time"
    # assert end_time > 0, "参数错误:end_time"
    assert end_time > begin_time, "end_time必须大于begin_time"
    card_meta_data["begin_time"] = begin_time
    card_meta_data["end_time"] = end_time
    if date_type == CardDateType.INTERVAL.value:
        start_day_count = data.get("start_day_count", -1)
        assert isinstance(start_day_count, int) and start_day_count >= 0, "参数:start_day_count错误"
        expire_day_count = data.get("expire_day_count", -1)
        assert isinstance(start_day_count, int) and expire_day_count > 0, "参数:expire_day_count错误"
        card_meta_data["start_day_count"] = start_day_count
        card_meta_data["expire_day_count"] = expire_day_count
    cover_img = data.get("cover_img")
    if data.get("source") == CardSource.CRM.value:
        cover_img = cover_img or ""
    else:
        assert cover_img, "参数:封面图必填"
    card_meta_data['cover_img'] = cover_img
    # 自建券参数
    total_quantity = data.get("total_quantity")
    assert total_quantity > 0, "参数：total_quantity错误"
    card_meta_data["total_quantity"] = data.get("total_quantity")

    if data.get("source") == CardSource.CRM.value:
        card_meta_data['icon'] = data.get("icon")
        card_meta_data['store_codes'] = data.get("store_codes", None)
        weekdays = data.get("weekdays", [])
        if not isinstance(weekdays, list):
            weekdays = []
        card_meta_data["weekdays"] = weekdays
        monthdays = data.get("monthdays")
        if monthdays is not None:
            card_meta_data["monthdays"] = monthdays
        scene = data.get("scene", [])
        if not isinstance(scene, list):
            scene = []
        card_meta_data["scene"] = scene
        start_time = data.get("day_begin_time", "00:00:00")
        # 时间格式判断
        try:
            s_hour, s_minute, _ = start_time.split(":")
        except Exception:
            raise ValueError("参数:start_time错误")
        card_meta_data["day_begin_time"] = start_time
        end_time = data.get("day_end_time", "23:59:59")
        try:
            e_hour, e_minute, _ = end_time.split(":")
            # e_hour = int(e_hour)
            # e_minute = int(e_minute)
        except Exception:
            raise ValueError("参数:end_time错误")

        # assert e_hour >= s_hour, "截止时间必须晚于起始时间"
        # if e_hour == s_hour:
        #     assert e_minute >= s_minute, "截止时间必须晚于起始时间"
        card_meta_data["day_end_time"] = end_time
        # 券码规则
        card_meta_data["generate_type"] = 1

        interests_type = data.get("interests_type")
        if interests_type:
            assert isinstance(interests_type, int) and interests_type in \
                   InterestsType.get_values(), "参数:interests_type错误"
            card_meta_data["interests_type"] = interests_type
            card_meta_data["interests_amount"] = data.get("interests_amount")

            interests_period_type = data.get("interests_period_type")
            if interests_period_type:
                assert isinstance(interests_period_type, int) and interests_period_type in \
                       InterestsPeriodType.get_values(), "参数:interests_period_type错误"
                assert isinstance(data.get("interests_period_amount"), float) or isinstance(data.get("interests_period_amount"), int), "参数:interests_period_amount错误"
                card_meta_data["interests_period_type"] = interests_period_type
                card_meta_data["interests_period_amount"] = data.get("interests_period_amount")

    elif data.get("source") == CardSource.WX_PAY.value:
        card_meta_data["card_id"] = data.get("card_id")
        pass
    else:
        assert False, "卡券source 错误"
    card_meta_data['extra_info'] = data.get("extra_info")
    card_meta_data["source"] = data.get("source")
    return card_meta_data


async def get_crm_coupon_stock(db, redis, crm_id, card_id, card_key):
    query = CouponCodeGenInfo.select(fn.sum(CouponCodeGenInfo.quantity).alias("total")).where(
        CouponCodeGenInfo.crm_id == crm_id, CouponCodeGenInfo.card_id == card_id)
    total_quantity = await db.get(query)
    total_quantity = total_quantity.total
    card_info = await db.get(CouponInfo.select().where(CouponInfo.card_id == card_id, CouponInfo.crm_id == crm_id))
    if not total_quantity:
        total_quantity = card_info.total_quantity
        result = {"total_quantity": total_quantity}
        return result
    # count_query = CouponCodeInfo.select(fn.count(1).alias("count")).where(
    #     CouponCodeInfo.crm_id == crm_id, CouponCodeInfo.card_id == card_id,
    #     CouponCodeInfo.card_code_status == CouponCodeStatus.INACTIVE.value)
    # total_count = await db.get(count_query)
    # total_count = total_count.count
    # code_len = await redis.llen(card_key)

    receive_query = UserCouponCodeInfo.select(
        fn.count(UserCouponCodeInfo.card_code.distinct()).alias("total_receive_count")).where(
        UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.received_time >= card_info.create_time,
        UserCouponCodeInfo.card_id == card_id)
    logger.info(f"{receive_query.sql()}")
    receive_result = await db.get(receive_query.dicts())
    total_receive_count = receive_result.get("total_receive_count", 0)

    gen_count = await db.count(CouponCodeGenInfo.select().where(
        CouponCodeGenInfo.crm_id == crm_id,
        CouponCodeGenInfo.gen_status != CouponCodeGenStatus.FINISH.value,
        CouponCodeGenInfo.card_id == card_id))
    # result = {"total_quantity": total_quantity, "total_count": total_count + code_len, "have_gen_record": gen_count > 0}
    result = {"total_quantity": total_quantity, "total_count": total_quantity - total_receive_count, "have_gen_record": gen_count > 0}
    return result


def verify_update_card_param(data):
    source = data.get("source")
    assert source in [1, 2], "卡券来源类型 错误 1 crm券，2.商家券"
    card_id = data["card_id"]
    title = data["title"]
    subtitle = data["subtitle"]
    notice = data["notice"]
    rule = data["rule"]
    bg_color = data["bg_color"]
    cover_img = data.get("cover_img")
    extra_info = data["extra_info"]
    card_meta_data = {
        "card_id": card_id, "title": title, "subtitle": subtitle, "notice": notice, "rule": rule, "cover_img": cover_img,
        "extra_info": extra_info
    }
    return card_meta_data


async def translate_coupon_channel(app, crm_id, in_str):
    """使用chanell_code和campaign_code翻译"""
    new_str = None
    if in_str.startswith("cam_crm"):
        # 翻译为活动名称
        new_str = await translate_campaign_code(app, in_str)
        if new_str: return new_str
    # 使用渠道code翻译
    channel_map = await cache_get_crm_channel_map(app.mgr, app.redis, crm_id)
    cn_label = channel_map.get(in_str, {}).get("channel_name")
    if cn_label:
        return cn_label
    return new_str
