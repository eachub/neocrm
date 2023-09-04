from datetime import datetime, date

from peewee import DoesNotExist
from sanic.kjson import json_loads

# 获取的数据列表，转化为list
from urllib.parse import urlencode

from sanic.log import logger
from mtkext.wx import WxBaseApi


class WXBaseFactory:
    _factory = {}

    @classmethod
    async def get_client(cls, appid, hcp, url_token):
        """
        根据appid获取wxbase client
        app主要是需要获取http client
        """
        if not appid:
            return None
        client = cls._factory.get(appid)
        if client is None:
            # 创建客户端
            client = WxBaseApi(hcp, appid, url_token=url_token)
            # 刷新token
            await client.updateTokens()
            cls._factory[appid] = client
        logger.info(f"wxbase factory get client: {appid} {client}")
        return client


def models_to_dict_list(models, is_fetch_one=False):
    dict_list = []
    for item in models:
        for k, v in item.items():
            if isinstance(v, bool):
                item[k] = int(v)
            elif isinstance(v, datetime):
                item[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(v, date):
                item[k] = v.strftime('%Y-%m-%d')
        dict_list.append(item)
    if is_fetch_one and dict_list: return dict_list[0]
    return dict_list


async def do_request(app, path, obj=None, method="POST", **kwargs):
    conf = app.conf
    http = app.http
    host = conf.WX_DATA_HOST
    env = 'prod' if app.cmd_args.env == "prod" else "trial"
    url = f"{host}/{env}/{path}"
    kwargs.update(parse_with_json=False)
    if method == "POST":
        result = await http.post(url, obj, **kwargs)
    else:
        if obj:
            url += "&" if "?" in url else "?" + urlencode(obj)
        result = await http.get(url, **kwargs)
    ###
    if result is None:
        return False, http.errinfo
    result = json_loads(result)
    return result.get('code', 0) == 0, result, url, obj




def is_number(s):
    try:
        float(s)
        return True
    except Exception as e1:
        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except Exception as e2:
            exception = f'{e1},{e2}'
    return False
