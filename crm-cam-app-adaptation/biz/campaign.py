# -*- coding: utf-8 -*-
from urllib.parse import urlencode

import ujson
from sanic import Blueprint
from sanic.log import logger
from sanic.response import json, redirect

from utils import *
from utils.const import *
from utils.common import models_to_dict_list
from utils.template import false_template
from mtkext.dt import getCurrentDatetime
import asyncio


CAMPAIGN_PLUGIN = {}

async def campaign_101_attach(request, campaign_info, result):
    app = request.app
    if request.ctx.member_no:
        result["is_member"] = 1
        crm_id = request.ctx.crm_id
        points_flag, points = await app.crm_client.points.summary({
            "member_no": request.ctx.member_no
        }, crm_id=crm_id, method="GET")
        logger.info(f"会员积分:{points}")
        if not points_flag:
            logger.error("未找到会员积分汇总：%s" % points)
        else:
            result["member"] = points

CAMPAIGN_PLUGIN["101"] = campaign_101_attach

async def campaign_102_attach(request, campaign_info, result):
    app = request.app
    obj = {
        "campaign_id": campaign_info["campaign_id"]
    }
    if request.ctx.member_no:
        result["is_member"] = 1
        obj["member_no"] = request.ctx.member_no
    instance_id = request.ctx.instance_id
    flag, remain_times = await app.cam_client.\
        campaign.fetch_remain_times(obj, instance_id=instance_id)
    if not flag:
        logger.error("查询活动抽奖次数失败：%s" % remain_times)
    else:
        result["plugin"] = {
            "remain_times" : remain_times.get("schedule_times", 0)
        }

CAMPAIGN_PLUGIN["102"] = campaign_102_attach


async def campaign_103_attach(request, campaign_info, result):
    # 1。 调用cam-app接口，判断时间、人群包或者标签逻辑
    # 2。 判断领券活动是商家券还是自制券
    # 3。 读取活动配置的优惠券信息
    # 4。 查询商家券领券状态
    # 5。 查询自制券领券状态

    app = request.app
    if request.ctx.member_no:
        result["is_member"] = 1
        instance_id = request.ctx.instance_id
        campaign_id = campaign_info["campaign_id"]
        flag, cam_result = await app.cam_client.campaign.fetch_card_page({
            "member_no": request.ctx.member_no,
            "campaign_id": campaign_id
        }, instance_id=instance_id)
        if not flag:
            logger.error("查询领券活动失败：%s" % cam_result)
        else:
            goods_info = cam_result.get("goods_info",{})
            campaign_child_no = cam_result.get("campaign_child_no")
            coupon_type = goods_info.get("coupon_type")
            result["plugin"] = {}
            if coupon_type == 1: # 自制券
                # 查询是否领取过
                # 对于未领取的，展示未领取标记
                # 如果全部领取，推送到底层，记录全部领取状态
                # 暂不支持部分领取
                coupon_result = cam_result.get("coupon_result")
                result["plugin"]["coupon_result"] = coupon_result
                is_all_received = 1
                for x in coupon_result:
                    if x["status"] == 0:
                        is_all_received = 0
                        break
                result["plugin"]["show_get_coupon"] = not is_all_received

            elif coupon_type == 2: # 商家券
                coupon_result = cam_result.get("coupon_result")
                result["plugin"]["coupon_result"] = coupon_result
                is_all_received = 1
                not_received_coupon = []
                wx_not_received = []
                # 使用的小程序的appid和openid，需要商户号绑定小程序
                appid, openid = request.ctx.appid, request.ctx.openid
                mchid = request.ctx.mchid
                for x in coupon_result:
                    if x["status"] == 0:
                        is_all_received = 0
                        wx_not_received.append(x["card_id"])
                        not_received_coupon.append(
                            app.omni.wxpay_get_user_coupon_all({
                                "appid":appid,"openid":openid,"stock_id":x["card_id"]
                            }, mchid=mchid))
                result["plugin"]["show_get_coupon"] = not is_all_received
                wx_coupon_list = await asyncio.gather(*not_received_coupon)
                logger.info(f"omni user coupon list: {wx_coupon_list}")
                wx_received = []
                for idx, x in enumerate( wx_coupon_list ):
                    flag, _x = x
                    if _x.get("total_count", 0):
                        # 本地记录未领取，但是从微信商家券接口查询出领取
                        wx_received.append(wx_not_received[idx])

                if wx_received: # 更新券结果
                    for x in coupon_result:
                        if x["card_id"] in wx_received:
                            x["status"] = 1
                        # 其他券状态不做更新
                    result["plugin"]["coupon_result"] = coupon_result

                    # 活动表更新领券记录历史
                    utm_source = request.args.get("utm_source")
                    await app.cam_client.campaign.receive_card({
                        "campaign_id": campaign_id,
                        "campaign_child_no": campaign_child_no,
                        "card_ids": wx_received,
                        "member_no": member_no,
                        "utm_source": utm_source,
                    }, instance_id=instance_id)

                wx_to_send = []
                is_all_received = True
                for x in coupon_result:
                    if x["status"] == 0:
                        is_all_received = False
                        wx_to_send.append(x["card_id"])
                result["plugin"]["show_get_coupon"] = not is_all_received
                if wx_to_send:
                    logger.info(f"wxpay_make_couponlist_params_v2: {wx_to_send}, {mchid}")
                    _, wx_coupon_sign = await app.omni.wxpay_make_couponlist_params_v2({
                        "card_ids": wx_to_send
                    }, mchid=mchid)
                    #wx_coupon_sign = [{
                    #    "cardId":x['cardId'], 
                    #    'cardExt':ujson.loads(x['cardExt'])} for x in wx_coupon_sign
                    #]
                    result["plugin"]['wx_coupon_sign'] = wx_coupon_sign

            else:
                logger.error(f"优惠券类型错误：{goods_info}")
    else:
        # 如果是非会员，返回显示点击注册非会员按钮
        pass

CAMPAIGN_PLUGIN["103"] = campaign_103_attach


async def campaign_default(request, campaign_info, result):
    pass


async def send_prize(request, event_no, prize_list, member_no, utm_campaign, campaign_name=""):
    app = request.app
    crm_id = request.ctx.crm_id
    for prize_info in prize_list:
        _type = prize_info.get("type")
        if _type == 1:  # 发送自制券
            card_info_list = [
                {"card_id": x, "qty": 1}
                for x in prize_info.get("goods_info", {}).get("coupon_list")
            ]
            _flag, _result = await app.crm_client.card.member_receive({
                "member_no": member_no,
                "receive_id": event_no,
                "card_info": card_info_list,
                "outer_str": utm_campaign
            }, crm_id=crm_id)
            logger.info(f"会员领券结果: {_result}")
            if not _flag:
                logger.error(f"会员领券错误: {_result}, {event_no}, {card_info_list}")
        # 3.3 发积分
        elif _type == 2:  # 发送积分
            goods_info = prize_info.get("goods_info", {})
            rule_id = goods_info.get("rule_id")
            receive_points = goods_info.get("points")
            _event_no = f"P{event_no}"
            _flag, _result = await app.crm_client.points.produce_by_rule({
                "member_no": member_no,
                "event_no": _event_no,
                "rule_id": rule_id,
                "points": receive_points,
                "event_type": "event",
                "action_scene": "campaign",
                "event_desc": "活动奖励",
                "campaign_code": utm_campaign
            }, crm_id=crm_id)
            logger.info(f"会员奖励积分结果: {_result}")
            if not _flag:
                logger.error(f"会员奖励积分错误: {_result}, {_event_no}, {receive_points}")
        elif prize_info.get("type") == 3:  # 未中奖
            logger.info("会员抽奖未中奖: {member_no} {event_no}")
        else:
            logger.error(f"会员奖励错误: {prize_info}")
