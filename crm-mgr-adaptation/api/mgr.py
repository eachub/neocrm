import ujson

from biz.coupon import create_coupon, update_coupon, query_user_crm_coupon, update_card_stock
from sanic.response import HTTPResponse
from inspect import isawaitable
from biz.heads import *
from biz.const import RC
from utils.wrapper import check_instance
from biz.utils import get_by_list_or_comma, make_time_range, result_by_hour, result_by_day, masked_nickname

bp = Blueprint('bp_mgr', url_prefix="")

FILE_EXPORT = ['member/export', 'points/export']


@bp.post("/member/list")
@check_instance
async def api_member_querey(request):
    user_info = request.ctx.user_info
    sub_id = user_info.get("sub")
    is_masked = True
    if sub_id in ('7762812b-7e2d-4a9c-9dc1-8f350a086985', '4b2cd6b2-d785-4624-8440-313a3aae9210', '58f92408-938b-48c7-bd20-07ef8565e1eb', '0724d947-b552-4de4-b268-2cb49cadbbe3'):
        is_masked = False
    app = request.app
    crm_id = request.ctx.instance.get("crm_id")
    query_string = request.query_string
    path = f"/api/crm/mgr/member/{crm_id}/list"
    url = f"{app.conf.CRM_SERVER_URL}{path}?{query_string}"
    logger.info(url)
    headers = {}
    ctype = request.headers.get("Content-Type")
    if ctype: headers["Content-Type"] = ctype
    result = await app.http.request(url,
                                    method=request.method,
                                    data=request.body or None,
                                    headers=headers,
                                    )
    if not result:
        logger.info(f"{request.app.http.errinfo}")
        return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))
    # 对名称进行加密展示
    if is_masked:
        resp = ujson.loads(result.decode('utf-8'))
        data = resp.get("data", {})
        if type(data) is dict:
            items = data.get("items") or []
            for item in items:
                nickname = item.get("nickname")
                _nickname = masked_nickname(nickname)
                if _nickname: item['nickname'] = _nickname
            return json(resp)
    return raw(result, content_type="application/json")


# 3. 其余接口
@bp.route("/<concept:member|points|analyze|open>/<action:path>",
          methods=["GET", "POST"])
@check_instance
async def proxy_handle_request(request, concept, action):
    app = request.app
    crm_id = request.ctx.instance.get("crm_id")
    try:
        headers = {}
        ctype = request.headers.get("Content-Type")
        if ctype: headers["Content-Type"] = ctype
        logger.info(f"this crm_id={crm_id}")
        ###
        path = f"/api/crm/mgr/{concept}/{crm_id}/{action}"
        # path = request.path
        logger.info(f"this action is {action}")
        query_string = request.query_string
        url = f"{app.conf.CRM_SERVER_URL}{path}?{query_string}"
        logger.info(url)
        result = await app.http.request(url,
                                        method=request.method,
                                        data=request.body or None,
                                        headers=headers,
                                        )
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))

        if 'export' in action:
            # 获取header
            disposition_key = 'Content-Disposition'
            disposition = app.http.headers.get(disposition_key)
            headers = {
                "Content-Disposition": disposition,
                "Access-Control-Expose-Headers": disposition_key
            }

            # 获取content_type
            content_type = app.http.headers.get('Content-Type')
            return HTTPResponse(body=result, status=200, headers=headers, content_type=content_type)
        logger.info(f"{url} {result}")
        return raw(result, content_type="application/json")
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


@bp.get("/card/wx/statistical_points_detail")
@check_instance
async def wx_statistical_points_detail(request):
    """积分商城商家券统计-柱状图"""
    app = request.app
    try:
        crm_id = request.ctx.instance.get("crm_id")
        mch_id = request.ctx.instance.get("mch_id")
        headers = {}
        ctype = request.headers.get("Content-Type")
        if ctype: headers["Content-Type"] = ctype
        logger.info(f"this crm_id={crm_id}")

        obj = {k: v for k, v in request.query_args}
        begin_time = obj.get("begin_time")
        end_time = obj.get("end_time")
        if begin_time and end_time:
            begin_time = dateFromString(begin_time)
            end_time = dateFromString(end_time)
            obj['begin_time'], obj['end_time'] = make_time_range(begin_time, end_time)

        card_ids = get_by_list_or_comma(request.args, 'card_ids')

        path = f"/api/crm/mgr/card/{crm_id}/points_card/list"

        query_string = request.query_string
        url = f"{app.conf.CRM_SERVER_URL}{path}?{query_string}&source=2"
        logger.info(url)
        result = await app.http.request(url, method=request.method, data=request.body or None, headers=headers,
                                        parse_with_json=True)
        logger.info(result)
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))

        card_list = result.get('data')
        if not card_ids:
            card_ids = [x.get('card_id') for x in card_list]
            if not card_ids:
                return json(dict(code=RC.OK, msg="ok", data={}))

        omni = request.app.omni
        _obj = {"obj": obj, "mchid": mch_id}

        result_list = []
        for card_id in card_ids:
            obj.update(card_id=card_id)
            flag, result = await omni.wxpay_coupon_statistical_time(obj, mch_id)
            if flag:
                result_list.append((card_id, result))

        total_receive_cards = total_receive_cards_user = total_redeem_cards = total_redeem_cards_user = 0
        results = []
        for card_id, result in result_list:
            result['card_id'] = card_id
            result['title'] = next((x.get('title') for x in card_list if x.get('card_id') == card_id), "卡券")
            total_receive_cards += sum(result.get('receive_cards'))
            total_receive_cards_user += sum(result.get('receive_cards_user'))
            total_redeem_cards += sum(result.get('redeem_cards'))
            total_redeem_cards_user += sum(result.get('redeem_cards_user'))
            results.append(result)

        data = dict(total_receive_cards=total_receive_cards, total_receive_cards_user=total_receive_cards_user,
                    total_redeem_cards=total_redeem_cards, total_redeem_cards_user=total_redeem_cards_user,
                    result_list=results)
        return json(dict(code=RC.OK, msg="ok", data=data))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.get("/card/wx/<action>")
@check_instance
async def wx_points_statistical(request, action):
    """积分商城商家券统计-总计/趋势/top"""
    app = request.app
    try:
        crm_id = request.ctx.instance.get("crm_id")
        mch_id = request.ctx.instance.get("mch_id")
        headers = {}
        ctype = request.headers.get("Content-Type")
        if ctype: headers["Content-Type"] = ctype
        logger.info(f"this crm_id={crm_id}")

        path = f"/api/crm/mgr/card/{crm_id}/points_card/list"

        query_string = request.query_string
        url = f"{app.conf.CRM_SERVER_URL}{path}?{query_string}&source=2"
        logger.info(url)
        result = await app.http.request(url, method=request.method, data=request.body or None, headers=headers,
                                        parse_with_json=True)
        logger.info(result)
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))

        obj = {k: v for k, v in request.query_args}
        begin_time = obj.get("begin_time")
        end_time = obj.get("end_time")

        card_ids = [x.get('card_id') for x in result.get('data')]
        if not card_ids:
            result = {}
            if action == 'statistical_points_total':  # 总计
                result = {"total_receive_user": 0, "total_receive_count": 0,
                          "total_redeem_user": 0, "total_redeem_count": 0}
            elif action == 'statistical_points_type':  # 趋势
                begin_time = dateFromString(begin_time)
                end_time = dateFromString(end_time)
                key_list = ["receive_cards", "receive_cards_user", "redeem_cards", "redeem_cards_user"]
                if (end_time - begin_time).days < 2:
                    result = result_by_hour([], begin_time, end_time, key_list)
                else:
                    result = result_by_day([], begin_time, end_time, key_list)
            elif action == 'statistical_points_top':  # top
                result = []

            return json(dict(code=RC.OK, msg="ok", data=result))

        obj['card_ids'] = card_ids
        ###
        omni = request.app.omni
        _obj = {"obj": obj, "mchid": mch_id}

        if action == 'statistical_points_total':    # 总计
            action = 'wxpay_coupon_statistical_total'
        elif action == 'statistical_points_type':   # 趋势
            action = 'wxpay_coupon_statistical_time'
        elif action == 'statistical_points_top':    # top
            action = 'wxpay_coupon_statistical_top'
        else:
            return json(dict(code=RC.PARAMS_INVALID, msg="参数错误", data=None))

        flag, result = True, getattr(omni, action)(**_obj)
        if isawaitable(result): flag, result = await result
        ###
        if flag:
            resp = dict(result=result) if type(result) in (str, int, float) else result
            return json(dict(code=RC.OK, msg="ok", data=resp))
        msg = result if type(result) == str else result.get("errmsg", "处理错误")
        return json(dict(code=RC.HANDLER_ERROR, msg=msg))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{str(ex)}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 3. 自建卡券代理接口
@bp.route("/card/<action:path>", methods=["GET", "POST"])
@check_instance
async def card_proxy_request(request, action):
    app = request.app
    try:
        headers = {}
        ctype = request.headers.get("Content-Type")
        if ctype: headers["Content-Type"] = ctype
        crm_id = request.ctx.instance.get("crm_id")
        mch_id = request.ctx.instance.get("mch_id")
        app_id = request.ctx.instance.get("app_id")
        _path = f"/api/crm/mgr/card/{crm_id}/{action}"
        query_string = request.query_string
        request_body = None
        if action == "create" and request.method == "POST":
            request_body = await create_coupon(app.omni, mch_id, app_id, request.json)
        elif action == "update" and request.method == "POST":
            request_body = await update_coupon(app.omni, mch_id, app_id, request.json)
        elif action == "add_stock" and request.method == "POST":
            request_body = request.json
            if request.json.get("source") == 2:
                status, data = await update_card_stock(app.omni, request.ctx.instance, request.json, app.http, app.conf.CRM_SERVER_URL)
                if not status:
                    return json(data)
                request_body['quantity'] = data

        elif action == "get_member_coupon_list" and request.method == "GET":
            status, query_string = await query_user_crm_coupon(query_string, request.args, request.app.client_crm, crm_id)
            if not status:
                return json(dict(code=RC.OK, msg="ok", data={"coupon_list": []}))
        else:
            request_body = request.json
        url = f"{app.conf.CRM_SERVER_URL}{_path}?{query_string}"
        logger.info(url)
        result = await app.http.request(url, method=request.method, parse_with_json=True, json=request_body, headers=headers)
        if not result:
            logger.info(f"{request.app.http.errinfo}")
            return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))
        logger.info(f"{url} {result}")
        return json(result)
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))


# 4. 查询实例信息
@bp.route("/info/detail", methods=["GET"])
@check_instance
async def info_detail(request):
    try:
        instance = request.ctx.instance
        return json(dict(code=RC.OK, data=instance))
    except AssertionError as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障，请稍后重试"))
