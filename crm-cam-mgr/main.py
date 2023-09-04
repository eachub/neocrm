# -*- coding: utf-8 -*-

from importlib import import_module
from sanic import Sanic
from sanic.log import logger
from sanic.blueprints import Blueprint
from sanic.blueprint_group import BlueprintGroup
from sanic.exceptions import SanicException, NotFound, InvalidUsage, MethodNotSupported
from sanic.response import json, raw
import time
import asyncio
from sanic.kjson import kjson, json_dumps
from urllib.parse import urlencode

from common.models.cam import *
from copy import deepcopy

from common.utils.const import RC
from common.utils.template import false_template

app = Sanic(name="eros-cam-mgr")


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
    ###
    from peewee_async import PooledMySQLDatabase, Manager
    from common.models.cam import db_neocam
    db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
    db_neocam.initialize(db)
    app.mgr = Manager(db_neocam, loop=loop)
    ###
    import aioredis
    app.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)


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
            logger.info(
                f'POST: {request.path} <== {request.body.decode(errors="replace")}')
    else:
        logger.info(f"{request.method}: {request.path}")


@app.exception(Exception)
def catch_exceptions(request, ex):
    if isinstance(ex, NotFound):
        return false_template(RC.REQUEST_ERROR, f'请求地址不存在!')
    elif isinstance(ex, MethodNotSupported):
        return false_template(RC.REQUEST_ERROR, f'请求方法错误')
    elif isinstance(ex, InvalidUsage):
        logger.exception(ex)
        return false_template(RC.PARAMS_INVALID, f'请求包体只支持Json')
    elif isinstance(ex, AssertionError):
        logger.exception(ex)
        return false_template(RC.PARAMS_INVALID, f'{ex}')
    elif isinstance(ex, KeyError):
        logger.exception(ex)
        return false_template(RC.PARSER_FAILED, f'解析错误: {ex}')
    else:
        logger.exception(ex)
        return false_template(RC.INTERNAL_ERROR, '服务器内部错误, 请稍后重试!')


