from sanic import Blueprint

import ujson

from common.biz.const import RC
from common.models.base import *
from common.biz.heads import *
from common.biz.wrapper import except_decorator
from biz.crm import *
from common.models.ecom import SkuInfo, GoodsInfo

bp = Blueprint('bp_open_mgr', url_prefix="/open")


@bp.post("/<crm_id>/goods_list")
@except_decorator
async def api_goods_list(request, crm_id):
    params = request.json or {}
    keyword = params.get("keyword")
    page_id = params.get("page_id") or 1
    page_size = params.get("page_size") or 50
    app = request.app
    model = SkuInfo
    where = [model.removed == False]
    if keyword:
        where.append(GoodsInfo.goods_name.like(keyword))

    query_sql = model.select(
        model.outer_sku_code.alias("sku_code"), GoodsInfo.goods_name, model.spec_value_1,
        model.spec_value_2, model.goods_id
    ).join(GoodsInfo, on=(GoodsInfo.goods_id == model.goods_id)).where(model.removed == False)
    total = await app.mgr.count(query_sql)
    items = await app.mgr.execute(query_sql.paginate(int(page_id), int(page_size)).dicts())

    return json(dict(code=RC.OK, msg="OK", data=dict(items=items, total=total)))