#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/7/1
"""
from common.biz.coupon_const import UserCardCodeStatus
from common.models.coupon import CouponInfo, UserCouponRedeemInfo, UserCouponCodeInfo, UserInterestsCostRecord
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict
from sanic.kjson import json_loads, json_dumps
from sanic.log import logger

instance_prefix = "crm_coupon_meta"


class CouponException(Exception):
    def __init__(self, code, msg, crm_id, card_id, member_no=None, card_code=None):
        super(CouponException, self).__init__(code, msg, crm_id, card_id)
        self.code = code
        self.msg = msg
        self.card_id = card_id
        self.crm_id = crm_id
        self.member_no = member_no
        self.card_code = card_code


async def get_coupon_meta_data(db, redis, crm_id, card_id):
    """
    获取卡券元信息
    """
    try:
        redis_key = f"{instance_prefix}{crm_id}_{card_id}"
        got = await redis.get(redis_key)
        if got:
            return json_loads(got)
        else:
            query = CouponInfo.select().where(CouponInfo.crm_id == crm_id, CouponInfo.card_id == card_id)
            data = await db.get(query.dicts())
            await redis.setex(redis_key, 60 * 1, json_dumps(data))
            # date_time和time类型 转化为str
            got = await redis.get(redis_key)
            return json_loads(got)
    except DoesNotExist:
        logger.exception(f"not find {crm_id} {card_id}")
        raise DoesNotExist


async def remove_coupon_meta_data(redis, crm_id, card_id):
    """
    删除元信息
    """
    redis_key = f"{instance_prefix}{crm_id}_{card_id}"
    await redis.delete(redis_key)


async def coupon_redeem_search(db, crm_id, member_no, page, page_size, store_code=None, redeem_cost_center=None, begin_time=None,
                               end_time=None, rollback_status=0, order_asc=0, cls=UserCouponRedeemInfo):
    """
    核销卡券列表查询
    """
    tc = cls.redeem_time
    where = [cls.crm_id == crm_id]
    if rollback_status == 0:
        where.append(cls.rollback_status == 0)
    elif rollback_status == 1:
        where.append(cls.rollback_status == rollback_status)
    if begin_time and end_time:
        where.append(tc.between(begin_time, end_time))
    if member_no:
        where.append(cls.member_no == member_no)
    if store_code:
        where.append(cls.store_code == store_code)
    if redeem_cost_center:
        where.append(cls.redeem_cost_center == redeem_cost_center)

    _select = [cls.card_id, cls.member_no, cls.card_code,
        cls.redeem_channel, cls.outer_redeem_id, cls.store_code,
        cls.redeem_cost_center, cls.rollback_status,
        cls.redeem_time, cls.rollback_time, CouponInfo.title, CouponInfo.subtitle, CouponInfo.scene,
        CouponInfo.notice, CouponInfo.rule, CouponInfo.description, CouponInfo.cash_amount, CouponInfo.cash_condition,
        CouponInfo.qty_condition, CouponInfo.discount, CouponInfo.icon, CouponInfo.cover_img]

    if cls == UserInterestsCostRecord:
        _select.append(cls.redeem_amount)

    items = await db.execute(cls.select(*_select).join(CouponInfo, on=(cls.card_id == CouponInfo.card_id)).where(*where).order_by(
        tc.asc() if order_asc else tc.desc()).paginate(page, page_size).dicts())
    total = await db.count(cls.select().where(*where))
    return total, items


async def user_coupon_search(db, crm_id, member_no, page, page_size, mtype, cost_center=None, begin_time=None,
                             end_time=None, order_asc=0, check_code_status=False):
    """
    mtype:  receive，present，expired，invalid 业务类型定义
    check_code_status: False 指不根据 当前userCouponCode  code_status查询。 仅根据时间判断流水信息，因暂缺事件数据 故提供当前实现方法。
                    True 可以适用与用户卡包状态查询，
                    todo 后需支持新增卡券元信息 类型查询。
    """
    where = [UserCouponCodeInfo.crm_id == crm_id]
    if member_no:
        where.append(UserCouponCodeInfo.member_no == member_no)
    if mtype == "receive":
        tc = UserCouponCodeInfo.received_time
        if check_code_status:
            where.append(UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value)
        # 成本中心
        if cost_center:
            where.append(UserCouponCodeInfo.cost_center == cost_center)
    elif mtype == "expired":
        tc = UserCouponCodeInfo.expired_time
        if check_code_status:
            where.append(
                UserCouponCodeInfo.code_status == UserCardCodeStatus.EXPIRED.value)
    elif mtype == "present":
        tc = UserCouponCodeInfo.present_time
        if check_code_status:
            where.append(
                UserCouponCodeInfo.code_status.in_([UserCardCodeStatus.PRESENTING.value, UserCardCodeStatus.PRESENT_RECEIVED.value]))
    elif mtype == "invalid":
        tc = UserCouponCodeInfo.obsoleted_time
        if check_code_status:
            where.append(
                UserCouponCodeInfo.code_status.in_([UserCardCodeStatus.INVALID.value, UserCardCodeStatus.RECEIVE_REVERSE.value]))
    else:
        return False, 0, "不支持的 mtype 参数"
    if begin_time and end_time:
        where.append(tc.between(begin_time, end_time))
    items = await db.execute(UserCouponCodeInfo.select(
        UserCouponCodeInfo.card_id, UserCouponCodeInfo.member_no, UserCouponCodeInfo.receive_id, UserCouponCodeInfo.card_code,
        UserCouponCodeInfo.start_time, UserCouponCodeInfo.end_time, UserCouponCodeInfo.code_status, UserCouponCodeInfo.outer_str,
        UserCouponCodeInfo.cost_center, UserCouponCodeInfo.received_time, UserCouponCodeInfo.redeem_time,
        UserCouponCodeInfo.present_time, UserCouponCodeInfo.obsoleted_time, UserCouponCodeInfo.receive_reverse_time,
        UserCouponCodeInfo.expired_time, CouponInfo.title, CouponInfo.subtitle, CouponInfo.scene, CouponInfo.notice,
        CouponInfo.rule, CouponInfo.description, CouponInfo.cash_amount, CouponInfo.cash_condition,
        CouponInfo.qty_condition, CouponInfo.discount, CouponInfo.icon, CouponInfo.cover_img
    ).join(CouponInfo, on=(UserCouponCodeInfo.card_id == CouponInfo.card_id)).where(*where).order_by(
        tc.asc() if order_asc else tc.desc()).paginate(page, page_size).dicts())
    total = await db.count(UserCouponCodeInfo.select().where(*where))
    return True, total, items
