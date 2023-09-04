#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy

from sanic import Blueprint
from sanic.log import logger
from sanic.response import json, raw, HTTPResponse

from biz.const import RC
from utils.check import build_cookie
from utils.wrapper import check_instance
bp = Blueprint('bp_wsm_transfer', url_prefix="/wsm")

FILE_PATH_DICT = {
    "group_analyze": ["export"],
    "ck_report": ["export"],
    "channel": ["download_channel_list"]
}


@bp.route("/<concept>/<action:path>", methods=["GET", "POST"])
@check_instance
async def proxy_handle_request(request, concept, action):
    try:
        logger.info(f'concept:{concept},action:{action}')
        app = request.app

        # CEP、WSM和NFT共用cookie
#        cookies = build_cookie(request.cookies, union_key=app.conf.COOKIE_NAME)
        ###
        transfer_headers = copy.deepcopy(request.headers)
        transfer_headers["X-SHARK-INSTANCE-ID"] = request.ctx.instance.get("instance_id", "")
        transfer_headers["corp_id"] = request.ctx.instance.get("corp_id", "")
#        transfer_headers['cookie'] = cookies
        transfer_headers.pop('x-forwarded-for', None)

        method_proxy = app.wsm_transfer.method_proxy(concept, action)
        if method_proxy:
            logger.info("use method proxy")
            flag, result = await app.wsm_transfer.execute(method_proxy, request, headers=transfer_headers)
            if not flag: return json(result)
            return json(dict(code=RC.OK, msg="ok", data=result))

        # 如果自定义了路径，从这里获取wsm中真实路径
        mapping_path = app.wsm_transfer.get_mapping_path(concept, action)

        # 组装路径，并发送请求
        conf = request.app.conf
        query_string = request.query_string
        url = f"{conf.WSM_DOMAIN}/wsm/{mapping_path}?{query_string}"
        logger.info(f'wsm转发url:{url}')
        result = await request.app.http.request(url, method=request.method, data=request.body or None, headers=transfer_headers)
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))

        if concept in FILE_PATH_DICT and action in FILE_PATH_DICT[concept]:
            # 获取headers
            disposition_key = 'Content-Disposition'
            disposition = app.http.headers.get(disposition_key)
            headers = {
                "Content-Disposition": disposition,
                "Access-Control-Expose-Headers": disposition_key
            }

            # 获取content_type
            content_type = app.http.headers.get('Content-Type')
            return HTTPResponse(body=result, status=200, headers=headers, content_type=content_type)
        logger.info(f"{url} {result}")
        return raw(result, content_type="application/json")
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))



PATH_DICT = {
    "corp/get_corp_setting_url": "get_corp_setting_url",
    "corp/get_corp_info": "get_corp_info",
    "corp/create_corp_config": "create_corp_config",
    "corp/create_corp_agent": "create_corp_agent",
    "corp/get_corp_agent": "get_corp_agent",
    "corp/get_corp_depart_users": "get_corp_depart_users",
    "corp/get_corp_follow_user_list": "get_corp_follow_user_list",
    "corp/get_corp_tags": "get_corp_tags",
    "corp/add_corp_tags": "add_corp_tags",
    "corp/update_corp_tag": "update_corp_tag",
    "corp/del_corp_tag": "del_corp_tag",
}


class WSMTransfer(object):
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

    def get_mapping_path(self, concept, action):
        path = f'{concept}/{action}'
        return PATH_DICT.get(path, path)
