#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/27
"""
import asyncio

from biz.coupon import verify_create_card_param, get_crm_coupon_stock, verify_update_card_param, \
    translate_coupon_channel
from biz.points_coupon import get_mall_points_card_list, get_mall_points_card_ids
from biz.utils import get_by_list_or_comma
from common.biz.const import RC
from common.biz.coupon import get_coupon_meta_data, remove_coupon_meta_data, coupon_redeem_search, user_coupon_search
from biz.member import get_members_by_member_nos
from common.biz.coupon_const import CardSource, CouponCodeGenStatus, UserCardCodeStatus
from common.biz.utils import result_by_hour, result_by_day, make_time_range
from common.biz.wrapper import safe_crm_instance
from common.models.coupon import CouponInfo, CouponCodeGenInfo, UserCouponCodeInfo, UserCouponRedeemInfo, \
    UserPresentCouponInfo, StatisticalCoupon, UserInterestsCostRecord, StatisticalCoupon, \
    UserInterestsCostInfo, UserInterestsCostInfo
from mtkext.dt import dateFromString, timestampFromString
from peewee import fn
from sanic import Blueprint
from sanic.log import logger
from sanic.response import json
from mtkext.guid import fast_guid
from sanic.kjson import json_loads, json_dumps
from peewee import fn
from mtkext.ass import assert_

bp = Blueprint("bp_card", url_prefix="/card")


@bp.post("/<crm_id>/create")
@safe_crm_instance
async def create_coupon(request, crm_id):
    """创建卡券，同步商家券 卡券元信息管理 初始化生成券码导入"""
    try:
        card_meta_data = verify_create_card_param(request.json)
        card_meta_data["crm_id"] = crm_id
        mgr = request.app.mgr
        code_gen = None
        if card_meta_data["source"] == CardSource.CRM.value:
            # 生成card_id
            card_meta_data["card_id"] = fast_guid().upper()
            # 生成券码导入任务
            code_gen = {
                "crm_id": crm_id, "card_id": card_meta_data["card_id"],
                "gen_status": CouponCodeGenStatus.PENDING.value, "quantity": card_meta_data["total_quantity"]}
            # 初始化 库存为0
            card_meta_data["total_quantity"] = 0
        async with mgr.atomic():
            coupon_id = await mgr.execute(CouponInfo.insert(**card_meta_data))
            if code_gen:
                await mgr.execute(CouponCodeGenInfo.insert(**code_gen))
        return json(dict(code=RC.OK, msg="ok", data={"card_id": card_meta_data["card_id"], "coupon_id": coupon_id}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/list")
@safe_crm_instance
async def coupon_list(request, crm_id):
    """
    分页获取卡券列表
    """
    try:
        request_data = request.args
        page = int(request_data.get("page", 1))
        page_size = int(request_data.get("page_size", 10))
        search_key = request_data.get("keyword", None)
        biz_type = request_data.get("biz_type", None)
        source = request_data.get("source")
        assert int(source) in [CardSource.CRM.value, CardSource.WX_PAY.value], "卡券类型必选"
        where = [CouponInfo.crm_id == crm_id, CouponInfo.removed == 0, CouponInfo.source == source]
        if search_key:
            where.append(
                CouponInfo.title.contains(search_key) | CouponInfo.card_id.contains(
                    search_key) | CouponInfo.subtitle.contains(
                    search_key))
        if biz_type:
            where.append(CouponInfo.biz_type == biz_type)
        mgr, redis = request.app.mgr, request.app.redis
        query = CouponInfo.select().order_by(CouponInfo.create_time.desc()).where(*where)
        logger.info(f"{query.sql()}")
        coupons = await mgr.execute(query.paginate(page, page_size).dicts())
        count = await mgr.count(query)
        tasks = []
        if int(source) == CardSource.CRM.value:
            for i in coupons:
                card_id = i.get("card_id")
                card_key = request.app.conf.CRM_COUPON_CODE_QUEUE_FORMAT.format(crm_id=crm_id, card_id=card_id)
                tasks.append(get_crm_coupon_stock(mgr, redis, crm_id, card_id, card_key))
            results = await asyncio.gather(*tasks)
            lists = zip(coupons, results)
            coupons = []
            logger.info(f'{lists}')
            for i in lists:
                i[0].update(i[1])
                coupons.append(i[0])
        return json(dict(code=RC.OK, msg="ok", data={"coupon_list": coupons, "count": count}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/detail")
@safe_crm_instance
async def get_coupon_detail(request, crm_id):
    """
    获取卡券详情
    """
    try:
        request_data = request.args
        card_id = request_data.get("card_id")
        mgr, redis = request.app.mgr, request.app.redis
        coupons = await get_coupon_meta_data(mgr, redis, crm_id, card_id)
        card_key = request.app.conf.CRM_COUPON_CODE_QUEUE_FORMAT.format(crm_id=crm_id, card_id=card_id)
        if coupons.get("source") == CardSource.CRM.value:
            result = await get_crm_coupon_stock(mgr, redis, crm_id, card_id, card_key)
            coupons.update(result)
        return json(dict(code=RC.OK, msg="ok", data={"coupon": coupons}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    pass


@bp.post("/<crm_id>/update")
async def update_coupon(request, crm_id):
    """
    修改部分字段（）
    """
    try:
        card_update_mata_info = verify_update_card_param(request.json)
        card_id = card_update_mata_info["card_id"]
        await request.app.mgr.execute(
            CouponInfo.update(card_update_mata_info).where(CouponInfo.crm_id == crm_id, CouponInfo.card_id == card_id))
        # 清除缓存
        await remove_coupon_meta_data(request.app.redis, crm_id, card_id)
        return json(dict(code=RC.OK, msg="ok", data={}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/receive_update")
async def update_receive_coupon(request, crm_id):
    """
    修改字段（start_time, end_time）
    """
    try:
        db = request.app.mgr
        params = request.json
        card_id = params.get("card_id")
        card_codes = params.get("card_codes")
        time_type = params.get("time_type")
        start_time = params.get("start_time")
        end_time = params.get("end_time")
        time_delta = params.get("time_delta")
        if not all([card_id, card_codes, time_type]):
            raise AssertionError("参数错误")
        todo_ids, plus_ids = [], []
        items = await db.execute(UserCouponCodeInfo.select().where(
            UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.card_id == card_id,
            UserCouponCodeInfo.card_code.in_(card_codes)
        ).dicts())
        for item in items:
            member_coupon_id = item.get("member_coupon_id")
            code_status = int(item.get("code_status"))
            if code_status in [3, 6, 7]:
                logger.info(f"卡券{item.get('code')}状态不能用于修改有效期")
                continue
            if code_status == 4:
                plus_ids.append(member_coupon_id)
            else:
                todo_ids.append(member_coupon_id)
        if not any([todo_ids, plus_ids]):
            raise AssertionError("参数错误, 没有卡券适用于修改有效期")
        if time_type == 1:
            assert end_time, "参数错误"
            up_obj = dict(end_time=end_time)
            if start_time:
                up_obj.update(start_time=start_time)
            if todo_ids:
                await db.execute(
                    UserCouponCodeInfo.update(**up_obj).where(UserCouponCodeInfo.member_coupon_id.in_(todo_ids))
                )
            if plus_ids:
                up_obj.update(code_status=1)
                await db.execute(
                    UserCouponCodeInfo.update(**up_obj).where(UserCouponCodeInfo.member_coupon_id.in_(plus_ids))
                )
        elif time_type == 2:
            assert time_delta, "参数错误"
            sql_1 = """
            update t_crm_coupon_user_info 
            set end_time = DATE_ADD(end_time, INTERVAL %s DAY)
            where member_coupon_id in %s
            """
            sql_2 = """
            update t_crm_coupon_user_info 
            set end_time = DATE_ADD(end_time, INTERVAL %s DAY), code_status = 1
            where member_coupon_id in %s
            """
            if todo_ids:
                await db.execute(UserCouponCodeInfo.raw(sql_1, time_delta, todo_ids))
            if plus_ids:
                await db.execute(UserCouponCodeInfo.raw(sql_2, time_delta, plus_ids))
        return json(dict(code=RC.OK, msg="ok", data={}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/add_stock")
@safe_crm_instance
async def add_stock(request, crm_id):
    """新增库存"""
    try:
        request_data = request.json
        card_id = request_data.get("card_id")
        quantity = int(request_data.get("quantity"))
        source = request_data.get("source")
        assert card_id, 'card_id不能为空'
        assert type(quantity) is int and quantity > 0, 'quantity >0'
        assert source in [CardSource.CRM.value, CardSource.WX_PAY.value], "source 【1,2】"
        if int(source) == CardSource.CRM.value:
            code_gen = {
                "crm_id": crm_id, "card_id": card_id,
                "gen_status": CouponCodeGenStatus.PENDING.value, "quantity": quantity}
            result = await request.app.mgr.execute(CouponCodeGenInfo.insert(**code_gen))
            return json(dict(code=RC.OK, msg="ok", data={"card_id": card_id, "gen_record": result}))
        if int(source) == CardSource.WX_PAY.value:
            result = await request.app.mgr.execute(CouponInfo.update({CouponInfo.total_quantity: quantity}).where(
                CouponInfo.card_id == card_id, CouponInfo.crm_id == crm_id))
            return json(dict(code=RC.OK, msg="ok", data={"card_id": card_id, "gen_record": result}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    pass


@bp.post("/<crm_id>/del")
@safe_crm_instance
async def delete(request, crm_id):
    """删除卡券"""
    try:
        request_data = request.json
        card_id = request_data.get("card_id")
        query = CouponInfo.update({CouponInfo.removed: 1}).where(CouponInfo.crm_id == crm_id,
                                                                 CouponInfo.card_id == card_id)
        await request.app.mgr.execute(query)
        return json(dict(code=RC.OK, msg="ok", data={}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    pass


@bp.post("/<crm_id>/get_stock")
@safe_crm_instance
async def get_stock(request, crm_id):
    """获取卡券库存"""
    try:
        request_data = request.json
        card_id = request_data.get("card_id")
        assert card_id, "card_id 必填"
        mgr, redis = request.app.mgr, request.app.redis
        card_key = request.app.conf.CRM_COUPON_CODE_QUEUE_FORMAT.format(crm_id=crm_id, card_id=card_id)
        result = await get_crm_coupon_stock(mgr, redis, crm_id, card_id, card_key)
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/get_member_coupon_list")
@safe_crm_instance
async def get_member_coupon_list(request, crm_id):
    """
    分页获取卡券列表
    """
    try:
        request_data = request.args

        page = int(request_data.get("page", 1))
        page_size = int(request_data.get("page_size", 10))
        member_no = request_data.get("member_no", None)
        code_status = request_data.getlist("code_status", None)
        where = [UserCouponCodeInfo.crm_id == crm_id]
        if member_no:
            where.append(UserCouponCodeInfo.member_no == member_no)
        if code_status:
            if len(code_status) > 1:
                where.append(UserCouponCodeInfo.code_status.in_(code_status))
            else:
                where.append(UserCouponCodeInfo.code_status == code_status)
        start_date = request_data.get("start_date", None)
        end_date = request_data.get("end_date", None)
        logger.info(f"{start_date} -> {end_date}")
        record_time_field = UserCouponCodeInfo.update_time
        if start_date and end_date:
            _code_status = code_status if type(code_status) == list else [code_status]
            logger.info(f"_code_status: {_code_status}")
            if '1' in code_status:  # 领取
                where.append(UserCouponCodeInfo.received_time >= start_date)
                where.append(UserCouponCodeInfo.received_time <= end_date)
                record_time_field = UserCouponCodeInfo.received_time
            elif '2' in code_status or '5' in code_status:
                where.append(UserCouponCodeInfo.present_time >= start_date)
                where.append(UserCouponCodeInfo.present_time <= end_date)
                record_time_field = UserCouponCodeInfo.present_time
            elif '3' in code_status:
                where.append(UserCouponCodeInfo.redeem_time >= start_date)
                where.append(UserCouponCodeInfo.redeem_time <= end_date)
                record_time_field = UserCouponCodeInfo.redeem_time
            elif '4' in code_status:
                where.append(UserCouponCodeInfo.expired_time >= start_date)
                where.append(UserCouponCodeInfo.expired_time <= end_date)
                record_time_field = UserCouponCodeInfo.expired_time
            elif '6' in code_status or '7' in code_status:
                where.append(UserCouponCodeInfo.obsoleted_time >= start_date)
                where.append(UserCouponCodeInfo.obsoleted_time <= end_date)
                record_time_field = UserCouponCodeInfo.obsoleted_time

        query = UserCouponCodeInfo.select(UserCouponCodeInfo, record_time_field.alias("record_time"), CouponInfo.title,
                                          CouponInfo.card_type).join(CouponInfo, on=(
                UserCouponCodeInfo.card_id == CouponInfo.card_id)).order_by(
            UserCouponCodeInfo.update_time.desc()).where(*where)
        logger.info(f"{query.sql()}")
        coupons = await request.app.mgr.execute(query.paginate(page, page_size).dicts())
        count = await request.app.mgr.count(query)
        return json(dict(code=RC.OK, msg="ok", data={"coupon_list": coupons, "count": count}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/coupon_search")
@safe_crm_instance
async def coupon_search(request, crm_id):
    try:
        member_no = request.args.get("member_no", None)
        cost_center = request.args.get("cost_center", None)
        begin_time = request.args.get("begin_time", None)
        end_time = request.args.get("end_time", None)
        mtype = request.args.get("mtype")
        assert_(mtype in ["receive", "present", "expired", "invalid"], "不合法的mtype参数")
        check_code_status = request.args.get("check_code_status", 0)
        assert_((begin_time is None and end_time is None) or (begin_time is not None and end_time is not None),
                "begin_time 和end_time 需同时有值，或者同时没有值")
        if begin_time and end_time:
            begin_time = dateFromString(begin_time)
            end_time = dateFromString(end_time)
            begin_time, end_time = make_time_range(begin_time, end_time)
        order_asc = int(request.args.get("order_asc", 0))
        page = int(request.args.get("page", 1))
        assert_(page > 0, "page从1开始")
        page_size = int(request.args.get("page_size", 20))
        assert_(1 < page_size <= 100000, "page_size不能小于2或超过100000")
        status, total, items = await user_coupon_search(
            request.app.mgr, crm_id, member_no, page, page_size, mtype, cost_center=cost_center,
            begin_time=begin_time, end_time=end_time, order_asc=order_asc, check_code_status=check_code_status)
        assert_(status, items)
        if not total:
            got = dict(crm_id=crm_id, total=0, record_list=[])
            return json(dict(code=RC.OK, msg="搜索不到记录", data=got))

        member_nos = [x.get("member_no") for x in items]
        members = await get_members_by_member_nos(request.app.mgr, crm_id, member_nos=member_nos)
        members_dict = {}
        for x in members:
            members_dict[x.member_no] = x.nickname
        for x in items:
            x["nickname"] = members_dict.get(x.get("member_no", ""), "")
        got = dict(crm_id=crm_id, total=total, record_list=items)
        return json(dict(code=RC.OK, msg="ok", data=got))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))


@bp.get("/<crm_id>/redeem_search")
@safe_crm_instance
async def redeem_search(request, crm_id):
    try:
        member_no = request.args.get("member_no", None)
        store_code = request.args.get("store_code", None)
        redeem_cost_center = request.args.get("cost_center", None)
        begin_time = request.args.get("begin_time", None)
        end_time = request.args.get("end_time", None)
        assert_((begin_time is None and end_time is None) or (begin_time is not None and end_time is not None),
                "begin_time 和end_time 需同时有值，或者同时没有值")
        if begin_time and end_time:
            begin_time = dateFromString(begin_time)
            end_time = dateFromString(end_time)
            begin_time, end_time = make_time_range(begin_time, end_time)

        page = int(request.args.get("page", 1))
        assert_(page > 0, "page从1开始")
        page_size = int(request.args.get("page_size", 20))
        assert_(1 < page_size <= 100000, "page_size不能小于2或超过100000")
        rollback_status = int(request.args.get("rollback_status", 0))
        interests_type = int(request.args.get("interests_type", 0))
        order_asc = int(request.args.get("order_asc", 0))

        cls = UserCouponRedeemInfo
        if interests_type:
            cls = UserInterestsCostRecord
        total, items = await coupon_redeem_search(
            request.app.mgr, crm_id, member_no, page, page_size, store_code=store_code,
            redeem_cost_center=redeem_cost_center,
            begin_time=begin_time, end_time=end_time, rollback_status=rollback_status, order_asc=order_asc, cls=cls)
        if not total:
            got = dict(crm_id=crm_id, total=0, record_list=[])
            return json(dict(code=RC.OK, msg="搜索不到核销记录", data=got))
        got = dict(crm_id=crm_id, total=total, record_list=items)
        return json(dict(code=RC.OK, msg="ok", data=got))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))


@bp.post("/<crm_id>/batch_query")
@safe_crm_instance
async def batch_query(request, crm_id):
    try:
        request_data = request.json
        member_coupon_id_list = request_data.get("member_coupon_id_list")
        assert isinstance(member_coupon_id_list, list) and len(member_coupon_id_list), "member_coupon_id_list 必填"
        mgr, redis = request.app.mgr, request.app.redis
        query = UserCouponCodeInfo.select(UserCouponCodeInfo, CouponInfo.title).join(CouponInfo, on=(
                UserCouponCodeInfo.card_id == CouponInfo.card_id)).where(
            UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_coupon_id.in_(member_coupon_id_list))
        result_list = await mgr.execute(query.dicts())
        return json(dict(code=RC.OK, msg="ok", data=result_list))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 领取统计
@bp.get("/<crm_id>/statistical_receive")
@safe_crm_instance
async def statistical_receive(request, crm_id):
    try:
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        end_time = dateFromString(request_data.get("end_time"))
        card_id = request_data.get("card_id", None)
        begin_time, end_time = make_time_range(begin_time, end_time)
        query = UserCouponCodeInfo.select(UserCouponCodeInfo.outer_str, fn.count(1).alias("count")).group_by(
            UserCouponCodeInfo.outer_str).where(
            UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.received_time >= begin_time,
            UserCouponCodeInfo.card_id == card_id if card_id else 1 == 1,
            UserCouponCodeInfo.received_time <= end_time)
        result = await request.app.mgr.execute(query.dicts())
        # 渠道转换为中文
        app = request.app
        for item in result:
            outer_str = item.get("outer_str")
            new_str = await translate_coupon_channel(app, crm_id, in_str=outer_str)
            if new_str:
                item["outer_str"] = new_str
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 核销统计
@bp.get("/<crm_id>/statistical_redeem")
@safe_crm_instance
async def statistical_redeem(request, crm_id):
    try:
        request_data = request.args
        card_id = request_data.get("card_id", None)
        begin_time = dateFromString(request_data.get("begin_time"))
        end_time = dateFromString(request_data.get("end_time"))
        begin_time, end_time = make_time_range(begin_time, end_time)
        query = UserCouponRedeemInfo.select(UserCouponRedeemInfo.redeem_channel, fn.count(1).alias("count")).group_by(
            UserCouponRedeemInfo.redeem_channel).where(
            UserCouponRedeemInfo.crm_id == crm_id, UserCouponRedeemInfo.redeem_time >= begin_time,
            UserCouponRedeemInfo.card_id == card_id if card_id else 1 == 1,
            UserCouponRedeemInfo.redeem_time <= end_time)
        result = await request.app.mgr.execute(query.dicts())
        # 渠道转换为中文
        app = request.app
        for item in result:
            outer_str = item.get("redeem_channel")
            new_str = await translate_coupon_channel(app, crm_id, in_str=outer_str)
            if new_str:
                item["redeem_channel"] = new_str
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 统计查询
@bp.get("/<crm_id>/statistical_top")
@safe_crm_instance
async def statistical_top(request, crm_id):
    try:
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        end_time = dateFromString(request_data.get("end_time"))
        begin_time, end_time = make_time_range(begin_time, end_time)
        event_type = request_data.get("event_type")
        card_id = request_data.get("card_id", None)
        top = int(request_data.get("top", 10))
        assert event_type in ["receive", "redeem"], "event_type 仅支持 receive, redeem"
        if event_type == 'receive':
            query = UserCouponCodeInfo.select(
                fn.count(UserCouponCodeInfo.card_code).alias("count"), UserCouponCodeInfo.card_id, CouponInfo.title,
                CouponInfo.subtitle).join(
                CouponInfo, on=(UserCouponCodeInfo.card_id == CouponInfo.card_id)).group_by(
                UserCouponCodeInfo.card_id).order_by(
                fn.count(UserCouponCodeInfo.card_code).alias("count").desc()).where(
                UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.received_time >= begin_time,
                UserCouponCodeInfo.received_time <= end_time,
                UserCouponCodeInfo.card_id == card_id if card_id else 1 == 1
            )
        else:
            query = UserCouponRedeemInfo.select(
                fn.count(UserCouponRedeemInfo.card_code).alias("count"), UserCouponRedeemInfo.card_id, CouponInfo.title,
                CouponInfo.subtitle).join(
                CouponInfo, on=(UserCouponRedeemInfo.card_id == CouponInfo.card_id)).group_by(
                UserCouponRedeemInfo.card_id).order_by(
                fn.count(UserCouponRedeemInfo.card_code).alias("count").desc()).where(
                UserCouponRedeemInfo.crm_id == crm_id, UserCouponRedeemInfo.redeem_time >= begin_time,
                UserCouponRedeemInfo.redeem_time <= end_time,
                UserCouponRedeemInfo.card_id == card_id if card_id else 1 == 1,
                UserCouponRedeemInfo.rollback_status == 0)
        logger.info(f"{query.sql()}")
        result = await request.app.mgr.execute(query.paginate(1, top).dicts())
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 统计总量查询
@bp.get("/<crm_id>/statistical_total")
@safe_crm_instance
async def statistical_total(request, crm_id):
    try:
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        card_id = request_data.get("card_id", None)
        end_time = dateFromString(request_data.get("end_time"))
        mgr = request.app.mgr
        redis = request.app.redis
        begin_time, end_time = make_time_range(begin_time, end_time)
        total_key = f"total_key_{begin_time}_{end_time}_{crm_id}_{card_id if card_id else 'all'}"
        got = await redis.get(total_key)
        if got:
            return json(dict(code=RC.OK, msg="ok", data=json_loads(got)))
        receive_query = UserCouponCodeInfo.select(
            fn.count(1).alias("total_receive_count"),
            fn.count(UserCouponCodeInfo.member_no.distinct()).alias("total_receive_user")).where(
            UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.received_time >= begin_time,
            UserCouponCodeInfo.received_time <= end_time, UserCouponCodeInfo.card_id == card_id if card_id else 1 == 1)
        logger.info(f"{receive_query.sql()}")
        receive_result = await mgr.get(receive_query.dicts())
        total_receive_count = receive_result.get("total_receive_count", 0)
        total_receive_user = receive_result.get("total_receive_user", 0)
        redeem_query = UserCouponRedeemInfo.select(
            fn.count(1).alias("total_redeem_count"),
            fn.count(UserCouponRedeemInfo.member_no.distinct()).alias("total_redeem_user")).where(
            UserCouponRedeemInfo.redeem_time >= begin_time, UserCouponRedeemInfo.redeem_time <= end_time,
            UserCouponRedeemInfo.card_id == card_id if card_id else 1 == 1, UserCouponRedeemInfo.crm_id == crm_id,
            UserCouponRedeemInfo.rollback_status == 0
        )
        redeem_result = await mgr.get(redeem_query.dicts())
        total_redeem_count = redeem_result.get("total_redeem_count", 0)
        total_redeem_user = redeem_result.get("total_redeem_user", 0)
        present_query = UserPresentCouponInfo.select(
            fn.count(1).alias("total_present_count"),
            fn.count(UserPresentCouponInfo.from_member_no.distinct()).alias("total_present_user")
        ).where(
            UserPresentCouponInfo.present_time >= begin_time, UserPresentCouponInfo.present_time <= end_time,
            UserPresentCouponInfo.card_id == card_id if card_id else 1 == 1, UserPresentCouponInfo.crm_id == crm_id
        )
        present_result = await mgr.get(present_query.dicts())
        total_present_count = present_result.get("total_present_count", 0)
        total_present_user = present_result.get("total_present_user", 0)
        result = {"total_receive_user": total_receive_user, "total_receive_count": total_receive_count,
                  "total_redeem_user": total_redeem_user, "total_redeem_count": total_redeem_count,
                  "total_present_user": total_present_user, "total_present_count": total_present_count}
        await redis.setex(total_key, 60 * 3, json_dumps(result))
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 统计时间查询 todo 返回时间点
@bp.get("/<crm_id>/statistical_type")
@safe_crm_instance
async def statistical(request, crm_id):
    try:
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        end_time = dateFromString(request_data.get("end_time"))
        card_id = request_data.get("card_id", None)
        assert begin_time <= end_time, "开始时间必须小于 结束时间"
        key_list = ["receive_cards", "receive_cards_user", "redeem_cards", "redeem_cards_user", "present_cards",
                    "present_cards_user"]
        if (end_time - begin_time).days < 2:
            items = await request.app.mgr.execute(StatisticalCoupon.select().where(
                StatisticalCoupon.crm_id == crm_id, StatisticalCoupon.tdate.between(begin_time, end_time),
                StatisticalCoupon.thour.between(0, 23), StatisticalCoupon.card_id == card_id if card_id else 1 == 1))
            result = result_by_hour(items, begin_time, end_time, key_list)
        else:
            items = await request.app.mgr.execute(StatisticalCoupon.select().where(
                StatisticalCoupon.crm_id == crm_id, StatisticalCoupon.tdate.between(begin_time, end_time),
                StatisticalCoupon.thour == 99, StatisticalCoupon.card_id == card_id if card_id else 1 == 1))
            result = result_by_day(items, begin_time, end_time, key_list)
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 拉去卡券数据接口
@bp.get("/<crm_id>/member/coupon_list")
async def coupon_list(request, crm_id):
    """获取卡券库存"""
    try:
        request_data = request.args
        coupon_code_list, count = await query_model_update_time(
            request.app.mgr, UserCouponCodeInfo, crm_id, request_data,
            UserCouponCodeInfo.member_coupon_id
        )
        result = {"coupon_code_list": coupon_code_list, "count": count}
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    pass


# 拉去核销数据接口
@bp.get("/<crm_id>/member/coupon_redeem_list")
async def coupon_redeem_list(request, crm_id):
    try:
        request_data = request.args
        redeem_list, count = await query_model_update_time(
            request.app.mgr, UserCouponRedeemInfo, crm_id, request_data,
            UserCouponRedeemInfo.redeem_coupon_id
        )
        result = {"redeem_list": redeem_list, "count": count}
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    pass


# 拉去卡券额度数据接口
@bp.get("/<crm_id>/member/coupon_interests_cost_info_list")
async def coupon_interests_cost_info_list(request, crm_id):
    """获取卡券库存"""
    try:
        request_data = request.args
        _list, count = await query_model_update_time(
            request.app.mgr, UserInterestsCostInfo, crm_id, request_data,
            UserInterestsCostInfo.redeem_coupon_id
        )
        result = {"data": _list, "count": count}
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 拉去卡券额度数据接口
@bp.get("/<crm_id>/member/coupon_interests_cost_record_list")
async def coupon_interests_cost_record_list(request, crm_id):
    try:
        request_data = request.args
        _list, count = await query_model_update_time(
            request.app.mgr, UserInterestsCostRecord, crm_id, request_data,
            UserInterestsCostRecord.redeem_coupon_id
        )
        result = {"data": _list, "count": count}
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 拉去转赠数据接口
@bp.get("/<crm_id>/member/coupon_present_list")
async def coupon_present_list(request, crm_id):
    try:
        request_data = request.args
        present_list, count = await query_model_update_time(
            request.app.mgr, UserPresentCouponInfo, crm_id, request_data,
            UserPresentCouponInfo.present_id
        )
        result = {"coupon_present_list": present_list, "count": count}
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    pass


# 拉去卡券元数据接口
@bp.get("/<crm_id>/coupon/list")
async def get_coupons_list(request, crm_id):
    try:
        request_data = request.args
        coupons_list, count = await query_model_create_time(request.app.mgr, CouponInfo, crm_id, request_data)
        result = {"coupon_list": coupons_list, "count": count}
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    pass


async def query_model_update_time(db, model_class, crm_id, request_data, pk_column=None):
    page = int(request_data.get("page", 1))
    page_size = int(request_data.get("page_size", 100))
    start_at = request_data.get("start_at", None)
    end_at = request_data.get("end_at", None)
    where = []
    if crm_id != "common":
        where.append(model_class.crm_id == crm_id)
    if start_at:
        where.append(model_class.update_time >= start_at)
    if end_at:
        where.append(model_class.update_time <= end_at)
    if where:
        order_by = pk_column if pk_column else model_class.update_time
        query = model_class.select().order_by(order_by).where(*where)
    else:
        query = model_class.select()
    logger.debug(f"{query.sql()}")
    result_list = await db.execute(query.paginate(page, page_size).dicts())
    count = await db.count(query)
    return result_list, count


async def query_model_create_time(db, model_class, crm_id, request_data):
    page = int(request_data.get("page", 1))
    page_size = int(request_data.get("page_size", 100))
    start_at = request_data.get("start_at", None)
    end_at = request_data.get("end_at", None)
    where = []
    if crm_id != "common":
        where.append(model_class.crm_id == crm_id)
    if start_at:
        where.append(model_class.create_time >= start_at)
    if end_at:
        where.append(model_class.create_time <= end_at)
    if where:
        query = model_class.select().order_by(model_class.create_time).where(*where)
    else:
        query = model_class.select()
    logger.debug(f"{query.sql()}")
    result_list = await db.execute(query.paginate(page, page_size).dicts())
    count = await db.count(query)
    return result_list, count


"""
================================= 以下是积分商城卡券统计 ====================================
"""


@bp.get("/<crm_id>/points_card/list")
@safe_crm_instance
async def points_card_list(request, crm_id):
    """获取添加到mall的未过期的积分卡券列表"""
    try:
        app = request.app
        source = request.args.get('source', '1')
        coupons = await get_mall_points_card_list(crm_id, app.mgr, app.mall, app.mall_id, source)
        return json(dict(code=RC.OK, msg="ok", data=coupons))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/statistical_points_detail")
@safe_crm_instance
async def statistical_points(request, crm_id):
    """根据卡券id列表和时间段获取卡券的领取信息"""
    try:
        app = request.app
        mgr = request.app.mgr
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        end_time = dateFromString(request_data.get("end_time"))

        card_ids = get_by_list_or_comma(request_data, 'card_ids')
        assert begin_time <= end_time, "开始时间必须小于 结束时间"
        if not card_ids:
            coupons = await get_mall_points_card_list(crm_id, app.mgr, app.mall, app.mall_id)
            coupons = coupons[:3]
        else:
            coupons = await mgr.execute(CouponInfo.select(CouponInfo.card_id, CouponInfo.title)
                                        .where(CouponInfo.card_id.in_(card_ids)).dicts())
        card_ids = [x.get('card_id') for x in coupons]
        key_list = ["receive_cards", "receive_cards_user", "redeem_cards", "redeem_cards_user"]
        result_list = []
        if (end_time - begin_time).days < 2:
            for card_id in card_ids:
                items = await mgr.execute(StatisticalCoupon.select().where(
                    StatisticalCoupon.crm_id == crm_id, StatisticalCoupon.tdate.between(begin_time, end_time),
                    StatisticalCoupon.thour.between(0, 23), StatisticalCoupon.card_id == card_id))
                result = result_by_hour(items, begin_time, end_time, key_list)
                result['card_id'] = card_id
                result_list.append(result)
        else:
            for card_id in card_ids:
                items = await mgr.execute(StatisticalCoupon.select().where(
                    StatisticalCoupon.crm_id == crm_id, StatisticalCoupon.tdate.between(begin_time, end_time),
                    StatisticalCoupon.thour == 99, StatisticalCoupon.card_id == card_id))
                result = result_by_day(items, begin_time, end_time, key_list)
                result['card_id'] = card_id
                result_list.append(result)

        total_receive_cards = total_receive_cards_user = total_redeem_cards = total_redeem_cards_user = 0
        for result in result_list:
            card_id = result.get('card_id')
            result['title'] = next((x.get('title') for x in coupons if x.get('card_id') == card_id), "卡券")
            total_receive_cards += sum(result.get('receive_cards'))
            total_receive_cards_user += sum(result.get('receive_cards_user'))
            total_redeem_cards += sum(result.get('redeem_cards'))
            total_redeem_cards_user += sum(result.get('redeem_cards_user'))

        data = dict(total_receive_cards=total_receive_cards, total_receive_cards_user=total_receive_cards_user,
                    total_redeem_cards=total_redeem_cards, total_redeem_cards_user=total_redeem_cards_user,
                    result_list=result_list)
        return json(dict(code=RC.OK, msg="ok", data=data))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/statistical_points_top")
@safe_crm_instance
async def statistical_points_top(request, crm_id):
    try:
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        end_time = dateFromString(request_data.get("end_time"))
        begin_time, end_time = make_time_range(begin_time, end_time)
        event_type = request_data.get("event_type")
        top = int(request_data.get("top", 10))
        assert event_type in ["receive", "redeem"], "event_type 仅支持 receive, redeem"
        app = request.app
        card_ids = await get_mall_points_card_ids(app.mall, app.mall_id)
        if event_type == 'receive':
            query = UserCouponCodeInfo.select(
                fn.count(UserCouponCodeInfo.card_code).alias("count"), UserCouponCodeInfo.card_id, CouponInfo.title,
                CouponInfo.subtitle).join(
                CouponInfo, on=(UserCouponCodeInfo.card_id == CouponInfo.card_id)).group_by(
                UserCouponCodeInfo.card_id).order_by(
                fn.count(UserCouponCodeInfo.card_code).alias("count").desc()).where(
                UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.received_time >= begin_time,
                UserCouponCodeInfo.received_time <= end_time, UserCouponCodeInfo.card_id.in_(card_ids)
            )
        else:
            query = UserCouponRedeemInfo.select(
                fn.count(UserCouponRedeemInfo.card_code).alias("count"), UserCouponRedeemInfo.card_id, CouponInfo.title,
                CouponInfo.subtitle).join(
                CouponInfo, on=(UserCouponRedeemInfo.card_id == CouponInfo.card_id)).group_by(
                UserCouponRedeemInfo.card_id).order_by(
                fn.count(UserCouponRedeemInfo.card_code).alias("count").desc()).where(
                UserCouponRedeemInfo.crm_id == crm_id, UserCouponRedeemInfo.redeem_time >= begin_time,
                UserCouponRedeemInfo.redeem_time <= end_time, UserCouponRedeemInfo.card_id.in_(card_ids),
                UserCouponRedeemInfo.rollback_status == 0)
        logger.info(f"{query.sql()}")
        result = await request.app.mgr.execute(query.paginate(1, top).dicts())
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 统计总量查询
@bp.get("/<crm_id>/statistical_points_total")
@safe_crm_instance
async def statistical_points_total(request, crm_id):
    try:
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        card_id = request_data.get("card_id", None)
        end_time = dateFromString(request_data.get("end_time"))
        app = request.app
        mgr = request.app.mgr
        redis = request.app.redis
        begin_time, end_time = make_time_range(begin_time, end_time)
        card_ids = await get_mall_points_card_ids(app.mall, app.mall_id)

        total_key = f"total_points_key_{begin_time}_{end_time}_{crm_id}_{card_id if card_id else 'all'}_{'-'.join(card_ids) if card_ids else 'all'}"
        got = await redis.get(total_key)
        if got:
            return json(dict(code=RC.OK, msg="ok", data=json_loads(got)))

        receive_query = UserCouponCodeInfo.select(
            fn.count(1).alias("total_receive_count"),
            fn.count(UserCouponCodeInfo.member_no.distinct()).alias("total_receive_user")).where(
            UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.received_time >= begin_time,
            UserCouponCodeInfo.received_time <= end_time, UserCouponCodeInfo.card_id == card_id if card_id else 1 == 1,
            UserCouponCodeInfo.card_id.in_(card_ids))
        logger.info(f"{receive_query.sql()}")
        receive_result = await mgr.get(receive_query.dicts())
        total_receive_count = receive_result.get("total_receive_count", 0)
        total_receive_user = receive_result.get("total_receive_user", 0)

        redeem_query = UserCouponRedeemInfo.select(
            fn.count(1).alias("total_redeem_count"),
            fn.count(UserCouponRedeemInfo.member_no.distinct()).alias("total_redeem_user")).where(
            UserCouponRedeemInfo.redeem_time >= begin_time, UserCouponRedeemInfo.redeem_time <= end_time,
            UserCouponRedeemInfo.card_id == card_id if card_id else 1 == 1, UserCouponRedeemInfo.crm_id == crm_id,
            UserCouponRedeemInfo.rollback_status == 0, UserCouponRedeemInfo.card_id.in_(card_ids)
        )
        redeem_result = await mgr.get(redeem_query.dicts())
        total_redeem_count = redeem_result.get("total_redeem_count", 0)
        total_redeem_user = redeem_result.get("total_redeem_user", 0)

        result = {"total_receive_user": total_receive_user, "total_receive_count": total_receive_count,
                  "total_redeem_user": total_redeem_user, "total_redeem_count": total_redeem_count}
        await redis.setex(total_key, 60 * 3, json_dumps(result))
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 统计时间查询
@bp.get("/<crm_id>/statistical_points_type")
@safe_crm_instance
async def statistical(request, crm_id):
    try:
        request_data = request.args
        begin_time = dateFromString(request_data.get("begin_time"))
        end_time = dateFromString(request_data.get("end_time"))
        card_id = request_data.get("card_id", None)
        assert begin_time <= end_time, "开始时间必须小于 结束时间"
        app = request.app
        card_ids = await get_mall_points_card_ids(app.mall, app.mall_id)

        where = [StatisticalCoupon.crm_id == crm_id, StatisticalCoupon.tdate.between(begin_time, end_time)]
        if card_id:
            where.append(StatisticalCoupon.card_id == card_id)
        if card_ids:
            where.append(StatisticalCoupon.card_id.in_(card_ids))

        key_list = ["receive_cards", "receive_cards_user", "redeem_cards", "redeem_cards_user"]
        if (end_time - begin_time).days < 2:
            where.append(StatisticalCoupon.thour.between(0, 23))
            items = await request.app.mgr.execute(StatisticalCoupon.select().where(*where))
            result = result_by_hour(items, begin_time, end_time, key_list)
        else:
            where.append(StatisticalCoupon.thour == 99)
            items = await request.app.mgr.execute(StatisticalCoupon.select().where(*where))
            result = result_by_day(items, begin_time, end_time, key_list)
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


"""
 ===========================================以下是微信商家券查询 ==============================
"""


@bp.get("/<crm_id>/wx/statistical_points_total")
@safe_crm_instance
async def wx_statistical_points_total(request, crm_id):
    try:
        app = request.app
        obj = {k: v for k, v in request.query_args}
        obj['card_ids'] = await get_mall_points_card_ids(app.mall, app.mall_id, source='2')
        ###
        omni = request.app.omni
        mch_id = request.headers.get("MCH_ID")
        flag, result = await omni.wxpay_coupon_statistical_total(obj, mch_id)
        ###
        if flag:  # 基本类型装进字典：{"result":xxx}
            resp = dict(result=result) if type(result) in (str, int, float) else result
            return json(dict(code=RC.OK, msg="ok", data=resp))
        msg = result if type(result) == str else result.get("errmsg", "处理错误")
        return json(dict(code=RC.HANDLER_ERROR, msg=msg))

    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/wx/statistical_points_type")
@safe_crm_instance
async def wx_statistical_points_type(request, crm_id):
    try:
        app = request.app
        obj = {k: v for k, v in request.query_args}
        obj['card_ids'] = await get_mall_points_card_ids(app.mall, app.mall_id, source='2')
        ###
        omni = request.app.omni
        mch_id = request.headers.get("MCH_ID")
        flag, result = await omni.wxpay_coupon_statistical_time(obj, mch_id)
        ###
        if flag:  # 基本类型装进字典：{"result":xxx}
            resp = dict(result=result) if type(result) in (str, int, float) else result
            return json(dict(code=RC.OK, msg="ok", data=resp))
        msg = result if type(result) == str else result.get("errmsg", "处理错误")
        return json(dict(code=RC.HANDLER_ERROR, msg=msg))

    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/wx/statistical_points_top")
@safe_crm_instance
async def wx_statistical_points_top(request, crm_id):
    try:
        app = request.app
        obj = {k: v for k, v in request.query_args}
        obj['card_ids'] = await get_mall_points_card_ids(app.mall, app.mall_id, source='2')
        ###
        omni = request.app.omni
        mch_id = request.headers.get("MCH_ID")
        _obj = {"obj": obj, "mchid": mch_id}
        flag, result = await omni.wxpay_coupon_statistical_top(obj, mch_id)
        ###
        if flag:  # 基本类型装进字典：{"result":xxx}
            resp = dict(result=result) if type(result) in (str, int, float) else result
            return json(dict(code=RC.OK, msg="ok", data=resp))
        msg = result if type(result) == str else result.get("errmsg", "处理错误")
        return json(dict(code=RC.HANDLER_ERROR, msg=msg))

    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/<crm_id>/wx/statistical_points_detail")
@safe_crm_instance
async def wx_statistical_points_detail(request, crm_id):
    try:
        app = request.app
        obj = {k: v for k, v in request.query_args}

        card_ids = get_by_list_or_comma(request.args, 'card_ids')
        if not card_ids:
            coupons = await get_mall_points_card_list(crm_id, app.mgr, app.mall, app.mall_id, source=2)
            coupons = coupons[:3]
        else:
            coupons = await app.mgr.execute(CouponInfo.select(CouponInfo.card_id, CouponInfo.title)
                                            .where(CouponInfo.card_id.in_(card_ids)).dicts())

        ###
        omni = request.app.omni
        mch_id = request.headers.get("MCH_ID")
        card_ids = [x.get('card_id') for x in coupons]

        result_list = []
        for card_id in card_ids:
            obj.update(card_id=card_id)
            flag, result = await omni.wxpay_coupon_statistical_time(obj, mch_id)
            if flag:
                result_list.append((card_id, result))

        total_receive_cards = total_receive_cards_user = total_redeem_cards = total_redeem_cards_user = 0
        results = []
        for card_id, result in result_list:
            result['card_id'] = card_id
            result['title'] = next((x.get('title') for x in coupons if x.get('card_id') == card_id), "卡券")
            total_receive_cards += sum(result.get('receive_cards'))
            total_receive_cards_user += sum(result.get('receive_cards_user'))
            total_redeem_cards += sum(result.get('redeem_cards'))
            total_redeem_cards_user += sum(result.get('redeem_cards_user'))
            results.append(result)

        data = dict(total_receive_cards=total_receive_cards, total_receive_cards_user=total_receive_cards_user,
                    total_redeem_cards=total_redeem_cards, total_redeem_cards_user=total_redeem_cards_user,
                    result_list=results)

        return json(dict(code=RC.OK, msg="ok", data=data))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
