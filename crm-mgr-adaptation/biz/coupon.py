#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/7/11
"""
import os
import time
from datetime import datetime
from inspect import isawaitable

from biz.utils import write_to_excel
from mtkext.dt import timestamp_to_rfc3339, datetimeToTimestamp, datetimeFromString
from mtkext.xlsx import XLSXBook
from sanic.log import logger
from sanic.response import file


async def create_coupon(omni, mch_id, appid, request_data):
    source = request_data.get("source")
    assert source in [1, 2], "卡券类型错误"
    if source == 2:
        params = build_wx_pay_coupon(request_data, mch_id, appid)
        flag, resp = await omni.wxpay_coupon_create(
            {"param": params}, mchid=mch_id)
        logger.info(f"{resp}")
        assert flag, f"{resp}"
        request_data["card_id"] = resp["stock_id"]
    request_data['extra_info'] = {
        "bg_color": request_data.get("bg_color", None),
        "miniapp_info": {
            "jump_path": request_data.get("jump_path", None), "home_path": request_data.get("home_path", None),
            "home_name": request_data.get("home_name", None), "appid": appid}
    }
    return request_data


async def update_coupon(omni, mch_id, appid, request_data):
    source = request_data.get("source")
    card_id = request_data.get("card_id")
    jump_path, bg_color, home_path, home_name = request_data.get("jump_path", None), request_data.get("bg_color"), request_data.get(
        "home_path", None), request_data.get("home_name", None)
    assert source in [1, 2], "卡券类型错误"
    assert card_id, "card_id 必填"
    # assert jump_path, "jump_path 必填"
    # assert bg_color, "bg_color 必填"
    # assert home_path, "home_path 必填"
    # assert home_name, "home_name 必填"
    request_data['extra_info'] = {
        "bg_color": bg_color,
        "miniapp_info": {"jump_path": jump_path, "home_path": home_path, "home_name": home_name, "appid": appid}
    }
    if source == 2:
        assert jump_path, "jump_path 必填"
        assert bg_color, "bg_color 必填"
        params = build_wx_pay_update_coupon(request_data, appid)
        flag, resp = await omni.wxpay_coupon_update({"param": params, "stock_id": card_id}, mchid=mch_id)
        logger.info(f"update {resp}")
    return request_data


def build_wx_pay_update_coupon(obj, appid):
    param = {
        "stock_name": obj['title'],
        "comment": obj["subtitle"],
        "goods_name": obj["notice"],
        "coupon_use_rule": {
            "use_method": "MINI_PROGRAMS",
            "mini_programs_appid": appid,
            "mini_programs_path": obj["jump_path"],
        },
        "display_pattern_info": {
            "description": obj["rule"],
            "background_color": obj["bg_color"],
            "coupon_image_url": obj["cover_img"],
        },
    }
    if obj.get("home_path"):
        param["custom_entrance"] = {
            "mini_programs_info": {
                "mini_programs_appid": appid,
                "mini_programs_path": obj["home_path"],
                "entrance_words": obj["home_name"]
            }}
    return param


def build_wx_pay_coupon(obj, mch_id, appid):
    param = dict(
        stock_name=obj["title"],
        belong_merchant=mch_id,
        comment=obj.get("subtitle") or "",
        goods_name=obj["notice"],
        coupon_use_rule={
            "coupon_available_time": {
                "available_begin_time": timestamp_to_rfc3339(datetimeToTimestamp(datetimeFromString(obj["begin_time"]))),
                "available_end_time": timestamp_to_rfc3339(datetimeToTimestamp(datetimeFromString(obj["end_time"]))),
            },
            "use_method": "MINI_PROGRAMS",  # 所有商家券都只支持小程序核销
            "mini_programs_appid": appid,
            "mini_programs_path": obj["jump_path"],
        },
        stock_send_rule={
            "max_coupons": obj["total_quantity"],
            "max_coupons_per_user": obj.get("get_limit", 100),
            # "natural_person_limit": False,
            # "prevent_api_abuse": False,
            # "transferable": obj.get("can_give_friend") or False, # 暂未开放
            # "shareable": False # 暂未开放

        },
        display_pattern_info={
            "description": obj["rule"],
            # "merchant_logo_url": instance.merchant_logo_url or "",
            # "merchant_name": instance.merchant_name or "",
            "background_color": obj["bg_color"],
            "coupon_image_url": obj["cover_img"],
        },
        custom_entrance={
            "code_display_mode": "NOT_SHOW"  # 不显示二维码
        },
        coupon_code_mode="WECHATPAY_MODE",  # 券码模式， 自生成券码
        notify_config={"notify_appid": appid},
    )
    if obj["card_type"] == 1:
        param["stock_type"] = "DISCOUNT"
        param["coupon_use_rule"].update(discount_coupon=dict(
            discount_percent=int(obj["discount"] * 100),
            transaction_minimum=int(obj["cash_condition"] * 100),
        ))
    elif obj["card_type"] in (2, 4):
        param["stock_type"] = "EXCHANGE"
        param["coupon_use_rule"].update(exchange_coupon=dict(
            exchange_price=0,
            transaction_minimum=0,
        ))
    elif obj["card_type"] == 3:
        # success, res = await app.mall.system.get_freight_templates({}, mall_id=mall_id)
        # if not success: return json(res)
        # freight_item = res.get('freight_templates', [{}])[0] if res and res.get('freight_templates') else {}
        #
        # # 包邮券
        param["stock_type"] = "NORMAL"
        param["coupon_use_rule"].update(fixed_normal_coupon=dict(
            discount_amount=1,
            transaction_minimum=obj["cash_condition"] * 100,
        ))
    else:
        param["stock_type"] = "NORMAL"
        param["coupon_use_rule"].update(fixed_normal_coupon=dict(
            discount_amount=obj["cash_amount"] * 100,
            transaction_minimum=obj["cash_condition"] * 100,
        ))
    ###
    if obj["date_type"] == 2:
        if obj["start_day_count"] > 0:
            param["coupon_use_rule"]["coupon_available_time"].update(
                wait_days_after_receive=obj["start_day_count"],
                available_day_after_receive=obj["expire_day_count"],
            )
        else:
            param["coupon_use_rule"]["coupon_available_time"].update(
                available_day_after_receive=obj["expire_day_count"],
            )

    if obj.get("home_path"):
        param["custom_entrance"].update(mini_programs_info=dict(
            mini_programs_appid=appid, mini_programs_path=obj["home_path"],
            entrance_words=obj["home_name"]))
    return param


async def query_user_crm_coupon(query_string, args, crm_client, crm_id):
    mobile = args.get("mobile", None)
    if not mobile:
        return True, query_string
    status, result = await crm_client.member.member_query(dict(mobile=mobile, platform="wechat", t_platform=False), crm_id=crm_id)
    if status:
        member_no = result.get("info").get("member_no")
        return True, f"{query_string}&member_no={member_no}"
    return False, None


async def update_card_stock(omni, instance, request_data, http, crm_server_url):
    card_id = request_data.get('card_id')
    quantity = request_data.get('quantity')
    assert card_id, 'card_id不能为空'
    assert type(quantity) is int and quantity > 0, 'quantity >0'
    _path = f"/api/crm/mgr/card/{instance.get('crm_id')}/detail?card_id={card_id}"
    url = f"{crm_server_url}{_path}"
    result = await http.get(url)
    if result.get("code") != 0:
        return False, result
    logger.info(f"{result}")
    total_quantity = result.get("data").get("coupon").get("total_quantity")
    total = total_quantity + quantity
    params = {
        "target_max": total,
        "current_max": total_quantity,
        "stock_id": card_id
    }
    flag, resp = await omni.wxpay_coupon_budget(params, mchid=instance.get("mch_id"))
    logger.info(f"{resp}")
    if not flag: return flag, resp
    return True, total


async def export_member_card(http, crm_id, member_coupon_id_list, crm_server_url):
    _path = f"/api/crm/mgr/card/{crm_id}/batch_query"
    url = f"{crm_server_url}{_path}"
    result = await http.post(url, obj={"member_coupon_id_list": member_coupon_id_list})
    if result.get("code") != 0:
        return False, result
    logger.info(f"{result}")
    status = ["", "领取", "转赠", "核销", "过期", "转赠", "作废", "作废"]

    sheet = (
        "卡券明细", ["卡券标题", "卡券ID", "用户会员号", "记录类型", "记录时间"],
        [[row.get("title"), row.get("card_id"), row.get("member_no"), status[row.get("code_status")], row.get("update_time")] for
         row in result["data"]]
    )
    fname = f"{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    if not os.path.exists("./target"):
        os.makedirs("./target")
    write_to_excel(fpath, [sheet])
    return True, (fpath, fname)


async def export_member_wxpay_card(result, event_type):
    _event_type = "领取" if event_type == "receive" else "核销"
    logger.info(f"result: {result}")
    sheet = (
        "卡券明细", ["卡券标题", "卡券ID", "用户会员号", "用户微信Unionid", "记录类型", "记录时间"],
        [[row.get("title"), row.get("card_id"), row.get("member_no", ""), row.get("unionid"), _event_type,
          row.get("send_time", row.get("redeem_time", ""))] for row in result]
    )
    fname = f"wxpay_coupon_{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    if not os.path.exists("./target"):
        os.makedirs("./target")
    write_to_excel(fpath, [sheet])
    return True, (fpath, fname)


async def export_member_wxpay_coupon(http, crm_id, member_coupon_id_list, crm_server_url):
    _path = f"/api/crm/mgr/card/{crm_id}/batch_query"
    url = f"{crm_server_url}{_path}"
    result = await http.post(url, obj={"member_coupon_id_list": member_coupon_id_list})
    if result.get("code") != 0:
        return False, result
    logger.info(f"{result}")
    status = ["", "领取", "转赠", "核销", "过期", "转赠", "作废", "作废"]

    sheet = (
        "卡券明细", ["卡券标题", "卡券ID", "用户会员号", "记录类型", "记录时间"],
        [[row.get("title"), row.get("card_id"), row.get("member_no"), status[row.get("code_status")], row.get("update_time")] for
         row in result["data"]]
    )
    fname = f"crm_coupon_{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    if not os.path.exists("./target"):
        os.makedirs("./target")
    write_to_excel(fpath, [sheet])
    return True, (fpath, fname)


async def query_stat(http, crm_id, crm_server_url, begin_date, end_date):
    statistical_receive = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_receive?begin_time={begin_date}&end_time={end_date}"
    statistical_redeem = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_redeem?begin_time={begin_date}&end_time={end_date}"
    statistical_top = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_top?begin_time={begin_date}&end_time={end_date}"
    statistical_total = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_total?begin_time={begin_date}&end_time={end_date}"
    statistical_type = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_type?begin_time={begin_date}&end_time={end_date}"
    # /api/crm/mgr/card/statistical_type?begin_time=2022-07-06&end_time=2022-07-08
    statistical_total = await http.get(statistical_total)
    if statistical_total.get("code") != 0:
        return False, statistical_total
    logger.info(statistical_total["data"])
    row = statistical_total["data"]
    sheet1 = (
        "卡券分析汇总", ["开始日期", "结束日期", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数", "转赠卡券", "转赠卡券人数"],
        [[begin_date, end_date, row.get("total_receive_count"), row.get("total_receive_user"), row.get("total_redeem_count"),
          row.get("total_redeem_user"), row.get("total_present_user"), row.get("total_present_count")]]
    )
    statistical_receive = await http.get(statistical_receive)
    if statistical_receive.get("code") != 0:
        return False, statistical_receive
    logger.info(statistical_receive["data"])
    sheet2 = (
        "领取渠道(分布)", ["开始日期", "结束日期", "指标名称", "数值"],
        [[begin_date, end_date, row.get("outer_str"), row.get("count")] for row in
         statistical_receive["data"]]
    )
    statistical_redeem = await http.get(statistical_redeem)
    if statistical_redeem.get("code") != 0:
        return False, statistical_redeem
    sheet3 = (
        "核销渠道(分布)", ["开始日期", "结束日期", "指标名称", "数值"],
        [[begin_date, end_date, row.get("redeem_channel"), row.get("count")] for row in
         statistical_redeem["data"]])
    statistical_receive_top = await http.get(f"{statistical_top}&event_type=receive")
    if statistical_receive_top.get("code") != 0:
        return False, statistical_receive_top
    sheet4 = (
        "领券top10", ["开始日期", "结束日期", "卡券名称", "数值"],
        [[begin_date, end_date, row.get("title"), row.get("count")] for row in statistical_receive_top["data"]])
    statistical_redeem_top = await http.get(f"{statistical_top}&event_type=redeem")
    if statistical_redeem_top.get("code") != 0:
        return False, statistical_redeem_top
    sheet5 = (
        "销券top10", ["开始日期", "结束日期", "卡券名称", "数值"],
        [[begin_date, end_date, row.get("title"), row.get("count")] for row in
         statistical_redeem_top["data"]])
    statistical_type = await http.get(statistical_type)
    if statistical_redeem_top.get("code") != 0:
        return False, statistical_type
    dim_ = [
        "receive_cards", "receive_cards_user",
        "redeem_cards", "redeem_cards_user",
        "present_cards", "present_cards_user",
    ]
    data = statistical_type.get("data")
    mode = data.get('mode')
    if mode == 'by_hour':
        dim_ = ['tdate', 'thour'] + dim_
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet6 = ("趋势分析", ["日期", "小时", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数", "转赠卡券", "转赠卡券人数"],
                  rows)
    else:
        dim_ = ['tdate'] + dim_
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet6 = ("趋势分析", ["日期", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数", "转赠卡券", "转赠卡券人数"],
                  rows)
        logger.info(f"{rows}")
    fname = f"crm_coupon_{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    if not os.path.exists("./target"):
        os.makedirs("./target")
    write_to_excel(fpath, [sheet1, sheet2, sheet3, sheet4, sheet5, sheet6])
    return True, (fpath, fname)


async def query_points_stat(http, crm_id, crm_server_url, begin_date, end_date):
    """积分商城自制券统计"""
    statistical_top = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_points_top?begin_time={begin_date}&end_time={end_date}"
    statistical_total = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_points_total?begin_time={begin_date}&end_time={end_date}"
    statistical_type = f"{crm_server_url}/api/crm/mgr/card/{crm_id}/statistical_points_type?begin_time={begin_date}&end_time={end_date}"
    # /api/crm/mgr/card/statistical_type?begin_time=2022-07-06&end_time=2022-07-08
    statistical_total = await http.get(statistical_total)
    if statistical_total.get("code") != 0:
        return False, statistical_total
    logger.info(statistical_total["data"])
    row = statistical_total["data"]
    sheet1 = (
        "卡券分析汇总", ["开始日期", "结束日期", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数"],
        [[begin_date, end_date, row.get("total_receive_count"), row.get("total_receive_user"), row.get("total_redeem_count"),
          row.get("total_redeem_user")]]
    )

    statistical_receive_top = await http.get(f"{statistical_top}&event_type=receive")
    if statistical_receive_top.get("code") != 0:
        return False, statistical_receive_top
    sheet4 = (
        "领券top10", ["开始日期", "结束日期", "卡券名称", "数值"],
        [[begin_date, end_date, row.get("title"), row.get("count")] for row in statistical_receive_top["data"]])
    statistical_redeem_top = await http.get(f"{statistical_top}&event_type=redeem")
    if statistical_redeem_top.get("code") != 0:
        return False, statistical_redeem_top
    sheet5 = (
        "销券top10", ["开始日期", "结束日期", "卡券名称", "数值"],
        [[begin_date, end_date, row.get("title"), row.get("count")] for row in
         statistical_redeem_top["data"]])
    statistical_type = await http.get(statistical_type)
    if statistical_redeem_top.get("code") != 0:
        return False, statistical_type
    dim_ = [
        "receive_cards", "receive_cards_user",
        "redeem_cards", "redeem_cards_user"
    ]
    data = statistical_type.get("data")
    mode = data.get('mode')
    if mode == 'by_hour':
        dim_ = ['tdate', 'thour'] + dim_
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet6 = ("趋势分析", ["日期", "小时", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数"],
                  rows)
    else:
        dim_ = ['tdate'] + dim_
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet6 = ("趋势分析", ["日期", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数"],
                  rows)
        logger.info(f"{rows}")
    fname = f"crm_coupon_points_{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    if not os.path.exists("./target"):
        os.makedirs("./target")
    write_to_excel(fpath, [sheet1, sheet4, sheet5, sheet6])
    return True, (fpath, fname)


async def query_wxpay_stat(omni, mch_id, begin_date, end_date, card_ids=None):
    _obj = {"obj": {"begin_time": begin_date, "end_time": end_date}, "mchid": mch_id}
    _receive = {"obj": {"begin_time": begin_date, "end_time": end_date, "event_type": "receive"}, "mchid": mch_id}
    _redeem = {"obj": {"begin_time": begin_date, "end_time": end_date, "event_type": "redeem"}, "mchid": mch_id}
    if card_ids:
        _obj['obj']['card_ids'] = _receive['obj']['card_ids'] = _redeem['obj']['card_ids'] = card_ids
    flag, statistical_total = await getattr(omni, "wxpay_coupon_statistical_total")(**_obj)
    row = statistical_total
    logger.info(f"{_obj} {_receive} {_redeem} {statistical_total}")
    sheet1 = (
        "卡券分析汇总", ["开始日期", "结束日期", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数"],
        [[begin_date, end_date, row.get("total_receive_count"), row.get("total_receive_user"), row.get("total_redeem_count"),
          row.get("total_redeem_user")]]
    )
    flag, statistical_top_receive = await getattr(omni, "wxpay_coupon_statistical_top")(**_receive)
    logger.info(f"{statistical_top_receive}")
    sheet2 = (
        "领券top10", ["开始日期", "结束日期", "卡券名称", "数值"],
        [[begin_date, end_date, row.get("title"), row.get("count")] for row in statistical_top_receive])
    flag, statistical_top_redeem = await getattr(omni, "wxpay_coupon_statistical_top")(**_redeem)
    logger.info(f"{statistical_top_redeem}")
    sheet3 = (
        "销券top10", ["开始日期", "结束日期", "卡券名称", "数值"],
        [[begin_date, end_date, row.get("title"), row.get("count")] for row in statistical_top_redeem])
    flag, statistical_time = await getattr(omni, "wxpay_coupon_statistical_time")(**_obj)
    logger.info(f"{statistical_time}")
    dim_ = [
        "receive_cards", "receive_cards_user",
        "redeem_cards", "redeem_cards_user"

    ]
    data = statistical_time
    mode = data.get('mode')
    if mode == 'by_hour':
        dim_ = ['tdate', 'thour'] + dim_
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet4 = ("趋势分析", ["日期", "小时", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数"], rows)
    else:
        dim_ = ['tdate'] + dim_
        rows = []
        for index, _ in enumerate(data['tdate']):
            row = [data[key][index] for key in dim_]
            rows.append(row)
        sheet4 = ("趋势分析", ["日期", "领取卡券", "领取卡券人数", "核销卡券", "核销卡券人数"], rows)
        logger.info(f"{rows}")
    fname = f"wxpay_coupon_{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    if not os.path.exists("./target"):
        os.makedirs("./target")
    write_to_excel(fpath, [sheet1, sheet2, sheet3, sheet4])
    return True, (fpath, fname)
