#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import asyncio
import logging
import time
from collections import OrderedDict

import ujson

from sanic.log import logger

action_maping = {
    "consume_direct": "consume/direct",
    "member_receive": "member/receive",
    "produce_by_rule": "produce/by_rule",
    "member_card_list": "member/card_list",
}


class CrmClient(object):

    __slots__ = (
        'member', 'points', "card",
        '_http', '_url_prefix', '_param', '_kwargs'
    )

    @property
    def client(self):
        return self._http

    def __init__(self, http, url_prefix, **kwargs):
        self._http = http
        self._url_prefix = url_prefix
        self._param = kwargs or {}
        self._kwargs = dict(timeout=10, retry=0)

    async def _remote_request(self, concept, action, obj, crm_id, method=None, version=None, **kwargs):
        assert concept and type(concept) is str, "crm-client：错误的参数concept"
        assert action and type(action) is str, "crm-client：错误的参数action"
        kwargs = dict(self._kwargs, **kwargs)
        sub = f"api/{version}" if version else "api"
        if '_' in action:
            new_action = action_maping.get(action)
            if new_action:
                action = new_action
        url = f"{self._url_prefix}/{sub}/crm/{concept}/{crm_id}/{action}"
        if method is None:
            method = "GET" if action.split("_")[0] in \
                ("fetch", "search", "get", "query", "show", "list", "find") else "POST"
        ###
        logger.info(f"CRM-CLIENT request: {url}, {obj}")
        if method == "GET":
            result = await self._http.get(url, params=obj, **kwargs)
        elif method == "POST":
            result = await self._http.post(url, obj, **kwargs)
        else:
            return None, dict(errcode=501, errmsg=f"不支持的请求类型：{method}")
        ###
        logger.info(f"CRM-CLIENT response: {result}")
        if result is None:
            return None, self._http.errinfo
        if result.get("code") == 0:
            return True, result.get("data", {})
        return False, result

    def __getattr__(self, concept):
        print(concept)
        class InnerClass():
            def __getattr__(that, action):
                def inner(obj={}, crm_id="common", **kwargs):  # 真实入口
                    return self._remote_request(concept, action, obj, crm_id, **kwargs)
                setattr(that, action, inner) # 主动注册，避免重复__getattr__
                return inner
        ###
        inst = InnerClass()
        setattr(self, concept, inst) # 只调用__getattr__()一次！
        return inst



if __name__ == '__main__':
    from mtkext.hcp import HttpClientPool
    from conf.test import PARAMS_FOR_CRM

    loop = asyncio.get_event_loop()
    http = HttpClientPool(loop=loop)
    client = CrmClient(http, **PARAMS_FOR_CRM)
    # from_time = 1628958001
    loop.run_until_complete(
        client.member.rules__({"goods_id": 200001}, crm_id=158000)
    )
    loop.run_until_complete(http.close())
    loop.close()
