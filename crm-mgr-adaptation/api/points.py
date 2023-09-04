from biz.const import RC
from biz.heads import *
from biz.utils import gen_event_no
from utils.wrapper import check_instance

bp = Blueprint('bp_adapt_points', url_prefix="/adapt/points")


@bp.post('/change_points')
@check_instance
async def api_change_user_points(request):
    """后台手动修改积分"""
    app = request.app
    params_dict = request.json
    crm_id = request.ctx.instance.get("crm_id")
    member_no = params_dict.get("member_no")
    points = params_dict.get("points")
    type = params_dict.get("type")  # produce consume
    operator = params_dict.get("operator")
    expire_days = params_dict.get("expire_days")
    assert type in ("produce", "consume"), "event_type 参数错误或缺失"

    ###
    event_no = gen_event_no("CRM")
    if type == "produce":
        req_obj = dict(member_no=member_no, event_no=event_no, event_type="event", operator=operator,
                       points=points, expire_days=expire_days, event_desc="crm后台增加积分")
        flag, result = await app.client_crm.points.produce_direct(req_obj, crm_id=crm_id, method='POST')
    else:
        req_obj = dict(member_no=member_no, event_no=event_no, points=points, operator=operator, event_desc="crm后台减少积分")
        flag, result = await app.client_crm.points.consume_direct(req_obj, crm_id=crm_id, method='POST')
    if flag:
        result = dict(code=RC.OK, msg="修改成功")
    return json(result)
