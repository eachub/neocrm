#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/27
"""
from datetime import datetime, timedelta

from biz.coupon import card_list_plug
from common.biz.const import RC, CouponError
from common.biz.coupon import get_coupon_meta_data, CouponException
from common.biz.coupon_const import UserCardCodeStatus, CardDateType, CouponCodeStatus, UserPresentStatus, InterestsType
from common.biz.wrapper import safe_crm_instance
from common.models.coupon import UserReceivedRecord, UserCouponReceivedDetail, UserCouponCodeInfo, CouponCodeInfo, \
    UserPresentCouponInfo, CouponInfo, UserCouponRedeemInfo, UserInterestsCostRecord, UserInterestsCostInfo
from mtkext.guid import fast_guid
from sanic import Blueprint
from sanic.response import json
from sanic.log import logger
import copy
from biz.utils import gen_period_value
from peewee import fn

bp = Blueprint("card", url_prefix="/card")


@bp.post("/<crm_id>/member/receive")
@safe_crm_instance
async def member_receive(request, crm_id):
    """
    普通用户领取卡券
    """
    try:
        obj = request.json
        member_no, receive_id = obj.get("member_no"), obj.get("receive_id")
        card_info = obj.get("card_info")
        outer_str = obj.get("outer_str", "default")
        card_code_key_format = request.app.conf.CRM_COUPON_CODE_QUEUE_FORMAT
        assert member_no, "member_no 必填"
        assert receive_id, "receive_id 必填"
        assert card_info and isinstance(card_info, list), "card_info 必填"
        for i in card_info:
            assert i.get("card_id"), "card_info.card_id 必填"
            assert i.get("qty"), "card_info.qty 必填 且 大于0"
            # assert i.get("cost_center"), "card_info.cost_center 必填"
        mgr = request.app.mgr
        redis = request.app.redis
        # 事务开始 领取记录
        async with mgr.atomic():
            query_len, query_status = await mgr.get_or_create(
                UserReceivedRecord, **{"crm_id": crm_id, "member_no": member_no, "receive_id": receive_id})
            # 创建成功 说明receive_id 未领取过
            if not query_status:
                # todo query receive_id card code info
                data_list = await mgr.execute(
                    UserCouponCodeInfo.select(
                        UserCouponCodeInfo.crm_id, UserCouponCodeInfo.card_id, UserCouponCodeInfo.member_no,
                        UserCouponCodeInfo.receive_id, UserCouponCodeInfo.card_code, UserCouponCodeInfo.start_time,
                        UserCouponCodeInfo.end_time, UserCouponCodeInfo.code_status, UserCouponCodeInfo.outer_str,
                        UserCouponCodeInfo.cost_center).where(
                        UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                        UserCouponCodeInfo.receive_id == receive_id).dicts())
                return json(dict(code=RC.OK, data={"coupon_result": data_list}))
            # 可领取
            result = []
            for i in card_info:
                card_id, qty, cost_center = i.get("card_id"), i.get("qty"), i.get("cost_center", None)
                card_meta_data = await get_coupon_meta_data(mgr, redis, crm_id, card_id)
                receive_data = {
                    "crm_id": crm_id, "card_id": card_id, "member_no": member_no, "receive_id": receive_id, "cost_center": cost_center,
                    "outer_str": outer_str, "received_info": obj, "code_status": UserCardCodeStatus.AVAILABLE.value}
                for _ in range(0, qty):
                    data = await receive_card(mgr, redis, receive_data, card_meta_data, card_code_key_format)
                    data.pop("received_info", None)
                    result.append(data)
        return json(dict(code=RC.OK, msg="ok", data={"coupon_result": result}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"{ex.msg} card_id {ex.card_id}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))
    pass


async def receive_card(db, redis, receive_data, meta_data, card_code_key_format):
    # 计算
    tmp_receive_data = copy.deepcopy(receive_data)
    date_type = meta_data.get("date_type")
    crm_id = tmp_receive_data.get("crm_id")
    card_id = tmp_receive_data.get("card_id")
    member_no = tmp_receive_data.get("member_no")
    # 固定时段
    if date_type == CardDateType.DURATION.value:
        start_time = meta_data.get("begin_time")
        end_time = meta_data.get("end_time")
    # 动态时段 参考商家券逻辑，所有卡券都配置begin_time 和end_time
    elif date_type == CardDateType.INTERVAL.value:
        fixed_term = meta_data.get('expire_day_count')
        begin_term = meta_data.get('start_day_count')
        today = datetime.today().date()
        card_start_time = meta_data.get("begin_time")
        start_time = (today + timedelta(days=begin_term)).strftime("%Y-%m-%d %H:%M:%S")
        if start_time <= card_start_time:
            start_time = card_start_time
            start_date = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            tmp_date = start_date + timedelta(fixed_term)
            end_time = (datetime(tmp_date.year, tmp_date.month, tmp_date.day) + timedelta(seconds=-1)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            tmp_date = (today + timedelta(days=begin_term) + timedelta(fixed_term))
            end_time = (datetime(tmp_date.year, tmp_date.month, tmp_date.day) + timedelta(seconds=-1)).strftime("%Y-%m-%d %H:%M:%S")
        card_end_time = meta_data.get("end_time")
        if end_time >= card_end_time:
            end_time = card_end_time
    else:
        start_time = "1970-01-01 00:00:00"
        end_time = "2100-12-31 23:59:59"
    tmp_receive_data['start_time'] = start_time
    tmp_receive_data['end_time'] = end_time
    user_receive_detail, status = await db.get_or_create(
        UserCouponReceivedDetail, **{"crm_id": crm_id, "member_no": member_no, "card_id": card_id})
    # 领取过判断限领
    if not status:
        get_limit = meta_data.get("get_limit")
        where = [UserCouponReceivedDetail.member_no == member_no, UserCouponReceivedDetail.card_id == card_id,
                 UserCouponReceivedDetail.crm_id == crm_id]
        if get_limit > 0:
            where.append(UserCouponReceivedDetail.count < get_limit)
        update_result = await db.execute(UserCouponReceivedDetail.update(
            {UserCouponReceivedDetail.count: UserCouponReceivedDetail.count + 1,
             UserCouponReceivedDetail.update_time: datetime.now()}).where(*where))
        if not update_result:
            raise CouponException(code=CouponError.RECEIVED_LIMIT, msg="卡券领取超限", card_id=card_id, crm_id=crm_id,
                                  member_no=member_no)
    # 获取券码信息
    key = card_code_key_format.format(crm_id=crm_id, card_id=card_id)
    card_code = await redis.rpop(key)
    card_code = card_code.decode() if card_code is not None else None
    if not card_code:
        raise CouponException(code=CouponError.NO_STOCK, msg="卡券库存不足", card_id=card_id, crm_id=crm_id, member_no=member_no)
    tmp_receive_data["card_code"] = card_code
    try:
        await db.execute(UserCouponCodeInfo.insert(**tmp_receive_data))
        count = await db.execute(CouponCodeInfo.update({CouponCodeInfo.card_code_status: CouponCodeStatus.RECEIVED.value}).where(
            CouponCodeInfo.crm_id == crm_id, CouponCodeInfo.card_id == card_id, CouponCodeInfo.card_code == card_code))
        return tmp_receive_data
    except Exception as ex:
        logger.exception(ex)
        raise CouponException(code=CouponError.RECEIVED_FAILED, msg="卡券领取异常", card_id=card_id, crm_id=crm_id,
                              member_no=member_no)


@bp.post("/<crm_id>/member/reverse_single_card")
@safe_crm_instance
async def reverse_single_card(request, crm_id):
    try:
        obj = request.json
        member_no, receive_id = obj.get("member_no"), obj.get("receive_id")
        card_id, card_code = obj.get("card_id"), obj.get("card_code")
        assert member_no, "member_no 必填"
        assert receive_id, "receive_id 必填"
        assert card_id, "card_id 必填"
        assert card_code, "card_code 必填"
        mgr = request.app.mgr
        query = UserCouponCodeInfo.select(
            UserCouponCodeInfo.crm_id, UserCouponCodeInfo.card_id, UserCouponCodeInfo.card_code, UserCouponCodeInfo.member_no,
            UserCouponCodeInfo.receive_id, UserCouponCodeInfo.code_status
        ).where(UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                UserCouponCodeInfo.receive_id == receive_id, UserCouponCodeInfo.card_id == card_id,
                UserCouponCodeInfo.card_code == card_code, UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value)
        user_card_list = await mgr.execute(query.dicts())
        if not len(user_card_list):
            # 没有查询到对应作废卡券的内容
            return json(dict(code=RC.OK, msg="ok", data={}))
        async with mgr.atomic():
            for item in user_card_list:
                await receive_reverse(mgr, item)
        return json(dict(code=RC.OK, msg="ok", data={}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


@bp.post("/<crm_id>/member/receive_reverse")
@safe_crm_instance
async def member_receive_reverse(request, crm_id):
    """
    冲正领取「限领额度退回」
    """
    try:
        obj = request.json
        member_no, receive_id = obj.get("member_no"), obj.get("receive_id")
        assert member_no, "member_no 必填"
        assert receive_id, "receive_id 必填"
        mgr = request.app.mgr
        query = UserCouponCodeInfo.select(
            UserCouponCodeInfo.crm_id, UserCouponCodeInfo.card_id, UserCouponCodeInfo.card_code, UserCouponCodeInfo.member_no,
            UserCouponCodeInfo.receive_id, UserCouponCodeInfo.code_status
        ).where(UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                UserCouponCodeInfo.receive_id == receive_id)
        user_card_list = await mgr.execute(query.dicts())
        if not len(user_card_list):
            # 没有查询到对应作废卡券的内容
            return json(dict(code=RC.OK, msg="ok", data={}))
        async with mgr.atomic():
            for item in user_card_list:
                await receive_reverse(mgr, item)
        return json(dict(code=RC.OK, msg="ok", data={}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


async def receive_reverse(db, user_coupon_code):
    crm_id = user_coupon_code.get("crm_id")
    card_id = user_coupon_code.get("card_id")
    member_no = user_coupon_code.get("member_no")
    receive_id = user_coupon_code.get("receive_id")
    card_code = user_coupon_code.get("card_code")
    code_status = user_coupon_code.get("code_status")
    # 已冲正
    if code_status == UserCardCodeStatus.RECEIVE_REVERSE.value:
        return
    query = UserCouponCodeInfo.update(
        {UserCouponCodeInfo.code_status: UserCardCodeStatus.RECEIVE_REVERSE.value,
         UserCouponCodeInfo.receive_reverse_time: datetime.now()}).where(
        UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.card_id == card_id, UserCouponCodeInfo.member_no == member_no,
        UserCouponCodeInfo.receive_id == receive_id, UserCouponCodeInfo.card_code == card_code,
        UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value)
    result = await db.execute(query)
    if not result:
        raise CouponException(code=CouponError.RECEIVE_REVERSE, msg="领取冲正失败", card_id=card_id, crm_id=crm_id,
                              member_no=member_no)
    await db.execute(UserCouponReceivedDetail.update(
        {UserCouponReceivedDetail.count: UserCouponReceivedDetail.count - 1}).where(
        UserCouponReceivedDetail.member_no == member_no, UserCouponReceivedDetail.card_id == card_id,
        UserCouponReceivedDetail.crm_id == crm_id))


@bp.post("/<crm_id>/member/present")
@safe_crm_instance
async def member_present(request, crm_id):
    """
    转赠接口
    """
    try:
        obj = request.json
        member_no, card_id, card_code = obj.get("member_no"), obj.get("card_id"), obj.get("card_code")
        assert member_no, "member_no 必填"
        assert card_id, "card_id 必填"
        assert card_code, "card_code 必填"
        mgr = request.app.mgr
        async with mgr.atomic():
            update_result = await mgr.execute(UserCouponCodeInfo.update({
                UserCouponCodeInfo.code_status: UserCardCodeStatus.PRESENTING.value,
                UserCouponCodeInfo.present_time: datetime.now()}).where(
                UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.card_id == card_id,
                UserCouponCodeInfo.member_no == member_no, UserCouponCodeInfo.card_code == card_code,
                UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value))
            if not update_result:
                raise CouponException(code=CouponError.PRESENT_FAILED, msg="转赠失败", card_id=card_id, member_no=member_no,
                                      crm_id=crm_id)
            present_gen_id = fast_guid().lower()
            data = {"crm_id": crm_id, "from_member_no": member_no, "card_id": card_id, "card_code": card_code,
                    "present_gen_id": present_gen_id, "present_type": 1}
            auto_id = await mgr.execute(UserPresentCouponInfo.insert(**data))
            logger.info(f"{data} present success {auto_id}")
        return json(dict(code=RC.OK, msg="ok", data={"present_gen_id": present_gen_id}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


@bp.post("/<crm_id>/member/present_receive")
@safe_crm_instance
async def member_present_receive(request, crm_id):
    """
    转赠领取
    """
    try:
        obj = request.json
        member_no = obj.get("member_no")
        present_gen_id = obj.get("present_gen_id")
        assert member_no, "member_no 必填"
        assert present_gen_id, "present_gen_id 必填"
        mgr = request.app.mgr
        update_query = UserPresentCouponInfo.update({
            UserPresentCouponInfo.to_member_no: member_no, UserPresentCouponInfo.received_time: datetime.now(),
            UserPresentCouponInfo.present_status: UserPresentStatus.RECEIVED.value
        }).where(
            UserPresentCouponInfo.crm_id == crm_id, UserPresentCouponInfo.from_member_no != member_no,
            UserPresentCouponInfo.present_gen_id == present_gen_id,
            UserPresentCouponInfo.present_status == UserPresentStatus.PRESENTING.value)
        async with mgr.atomic():
            result = await mgr.execute(update_query)
            if not result:
                raise CouponException(code=CouponError.PRESENT_RECEIVED_FAILED, msg="转赠领取失败", crm_id=crm_id, card_id="")
            # 查询转赠记录
            present_query = UserPresentCouponInfo.select().where(
                UserPresentCouponInfo.present_gen_id == present_gen_id, UserPresentCouponInfo.crm_id == crm_id)
            present_info = await mgr.get(present_query.dicts())
            # 查询券码信息
            query = UserCouponCodeInfo.select().where(
                UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.card_id == present_info.get("card_id"),
                UserCouponCodeInfo.card_code == present_info.get("card_code"),
                UserCouponCodeInfo.member_no == present_info.get("from_member_no"),
                UserCouponCodeInfo.code_status == UserCardCodeStatus.PRESENTING.value)
            old_user_coupons = await mgr.execute(query)
            if len(old_user_coupons) == 0:
                raise CouponException(code=CouponError.PRESENT_RECEIVED_FAILED, msg="转赠领取失败", crm_id=crm_id, card_id="")
            old_user_coupon = old_user_coupons[0]
            # 转赠卡券修改状态
            await mgr.execute(UserCouponCodeInfo.update({
                UserCouponCodeInfo.code_status: UserCardCodeStatus.PRESENT_RECEIVED.value}).where(
                UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.card_id == present_info.get("card_id"),
                UserCouponCodeInfo.card_code == present_info.get("card_code"),
                UserCouponCodeInfo.member_no == present_info.get("from_member_no"),
                UserCouponCodeInfo.code_status == UserCardCodeStatus.PRESENTING.value
            ))
            # 获取新的券卡券信息
            new_user_coupon = {
                "crm_id": old_user_coupon.crm_id, "card_id": old_user_coupon.card_id, "member_no": member_no,
                "receive_id": present_gen_id, "card_code": old_user_coupon.card_code, "start_time": old_user_coupon.start_time,
                "end_time": old_user_coupon.end_time, "code_status": UserCardCodeStatus.AVAILABLE.value,
                "outer_str": "present_received", "cost_center": old_user_coupon.cost_center, "received_info": obj,
            }
            # 插入新的券卡券信息 todo 判断当前卡券是否已过期
            await mgr.execute(UserCouponCodeInfo.insert(**new_user_coupon))
            return json(dict(code=RC.OK, msg="ok", data={}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))
    pass


@bp.get("/<crm_id>/member/present_list")
@safe_crm_instance
async def member_present_list(request, crm_id):
    """
    查询转赠列表
    """
    try:
        obj = request.args
        member_no = obj.get("member_no")
        page = int(obj.get("page", 1))
        page_size = int(obj.get("page_size", 5))
        assert member_no, "member_no 必填"
        mgr = request.app.mgr
        query = UserPresentCouponInfo.select(
            UserPresentCouponInfo.from_member_no, UserPresentCouponInfo.to_member_no,
            UserPresentCouponInfo.card_id, UserPresentCouponInfo.present_gen_id,
            UserPresentCouponInfo.present_status, UserPresentCouponInfo.received_time,
            UserPresentCouponInfo.go_back_time, CouponInfo.card_type, CouponInfo.title, CouponInfo.subtitle, CouponInfo.scene,
            CouponInfo.notice, CouponInfo.rule, CouponInfo.description, CouponInfo.weekdays, CouponInfo.monthdays,
            CouponInfo.day_begin_time, CouponInfo.day_end_time, CouponInfo.cash_amount, CouponInfo.cash_condition,
            CouponInfo.qty_condition, CouponInfo.discount, CouponInfo.icon, CouponInfo.cover_img
        ).join(CouponInfo, on=(UserPresentCouponInfo.card_id == CouponInfo.card_id)).where(
            UserPresentCouponInfo.crm_id == crm_id, UserPresentCouponInfo.from_member_no == member_no)
        result = await mgr.execute(query.paginate(page, page_size).dicts())
        return json(dict(code=RC.OK, msg="ok", data={"present_list": result}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))
    pass


@bp.get("/<crm_id>/member/present_detail")
@safe_crm_instance
async def member_present_detail(request, crm_id):
    """
    查询转赠信息
    """
    try:
        obj = request.args
        present_gen_id = obj.get("present_gen_id")
        assert present_gen_id, "present_gen_id 必填"
        mgr = request.app.mgr
        query = UserPresentCouponInfo.select(
            UserPresentCouponInfo.from_member_no, UserPresentCouponInfo.to_member_no,
            UserPresentCouponInfo.card_id, UserPresentCouponInfo.present_gen_id,
            UserPresentCouponInfo.present_status, UserPresentCouponInfo.received_time,
            UserPresentCouponInfo.go_back_time, CouponInfo.card_type, CouponInfo.title, CouponInfo.subtitle, CouponInfo.scene,
            CouponInfo.notice, CouponInfo.rule, CouponInfo.description, CouponInfo.weekdays, CouponInfo.monthdays,
            CouponInfo.day_begin_time, CouponInfo.day_end_time, CouponInfo.cash_amount, CouponInfo.cash_condition,
            CouponInfo.qty_condition, CouponInfo.discount, CouponInfo.icon, CouponInfo.cover_img
        ).join(CouponInfo, on=(UserPresentCouponInfo.card_id == CouponInfo.card_id)
               ).where(
            UserPresentCouponInfo.crm_id == crm_id, UserPresentCouponInfo.present_gen_id == present_gen_id)
        result = await mgr.get(query.dicts())
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))
    pass


@bp.get("/<crm_id>/member/card_list")
@safe_crm_instance
async def member_card_list(request, crm_id):
    try:
        obj = request.args
        member_no = obj.get("member_no")
        page = int(obj.get("page", 1))
        page_size = int(obj.get("page_size", 5))
        code_status = int(obj.get("code_status", 0))
        biz_type = obj.get("biz_type", None)
        card_id = obj.get('card_id')
        receive_id = obj.get('receive_id')
        order_by = obj.get("order_by")
        order_asc = int(obj.get("order_asc", 1))
        assert not order_by or order_by in ["received_time", "redeem_time"], "order_by排序字段需要取值received_time或redeem_time"
        if order_by:
            assert order_asc in [0, 1], "order_asc顺序取值错误。合法值是0或1。"

        where = [UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no]
        if biz_type:
            where.append(CouponInfo.biz_type == biz_type)
        if code_status:
            where.append(UserCouponCodeInfo.code_status == code_status)
        if card_id:
            where.append(UserCouponCodeInfo.card_id == card_id)
        if receive_id:
            where.append(UserCouponCodeInfo.receive_id == receive_id)
        interests_type = obj.get("interests_type", None)
        if interests_type:
            where.append(CouponInfo.interests_type == interests_type)
        assert member_no, "member_no 必填"
        mgr = request.app.mgr
        query = UserCouponCodeInfo.select(
            UserCouponCodeInfo.card_id, UserCouponCodeInfo.member_no, UserCouponCodeInfo.receive_id,
            UserCouponCodeInfo.card_code, UserCouponCodeInfo.start_time, UserCouponCodeInfo.end_time,
            UserCouponCodeInfo.code_status, UserCouponCodeInfo.outer_str, UserCouponCodeInfo.received_time,
            UserCouponCodeInfo.redeem_time, UserCouponCodeInfo.present_time, UserCouponCodeInfo.obsoleted_time,
            UserCouponCodeInfo.receive_reverse_time, UserCouponCodeInfo.expired_time,
            CouponInfo.card_type, CouponInfo.title, CouponInfo.subtitle, CouponInfo.scene,
            CouponInfo.notice, CouponInfo.rule, CouponInfo.description, CouponInfo.weekdays,
            CouponInfo.monthdays, CouponInfo.day_begin_time, CouponInfo.day_end_time, CouponInfo.cash_amount,
            CouponInfo.cash_condition, CouponInfo.qty_condition, CouponInfo.discount, CouponInfo.icon,
            CouponInfo.cover_img, CouponInfo.interests_type, CouponInfo.interests_amount,
            CouponInfo.interests_period_type, CouponInfo.interests_period_amount
        ).join(
            CouponInfo, on=(UserCouponCodeInfo.card_id == CouponInfo.card_id)
        ).where(*where)
        count = await mgr.count(query)
        if order_by == "received_time":
            _order = UserCouponCodeInfo.received_time.asc() if order_asc else UserCouponCodeInfo.received_time.desc()
            query = query.order_by(_order, UserCouponCodeInfo.member_coupon_id.desc())
        elif order_by == "redeem_time":
            _order = UserCouponCodeInfo.redeem_time.asc() if order_asc else UserCouponCodeInfo.redeem_time.desc()
            query = query.order_by(_order, UserCouponCodeInfo.member_coupon_id.desc())
        result = await mgr.execute(query.paginate(page, page_size).dicts())
        # 加入额度和频次相关字段
        result = await card_list_plug(mgr, result, member_no, crm_id)
        return json(dict(code=RC.OK, msg="ok", data={"coupon_list": result, "count": count}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


@bp.post("/<crm_id>/member/card_detail")
@safe_crm_instance
async def member_card_detail(request, crm_id):
    try:
        obj = request.json
        member_no, card_id, card_code = obj.get("member_no"), obj.get("card_id"), obj.get("card_code")
        assert member_no, "member_no 必填"
        assert card_id, "card_id 必填"
        assert card_code, "card_code 必填"
        mgr = request.app.mgr
        query = UserCouponCodeInfo.select(
            UserCouponCodeInfo.card_id, UserCouponCodeInfo.member_no, UserCouponCodeInfo.receive_id,
            UserCouponCodeInfo.card_code, UserCouponCodeInfo.start_time, UserCouponCodeInfo.end_time,
            UserCouponCodeInfo.code_status, UserCouponCodeInfo.outer_str, UserCouponCodeInfo.received_time,
            UserCouponCodeInfo.redeem_time, UserCouponCodeInfo.present_time, UserCouponCodeInfo.obsoleted_time,
            UserCouponCodeInfo.receive_reverse_time, UserCouponCodeInfo.expired_time,
            CouponInfo.card_type, CouponInfo.title, CouponInfo.subtitle, CouponInfo.scene,
            CouponInfo.notice, CouponInfo.rule, CouponInfo.description, CouponInfo.weekdays,
            CouponInfo.monthdays, CouponInfo.day_begin_time, CouponInfo.day_end_time, CouponInfo.cash_amount,
            CouponInfo.cash_condition, CouponInfo.qty_condition, CouponInfo.discount, CouponInfo.icon, CouponInfo.cover_img).join(
            CouponInfo, on=(UserCouponCodeInfo.card_id == CouponInfo.card_id)
        ).where(UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                UserCouponCodeInfo.card_code == card_code, UserCouponCodeInfo.card_id == card_id)
        result = await mgr.get(query.dicts())
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


@bp.post("/<crm_id>/member/card_interests_record")
@safe_crm_instance
async def card_interests_record(request, crm_id):
    try:
        obj = request.json
        member_no, card_id, card_code = obj.get("member_no"), obj.get("card_id"), obj.get("card_code")
        assert member_no, "member_no 必填"
        assert card_id, "card_id 必填"
        assert card_code, "card_code 必填"
        mgr = request.app.mgr
        query = UserInterestsCostRecord.select(
            UserInterestsCostRecord.store_code,
            UserInterestsCostRecord.redeem_cost_center,
            UserInterestsCostRecord.redeem_channel,
            UserInterestsCostRecord.redeem_amount,
            UserInterestsCostRecord.redeem_time,
            UserInterestsCostRecord.rollback_status,
            UserInterestsCostRecord.rollback_time,
            UserInterestsCostRecord.outer_redeem_id
        ).where(
            UserInterestsCostRecord.crm_id == crm_id,
            UserInterestsCostRecord.member_no == member_no,
            UserInterestsCostRecord.card_code == card_code,
            UserInterestsCostRecord.card_id == card_id,
        )
        result = await mgr.execute(query.dicts())
        return json(dict(code=RC.OK, msg="ok", data={"result": result}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


@bp.post("/<crm_id>/member/redeem")
@safe_crm_instance
async def member_redeem(request, crm_id):
    try:
        obj = request.json
        redeem_channel, outer_redeem_id = obj.get("redeem_channel", "default"), obj.get("outer_redeem_id")
        store_code = obj.get("store_code", None)
        redeem_cost_center = obj.get("redeem_cost_center", None)
        member_no, card_id, card_code = obj.get("member_no"), obj.get("card_id"), obj.get("card_code")
        assert member_no, "member_no 必填"
        assert outer_redeem_id, "outer_redeem_id 必填"
        assert card_id, "card_id 必填"
        assert card_code, "card_code 必填"
        mgr = request.app.mgr
        coupon_meta_data = await get_coupon_meta_data(mgr, request.app.redis, crm_id, card_id)
        store_codes = coupon_meta_data.get("store_codes", None)
        weekdays = coupon_meta_data.get("weekdays", None)
        monthdays = coupon_meta_data.get("monthdays", None)
        day_begin_time = coupon_meta_data.get("day_begin_time")
        day_end_time = coupon_meta_data.get("day_end_time")
        date_time = datetime.now()
        if store_codes and store_code:
            assert store_code in store_codes, f"{store_code} 门店不在适用门店 {store_codes}"
        if weekdays:
            assert date_time.weekday() in weekdays, f"{date_time.weekday()} 不在适用日期内 {weekdays}"
        if monthdays:
            assert date_time.day in monthdays, f"{date_time.day} 不在适用日期内 {monthdays}"
        assert day_begin_time <= date_time.time().strftime("%H:%M:%S") <= day_end_time, "不在可用时段"

        # 额度卡和频次卡控制
        amount = obj.get("amount")
        if amount and amount > 0 and coupon_meta_data.get("interests_type") in InterestsType.get_values():
            # 先判断这个券码的状态是否可用
            _query = UserCouponCodeInfo.select().where(
                UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                UserCouponCodeInfo.card_code == card_code, UserCouponCodeInfo.card_id == card_id,
                UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value)
            result = await mgr.execute(_query)
            if not result:
                logger.info(f"核销失败，优惠券券码状态错误: {crm_id}, {card_id}, {card_code}")
                raise CouponException(code=CouponError.REDEEM_FAILED, msg="核销失败", crm_id=crm_id, card_id=card_id,
                                      card_code=card_code)

            interests_period_type = coupon_meta_data.get("interests_period_type") or 0
            interests_period_value = gen_period_value(interests_period_type)
            # 检查周期限制
            if interests_period_type:
                cost_info_query = UserInterestsCostInfo.select().where(
                    UserInterestsCostInfo.crm_id == crm_id,
                    UserInterestsCostInfo.member_no == member_no,
                    UserInterestsCostInfo.card_code == card_code,
                    UserInterestsCostInfo.card_id == card_id,
                    UserInterestsCostInfo.interests_period_type == interests_period_type,
                    UserInterestsCostInfo.interests_period_value == interests_period_value)
                result = await mgr.execute(cost_info_query.dicts())
                if len(result) == 0:
                    logger.info("未查到周期消耗汇总记录")
                else:
                    user_interests_cost_info = result[0]
                    if user_interests_cost_info.get("redeem_amount") + amount > coupon_meta_data.get("interests_period_amount"):
                        logger.error(f'预检查失败，超过周期内额度限制, {amount}, {user_interests_cost_info}, {coupon_meta_data}')
                        raise CouponException(code=CouponError.REDEEM_FAILED, msg="扣减失败，超过周期内额度限制", crm_id=crm_id,
                                              card_id=card_id, card_code=card_code)

            # 检查总额限制
            if coupon_meta_data.get("interests_amount"):
                _query = UserInterestsCostInfo.select(
                    fn.SUM(UserInterestsCostInfo.redeem_amount).alias("redeem_amount")) \
                    .where(UserInterestsCostInfo.crm_id == crm_id, UserInterestsCostInfo.member_no == member_no,
                           UserInterestsCostInfo.card_code == card_code, UserInterestsCostInfo.card_id == card_id, )
                _result = await mgr.get(_query.dicts())
                total_redeem_amount = _result['redeem_amount'] or 0
                if total_redeem_amount + amount > coupon_meta_data.get("interests_amount"):
                    logger.error(f'预检查失败，超过整体额度限制, {amount}, {_result}, {coupon_meta_data}')
                    raise CouponException(code=CouponError.REDEEM_FAILED, msg="扣减失败，超过整体额度限制", crm_id=crm_id,
                                          card_id=card_id, card_code=card_code)

            async with mgr.atomic():
                query_len, query_status = await mgr.get_or_create(
                    UserInterestsCostRecord,
                    **{"crm_id": crm_id, "card_id": card_id, "member_no": member_no, "card_code": card_code,
                       "redeem_channel": redeem_channel, "outer_redeem_id": outer_redeem_id,
                       "store_code": store_code, "redeem_cost_center": redeem_cost_center, "redeem_info": obj,
                       "redeem_amount": amount})
                if not query_status:
                    raise CouponException(code=CouponError.REDEEM_FAILED, msg="扣减失败", crm_id=crm_id, card_id=card_id,
                                          card_code=card_code)

                # 记录周期消耗
                if interests_period_type and interests_period_value:
                    user_cost_info = {
                        "crm_id": crm_id,
                        "card_id": card_id,
                        "member_no": member_no,
                        "card_code": card_code,
                        "interests_period_type": interests_period_type,
                        "interests_period_value": interests_period_value,
                        "redeem_amount": amount
                    }
                    result = await mgr.execute(UserInterestsCostInfo.insert(user_cost_info).on_conflict(
                        update={"redeem_amount": UserInterestsCostInfo.redeem_amount + amount}))
                    if not result:
                        logger.error("消耗汇总记录更新失败")
                        raise CouponException(code=CouponError.REDEEM_FAILED, msg="扣减失败", crm_id=crm_id, card_id=card_id,
                                              card_code=card_code)
                    query = UserInterestsCostInfo.select().where(
                        UserInterestsCostInfo.crm_id == crm_id,
                        UserInterestsCostInfo.member_no == member_no,
                        UserInterestsCostInfo.card_code == card_code,
                        UserInterestsCostInfo.card_id == card_id,
                        UserInterestsCostInfo.interests_period_type == interests_period_type,
                        UserInterestsCostInfo.interests_period_value == interests_period_value)
                    result = await mgr.execute(query.dicts())
                    if len(result) == 0:
                        logger.error("未查到消耗汇总记录")
                        raise CouponException(code=CouponError.REDEEM_FAILED, msg="扣减失败", crm_id=crm_id, card_id=card_id,
                                              card_code=card_code)
                    user_interests_cost_info = result[0]
                    if user_interests_cost_info.get("redeem_amount") > coupon_meta_data.get("interests_period_amount"):
                        logger.error(f'扣减失败，超过周期内额度限制, {user_interests_cost_info}, {coupon_meta_data}')
                        raise CouponException(code=CouponError.REDEEM_FAILED, msg="扣减失败，超过周期内额度限制", crm_id=crm_id,
                                              card_id=card_id, card_code=card_code)

                if coupon_meta_data.get("interests_amount"):
                    _query = UserInterestsCostInfo.select(
                        fn.SUM(UserInterestsCostInfo.redeem_amount).alias("redeem_amount")) \
                        .where(UserInterestsCostInfo.crm_id == crm_id, UserInterestsCostInfo.member_no == member_no,
                               UserInterestsCostInfo.card_code == card_code, UserInterestsCostInfo.card_id == card_id, )
                    _result = await mgr.get(_query.dicts())
                    total_redeem_amount = _result['redeem_amount'] or 0
                    if total_redeem_amount > coupon_meta_data.get("interests_amount"):
                        logger.error(f'扣减失败，超过整体额度限制, {_result}, {coupon_meta_data}')
                        raise CouponException(code=CouponError.REDEEM_FAILED, msg="扣减失败，超过整体额度限制", crm_id=crm_id,
                                              card_id=card_id, card_code=card_code)

        else:
            async with mgr.atomic():
                query_len, query_status = await mgr.get_or_create(
                    UserCouponRedeemInfo,
                    **{"crm_id": crm_id, "card_id": card_id, "member_no": member_no, "card_code": card_code,
                       "redeem_channel": redeem_channel, "outer_redeem_id": outer_redeem_id,
                       "store_code": store_code, "redeem_cost_center": redeem_cost_center, "redeem_info": obj})
                if not query_status:
                    raise CouponException(code=CouponError.REDEEM_FAILED, msg="核销失败", crm_id=crm_id, card_id=card_id,
                                          card_code=card_code)

                query = UserCouponCodeInfo.update({UserCouponCodeInfo.code_status: UserCardCodeStatus.REDEEM.value}).where(
                    UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                    UserCouponCodeInfo.card_code == card_code, UserCouponCodeInfo.card_id == card_id,
                    UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value)
                result = await mgr.execute(query)
                if not result:
                    raise CouponException(code=CouponError.REDEEM_FAILED, msg="核销失败", crm_id=crm_id, card_id=card_id,
                                          card_code=card_code)
        return json(dict(code=RC.OK, msg="ok", data={}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


@bp.post("/<crm_id>/member/redeem_reverse")
@safe_crm_instance
async def member_redeem_reverse(request, crm_id):
    try:
        obj = request.json
        outer_redeem_id = obj.get("outer_redeem_id")
        member_no = obj.get("member_no")
        assert outer_redeem_id, "outer_redeem_id 必填"
        assert member_no, "member_no 必填"
        mgr = request.app.mgr

        card_id = obj.get("card_id")
        assert card_id, "card_id 必填"

        async def reverse_card_code():
            query = UserCouponRedeemInfo.select().where(
                UserCouponRedeemInfo.crm_id == crm_id, UserCouponRedeemInfo.outer_redeem_id == outer_redeem_id,
                UserCouponRedeemInfo.member_no == member_no, UserCouponRedeemInfo.rollback_status == 0)
            result = await mgr.execute(query.dicts())
            if len(result) == 0:
                raise CouponException(code=CouponError.REDEEM_FAILED, msg="未查询到对应的核销记录", crm_id=crm_id, card_id='',
                                      card_code='')
            update_query = UserCouponRedeemInfo.update(
                {UserCouponRedeemInfo.rollback_status: 1, UserCouponRedeemInfo.rollback_time: datetime.now()}).where(
                UserCouponRedeemInfo.crm_id == crm_id, UserCouponRedeemInfo.outer_redeem_id == outer_redeem_id,
                UserCouponRedeemInfo.member_no == member_no, UserCouponRedeemInfo.rollback_status == 0)
            async with mgr.atomic():
                update_result = await mgr.execute(update_query)
                if not update_result:
                    raise CouponException(code=CouponError.REDEEM_FAILED, msg="核销回滚失败", crm_id=crm_id, card_id='',
                                          card_code='')
                result = result[0]
                # "code_status": UserCardCodeStatus.AVAILABLE.value,
                update_user_card_code = UserCouponCodeInfo.update({
                    UserCouponCodeInfo.code_status: UserCardCodeStatus.AVAILABLE.value,
                    UserCouponCodeInfo.redeem_time: None}).where(
                    UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                    UserCouponCodeInfo.card_id == result.get("card_id"),
                    UserCouponCodeInfo.card_code == result.get("card_code"),
                    UserCouponCodeInfo.code_status == UserCardCodeStatus.REDEEM.value)
                await mgr.execute(update_user_card_code)
                logger.debug(f"{update_user_card_code.sql()}")
            return json(dict(code=RC.OK, msg="ok", data={}))

        coupon_meta_data = await get_coupon_meta_data(mgr, request.app.redis, crm_id, card_id)

        if coupon_meta_data.get("interests_type"):
            # 先查询额度消耗记录
            query = UserInterestsCostRecord.select().where(
                UserInterestsCostRecord.crm_id == crm_id, UserInterestsCostRecord.outer_redeem_id == outer_redeem_id,
                UserInterestsCostRecord.member_no == member_no, UserInterestsCostRecord.rollback_status == 0)
            result = await mgr.execute(query.dicts())
            # 如果额度消耗记录没有，就查询卡券领券记录
            if len(result) == 0:
                res = await reverse_card_code()
                return res
            else:
                # 冲正额度消耗
                update_query = UserInterestsCostRecord.update(
                    {UserInterestsCostRecord.rollback_status: 1,
                     UserInterestsCostRecord.rollback_time: datetime.now()}).where(
                    UserInterestsCostRecord.crm_id == crm_id, UserInterestsCostRecord.outer_redeem_id == outer_redeem_id,
                    UserInterestsCostRecord.member_no == member_no, UserInterestsCostRecord.rollback_status == 0)
                async with mgr.atomic():
                    update_result = await mgr.execute(update_query)
                    if not update_result:
                        raise CouponException(code=CouponError.REDEEM_FAILED, msg="消耗记录回滚失败", crm_id=crm_id, card_id='',
                                              card_code='')

                    cost_record = await mgr.get(UserInterestsCostRecord.select().where(
                        UserInterestsCostRecord.crm_id == crm_id,
                        UserInterestsCostRecord.outer_redeem_id == outer_redeem_id,
                        UserInterestsCostRecord.member_no == member_no
                    ))

                    create_time = cost_record.create_time

                    result = result[0]
                    # 回滚额度或者频次汇总表
                    interests_period_type = coupon_meta_data.get("interests_period_type") or 0
                    interests_period_value = gen_period_value(interests_period_type, create_time)
                    amount = result.get("redeem_amount")
                    update_user_interests_cost_info = UserInterestsCostInfo.update({
                        UserInterestsCostInfo.redeem_amount: UserInterestsCostInfo.redeem_amount - amount}).where(
                        UserInterestsCostInfo.crm_id == crm_id,
                        UserInterestsCostInfo.member_no == member_no,
                        UserInterestsCostInfo.card_id == result.get("card_id"),
                        UserInterestsCostInfo.card_code == result.get("card_code"),
                        UserInterestsCostInfo.interests_period_type == interests_period_type,
                        UserInterestsCostInfo.interests_period_value == interests_period_value)
                    await mgr.execute(update_user_interests_cost_info)
                    logger.debug(f"{update_user_interests_cost_info.sql()}")
                return json(dict(code=RC.OK, msg="ok", data={}))
        else:
            res = await reverse_card_code()
            return res
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))


@bp.get("/<crm_id>/member/available_card_list")
@safe_crm_instance
async def member_card_list(request, crm_id):
    try:
        obj = request.args
        member_no = obj.get("member_no")
        assert member_no, "member_no 必填"
        page = int(obj.get("page", 1))
        page_size = int(obj.get("page_size", 5))
        now = datetime.now()
        now_time = now.time()
        where = [UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == member_no,
                 UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value,
                 UserCouponCodeInfo.start_time <= now, UserCouponCodeInfo.end_time >= now,
                 CouponInfo.day_begin_time <= now_time, CouponInfo.day_end_time >= now_time]
        biz_type = obj.get("biz_type", None)
        if biz_type:
            where.append(CouponInfo.biz_type == biz_type)
        interests_type = obj.get("interests_type", None)
        if interests_type:
            where.append(CouponInfo.biz_type == interests_type)
        mgr = request.app.mgr
        query = UserCouponCodeInfo.select(
            UserCouponCodeInfo.card_id, UserCouponCodeInfo.member_no, UserCouponCodeInfo.receive_id,
            UserCouponCodeInfo.card_code, UserCouponCodeInfo.start_time, UserCouponCodeInfo.end_time,
            UserCouponCodeInfo.code_status, UserCouponCodeInfo.outer_str, UserCouponCodeInfo.received_time,
            UserCouponCodeInfo.redeem_time, UserCouponCodeInfo.present_time, UserCouponCodeInfo.obsoleted_time,
            UserCouponCodeInfo.receive_reverse_time, UserCouponCodeInfo.expired_time,
            CouponInfo.card_type, CouponInfo.title, CouponInfo.subtitle, CouponInfo.scene,
            CouponInfo.notice, CouponInfo.rule, CouponInfo.description, CouponInfo.weekdays,
            CouponInfo.monthdays, CouponInfo.day_begin_time, CouponInfo.day_end_time, CouponInfo.cash_amount,
            CouponInfo.cash_condition, CouponInfo.qty_condition, CouponInfo.discount, CouponInfo.icon,
            CouponInfo.cover_img, CouponInfo.interests_type, CouponInfo.interests_amount,
            CouponInfo.interests_period_type, CouponInfo.interests_period_amount).join(
            CouponInfo, on=(UserCouponCodeInfo.card_id == CouponInfo.card_id)
        ).where(*where)
        logger.info(f"{query.sql()}")
        result = await mgr.execute(query.paginate(page, page_size).dicts())
        # 加入额度和频次相关字段
        result = await card_list_plug(mgr, result, member_no, crm_id)
        count = await mgr.count(query)
        return json(dict(code=RC.OK, msg="ok", data={"coupon_list": result, "count": count}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except CouponException as ex:
        return json(dict(code=ex.code, msg=f"card_id {ex.card_id} {ex.msg}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.HANDLER_ERROR, msg=f"参数错误：{ex}"))
