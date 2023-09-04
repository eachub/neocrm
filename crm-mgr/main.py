# -*- coding: utf-8 -*-

from importlib import import_module

import ujson
from sanic import Sanic
from sanic.log import logger
from sanic.blueprints import Blueprint
from sanic.blueprint_group import BlueprintGroup
from sanic.exceptions import SanicException, NotFound, InvalidUsage
from sanic.response import json, raw
import time
import asyncio
from sanic.kjson import kjson, json_dumps
from urllib.parse import urlencode

app = Sanic(name="eros-crm-mgr")


# 服务初始化，建立相关连接池
@app.listener('before_server_start')
async def init_server(app, loop):
    from sanic.config import Config
    app.conf = args = Config()
    args.update_config(f"common/conf/{app.cmd_args.env}.py")
    args.update_config(f"conf/{app.cmd_args.env}.py")

    ###
    from glob import glob
    for subname in glob("api/*.py"):
        modname = subname.replace('/', '.')[:-3]
        module = import_module(modname)
        bp = getattr(module, "bp", None)
        if bp and isinstance(bp, (Blueprint, BlueprintGroup)):
            app.blueprint(bp, url_prefix=args.URL_PREFIX + bp.url_prefix)
    ###
    from aiohttp import ClientSession, ClientTimeout, TCPConnector, DummyCookieJar
    client = ClientSession(connector=TCPConnector(
        limit=1000, keepalive_timeout=300, ssl=False, loop=loop),
        cookie_jar=DummyCookieJar(),
        json_serialize=json_dumps,
        timeout=ClientTimeout(total=120))
    ###
    from mtkext.cache import LocalCache
    app.cache = LocalCache()
    from mtkext.hcp import HttpClientPool
    app.http = HttpClientPool(loop=loop, client=client)
    ###
    import aioredis
    app.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)
    ###
    from common.models.base import db_eros_crm
    from biz.utils import init_db_manager
    app.mgr, app.mgv = init_db_manager(loop, db_eros_crm, args.PARAM_FOR_MYSQL, args.PARAM_FOR_VIEW,
                                       args.COMMON_DB)
    ###
    # init session and auth
    from mtkext.ses import install_session
    install_session(app, app.redis, cookie_name="__eros_uuid__", expiry=3600)
    ###
    # 初始化加载一些常用
    with open('data/region.json', 'r', encoding='utf-8') as fp:
        region_data = ujson.load(fp)
    app.region_data = region_data
    # 加密 cipher
    from common.biz.codec import define_cipher
    app.cipher = define_cipher("EROS#CRM987")

    # 初始化常用的client
    from clients.cam_client import CamClient
    app.cam_app_client = CamClient(app.http, **app.conf.CAM_CLIENT)

    from mtkext.clients.mall import MallClient
    app.mall = MallClient(app.http, args.PARAMS_FOR_MALL_CLIENT.get('url_prefix'))
    app.mall_id = args.PARAMS_FOR_MALL_CLIENT.get('mall_id')

    from mtkext.clients.omni import OmniGateway
    app.omni = OmniGateway(app.http, url_prefix=args.OMNI_GATEWAY_URL)


# 回显所有路由信息
@app.listener('after_server_start')
async def check_server(app, loop):
    for uri, route in app.router.routes_all.items():
        method = "|".join(route.methods)
        logger.info(f"{uri} ==({method})==> {route.name}")


# 停止服务，回收资源
@app.listener('after_server_stop')
async def kill_server(app, loop):
    await app.http.close()
    await app.mgr.close()
    app.redis.close()
    await app.redis.wait_closed()


@app.middleware('request')
async def record_request(request):
    if request.method == "POST":
        ctype = request.headers.get("Content-Type")
        if ctype and ctype.find("multipart") < 0 and request.body:
            logger.info(f'POST: {request.path} <== {request.body.decode(errors="replace")}')
    else:
        logger.info(f"{request.method}: {request.path}")
