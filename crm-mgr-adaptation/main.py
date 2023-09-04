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
import aiojobs

app = Sanic(name="eros-crm-app")


# 服务初始化，建立相关连接池
@app.listener('before_server_start')
async def init_server(app, loop):
    from sanic.config import Config
    app.conf = args = Config()
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

    app.wsm_redis = await aioredis.create_redis_pool(**args.WSM_REDIS_CONFIG, loop=loop)
    ###
    from peewee_async import PooledMySQLDatabase, Manager
    from models import db_neocrm_adapt
    db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
    db_neocrm_adapt.initialize(db)
    app.mgr = Manager(db_neocrm_adapt, loop=loop)
    # 初始化其他数据库连接 无模型类
    from peewee import Proxy
    event_proxy = Proxy()
    # 后续更新为dict映射
    db_event = PooledMySQLDatabase(**args.DB_EVENT_MYSQL)
    event_proxy.initialize(db_event)
    app.db_event_mgr = Manager(event_proxy, loop=loop)
    ###
    # todo 集成omni

    from mtkext.clients.omni import OmniGateway
    app.omni = OmniGateway(app.http, url_prefix=args.OMNI_GATEWAY_URL)
    # init session and auth
    from mtkext.ses import install_session
    install_session(app, app.redis, cookie_name=app.conf.COOKIE_NAME, expiry=3600)
    # 初始化wsm转发服务
    from api.wsm_transfer import WSMTransfer
    app.wsm_transfer = WSMTransfer(app)
    # 初始化cms转发服务
    from api.cms_transfer import CMSTransfer
    from clients import CmsClient
    app.cms_transfer = CMSTransfer(app)
    app.client_cms = CmsClient(app.http, url_prefix=app.conf.CMS_CLIENT["host"])
    # 初始化crm client
    from clients import CrmClient
    app.client_crm = CrmClient(app.http, url_prefix=app.conf.CRM_APP_SERVER_URL)
    app.client_crm_mgr = CrmClient(app.http, url_prefix=app.conf.CRM_SERVER_URL, url_mid="crm/mgr")

    from clients import CamClient
    app.client_cam = CamClient(app.http, url_prefix=app.conf.CAM_CLIENT["host"])

    # 初始化cam转发服务
    from api.cam_transfer import CAMTransfer
    app.cam_transfer = CAMTransfer(app)

    # keycloak
    from utils.keycloak_client import KeycloakClient
    app.kc = KeycloakClient(http=app.http, **args.KC_CLIENT_PARAM)

    from mtkext.qr import QrCodeFactory
    app.codeFactory = QrCodeFactory(None, True)

    from utils.factory import WXBaseFactory, init_all_woa_client
    app.wxbase_factory = WXBaseFactory
    from models import InstanceInfo
    async def get_all_instance():
        rows = await app.mgr.execute(InstanceInfo.select().where(InstanceInfo.woa_app_id.is_null(False)))
        result = [ x.woa_app_id for x in rows ]
        return result
    await init_all_woa_client(app,get_all_instance)
    app.job = await aiojobs.create_scheduler()
    await app.job.spawn(init_all_woa_client(app, get_all_instance, is_refresh=True))



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


@app.middleware('request')
async def test_process_request(request):

    ###
    ses = request.ctx.session
    instance_id = ses.get("instanceInfo", {}).get('instance_id')
    # instance_id = 1000000
    request.ctx.instance_id = instance_id
    request.ctx.user_info = ses.get("userInfo", {})
    user_id = ses.get("userInfo", {}).get("user_id")
    # user_id = 'xiaoming'
    request.ctx.user_id = user_id
    logger.info(f"test process instance_id:{instance_id}")
    # if not instance_id:
    #     return false_template(RC.NOT_LOGIN, '未登录')
