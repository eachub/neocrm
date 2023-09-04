# -*- coding: utf-8 -*-
"""
@Time    : 2021/9/22 11:07 上午
@Author  : huanghuang
"""
from peewee import DoesNotExist
from peewee_async import Manager

from common.models.base import CRMModel
from mtkext.db import peewee_normalize_dict

from common.models.helper import _query_by_key_id


async def init_new_crm(db, instance_id, **kwargs):
    d = dict(instance_id=instance_id, **kwargs)
    _d = peewee_normalize_dict(CRMModel, d)
    return await db.execute(CRMModel.insert(d).on_conflict_ignore())

async def query_crm_info(mgr,**kwargs):
    """获取所有的crm_info信息"""
    excluded = [CRMModel.auto_id, CRMModel.create_time]
    return await _query_by_key_id(mgr, excluded, CRMModel, kwargs)

async def get_instance_by_crm_id(db: Manager, crm_id):
    try:
        return await db.get(CRMModel.select().where(CRMModel.crm_id == crm_id))
    except DoesNotExist:
        return None


# 获取当前有设置tmall或者jd salt的实例
async def get_instances(db):
    w = [(CRMModel.jd_salt.is_null(False)) | (CRMModel.salt.is_null(False))]
    q = CRMModel.select().where(*w)
    return await db.execute(q.dicts())


