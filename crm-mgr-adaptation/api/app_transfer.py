# app端的接口转发
import ujson
from sanic.response import HTTPResponse

from biz.heads import *
from biz.const import RC
from biz.utils import masked_nickname
from utils.wrapper import check_instance

bp = Blueprint('bp_app', url_prefix="/app")


@bp.post("/member/member_query")
@check_instance
async def api_member_querey(request):
    user_info = request.ctx.user_info
    sub_id = user_info.get("sub")
    is_masked = True
    if sub_id in ('7762812b-7e2d-4a9c-9dc1-8f350a086985', '4b2cd6b2-d785-4624-8440-313a3aae9210', '58f92408-938b-48c7-bd20-07ef8565e1eb', '0724d947-b552-4de4-b268-2cb49cadbbe3'):
        data = request.json or dict()
        data['plained'] = 1
        body = ujson.dumps(data)
        body = body.encode('utf-8')
        is_masked = False
    else:
        body = request.body

    app = request.app
    crm_id = request.ctx.instance.get("crm_id")
    query_string = request.query_string
    path = f"/api/crm/member/{crm_id}/member_query"
    url = f"{app.conf.CRM_APP_SERVER_URL}{path}?{query_string}"
    logger.info(url)
    headers = {}
    ctype = request.headers.get("Content-Type")
    if ctype: headers["Content-Type"] = ctype
    result = await app.http.request(url,
                                    method=request.method,
                                    data=body or None,
                                    headers=headers,
                                    )
    if not result:
        logger.info(f"{request.app.http.errinfo}")
        return json(dict(code=RC.INTERNAL_ERROR, msg="网络错误"))
    if is_masked:
        resp = ujson.loads(result.decode("utf-8"))
        data = resp.get("data", {})
        if type(data) is dict:
            #
            familys = data.get("family") or []
            for family in familys:
                nickname = family.get("nickname")
                _nickname = masked_nickname(nickname)
                if _nickname:
                    family['nickname'] = _nickname
            #
            info = data.get("info") or {}
            nickname = info.get("nickname")
            _nickname = masked_nickname(nickname)
            if _nickname:
                info['nickname'] = _nickname
            #
            we_info = data.get("wechat_member_info") or {}
            nickname = we_info.get("nickname")
            _nickname = masked_nickname(nickname)
            if _nickname:
                we_info['nickname'] = _nickname
            return json(resp)
    return raw(result, content_type="application/json")


@bp.route("/<concept:member|points|analyze|card>/<action:path>",
          methods=["GET", "POST"])
@check_instance
async def proxy_handle_request(request, concept, action):
    app = request.app
    crm_id = request.ctx.instance.get("crm_id")
    try:
        headers = {}
        ctype = request.headers.get("Content-Type")
        if ctype: headers["Content-Type"] = ctype
        ###
        path = f"/api/crm/{concept}/{crm_id}/{action}"
        logger.info(f"this action is {action}")
        query_string = request.query_string
        url = f"{app.conf.CRM_APP_SERVER_URL}{path}?{query_string}"
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
