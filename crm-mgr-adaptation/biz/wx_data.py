import os
from io import BytesIO
from urllib.parse import urlencode
import aiofiles
from sanic.kjson import json_dumps, json_loads
from sanic.log import logger


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
