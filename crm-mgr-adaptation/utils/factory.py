from datetime import datetime, date

from peewee import DoesNotExist
from sanic.kjson import json_loads

# 获取的数据列表，转化为list
from urllib.parse import urlencode
from mtkext.wx.wxbase import WxBaseApi
from sanic.log import logger
import asyncio

class WXBaseFactory:
    _factory = {}

    @classmethod
    async def get_client(cls, appid, hcp, url_token):
        """
        根据appid获取wxbase client
        app主要是需要获取http client
        """
        client = cls._factory.get(appid)
        if client is None:
            # 创建客户端
            client = WxBaseApi(hcp, appid, url_token=url_token)
            # 刷新token
            await client.updateTokens()
            cls._factory[appid] = client
        return client

from datetime import datetime, date

from peewee import DoesNotExist
from sanic.kjson import json_loads

# 获取的数据列表，转化为list
from urllib.parse import urlencode

from sanic.log import logger


class WXBaseFactory:
    _factory = {}

    @classmethod
    async def get_client(cls, appid, hcp, url_token):
        """
        根据appid获取wxbase client
        app主要是需要获取http client
        """
        client = cls._factory.get(appid)
        if client is None:
            # 创建客户端
            client = WxBaseApi(hcp, appid, url_token=url_token)
            # 刷新token
            await client.updateTokens()
            cls._factory[appid] = client
        return client

async def init_all_woa_client(app, get_all_instance, is_refresh = False):
    import socket
    try:
        if is_refresh:
            await asyncio.sleep(30)
        logger.info(f"init_all_woa_client is_refresh: {is_refresh}")
        woa_instance = await get_all_instance()
        for woa_appid in woa_instance:
            logger.info(f"init woa client: {woa_appid}")
            try:
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
