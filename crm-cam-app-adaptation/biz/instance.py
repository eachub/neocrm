# -*- coding: utf-8 -*-
"""
@Time    : 2021/9/6 8:28 下午
@Author  : huanghuang
"""
from peewee import DoesNotExist

from models import Instance


async def get_instance_by_appid(db, appid):
    try:
        return await db.get(Instance.select().where(Instance.appid == appid))
    except DoesNotExist:
        return None


async def get_instance_with_woa(db):
    try:
        return await db.execute(Instance.select().where(Instance.woa_appid.is_null(False)))
    except DoesNotExist:
        return None



