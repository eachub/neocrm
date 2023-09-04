from sanic import Blueprint
from sanic.log import logger
from common.utils.const import *
from biz.people_parse import file_upload_api
from sanic.response import json
from peewee import DoesNotExist
from common.models.cam import PeopleFile,model_to_dict

bp = Blueprint("people", url_prefix="/people")


@bp.post("/<instance_id>/file_upload")
async def file_upload(request, instance_id):
    try:
        files = request.files
        assert files, "文件参数缺失"
        params = request.form
        file_type = int(params.get("type"))
        assert file_type in [1, 2], "type参数异常"
        params = {"files": files, "type": file_type, "instance_id": instance_id}
        flag, result = await file_upload_api(request.app, params)
        if flag:
            return json(dict(**result, code=RC.OK, msg="ok",))
        else:
            return json(dict(**result, code=RC.PARAMS_INVALID, msg="上传人群包失败",))
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e)))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试"))


@bp.get("/<instance_id>/file_fetch")
async def people_fetch(request, instance_id):
    people_id = int(request.args.get("people_id"))
    try:
        assert people_id, "缺少people_id参数"
        app = request.app
        one = await app.mgr.get(PeopleFile, auto_id=people_id, instance_id=instance_id)
        excluded = [PeopleFile.instance_id]
        one = model_to_dict(one, exclude=excluded)
        return json(dict(code=RC.OK, msg="ok", data=one))
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except DoesNotExist as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"找不到文件：{people_id}"))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


