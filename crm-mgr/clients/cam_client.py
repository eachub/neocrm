#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import asyncio

from sanic.log import logger

action_maping = {
    'consume_rule': 'consume/by_rule',
    "produce_direct": "produce/direct",
    "consume_direct": "consume/direct",
    "member_receive": "member/receive",
}


class CrmClient(object):
    __slots__ = (
        'member', 'points', 'card',
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

    async def _remote_request(self, concept, action, obj, crm_id, method=None, version=None, preview_url=False,
                              **kwargs):
        """:param preview_url 预览url和请求方法"""
        assert concept and type(concept) is str, "crm-client：错误的参数concept"
        assert action and type(action) is str, "crm-client：错误的参数action"
        kwargs = dict(self._kwargs, **kwargs)
        sub = f"api/{version}" if version else "api"
        if '_' in action:
            new_action = action_maping.get(action)
            if new_action:
                action = new_action
        url = f"{self._url_prefix}/{sub}/crm/{concept}/{crm_id}/{action}"
        logger.info(f"method={method} url={url}")
        if preview_url:
            return True, dict(method=method, url=url, obj=obj, crm_id=crm_id)
        if method is None:
            method = "GET" if action.split("_")[0] in \
                              ("fetch", "search", "get", "query", "show", "list", "find") else "POST"
        ###
        if method == "GET":
            result = await self._http.get(url, params=obj, **kwargs)
        elif method == "POST":
            result = await self._http.post(url, obj, **kwargs)
        else:
            return None, dict(errcode=501, errmsg=f"不支持的请求类型：{method}")
        # print(ujson.dumps(result))
        ###
        if result is None:
            return None, self._http.errinfo
        if result.get("code") == 0:
            return True, result.get("data", {})
        return False, result

    def __getattr__(self, concept):

        class InnerClass():
            def __getattr__(that, action):
                def inner(obj={}, crm_id="common", **kwargs):  # 真实入口
                    return self._remote_request(concept, action, obj, crm_id, **kwargs)

                setattr(that, action, inner)  # 主动注册，避免重复__getattr__
                return inner

        ###
        inst = InnerClass()
        setattr(self, concept, inst)  # 只调用__getattr__()一次！
        return inst


class CrmBiz:

    @staticmethod
    async def member_query(crm, crm_id, member_no):
        req_obj = dict(member_no=member_no, platform="wechat", t_platform=True)
        flag, result = await crm.member.member_query(req_obj, crm_id=crm_id, method='POST')
        return flag, result


class CamClient(object):
    __slots__ = (
        'campaign',
        '_http', '_url_prefix', '_param', '_kwargs', '_instance_id'
    )

    @property
    def client(self):
        return self._http

    def __init__(self, http, url_prefix, **kwargs):
        self._http = http
        self._url_prefix = url_prefix
        self._instance_id = kwargs.get("instance_id")
        self._param = kwargs or {}
        self._kwargs = dict(timeout=10, retry=0)

    async def _remote_request(self, concept, action, obj, instance_id=None, method=None, version=None, preview_url=False,
                              **kwargs):
        """:param preview_url 预览url和请求方法"""
        if not instance_id:
            instance_id = self._instance_id
        assert concept and type(concept) is str, "cam-client：错误的参数concept"
        assert action and type(action) is str, "cam-client：错误的参数action"
        kwargs = dict(self._kwargs, **kwargs)
        sub = f"api/{version}" if version else "api"
        if '_' in action:
            new_action = action_maping.get(action)
            if new_action:
                action = new_action
        url = f"{self._url_prefix}/{sub}/cam/mgr/{concept}/{instance_id}/{action}"
        logger.info(f"method={method} url={url}")
        if preview_url:
            return True, dict(method=method, url=url, obj=obj, instance_id=instance_id)
        if method is None:
            method = "GET" if action.split("_")[0] in \
                              ("fetch", "search", "get", "query", "show", "list", "find") else "POST"
        ###
        if method == "GET":
            result = await self._http.get(url, params=obj, **kwargs)
        elif method == "POST":
            result = await self._http.post(url, obj, **kwargs)
        else:
            return None, dict(errcode=501, errmsg=f"不支持的请求类型：{method}")
        # print(ujson.dumps(result))
        ###
        if result is None:
            return None, self._http.errinfo
        if result.get("code") == 0:
            return True, result.get("data", {})
        return False, result

    def __getattr__(self, concept):

        class InnerClass():
            def __getattr__(that, action):
                def inner(obj={}, instance_id="common", **kwargs):  # 真实入口
                    logger.info(f"instance_id: {instance_id}")
                    return self._remote_request(concept, action, obj, instance_id, **kwargs)

                setattr(that, action, inner)  # 主动注册，避免重复__getattr__
                return inner

        ###
        inst = InnerClass()
        setattr(self, concept, inst)  # 只调用__getattr__()一次！
        return inst


if __name__ == '__main__':
    from mtkext.hcp import HttpClientPool
    from conf.test import CRM_URL_PREFIX

    loop = asyncio.get_event_loop()
    http = HttpClientPool(loop=loop)
    client = CrmClient(http, CRM_URL_PREFIX)
    # from_time = 1628958001
    obj = dict(member_no='M220704308572703018', platform="wechat", t_platform=True)
    loop.run_until_complete(
        client.member.member_query(obj, crm_id=10080)
    )
    loop.run_until_complete(http.close())
    loop.close()
