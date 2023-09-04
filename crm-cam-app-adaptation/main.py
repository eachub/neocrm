# -*- coding: utf-8 -*-

from importlib import import_module
from sanic import Sanic
from sanic.log import logger
from sanic.blueprints import Blueprint
from sanic.blueprint_group import BlueprintGroup
from sanic.response import json, raw
import asyncio
from sanic.kjson import kjson, json_dumps
from urllib.parse import urlencode

from utils.template import false_template
from mtkext.cors import CORS

app = Sanic(name="eros-crm-app-adaptation")
cors = CORS(app)


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
    ###
    # 连接适配册数据库
    from peewee_async import PooledMySQLDatabase, Manager
    from models import db_neocam_adapt
    db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
    db_neocam_adapt.initialize(db)
    app.mgr = Manager(db_neocam_adapt, loop=loop)
    ###
    # todo 集成omni
    from mtkext.clients.omni import OmniGateway
    app.omni = OmniGateway(app.http, args.OMNI_GATEWAY_URL)

    # if app.conf.WOA_TOKEN_CLIENT_URL: # 查询授权三方平台实例信息
    #     from mtkext.clients.token import TokenClient
    #     app.token = TokenClient(app.http, app.conf.WOA_TOKEN_CLIENT_URL)

    from clients.crm_clients import CrmClient
    app.crm_client = CrmClient(app.http, app.conf.CRM_CLIENT_URL)

    from clients.cam_clients import CamClient
    app.cam_client = CamClient(app.http, app.conf.CAM_CLIENT_URL)

    import aiojobs
    from utils.common import WXBaseFactory
    app.wxbase_factory = WXBaseFactory
    await init_all_woa_client(app)
    app.job = await aiojobs.create_scheduler()
    await app.job.spawn(init_all_woa_client(app, is_refresh=True))


async def init_all_woa_client(app, is_refresh = False):
    from biz import instance as instance_biz
    import socket
    try:
        if is_refresh:
            await asyncio.sleep(30)
        woa_instance = await instance_biz.get_instance_with_woa(app.mgr)
        for x in woa_instance:
            logger.info(f"init woa client: {x.auto_id}->{x.woa_appid}")
            try:
                woa_appid = x.woa_appid
                if is_refresh:
                    flag, data = await app.omni.fetch_token({
                        "appid": woa_appid, "from": socket.gethostname()})
                    if flag:
                        client = await app.wxbase_factory.get_client(woa_appid, app)
                        await client.updateTokens(data)
                    else:
                        logger.error(f"fetch_token: {woa_appid} {flag} {data}")
                else:
                    await app.wxbase_factory.get_client(woa_appid, app.http, app.conf.ACCESS_TOKEN_URL)
            except Exception as e:
                logger.exception(f"init woa client error with {e}")
        # todo 清除数据库中失效的woa appid
    except Exception as e:
        logger.exception(f"init woa client error with {e}")



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

WHITE_PATH = []


@app.middleware("request")
async def get_user_instance_info(request):
    from utils.const import RC
    from models import Instance
    from sanic import kjson
    from peewee import DoesNotExist
    app = request.app
    db = app.mgr
    path = request.path

    env = request.headers.get('X-EACH-ENV', 'wxminiapp').lower()
    request.ctx.member_no = ""
    if env == 'wechat': # woa登录
        user_info = request.ctx.session.get('user')
        if not user_info:
            return false_template(RC.NOT_LOGIN, '未登录')
        # [True, dict()]
        request.ctx.user_info = user_info
        request.ctx.unionid = user_info['unionid']
        request.ctx.openid = user_info['openid']
        request.ctx.appid = user_info['appid']


    elif env == 'wxminiapp': # 微信小程序登录
        if path not in WHITE_PATH:
            sessionId = request.headers.get("X-EACH-SESSION-ID")
            if not sessionId:
                return json(dict(code=-1, msg="please login"))
            ###
            omni = request.app.omni
            logger.info(f"headers: {request.headers}")
            flag, result = await omni.session_get_value({
                "sessionId": sessionId,
                "key": "SessionInfo,UserInfo",
            })
            logger.info(result)
            if not flag:
                return json(result)
            SessionInfo = result.get("SessionInfo")

            SessionInfo = kjson.json_loads(SessionInfo) if SessionInfo else {}
            UserInfo = result.get("UserInfo")
            UserInfo = kjson.json_loads(UserInfo) if UserInfo else {}
            unionid = SessionInfo.get("unionId") or UserInfo.get("unionId")
            openid = SessionInfo.get("openId") or UserInfo.get("openId")
            appid = SessionInfo.get("appId")
            #appid = "wx71031dea78e9d57b"
            #unionid = None
            #openid = "oGlFU5VKLq38ZXhbwoG-FlAFVyHE"
            request.ctx.appid = appid
            request.ctx.unionid = unionid
            request.ctx.openid = openid
    else:
        logger.error("登录失败")
        return false_template(RC.NOT_LOGIN, '未登录')
    if request.ctx.appid:
        appid = request.ctx.appid
        instance = None
        try:
            instance = await db.get(Instance.select().where(Instance.appid == appid))
        except DoesNotExist:
            pass
        if instance is None:
            return json(dict(code=RC.NOT_FOUND, msg="实例不存在"))
        request.ctx.instance_id = instance.instance_id
        request.ctx.crm_id = instance.crm_id
        request.ctx.mchid = instance.mchid
        request.ctx.woa_appid = instance.woa_appid
        unionid = request.ctx.unionid
        openid = request.ctx.openid
        flag, member_info = await app.crm_client.member.member_query({
            "unionid": unionid,
            "openid": openid,
            "appid": appid,
            "platform": "wechat", # crm注册平台
        },crm_id=instance.crm_id)
        if not flag:
            logger.info(f"用户非会员，unionid: {unionid}, openid: {openid}")
        else:
            member_no = member_info.get("info", {}).get("member_no")
            request.ctx.member_no = member_no
    else:
        logger.error("ctx no appid: %s", request.ctx)


@app.middleware('request')
async def record_request(request):
    if request.method == "POST":
        ctype = request.headers.get("Content-Type")
        if ctype and ctype.find("multipart") < 0 and request.body:
            logger.info(f'POST: {request.path} <== {request.body.decode(errors="replace")}')
    else:
        logger.info(f"{request.method}: {request.path}")
