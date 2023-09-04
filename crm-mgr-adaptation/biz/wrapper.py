#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/28
"""
from functools import wraps
from sanic.log import logger
from sanic.response import json
from biz.const import RC


def except_decorator(f):
    """异常捕获的装饰器 方法里面不用写try except"""

    @wraps(f)
    async def decorated_function(request, *args, **kwargs):
        try:
            response = await f(request, *args, **kwargs)
            return response
        except (AssertionError, KeyError, TypeError, ValueError) as ex:
            logger.exception(ex)
            return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
        except Exception as e:
            logger.exception(e)
            return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))

    return decorated_function
