#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy

from sanic import Blueprint
from sanic.log import logger
from sanic.response import json, raw, HTTPResponse

from biz.const import RC
from utils.wrapper import check_instance

import aiofiles
import os
from urllib.parse import quote

bp = Blueprint('bp_campaign_transfer', url_prefix="/cam")



# 2. 活动预览
@bp.get("/campaign/preview")
#@check_instance
async def campaign_preview(request):
    #instance_id = request.ctx.instance_id
    instance_id = request.args.get("instance_id")
    #instance_id = request.args.get("instance_id","neo_instance_id")
    #app_id = request.args.get("app_id", "wx71031dea78e9d57b")
    app_id = request.args.get("app_id")
    campaign_id = request.args.get("campaign_id", "cid")
    try:
        assert campaign_id, "campaign_id参数错误"
        app = request.app
        conf = app.conf
        flag, cam_info = await app.client_cam.campaign.fetch(
            dict(campaign_id=campaign_id), instance_id=instance_id)
        if not flag or not cam_info:
            logger.info(f"未找到活动{campaign_id}, {cam_info}")
            return json(dict(code=RC.DATA_NOT_FOUND, msg=f"未找到活动{campaign_id}"))
        campaign_child_no = request.args.get("campaign_child_no")

        base = conf.UPLOAD_DIR
        dirs = f"{base}/cam/preview/qrcode/{instance_id}"
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        fname = f"{campaign_id}.jpg" if not campaign_child_no else f"{campaign_id}_{campaign_child_no}.jpg"
        path = f"{dirs}/{fname}"
        if os.path.exists(path):
            async with aiofiles.open(path, mode='rb') as fp:
                buffer = await fp.read()
                logger.info(f"read from local file: {fname}")
                headers = {"content-type": "image/png", "content-length": len(buffer)}
                return raw(buffer, headers=headers)
        #app_id = request.ctx.instance.get("app_id")
        crm_h5 = app.conf.CRM_H5_PREVIEW
        query = f"cid={campaign_id}"
        if campaign_child_no :
            query = f"{query}&ccn={campaign_child_no}"
        query = quote(query)
        preview_path = f"{crm_h5}{query}"
        wxbase = await app.wxbase_factory.get_client(app_id, app.http, app.conf.ACCESS_TOKEN_URL)
        logger.info(f"{campaign_id}->{campaign_child_no}活动路径：{preview_path}")
        if app.cmd_args.env == "test":
            logger.info("trial env qrcode")
            success, res = await wxbase.createMpQrCode(
                isQrcode=False, path=preview_path, env_version="trial")
            if success is False:
                logger.info(f"res: {res}")
                return json(res)
        else:
            logger.info("release env qrcode")
            success, res = await wxbase.createMpQrCode(
                isQrcode=False,
                path=preview_path)
            if success is False:
                logger.info(f"res: {res}")
                return json(res)
        buffer = res.get("buffer")
        headers = {"content-type": "image/png", "content-length": len(buffer)}
        async with aiofiles.open(path, mode='wb') as fp:
            await fp.write(buffer)
        return raw(buffer, headers=headers)
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.route("/<concept>/<action>", methods=["GET", "POST"])
@check_instance
async def proxy_handle_request(request, concept, action):
    try:
        logger.info(f'活动管理转发 concept: {concept} action: {action}')
        app = request.app

        instance = request.ctx.instance
        transfer_headers = copy.deepcopy(request.headers)
        transfer_headers["X-SHARK-CRM"] = instance.get("crm_id")
        logger.info(f"transfer_headers: {transfer_headers}")
        method_proxy = app.cam_transfer.method_proxy(concept, action)
        if method_proxy:
            logger.info("use method proxy")
            flag, result = await app.cam_transfer.execute(method_proxy, request, headers=transfer_headers)
            if not flag: return json(result)
            return json(dict(code=RC.OK, msg="ok", data=result))

        # 如果自定义了路径，从这里获取cms中真实路径
        mapping_path = app.cam_transfer.get_mapping_path(concept, action, request.ctx.instance_id)

        # 组装路径，并发送请求
        conf = request.app.conf
        query_string = request.query_string
        cam_conf = conf.CAM_CLIENT
        url = f"{cam_conf['host']}{cam_conf['prefix']}/{mapping_path}?{query_string}"
        logger.info(f'cam转发url:{url}')
        # 文件
        if 'export' in url:
            result = await app.http.request(url, method=request.method, data=request.body or None,
                                            headers=transfer_headers, timeout=180)
            # 获取header
            disposition_key = 'Content-Disposition'
            disposition = app.http.headers.get(disposition_key)
            headers = {
                "Content-Disposition": disposition,
                "Access-Control-Expose-Headers": disposition_key
            }

            # 获取content_type
            content_type = app.http.headers.get('Content-Type')
            return HTTPResponse(body=result, status=200, headers=headers, content_type=content_type)
        else:
            result = await app.http.request(url, method=request.method, data=request.body or None, parse_with_json=True,
                                            headers=transfer_headers, timeout=180)
        logger.info(f"活动转发结果: {url} {result}")
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))
        return json(result)

    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


PATH_DICT = {

}


class CAMTransfer(object):
    def __init__(self, app):
        self.app = app
        self.mgr = app.mgr
        self.redis = app.redis

    def method_proxy(self, concept, action):
        attr_name = f"_{concept}_{action}"
        if hasattr(self, attr_name):
            appender = getattr(self, attr_name)
            return appender
        return None

    async def execute(self, appender, request, **kwargs):
        adt = {}
        if appender: adt = await appender(request, **kwargs)
        return adt

    async def _todo_method(self, request, **kwargs):
        return True, dict(code=0, msg='可扩展方法')

    def get_mapping_path(self, concept, action, instance_id):
        path = f'{concept}/{instance_id}/{action}'
        return PATH_DICT.get(path, path)
