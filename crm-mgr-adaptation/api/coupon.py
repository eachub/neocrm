#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/7/11
"""
import asyncio
import hashlib
from base64 import b64encode
from inspect import isawaitable

from biz.const import RC
from biz.coupon import export_member_card, query_stat, query_wxpay_stat, export_member_wxpay_card, query_points_stat
from models import WxpayImage
from sanic import Blueprint
from sanic.exceptions import InvalidUsage
from sanic.response import json, file
from utils.wrapper import check_instance
from sanic.log import logger


bp = Blueprint('bp_wx_coupon', url_prefix="/coupon")


@bp.post("/upload_wxpay_image")
@check_instance
async def upload_wxpay_image(request):
    instance = request.ctx.instance
    try:
        app = request.app
        request_data = request.json
        media_url = request_data.get('media_url')
        instance_id = request.ctx.instance_id
        assert media_url, '图片字段file不能为空'
        hashcode = hashlib.sha256(media_url.encode()).hexdigest()
        items = await app.mgr.execute(WxpayImage.select().where(WxpayImage.hashcode == hashcode))
        if items:
            resp = items[0].info
        else:
            content = await app.http.request(media_url, method="GET")
            b64content = b64encode(content).decode()
            flag, resp = await app.omni.wxpay_image_upload({"content": b64content}, mchid=instance.get("mch_id"))
            if not flag: return json(resp)
            await app.mgr.execute(WxpayImage.insert(instance_id=instance_id, hashcode=hashcode, info=resp, origin_url=media_url))
        resp.update(src="/direct/" + resp.get("media_url", "").replace("://", "/"))
        return json(dict(code=RC.OK, msg="ok", data=resp))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"错误：{ex}"))
    except (KeyError, TypeError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg="系统错误，请稍后重试"))


@bp.get("/list")
@check_instance
async def coupon_list(request):
    instance = request.ctx.instance
    try:
        app = request.app
        request_body = request.json
        crm_id = instance.get("crm_id")
        mch_id = instance.get("mch_id")
        _path = f"/api/crm/mgr/card/{crm_id}/list"
        query_string = request.query_string
        url = f"{app.conf.CRM_SERVER_URL}{_path}?{query_string}&source=2"
        logger.info(url)
        result = await app.http.request(url, method=request.method, parse_with_json=True, json=request_body, headers={})
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))
        data = result.get("data").get("coupon_list")
        tasks = []
        for item in data:
            tasks.append(app.omni.wxpay_coupon_query(obj={"stock_id": item.get("card_id")}, mchid=mch_id))
        results = await asyncio.gather(*tasks)
        lists = zip(data, results)
        datas = []
        for i in lists:
            tmp = i[0]
            if i[1][0]:
                pay_data = i[1][1]
                max_coupons = pay_data.get("stock_send_rule", {}).get("max_coupons")
                total_send_coupons = pay_data.get("send_count_information", {}).get("total_send_num")
                total_count = max_coupons - total_send_coupons
                tmp["total_count"] = total_count if total_count else 0
            datas.append(tmp)
        result["data"]["coupon_list"] = datas
        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"错误：{ex}"))
    except (KeyError, TypeError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg="系统错误，请稍后重试"))


@bp.post("/export_crm_coupon_list")
@check_instance
async def export_crm_coupon_list(request):
    app = request.app
    try:
        member_coupon_id_list = request.json.get("member_coupon_id_list", [])
        assert isinstance(member_coupon_id_list, list) and len(member_coupon_id_list), 'member_coupon_id_list 不能为空'
        status, result = await export_member_card(
            app.http, request.ctx.instance.get("crm_id"), member_coupon_id_list, app.conf.CRM_SERVER_URL)
        if not status:
            return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，请重试！"))
        return await file(result[0], filename=result[1])
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.get("/export_crm_coupon_stat")
@check_instance
async def export_crm_coupon_stat(request):
    app = request.app
    try:
        request_data = request.args
        begin_date = request_data.get("begin_date")
        end_date = request_data.get("end_date")
        status, result = await query_stat(app.http, request.ctx.instance.get("crm_id"), app.conf.CRM_SERVER_URL, begin_date, end_date)
        if not status:
            return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，请重试！"))
        return await file(result[0], filename=result[1])
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.get("/export_crm_points_coupon_stat")
@check_instance
async def export_crm_points_coupon_stat(request):
    """导出积分商城自制券统计"""
    app = request.app
    try:
        request_data = request.args
        begin_date = request_data.get("begin_date")
        end_date = request_data.get("end_date")
        status, result = await query_points_stat(app.http, request.ctx.instance.get("crm_id"), app.conf.CRM_SERVER_URL, begin_date, end_date)
        if not status:
            return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，请重试！"))
        return await file(result[0], filename=result[1])
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.get("/export_wxpay_coupon_stat")
@check_instance
async def export_wxpay_coupon_stat(request):
    app = request.app
    try:
        request_data = request.args
        begin_date = request_data.get("begin_date")
        end_date = request_data.get("end_date")
        instance = request.ctx.instance
        mch_id = instance.get("mch_id")
        status, result = await query_wxpay_stat(request.app.omni, mch_id, begin_date, end_date)
        if not status:
            return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，请重试！"))
        return await file(result[0], filename=result[1])
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.get("/export_wxpay_points_coupon_stat")
@check_instance
async def export_wxpay_points_coupon_stat(request):
    """导出积分商城商家券统计"""
    app = request.app
    try:
        request_data = request.args
        begin_date = request_data.get("begin_date")
        end_date = request_data.get("end_date")
        instance = request.ctx.instance
        crm_id = instance.get('crm_id')
        mch_id = instance.get("mch_id")

        headers = {"MCH_ID": mch_id}
        ctype = request.headers.get("Content-Type")
        if ctype: headers["Content-Type"] = ctype
        logger.info(f"this crm_id={crm_id}")

        path = f"/api/crm/mgr/card/{crm_id}/points_card/list"

        query_string = request.query_string
        url = f"{app.conf.CRM_SERVER_URL}{path}?{query_string}&source=2"
        logger.info(url)
        result = await app.http.request(url, method=request.method, data=request.body or None, headers=headers, parse_with_json=True)
        logger.info(result)
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))

        card_ids = [x.get('card_id') for x in result.get('data')]

        status, result = await query_wxpay_stat(request.app.omni, mch_id, begin_date, end_date, card_ids)
        if not status:
            return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，请重试！"))
        return await file(result[0], filename=result[1])
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


def register_handler(uri, action, method):
    @check_instance
    async def hander(request):
        try:
            nonlocal action, method
            if method == "GET":
                obj = {k: v for k, v in request.query_args}
            else:
                obj = request.json
            ###
            omni_client = request.app.omni
            instance = request.ctx.instance
            mch_id = instance.get("mch_id")
            _obj = {"obj": obj, "mchid": mch_id}
            flag, result = True, getattr(omni_client, action)(**_obj)
            if isawaitable(result): flag, result = await result
            ###
            if flag:  # 基本类型装进字典：{"result":xxx}
                resp = dict(result=result) if type(result) in (str, int, float) else result
                return json(dict(code=RC.OK, msg="ok", data=resp))
            msg = result if type(result) == str else result.get("errmsg", "处理错误")
            return json(dict(code=RC.HANDLER_ERROR, msg=msg))
        except AssertionError as ex:
            return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
        except (InvalidUsage, TypeError, FileNotFoundError) as ex:
            return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
        except Exception as ex:
            logger.exception(ex)
            return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))

    bp.add_route(hander, uri, methods=[method])


register_handler("/wxpay/statistical_top", "wxpay_coupon_statistical_top", "GET")
register_handler("/wxpay/statistical_total", "wxpay_coupon_statistical_total", "GET")
register_handler("/wxpay/statistical_time", "wxpay_coupon_statistical_time", "GET")
# register_handler("/wxpay/search_data", "wxpay_coupon_search_data", "POST")

@bp.post("/get_member_coupon_list")
@check_instance
async def get_member_coupon_list(request):
    app = request.app
    try:
        obj = request.json
        crm_client = request.app.client_crm
        crm_id = request.ctx.instance.get("crm_id")

        member_obj = dict(platform="wechat")
        mobile = obj.get("mobile")
        member_no = obj.get("member_no")
        unionid = None
        if mobile or member_no:
            if mobile: member_obj["mobile"] = mobile
            if member_no: member_obj["member_no"] = member_no
            status, result = await crm_client.member.member_query(member_obj, crm_id=crm_id)
            logger.info(f"query member: {member_obj}, {result}")
            if status:
                unionid = result.get("wechat_member_info",{}).get("unionid")
            else:
                return json(dict(code=RC.OK, msg="ok", data={"coupon_code_list": [],"count":0}))
        if unionid:
            obj["unionid"] = unionid

        omni_client = request.app.omni
        instance = request.ctx.instance
        mch_id = instance.get("mch_id")
        _obj = {"obj": obj, "mchid": mch_id}

        status, result = await omni_client.wxpay_coupon_search_data(**_obj)
        if not status:
            return json(dict(code=RC.OK, msg="ok", data={"coupon_code_list": [],"count":0}))

        all_unionids = list(set( [ x.get("unionid") for x in result.get("coupon_code_list") if x.get("unionid")  ] ))
        unionid_obj = {"unionid_li": all_unionids}
        logger.info(f"unionid_obj: {unionid_obj}")
        _flag,_result = await request.app.client_crm_mgr.member.fetch_member_nos(unionid_obj, crm_id=crm_id, method="POST")
        if _flag and _result:
            _res = dict()
            for x in _result:
                _res[x['unionid']] = x
            for x in result.get("coupon_code_list"):
                _member = _res.get(x.get("unionid"))
                x['member_no'] = _member.get("member_no")
                x['nickname'] = _member.get("nickname")

        return json(dict(code=RC.OK, msg="ok", data=result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))

@bp.post("/export_member_coupon_list")
@check_instance
async def export_member_coupon_list(request):
    app = request.app
    try:
        event_id_list = request.json.get("event_id_list", [])
        assert isinstance(event_id_list, list) and len(event_id_list), 'event_id_list 不能为空'
        omni_client = request.app.omni
        instance = request.ctx.instance
        mch_id = instance.get("mch_id")
        _obj = {"obj": request.json, "mchid": mch_id}

        status, result = await omni_client.wxpay_coupon_search_data(**_obj)
        if not status:
            return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，没有数据！"))
        status, result = await export_member_wxpay_card(result.get("coupon_code_list",[]), request.json.get("event_type"))
        if not status:
            return json(dict(code=RC.PARAMS_INVALID, msg="导出失败，请重试！"))
        return await file(result[0], filename=result[1])
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))

