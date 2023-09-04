# -*- coding: utf-8 -*-
from urllib.parse import urlencode

from sanic import Blueprint
from sanic.log import logger
from sanic.response import json

from common.utils.const import *
from common.utils.common import get_campaign_path
from common.models.cam import *

from mtkext.dt import getCurrentDatetime
from biz.campaign import CAMPAIGN_PRIZE_PLUGIN, campaign_prize_default
from datetime import datetime

bp = Blueprint('bp_campaign', url_prefix="/campaign")

@bp.get("/<instance_id>/fetch")
async def campaign_fetch(request, instance_id):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or 0)
    try:
        assert campaign_id, "缺少campaign_id参数"
        one = await app.mgr.get(CampaignInfo, campaign_id=campaign_id, instance_id=instance_id)
        excluded = [CampaignInfo.instance_id]
        one = model_to_dict(one, exclude=excluded)

        campaign_child_no = request.args.get("campaign_child_no")

        # todo 抽取到活动子模块来规整返回活动数据
        if one["detail"] and one["detail"].get("lottery_item"):
            lottery_item = [{
                "order": x.get("order"),
                "name": x.get("name"),
                "prize_no": x.get("prize_no"),
                "type": x.get("type"),
            }  for x in one["detail"].get("lottery_item") ]
            one["detail"]["lottery_item"] = lottery_item

        if campaign_child_no and one["detail"].get("children"):
            for child in one["detail"].get("children"):
                if child.get("campaign_child_no") == campaign_child_no:
                    child["status"] = one["status"]
                    child["campaign_type"] = one["campaign_type"]
                    child["campaign_id"] = one["campaign_id"]
                    return json(dict(code=RC.OK, msg="ok", data=child))
        elif not campaign_child_no and one["detail"].get("children"):
            cam_ins = app.campaign_instance.get(f"cam_{campaign_id}")
            if not cam_ins:
                logger.error(f"参加活动失败，没有找到活动缓存 {campaign_id}")
                return json(dict(code=RC.STATUS_ERROR, msg=f"参加活动失败，活动不在有效期内：{campaign_id}"))
            flag, result = await cam_ins.get_member_card()
            if not flag:
                logger.error(f"打开领券活动失败：{result}")
            result['data']['status'] = one["status"]
            result['data']['campaign_type'] = one["campaign_type"]
            result['data']['campaign_id'] = one["campaign_id"]
            return json(result)
        return json(dict(code=RC.OK, msg="ok", data=one))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"找不到活动：{campaign_id}"))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


async def check_campaign(request, app, campaign_id, instance_id, _campaign_type):
    campaign_info = await app.mgr.get(CampaignInfo, campaign_id=campaign_id, instance_id=instance_id)
    logger.info(f"check_draw_campaign campaign info: {campaign_info}")
    begin_time = campaign_info.begin_time.strftime("%Y-%m-%d %H:%M:%S")
    end_time = campaign_info.end_time.strftime("%Y-%m-%d %H:%M:%S")

    cur_time = getCurrentDatetime().strftime("%Y-%m-%d %H:%M:%S")

    if campaign_info.status == 1 and (begin_time <= cur_time <= end_time):
        pass
    else:
        logger.error("参加活动失败，活动不在有效期内: %s" % campaign_info)
        return False, dict(code=RC.STATUS_ERROR, msg=f"参加活动失败，活动不在有效期内：{campaign_id}")
    campaign_type = campaign_info.campaign_type
    if campaign_type != _campaign_type:  # 活动类型错误
        logger.error("参加活动失败，活动类型错误: %s" % campaign_info)
        return False, dict(code=RC.STATUS_ERROR, msg=f"参加活动失败，活动类型错误：{campaign_id}")


    cam_ins = app.campaign_instance.get(f"cam_{campaign_id}")
    if not cam_ins:
        logger.error(f"参加活动失败，没有找到活动缓存 {campaign_id}")
        return False, dict(code=RC.STATUS_ERROR, msg=f"参加活动失败，活动不在有效期内：{campaign_id}")
    return True, cam_ins


@bp.get("/<instance_id>/fetch_remain_times")
async def fetch_remain_times(request, instance_id):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    assert campaign_id, "缺少campaign_id参数"
    member_no = request.args.get("member_no")
    try:
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 102)
        if not check_flag:
            logger.error(f"抽奖活动检测失败: {cam_ins}")
            return json(cam_ins)
        if member_no:
            schedule_times = await cam_ins.get_remain_times(member_no)
        else:
            schedule_times = cam_ins.get_schedule_times()
        return json(dict(code=RC.OK, msg="ok", data=dict(schedule_times=schedule_times)))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"找不到活动：{campaign_id}"))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post("/<instance_id>/lucky_draw")
async def lucky_draw(request, instance_id):
    app = request.app
    campaign_id = int(request.json.get("campaign_id") or request.json.get('cid') or 0)
    assert campaign_id, "缺少campaign_id参数"
    utm_source = request.json.get("utm_source")
    member_no = request.json.get("member_no")
    assert member_no, "缺少member_no参数"
    try:
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 102)
        if not check_flag:
            logger.error(f"抽奖活动检测失败: {cam_ins}")
            return json(cam_ins)
        flag, draw_result = await cam_ins.start_lottery(member_no, utm_source)
        if not flag:
            logger.error("抽奖失败，%s" % draw_result)
        return json(draw_result)
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"找不到活动：{campaign_id}"))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post("/<instance_id>/lock_lucky_draw")
async def lock_lucky_draw(request, instance_id):
    app = request.app
    campaign_id = int(request.json.get("campaign_id") or request.json.get('cid') or 0)
    assert campaign_id, "缺少campaign_id参数"
    member_no = request.json.get("member_no")
    assert member_no, "缺少member_no参数"
    try:
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 102)
        if not check_flag:
            logger.error(f"抽奖活动检测失败: {cam_ins}")
            return json(cam_ins)
        flag, _result = await cam_ins.lock_lottery_draw(member_no)
        if not flag:
            logger.error("抽奖锁定失败，%s" % _result)
        return json(dict(code=RC.OK, msg="ok", data=_result))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"找不到活动：{campaign_id}"))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post("/<instance_id>/unlock_lucky_draw")
async def unlock_lucky_draw(request, instance_id):
    app = request.app
    campaign_id = int(request.json.get("campaign_id") or request.json.get('cid') or 0)
    member_no = request.json.get("member_no")
    try:
        assert campaign_id, "缺少campaign_id参数"
        assert member_no, "缺少member_no参数"
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 102)
        if not check_flag:
            logger.error(f"抽奖活动检测失败: {cam_ins}")
            return json(cam_ins)
        flag, _result = await cam_ins.unlock_lottery_draw(member_no)
        if not flag:
            logger.error("抽奖解锁失败，%s" % _result)
        return json(dict(code=RC.OK, msg="ok", data=_result))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"找不到活动：{campaign_id}"))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))

@bp.get("/<instance_id>/fetch_my_prize")
async def fetch_my_prize(request, instance_id):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    member_no = request.args.get("member_no")
    page_id = request.args.get("page_id", 1)
    page_size = request.args.get("page_size", 10)
    try:
        assert campaign_id, "缺少campaign_id参数"
        assert member_no, "缺少member_no参数"
        campaign_info = await app.mgr.get(CampaignInfo, campaign_id=campaign_id, instance_id=instance_id)
        attach_func = CAMPAIGN_PRIZE_PLUGIN.get(str(campaign_info.campaign_type), campaign_prize_default)
        logger.info(f"attach func: {attach_func}")
        result = await attach_func(request, campaign_id, member_no, page_id, page_size)
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"找不到活动：{campaign_id}", data=[]))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"参数错误：{ex}", data=[]))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg="服务内部故障", data=[]))


@bp.get("/<instance_id>/fetch_my_calendar")
async def fetch_my_calendar(request, instance_id):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    member_no = request.args.get("member_no")
    month = request.args.get("month")
    try:
        assert campaign_id, "缺少campaign_id参数"
        if not member_no:
            logger.info("fetch_my_calendar no member_no")
            return json(dict(code=RC.OK, msg="ok", data=dict(sign_in_days=0, calendar=[])))
        if not month:
            month = getCurrentDatetime().strftime("%Y%m") # 目前不使用月份做过滤。因为会导致累计天数计算错误。
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 101)
        if not check_flag:
            logger.error(f"签到活动检测失败: {cam_ins}")
            return json(cam_ins)
        signin_record = await cam_ins.get_signin_info(member_no)
        calendar = cam_ins.convert_member_calendar(signin_record)
        latest_sign_day, now_date = cam_ins.get_latest_sign_day(signin_record)
        count, signin_text = cam_ins.get_signin_text(signin_record, latest_sign_day, now_date)
        return json(dict(code=RC.OK, msg="ok", data=dict(sign_in_days=count, calendar=calendar, sign_in_text=signin_text)))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"找不到活动：{campaign_id}", data=[]))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"参数错误：{ex}", data=[]))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg="服务内部故障", data=[]))

@bp.post("/<instance_id>/signin")
async def signin(request, instance_id):
    app = request.app
    campaign_id = int(request.json.get("campaign_id") or request.json.get('cid') or 0)
    member_no = request.json.get("member_no")
    utm_source = request.json.get("utm_source")
    try:
        assert campaign_id, "缺少campaign_id参数"
        assert member_no, "缺少member_no参数"
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 101)
        if not check_flag:
            logger.error(f"签到活动检测失败: {cam_ins}")
            return json(cam_ins)
        flag, result = await cam_ins.signin(member_no, utm_source)
        if not flag:
            logger.error(f"签到失败：{result}")
        return json(result)
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"找不到活动：{campaign_id}", data=[]))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"参数错误：{ex}", data=[]))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg="服务内部故障", data=[]))


@bp.get("/<instance_id>/fetch_card_page")
async def fetch_card_page(request, instance_id):
    app = request.app
    campaign_id = int(request.args.get("campaign_id") or request.args.get('cid') or 0)
    member_no = request.args.get("member_no")
    try:
        assert campaign_id, "缺少campaign_id参数"
        assert member_no, "缺少member_no参数"
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 103)
        if not check_flag:
            logger.error(f"打开领券活动检测失败: {cam_ins}")
            return json(cam_ins)
        flag, result = await cam_ins.get_member_card(member_no)
        if not flag:
            logger.error(f"打开领券活动失败：{result}")
        return json(result)
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"找不到活动：{campaign_id}", data=[]))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"参数错误：{ex}", data=[]))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg="服务内部故障", data=[]))


@bp.post("/<instance_id>/receive_card")
async def receive_card(request, instance_id):
    app = request.app
    campaign_id = int(request.json.get("campaign_id") or request.json.get('cid') or 0)
    campaign_child_no = request.json.get("campaign_child_no")
    card_ids = request.json.get("card_ids", [])
    member_no = request.json.get("member_no")
    utm_source = request.json.get("utm_source")
    try:
        assert campaign_id, "缺少campaign_id参数"
        assert campaign_child_no, "缺少campaign_child_no参数"
        assert member_no, "缺少member_no参数"
        check_flag, cam_ins = await check_campaign(request, app, campaign_id, instance_id, 103)
        if not check_flag:
            logger.error(f"参加领券活动检测失败: {cam_ins}")
            return json(cam_ins)
        flag, result = await cam_ins.append_received_card(member_no, card_ids, campaign_child_no, utm_source)
        if not flag:
            logger.error(f"参加领券活动失败：{result}")
        return json(result)
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"找不到活动：{campaign_id}", data=[]))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg=f"参数错误：{ex}", data=[]))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.OK, msg="服务内部故障", data=[]))

