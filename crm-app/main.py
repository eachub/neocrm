# -*- coding: utf-8 -*-
from copy import deepcopy
from importlib import import_module

from mtkext.db import create_all_tables
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

from biz.crm import query_crm_info

app = Sanic(name="eros-crm-app")


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
    from peewee_async import PooledMySQLDatabase, Manager
    from common.models.base import db_eros_crm
    db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
    db_eros_crm.initialize(db)
    app.mgr = Manager(db_eros_crm, loop=loop)

    from common.models import member, points, coupon, analyze, base, ecom
    from common.models.member import UserTags
    create_all_tables(member, [UserTags])
    create_all_tables(points, [])
    create_all_tables(analyze, [])
    create_all_tables(coupon, [])
    create_all_tables(base, [])
    create_all_tables(ecom, [])
    ###
    # init session and auth
    from mtkext.ses import install_session
    install_session(app, app.redis, cookie_name="__eros_uuid__", expiry=3600)
    ###
    init_finder(app)
    init_geo_filter(app)

    # 加密 cipher
    from common.biz.codec import define_cipher
    app.cipher = define_cipher("EROS#CRM987")

    ###
    await update_app_info(app)
    import aiojobs
    app.jobs = await aiojobs.create_scheduler(close_timeout=0.5)
    await app.jobs.spawn(cron_job(app))


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


async def update_app_info(app):
    def handle_info(info, key, pkey):
        if info is None:
            logger.error(f"failed to get {key}")
        elif getattr(app.conf, key, None) != info:
            setattr(app.conf, key, info)
            info = {t[pkey]: t for t in info}
            setattr(app, key.lower(), info)
            logger.info(f"{key} is updated: {info}")
    ###
    try:
        info = await query_crm_info(app.mgr)
        handle_info(info, "CRM_INFO", "crm_id")
        logger.info(f"crm_info:{app.crm_info}")
    except Exception as ex:
        logger.info(ex)
        logger.info("初始化加载数据问题")


async def cron_job(app):
    prevStamp = int(time.time())
    while not app.jobs.closed:
        now = int(time.time())
        if now - prevStamp >= 3600:
            try:
                await update_app_info(app)
                prevStamp = now
            except Exception as ex:
                logger.exception(ex)
        await asyncio.sleep(0.3)


def init_finder(app):
    from utils.ip2region import Ipv4Finder
    ip_finder = Ipv4Finder(app.conf.IP_DB_PATH)
    app.ip_finder = ip_finder
    from utils.mobile2region import MobileFinder
    mobile_finder = MobileFinder(app.conf.MOBILE_REGION_PATH)
    app.mobile_finder = mobile_finder


def init_geo_filter(app):
    from utils.geo_filter import GeoFilter
    geo_filter = GeoFilter(app.conf.GEO_BASE_PATH)
    app.geo_filter = geo_filter