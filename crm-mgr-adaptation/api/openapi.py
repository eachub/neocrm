#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy

from sanic import Blueprint
from sanic.log import logger
from sanic.response import json

from biz.const import RC
from utils.wrapper import check_instance
from models import MaterialApply

bp = Blueprint('bp_inner', url_prefix="/inner")

# 1. 处理审批通知
@bp.post("/<instance_id>/apply")
async def material_apply(request, instance_id):
    obj = request.json
    third_no = obj.get("third_no")
#    instance_id = obj.get("instance_id")
    status = obj.get("status")
    try:
        assert instance_id, "instance_id参数错误"
        assert third_no, "third_no参数错误"
        assert status, "status参数错误"
        app = request.app

        await app.mgr.execute(
            MaterialApply.update(apply_status=status)\
                .where(MaterialApply.third_no == third_no,
                       MaterialApply.instance_id == instance_id))

        if status == "2":
            applies = await app.mgr.execute(MaterialApply.select()\
                .where(MaterialApply.third_no == third_no, MaterialApply.instance_id == instance_id))
            for row in applies:
                res = await app.client_cms.material.publish(\
                    dict(material_no=row.material_no,status=1), instance_id=instance_id)
                logger.info(f"material publish result: {res}")
        return json(dict(code=RC.OK, msg="ok"))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))
