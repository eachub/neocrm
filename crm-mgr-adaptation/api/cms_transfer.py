#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy

from sanic import Blueprint
from sanic.log import logger
from sanic.response import json, stream, raw

import os
import aiofiles

from biz.const import RC
from utils.wrapper import check_instance, check_wxwork_instance
from models import MaterialApply
from mtkext.guid import fast_guid
from urllib.parse import urlencode

bp = Blueprint('bp_material_transfer', url_prefix="/cms")


@bp.route("/<concept>/<action>", methods=["GET", "POST"])
@check_instance
async def proxy_handle_request(request, concept, action):
    try:
        logger.info(f'素材管理转发 concept: {concept} action: {action}')
        app = request.app

        transfer_headers = copy.deepcopy(request.headers)
        transfer_headers["appid"] = request.ctx.instance.get("woa_app_id", "")
        transfer_headers["corp_id"] = request.ctx.instance.get("corp_id", "")
        logger.info(f"transfer_headers: {transfer_headers}")
        method_proxy = app.cms_transfer.method_proxy(concept, action)
        if method_proxy:
            logger.info("use method proxy")
            headers = {}
            headers["appid"] = request.ctx.instance.get("woa_app_id", "")
            headers["corp_id"] = request.ctx.instance.get("corp_id", "")
            flag, result = await app.cms_transfer.execute(method_proxy, request, headers=headers)
            if not flag: return json(result)
            return json(dict(code=RC.OK, msg="ok", data=result))

        # 如果自定义了路径，从这里获取cms中真实路径
        mapping_path = app.cms_transfer.get_mapping_path(concept, action, request.ctx.instance_id)

        # 组装路径，并发送请求
        conf = request.app.conf
        query_string = request.query_string
        cms_conf = conf.CMS_CLIENT
        url = f"{cms_conf['host']}{cms_conf['prefix']}/{mapping_path}?{query_string}"
        logger.info(f'cms转发url:{url}')

        result = await app.http.request(url, method=request.method, data=request.body or None, parse_with_json=True,
                                        headers=transfer_headers, timeout=180)
        logger.info(f"素材转发结果: {url} {result}")
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))
        return json(result)

    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.route("/apply/create", methods=["POST"])
@check_instance
async def apply_create(request):
    try:
        app = request.app
        third_no = fast_guid()
        material_nos = request.json.get("material_nos")
        remark = request.json.get("remark")
        assert material_nos, "必须传递material_nos字段"
        rows = await app.mgr.execute(MaterialApply.select()
                                     .where(MaterialApply.material_no.in_(material_nos),
                                            MaterialApply.apply_status.in_([1,2])))
        for x in rows:
            logger.error(f"素材已经在审批处理，{x}")
            return json(dict(code=RC.PARAMS_INVALID, msg=f"素材({x.material_no})已经在审批处理，提交失败。"))

        await app.mgr.execute(MaterialApply.update(third_no=third_no).where(MaterialApply.material_no.in_(material_nos)))

        remark = urlencode({"remark":remark})
        corp_id = request.ctx.instance.get("corp_id","")
        url = app.conf.APPLY_URL + f"&third_no={third_no}&{remark}&corp_id={corp_id}"
        logger.info(f"apply url: {url}")
        buf = app.codeFactory.makeStream(url)
        instance_id = request.ctx.instance_id
        # headers = {"content-type": "image/png", "content-length": len(buf)}
        base = app.conf.UPLOAD_DIR
        dirs = f"{base}/cms/apply/qrcode/{instance_id}"
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        fname = f"{third_no}.jpg"
        path = f"{dirs}/{fname}"
        sim_path = f"/cms/apply/qrcode/{instance_id}/{fname}"
        async with aiofiles.open(path, mode='wb') as fp:
            await fp.write(buf)
        return json(dict(code=RC.OK, msg="ok", data={"path": sim_path}))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))



@bp.route("/apply/search", methods=["GET"])
@check_instance
async def apply_search(request):
    try:
        app = request.app
        page_id = int(request.args.get("page_id", 1))
        assert page_id > 0, "page_id从1开始"
        page_size = int(request.args.get("page_size", 20))
        assert 1 < page_size <= 500, "page_size不能小于2或超过500"

        instance_id = request.ctx.instance_id
        third_no = request.args.get("third_no")
        if third_no:
            where = [
                MaterialApply.third_no == third_no,
                MaterialApply.instance_id == instance_id,
            ]
        else:
            where = [
                MaterialApply.apply_status == 0,
                MaterialApply.instance_id == instance_id,
                ]
        where.append(MaterialApply.removed == 0)
        query = MaterialApply.select().where(*where)
        total = await request.app.mgr.count(query)
        rows = await app.mgr.execute(query.paginate(page_id, page_size))
        instance_id = None
        material_nos = []
        for x in rows:
            material_nos.append(x.material_no)
            instance_id = x.instance_id
        # material_nos = [ x.material_no for x in rows ]
        flag, result = await app.client_cms.material.search(obj={
            "page_size": 500,
            "material_nos": material_nos,
            },instance_id=instance_id)
        material_dict = {}
        if flag and result:
            for x in result.get("material_list"):
                material_dict[x["material_no"]] = x

        _result = []
        for x in rows:
            material_no = x.material_no
            material = material_dict.get(material_no)
            if material:
                material["apply_status"] = x.apply_status
                material["third_no"] = x.third_no
                _result.append(material)
        return json(dict(code=RC.OK, msg="ok", data=dict(list=_result, total=total)))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.route("/apply/task", methods=["POST"])
@check_wxwork_instance
async def apply_task(request):
    try:
        app = request.app

        instance_id = request.ctx.instance_id
        third_no = request.json.get("third_no")
        assert third_no, "third_no必须传"
        where = [
            MaterialApply.third_no == third_no,
            MaterialApply.instance_id == instance_id,
        ]

        rows = await app.mgr.execute(MaterialApply.select()
                                     .where(*where))
        material_nos = []
        for x in rows:
            material_nos.append(x.material_no)
        flag, result = await app.client_cms.material.search(obj={
            "page_size": 500,
            "material_nos": material_nos,
            },instance_id=instance_id)
        material_dict = {}
        if flag and result:
            for x in result.get("material_list"):
                material_dict[x["material_no"]] = x

        _result = []
        for x in rows:
            material_no = x.material_no
            material = material_dict.get(material_no)
            if material:
                material["apply_status"] = x.apply_status
                material["third_no"] = x.third_no
                _result.append(material)
        return json(dict(code=RC.OK, msg="ok", data=_result))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))



PATH_DICT = {

}


class CMSTransfer(object):
    def __init__(self, app):
        self.app = app
        self.mgr = app.mgr
        self.redis = app.redis

    def method_proxy(self, concept, action):
        attr_name = f"_{concept}_{action}"
        if hasattr(self, attr_name):
            appender = getattr(self, attr_name)
            return appender
        return None

    async def execute(self, appender, request, **kwargs):
        adt = {}
        if appender: adt = await appender(request, **kwargs)
        return adt

    async def _todo_method(self, request, **kwargs):
        return True, dict(code=0, msg='可扩展方法')


    async def _material_search(self, request, **kwargs):
        app = request.app
        instance_id = request.ctx.instance_id
        flag, result = await app.client_cms.material.search(obj=request.args,
                                                       instance_id=instance_id, **kwargs)
        if flag and result:
            mnos = [ x.get("material_no") for x in result.get("material_list")]
            m_apply_status = await app.mgr.execute(MaterialApply.select().where( MaterialApply.material_no.in_(mnos)))
            mstatus = dict()
            for row in m_apply_status:
                mstatus[row.material_no] = row.apply_status
            for x in result.get("material_list"):
                x["apply_status"] = mstatus.get(x.get("material_no"), 0)

        return True, result


    async def _material_update(self, request, **kwargs):
        app = request.app
        instance_id = request.ctx.instance_id
        material_no = request.json.get("material_no")
        rows = await app.mgr.execute(MaterialApply.select()\
                                     .where(MaterialApply.material_no==material_no,
                                            MaterialApply.apply_status.in_([1,2]) )
                                     )
        for x in rows:
            logger.warning(f"素材审批状态错误，更新失败, {x}")
            return False, {"code": RC.FORBIDDEN, "msg": "非待审批状态，禁止操作"}
        logger.info(f"素材审批 update json={request.json}")
        obj = dict(request.json)
        flag, result = await app.client_cms.material.update(obj=obj,
                                                       instance_id=instance_id, **kwargs)
        _obj = {
            "instance_id": instance_id,
            "material_no": material_no,
            "apply_status": 0,
        }
        await app.mgr.execute(MaterialApply.insert(_obj).on_conflict(update=_obj))
        return flag, result


    async def _material_upload(self, request, **kwargs):
        app = request.app
        instance_id = request.ctx.instance_id

        flag, result = await app.client_cms.material.upload(obj=request.json,
                                                       instance_id=instance_id, **kwargs)
        if result.get("material_type") in [7,8,9] :
            material_no = result.get("material_no")
            _obj = {
                "instance_id": instance_id,
                "material_no": material_no,
                "apply_status": 0,
            }
            await app.mgr.execute(MaterialApply.insert(_obj).on_conflict(update=_obj))
        return flag, result


    async def _material_remove(self, request, **kwargs):
        app = request.app
        instance_id = request.ctx.instance_id
        material_nos = request.json.get("material_nos")
        rows = await app.mgr.execute(MaterialApply.select()\
                                     .where(MaterialApply.material_no.in_(material_nos), MaterialApply.apply_status.in_([1,2]) ))
        for x in rows:
            logger.warning(f"素材审批状态错误，更新失败, {x}")
            return False, {"code": RC.FORBIDDEN, "msg": "非待审批状态，禁止操作"}

        flag, result = await app.client_cms.material.remove(obj=request.json,
                                                       instance_id=instance_id, **kwargs)
        # _obj = {
        #     "instance_id": instance_id,
        #     "material_no": material_no,
        #     "apply_status": 0,
        # }
        await app.mgr.execute(MaterialApply.update(removed=1)
                              .where(MaterialApply.material_no.in_(material_nos), MaterialApply.apply_status == 0,
                                     MaterialApply.instance_id == instance_id))
        return flag, result

    def get_mapping_path(self, concept, action, instance_id):
        path = f'{concept}/{instance_id}/{action}'
        return PATH_DICT.get(path, path)
