#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/28
"""
from functools import wraps
from common.biz.crm import get_instance_info
from sanic.log import logger
from sanic.response import json
from common.biz.const import RC
from peewee import DoesNotExist


def safe_crm_instance(handle):
    async def wrapper(request, crm_id, **kwargs):
        try:
            data = await get_instance_info(request.app.mgr, request.app.redis, crm_id)
            logger.info(f'get_instance_info {data}')
            if not data:
                return json(dict(code=-1, msg=f"{crm_id} not find instance"))
            resp = await handle(request, crm_id, **kwargs)
            return resp
        except AssertionError as e:
            logger.exception(e)
            return json(dict(code=53001, msg=str(e)))
        except Exception as e:
            logger.exception(e)
            return json(dict(code=31999, msg=f"Error: {e}"))

    return wrapper


def except_decorator(f):
    """异常捕获的装饰器 方法里面不用写try except"""
    @wraps(f)
    async def decorated_function(request, *args, **kwargs):
        try:
            response = await f(request, *args, **kwargs)
            return response
        except DoesNotExist as ex:
            logger.exception(ex)
            return json(dict(code=RC.DATA_NOT_FOUND, msg="data not found"))
        except (AssertionError, KeyError, TypeError, ValueError) as ex:
            logger.exception(ex)
            return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
        except Exception as e:
            logger.exception(e)
            return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))
    return decorated_function
