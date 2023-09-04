from sanic.response import json
from sanic.log import logger
from utils.const import RC


def true_template(data, code=0):
    response = {
        'code': code,
        'data': data,
        'msg': '处理成功'
    }
    return json(response)


def false_template(code, msg):
    response = {
        'code': code,
        'msg': msg
    }
    return json(response)
