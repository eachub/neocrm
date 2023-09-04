# -*- coding: utf-8 -*-
import uuid
from urllib.parse import urlencode

import ujson
from sanic import Blueprint
from sanic.log import logger
from sanic.response import json, redirect

from utils.const import *
from biz.campaign import *
from utils.common import models_to_dict_list
from utils.template import false_template
from mtkext.dt import getCurrentDatetime
from mtkext.guid import fast_guid

bp = Blueprint('bp_campaign', url_prefix="/campaign")


@bp.get("/fetch")
async def campaign_fetch(request):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    try:
        assert campaign_id, "缺少campaign_id参数"
        instance_id = request.ctx.instance_id
        campaign_child_no = request.args.get("campaign_child_no")
        obj = {"campaign_id": campaign_id}
        if campaign_child_no:
            obj["campaign_child_no"] = campaign_child_no
        flag, campaign_info = await app.cam_client.campaign.fetch(obj, instance_id = instance_id)
        if not flag:
            logger.error("查询活动信息失败: %s" % campaign_info)
            return json(dict(code=RC.NOT_FOUND, msg=f"查询活动信息失败：{campaign_id}"))

        # 状态 0-未开始 1-已开始 2-已结束
        begin_time = campaign_info.get('begin_time', campaign_info.get("start_time"))
        end_time = campaign_info.get('end_time')

        cur_time = getCurrentDatetime().strftime("%Y-%m-%d %H:%M:%S")
        # 判断活动是否在有效期
        if campaign_info['status'] == 1 and (begin_time > cur_time or cur_time > end_time) :
            campaign_info['status'] = 3

        if request.ctx.member_no:
            campaign_info["is_member"] = 1
            campaign_info["member_no"] = request.ctx.member_no
        else:
            campaign_info["is_member"] = 0
        attach_func = CAMPAIGN_PLUGIN.get(str(campaign_info["campaign_type"]), campaign_default)
        await attach_func(request, campaign_info, campaign_info)
       
        logger.info(f"campagin info: {campaign_info}")
        return json(dict(code=RC.OK, msg="ok", data=campaign_info))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.get("/lucky_draw")
async def lucky_draw(request):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    utm_source = request.args.get("utm_source")
    try:
        assert campaign_id, "缺少campaign_id参数"
        if not request.ctx.member_no:
            logger.error("抽奖失败，请先注册会员: %s" % request.ctx)
            return json(dict(code=RC.MEMBER_ERROR, msg=f"抽奖失败，请先注册会员"))
        instance_id = request.ctx.instance_id
        member_no = request.ctx.member_no

        lock_flag, lock_result = await app.cam_client.campaign.lock_lucky_draw({
            "member_no": request.ctx.member_no,
            "campaign_id": campaign_id
        }, instance_id=instance_id)
        if not lock_flag:
            logger.error("抽奖失败，查询活动抽奖次数失败：%s" % lock_result)
            return json(dict(code=RC.LIMIT_ERROR, msg="抽奖检测失败"))

        if lock_result.get("remain_times", 0) == 0:
            logger.error(f"{member_no} 已经没有活动 {campaign_id} 抽奖次数")
            return json(dict(code=RC.LIMIT_ERROR, msg="抽奖次数已经用完"))

        consume_points = lock_result.get("points")
        if not consume_points:
            logger.error(f"{campaign_id} 积分值配置错误")
            return json(dict(code=RC.STATUS_ERROR, msg="抽奖活动错误"))
        # 1. 扣积分
        event_no = f"CAM{campaign_id}" + fast_guid()
        crm_id = request.ctx.crm_id
        utm_campaign = f"cam_crm_{campaign_id}"
        points_flag, points_result = await app.crm_client.points.consume_direct({
            "event_no": event_no,
            "member_no": member_no,
            "points": consume_points,
            "action_scene": utm_campaign,
            "event_desc": "参加抽奖"
        }, crm_id=crm_id)
        points_flag = True
        if not points_flag:
            logger.error(f"抽奖活动{campaign_id},{member_no}积分扣减{consume_points}失败：{points_result}")
            await app.cam_client.campaign.unlock_lucky_draw({
                "member_no": member_no,
                "campaign_id": campaign_id
            }, instance_id=instance_id)
            return json(dict(code=RC.LIMIT_ERROR, msg="抽奖失败，积分不足"))
        else:
            logger.info(f"抽奖活动{campaign_id},{member_no}积分扣减{consume_points}成功")
        # 2. 抽奖
        draw_flag, draw_result = await app.cam_client.campaign.lucky_draw({
            "member_no": member_no,
            "utm_source": utm_source,
            "campaign_id": campaign_id,
        }, instance_id=instance_id)
        if not draw_flag:
            logger.error("抽奖失败，%s" % draw_result)
            await app.cam_client.campaign.unlock_lucky_draw({
                "member_no": member_no,
                "campaign_id": campaign_id
            }, instance_id=instance_id)
            return json(draw_flag)
        # 3. 发奖品
        lottery_data = draw_result.get("lottery_data", {})
        lottery_info = lottery_data.get("lottery_info")
        await send_prize(request, event_no, [lottery_info], member_no, utm_campaign)
        lottery_type = lottery_info.get("type")
        is_lucky = lottery_type in [1,2]
        order = lottery_info.get("order")
        name = lottery_info.get("name")
        return json(dict(code=RC.OK, msg="ok", data=dict(order=order,name=name,is_lucky=is_lucky)))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post("/signin")
async def signin(request):
    app = request.app
    campaign_id = int(request.json.get("campaign_id") or request.json.get('cid') or 0)
    utm_source = request.json.get("utm_source")
    try:
        assert campaign_id, "缺少campaign_id参数"
        if not request.ctx.member_no:
            logger.error("抽奖失败，请先注册会员: %s" % request.ctx)
            return json(dict(code=RC.MEMBER_ERROR, msg=f"抽奖失败，请先注册会员"))
        instance_id = request.ctx.instance_id
        member_no = request.ctx.member_no

        _flag, _result = await app.cam_client.campaign.signin({
            "member_no": request.ctx.member_no,
            "campaign_id": campaign_id,
            "utm_source": utm_source
        }, instance_id=instance_id)
        if not _flag:
            logger.error("签到失败：%s" % _result)
            return json(dict(code=RC.CAMPAIGN_ERROR, msg="签到失败"))

        utm_campaign = f"cam_crm_{campaign_id}"
        campaign_name = _result.get("campaign_name")
        prize_info = _result.get("prize_info")
        event_no = _result.get("event_no")
        if prize_info and event_no:
            # 3. 发奖品
            await send_prize(request, event_no, prize_info, member_no, utm_campaign)
        return json(dict(code=RC.OK, msg="ok", data=_result))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.get("/fetch_my_bag")
async def fetch_my_bag(request):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    try:
        assert campaign_id, "缺少campaign_id参数"
        instance_id = request.ctx.instance_id
        flag, _info = await app.cam_client.campaign.fetch_my_prize({
            "campaign_id": campaign_id,
            "member_no": request.ctx.member_no,
        }, instance_id=instance_id)
        if not flag:
            logger.error("查询活动日历信息失败: %s" % _info)
            return json(dict(code=RC.OK, msg=f"查询活动日历信息失败：{campaign_id}", data=dict(
                sign_in_days=0, calendar=[]
            )))

        return json(dict(code=RC.OK, msg="ok", data=_info))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.get("/fetch_my_calendar")
async def fetch_my_calendar(request):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    try:
        assert campaign_id, "缺少campaign_id参数"
        instance_id = request.ctx.instance_id
        flag, _info = await app.cam_client.campaign.fetch_my_calendar({
            "campaign_id": campaign_id,
            "member_no": request.ctx.member_no,
        }, instance_id=instance_id)
        if not flag:
            logger.error("查询活动日历信息失败: %s" % _info)
            return json(dict(code=RC.OK, msg=f"查询活动日历信息失败：{campaign_id}", data=dict(
                sign_in_days=0, calendar=[]
            )))

        return json(dict(code=RC.OK, msg="ok", data=_info))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post("/receive_card_page")
async def receive_card_page(request):
    app = request.app
    campaign_id = int(request.json.get("campaign_id") or request.json.get('cid') or 0)
    campaign_child_no = request.json.get("campaign_child_no")
    try:
        assert campaign_id, "缺少campaign_id参数"
        assert campaign_child_no, "缺少campaign_child_no参数"

        if not request.ctx.member_no:
            logger.error("领券失败，请先注册会员: %s" % request.ctx)
            return json(dict(code=RC.MEMBER_ERROR, msg=f"领券失败，请先注册会员"))

        instance_id = request.ctx.instance_id
        flag, campaign_info = await app.cam_client.campaign.fetch({
            "campaign_id": campaign_id,
            "campaign_child_no": campaign_child_no
        }, instance_id=instance_id)
        if not flag:
            logger.error("查询活动信息失败: %s" % campaign_info)
            return json(dict(code=RC.NOT_FOUND, msg=f"查询活动信息失败：{campaign_id}"))

        goods_info = campaign_info.get("goods_info")
        campaign_name = campaign_info.get("campaign_name")
        member_no = request.ctx.member_no
        if goods_info.get("coupon_type") == 1:
            utm_campaign = f"cam_crm_{campaign_id}"
            campaign_info["type"] = 1
            event_no = f"CAM{campaign_id}:" + fast_guid()
            await send_prize(request, event_no, [campaign_info], member_no, utm_campaign)

        instance_id = request.ctx.instance_id
        utm_source = request.json.get("utm_source")
        flag, _info = await app.cam_client.campaign.receive_card({
            "campaign_id": campaign_id,
            "campaign_child_no": campaign_child_no,
            "member_no": member_no,
            "utm_source": utm_source,
        }, instance_id=instance_id)
        if not flag:
            logger.error("领券失败: %s" % _info)
            return json(
                dict(code=RC.OK, msg=f"领券失败：{campaign_id}-{campaign_child_no}",
                     data={}))

        return json(dict(code=RC.OK, msg="ok", data=_info))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.get("/auth")
async def woa_user_auth(request):
    code = request.args.get('code')
    assert code, 'code必传'
    appid = request.args.get('appid')
    assert appid, 'appid必传'
    campaign_id = request.args.get('campaign_id') or request.args.get('cid')
    assert campaign_id, 'campaign_id必传'
    jump = request.args.get('url')
    assert jump, 'url必传'
    ###
    token = request.app.token
    flag, user_info = await token.get_user_info({"appid": appid, "code": code}, industry="matrix")
    if not flag:
        logger.error("公众号用户数据获取失败")
        logger.error("user info: %s" % user_info)
        return json(dict(code=RC.INTERNAL_ERROR, msg="公众号用户数据获取失败"))
    user_info["appid"] = appid
    request.ctx.session["user"] = user_info
    jump_char = "?" if jump.find("?") < 0 else "&"

    return redirect(f'{jump}{jump_char}SESSION_ID={request.ctx.session.sid}&campaign_id={campaign_id}')


@bp.get("/get_woa_sign")
async def get_woa_sign(request):
    try:
        woa_appid = request.ctx.woa_appid
        url = request.args.get('url')
        assert url, 'url必传'
        app = request.app
        # 获取wxbase_client
        wxbase_client = await app.wxbase_factory.get_client(woa_appid, app.http, app.conf.ACCESS_TOKEN_URL)
        if not wxbase_client:
            logger.error(f"未找到WOA客户端:{woa_appid}")
            return json(dict(code=RC.OK, msg='ok', data={}))
        logger.info(f"/get_woa_sign url: {url}")
        sign = wxbase_client.makeJsapiSign(url)
        sign['appid'] = woa_appid
        return json(dict(code=RC.OK, msg='ok', data=sign))
    except AssertionError as ex:
        logger.error(f'参数异常:{ex}')
        return json(dict(code=RC.PARAMS_INVALID, msg=f'参数异常{ex}'))
    except Exception as ex:
        logger.exception(ex)
        logger.error(f'服务内部故障:{ex}')
        return json(dict(code=RC.INTERNAL_ERROR, msg=f'服务内部故障'))
