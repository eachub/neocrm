import ujson

from common.biz.const import RC
from common.models.base import *
from common.biz.heads import *
from common.biz.wrapper import except_decorator
from biz.crm import *
from common.models.ecom import ProductMain

bp = Blueprint('bp_points_crm', url_prefix="")


@bp.get("/<crm_id>/info")
async def api_instance_info(request, crm_id):
    try:
        app = request.app
        
        one = await app.get(CRMModel, crm_id=crm_id)
        exclude=[CRMModel.jd_salt, CRMModel.salt, CRMModel.member_code_rule]
        result = model_to_dict(one, exclude=exclude)
        return json(dict(code=RC.OK, msg="OK", data=result))
    except DoesNotExist:
        return json(dict(code=RC.DATA_NOT_FOUND, msg="crm实例不存在"))
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


def res_ok(code=RC.OK, msg="ok", data='', **kwargs):
    return json(dict(code=code, msg=msg, data=data))


def res_ng(code=RC.PARAMS_INVALID, msg='', data='', **kwargs):
    return json(dict(code=code, msg=msg, data=data))


def check_params(r_k, o_k, params):
    l_k, r_k_v, o_k_v = [], {}, {}
    for k in r_k:
        v = params.get(k, None)
        if v is not None:
            r_k_v[k] = v
        else:
            l_k.append(k)
    assert not l_k, f"{','.join(l_k)}参数缺失"
    o_k_v = {k: params.get(k) for k in o_k if params.get(k) is not None}
    o_k_v.update(r_k_v)
    return o_k_v


async def update_product_main_api(app, params):
    db = app.db
    is_last = params.get("is_last")
    version = params.get("version")
    items = params.get("items")
    await db.execute(ProductMain.replace_many(items))
    if is_last:
        await db.execute(ProductMain.update(removed=1).where(ProductMain.version != version))
    return 1, dict()


@bp.post("/update_product_main")
async def update_product_main(request):
    try:
        params = request.json
        r_k = ["is_last", "version", "items"]
        params = check_params(r_k, [], params)
        flag, result = await update_product_main_api(request.app, params)
        return res_ok(**result) if flag else res_ng(**result)
    except AssertionError as e:
        return res_ng(code=RC.PARAMS_INVALID, msg=str(e))
    except Exception as e:
        logger.exception(e)
        return res_ng(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试")