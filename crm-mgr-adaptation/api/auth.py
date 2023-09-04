import datetime
from sanic import Blueprint
from sanic.request import Request
from sanic.response import json, html, redirect
from sanic.log import logger
from biz.const import RC
from utils.wrapper import check_instance

bp = Blueprint(name="mgr_user", url_prefix="/auth")

@bp.get("/login/callback")
async def user_login_callback(request: Request):
    # 登陆之后的回调
    try:
        args = request.args
        logger.info(f"登陆回调:{args}")
        code = args.get("code")
        state = args.get("state")
        assert code, "缺失参数:code"
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=f'参数错误: {str(e)}'))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.PARAMS_INVALID, msg='参数错误'))
    kc = request.app.kc
    redis = request.app.redis

    try:
        success, res = await kc.fetch_token_by_code(code)
        logger.info(f"根据code获取token:{success} {res}")
        if not success:
            return html("<h2>登陆异常，请稍后重试..</h2>")
        key = res.get("access_token")
        key = f"SSO:{key}"
        value = f"{key}:::{res.get('refresh_token')}"
        # res={"access_token": "", "refresh_token": "", "refresh_expire_in": ""}
        logger.info(f"set redis: {key}")
        await redis.setex(key, int(res['refresh_expires_in']) - 30, value)
        home = request.app.conf.HOME_PATH
        resp = redirect(f"{home}?access_token={res['access_token']}")
        return resp
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=f'参数错误: {str(e)}'))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg='服务器内部错误'))


@bp.post("/logout")
@check_instance
async def user_logout(request: Request):
    kc = request.app.kc
    try:
        await kc.logout(request.ctx.token_info["refresh_token"])
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg='服务器内部错误'))
    return json(dict(code=RC.OK, msg="登出成功"))





@bp.get("/center")
@check_instance
async def user_center(request: Request):
#     """
#         {
#             'sub': '55774c04-3dac-463f-901d-7e655a0bb00e',
#             'resource_access': {
#                 'OCP-EC': {
#                     'roles': ['超级管理员']
#                 },
#                 'account': {
#                     'roles': ['manage-account', 'manage-account-links', 'view-profile']
#                 }
#             },
#             'email_verified': False,
#             'instance_name': ['积分乐园'],
#             'realm_access': {
#                 'roles': ['offline_access', 'uma_authorization', 'default-roles-ocp']
#             },
#             'name': '黄',
#             'preferred_username': 'huanghuang',
#             'given_name': '',
#             'locale': 'zh-CN',
#             'family_name': '黄',
#             'email': '2409561687@qq.com'
#             }
#     """
     conf = request.app.conf
     role_key = getattr(conf, "ROLE_KEY", "CRM")
     user_info = request.ctx.user_info
     format_user_info = {}
     format_user_info["user_id"] = user_info.get("sub")
     format_user_info["nickname"] = user_info.get("given_name")
     format_user_info["instance_id"] = request.ctx.instance_id
     format_user_info["email"] = user_info.get("email")
     role = user_info.get("resource_access", {}).get(role_key, {}).get("roles")
     format_user_info["role"] = role
     return json(dict(code=RC.OK, msg="ok", data=format_user_info))
