# -*- coding: utf-8 -*-

from importlib import import_module
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

from biz.campaign import get_all_campaign, get_recent_update_campaign, get_all_tag_info
from biz.lottery import DrawLottery
from biz.signin import SignInGift
from biz.card import CardPage
from common.models.cam import *
from copy import deepcopy


app = Sanic(name="eros-cam-app")


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
    from common.models.cam import db_neocam
    db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
    db_neocam.initialize(db)
    app.mgr = Manager(db_neocam, loop=loop)

    # 读取CRM的备份库
    from common.models.crm import db_eros_crm
    crm_db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL_CRM)
    db_eros_crm.initialize(crm_db)
    app.crm_mgr = Manager(db_eros_crm, loop=loop)

    ### 获取所有实例信息，暂不需要
#    await update_app_info(app)
#    import aiojobs
#    app.jobs = await aiojobs.create_scheduler(close_timeout=0.5)
#    await app.jobs.spawn(cron_job(app))

    import aiojobs
    await init_all_campaign(app)
    app.job = await aiojobs.create_scheduler()
    await app.job.spawn(reload_db_campaign(app))

    app.all_crm_tag = {}
    await app.job.spawn(get_all_tag_info_job(app))


CAMPAIGN_INSTANCE = {
    "101": SignInGift,
    "102": DrawLottery,
    "103": CardPage, 
}

async def init_all_campaign(app):
    app.campaign_instance = {}
    try:
        campaigns_info = await get_all_campaign(app)
        for x in campaigns_info:
            cid = x.campaign_id
            logger.info(f"init campaign: {cid}")
            try:
                _ins = CAMPAIGN_INSTANCE.get(str(x.campaign_type))
                if _ins:
                    app.campaign_instance[f"cam_{cid}"] = _ins(app, model_to_dict(x))
                    logger.info(f"init campaign: {cid}")
                else:
                    logger.error(f"unknown campaign type: {x}")
            except Exception as e:
                logger.exception(e)
                logger.error(f"init draw lottery error: {cid}")
    except Exception as e:
        logger.exception(f"init campaign error with {e}")

async def reload_db_campaign(app):
    """
    每分钟扫描一次活动表，根据是否有更新来同步缓存和内存
    :param app:
    :return:
    """
    await asyncio.sleep(30)
    try:
        campaigns_info = await get_recent_update_campaign(app)
        if not campaigns_info :   # 内存数据过期，重新加载
            pass
        else:   # 加载最近10分钟更新的活动，对比版本，更新对象
            for x in campaigns_info:
                cid = x.campaign_id
                if x.status != 1 :
                    app.campaign_instance.pop(f"cam_{cid}", None)
                else:
                    logger.info(f"start init campaign: {cid}")
                    _ins = CAMPAIGN_INSTANCE.get(str(x.campaign_type))
                    if _ins:
                        app.campaign_instance[f"cam_{cid}"] = _ins(app, model_to_dict(x))
                        logger.info(f"init campaign: {cid}")
                    else:
                        logger.error(f"unknown campaign type: {x}")
    except Exception as e:
        logger.exception(f"reload campaign error with {e}")
    await app.job.spawn(reload_db_campaign(app))

async def get_all_tag_info_job(app):
    try:
        tag_infos = await get_all_tag_info(app)
        for x in tag_infos:
            #logger.info(f"init tag info: {x.tag_id}")
            app.all_crm_tag[x.tag_id] = x.bind_field
        logger.info(f"finish tag info: {app.all_crm_tag}")
    except Exception as e:
        logger.exception(f"init campaign error with {e}")
    await asyncio.sleep(30)
    await app.job.spawn(get_all_tag_info_job(app))

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




