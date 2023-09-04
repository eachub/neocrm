from models import InstanceInfo
from sanic.log import logger
from sanic.response import json

from biz.const import RC
from biz.wx_data import do_request
from utils.check import build_cookie
from peewee import DoesNotExist
from datetime import datetime
from sanic.kjson import json_loads


async def get_user_info_sso(request):
    request.ctx.event_time = datetime.now()
    kc = request.app.kc
    redirect_url = kc.make_auth_url()
    headers = request.headers
    logger.info(f"拿到的header={headers}")
    authorization = headers.get("Authorization")
    if not authorization:
        return False, json(dict(code=-10, msg=redirect_url, data=redirect_url))
    bearer, actk = authorization.split()
    if bearer != "Bearer":
        logger.info(f"bearer{bearer} != Bearer ")
        return False, json(dict(code=-10, msg=redirect_url, data=redirect_url))
    if actk == "dev":
        request.ctx.user_info = dict(roles=["管理员"], platform=None, mall=None, brand=None, erp=None, general=None,
                                     auth=['ALL'])
    if actk == "mVE88pgmliP8AzZee^@zi":  # 监控服务使用
        return True, {'user_info': {'sub': '7762812b-7e2d-4a9c-9dc1-8f350a086985', 'resource_access': {'CRM': {'roles': ['管理员']}}, 'instance_id': ['mt2022080800001-troy'], 'email_verified': False, 'preferred_username': 'andy.xue@globaltroy.com'}, 'token_info': {'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI5ZGNhMGE2My0zMzFkLTQyNTYtOWJmOS1hMDQxNjI2ZTVmNjgifQ.eyJleHAiOjE2NzA4MTk5NzYsImlhdCI6MTY3MDgxODE3NiwianRpIjoiZTRiZWIxMTQtNjg0OC00MmNjLTgxNTEtN2Q1NzAxZjU1NmU4IiwiaXNzIjoiaHR0cHM6Ly9jcm0udHJveWxpZmUuY24vYXV0aC9yZWFsbXMvVFJPWSIsImF1ZCI6Imh0dHBzOi8vY3JtLnRyb3lsaWZlLmNuL2F1dGgvcmVhbG1zL1RST1kiLCJzdWIiOiI3NzYyODEyYi03ZTJkLTRhOWMtOWRjMS04ZjM1MGEwODY5ODUiLCJ0eXAiOiJSZWZyZXNoIiwiYXpwIjoiQ1JNIiwic2Vzc2lvbl9zdGF0ZSI6ImExOTkwMjY1LTI4YzItNGYyYS1iZjQwLTBkYjQyNjE3OGZkYiIsInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsInNpZCI6ImExOTkwMjY1LTI4YzItNGYyYS1iZjQwLTBkYjQyNjE3OGZkYiJ9.wPEZQ6Dbr_MRNulW6a5TIw53rfxUmUnWQ-6znevZFxY', 'access_token': 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJISmJoQTBlVGdxckZPM1RmbjJxYUg2LUkzMFJwdG5KRjBNRzZLZ3lPSGxZIn0.eyJleHAiOjE2NzA4MTg0NzYsImlhdCI6MTY3MDgxODE3NiwiYXV0aF90aW1lIjoxNjcwODE4MTc2LCJqdGkiOiI4YTE0ZmZmYi00NGRkLTQwMTctYmRmNS1iMGFkOWE4M2QwYTAiLCJpc3MiOiJodHRwczovL2NybS50cm95bGlmZS5jbi9hdXRoL3JlYWxtcy9UUk9ZIiwic3ViIjoiNzc2MjgxMmItN2UyZC00YTljLTlkYzEtOGYzNTBhMDg2OTg1IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiQ1JNIiwic2Vzc2lvbl9zdGF0ZSI6ImExOTkwMjY1LTI4YzItNGYyYS1iZjQwLTBkYjQyNjE3OGZkYiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiIl0sInJlc291cmNlX2FjY2VzcyI6eyJDUk0iOnsicm9sZXMiOlsi566h55CG5ZGYIl19fSwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwic2lkIjoiYTE5OTAyNjUtMjhjMi00ZjJhLWJmNDAtMGRiNDI2MTc4ZmRiIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJhbmR5Lnh1ZUBnbG9iYWx0cm95LmNvbSJ9.i3rK2CrNkdENEw6F53Y29zOcHhrkTjWfQl38Z0-KAumbfo5Pq710PkDiKQwe-9MTF_m-9h7j-dS5ThOsp1FDe5aIkwU7sxMiq5dfjNu0ASclYus3TWVwO1djHJ-HMwt0K4MEGf2-RpLZeqR0Iyhl5dMgdTHW7CAHC0DEroMFvq3ibZ8W26JT-zsqi5OBX-hi4h4GIeZib4C0uq6tlNSPNDW-o4yRPhOsTx5Kj1NPjLWzGXpc_f7dWFnqg7lh6DIg0_RFWY1s9nOxUdwChvjrwi3B8hQwh44kR9xSnjRFOvG1t9Ar8RvVzsPO1QQ5GLn8NZ9n1G5Q0F2ztaoMTnJ2mQ'}}
    redis = request.app.redis
    actk = f"SSO:{actk}"
    value = await redis.get(actk)
    logger.info(f"redis key: {actk} -> value: {value}")
    if not value:
        return False, json(dict(code=-10, msg=redirect_url, data=redirect_url))
    value = value.decode()
    logger.info(f"value: {value}")
    access_token, refresh_token = value.split(":::")
    access_token = access_token[4:]
    if access_token is None:
        return False, json(dict(code=-10, msg=redirect_url, data=redirect_url))

    success, user_info = await kc.get_userinfo(access_token)
    logger.info(f"第一次获取用户信息:{success} {user_info}")
    if not success:
        # 使用access_token获取用户数据失败
        # 使用刷新token获取access_token
        success2, new_token_info = await kc.fetch_token_by_refresh(refresh_token)
        logger.info(f"使用刷新token获取access_token:{success2} {new_token_info}")
        if not success2:
            return False, json(dict(code=-10, msg=redirect_url, data=redirect_url))

        refresh_expire_in = new_token_info["refresh_expires_in"]
        refresh_token = new_token_info['refresh_token']
        _access_token = new_token_info['access_token']
        akey = f"SSO:{_access_token}"
        await redis.setex(akey, int(refresh_expire_in) - 30,
                          f"{_access_token}:::{refresh_token}")
        success3, user_info = await kc.get_userinfo(_access_token)
        logger.info(f"第二次获取用户信息:{success3} {user_info}")
        # 使用刷新之后的access_token重新获取用户信息
        if not success3:
            return False, json(dict(code=-10, msg=redirect_url, data=redirect_url))
    instance_id = user_info.get("instance_id")
    if instance_id is None:
        return False, json(dict(code=RC.INTERNAL_ERROR, msg="账号设置缺少实例ID,请联系管理员重新设置"))
    return True, {"user_info":user_info,"token_info":{"refresh_token": refresh_token, "access_token": access_token}}

def check_instance(handle):
    async def wrapper(request, **kwargs):
        try:
            # 接入sso后调整
            flag, res = await get_user_info_sso(request)
            logger.info(f"从SSO获取instance id: {res}")
            if not flag:
                logger.error(f"从SSO获取instance id失败：{res}")
                return res
            instance_id = res.get("user_info",{}).get("instance_id")[0]
            request.ctx.instance_id = instance_id
            mgr = request.app.mgr
            instance = await mgr.get(InstanceInfo.select(
                InstanceInfo.instance_id, InstanceInfo.crm_id, InstanceInfo.app_id, InstanceInfo.mch_id,
                InstanceInfo.woa_app_id,
                InstanceInfo.corp_id).where(InstanceInfo.instance_id == instance_id).dicts())
            # instance_info
            logger.info(f"{instance}")
            request.ctx.instance = instance
            if flag:
                request.ctx.user_info = res.get("user_info")
                request.ctx.token_info = res.get("token_info")
            resp = await handle(request, **kwargs)
            return resp
        except DoesNotExist as e:
            logger.exception(e)
            return json(dict(code=RC.PARAMS_INVALID, msg=str(e)))
        except AssertionError as e:
            logger.exception(e)
            return json(dict(code=RC.PARAMS_INVALID, msg=str(e)))
        except Exception as e:
            logger.exception(e)
            return json(dict(code=31999, msg=f"Error: {e}"))

    return wrapper


def check_wxwork_instance(handle):
    async def wrapper(request, **kwargs):
        try:
            sessionId = request.headers.get("X-SHARK-SESSION-ID", None)
            if not sessionId:
                return json(dict(code=-1, msg="please login"))
            session_client = request.app.wsm_redis
            await session_client.get(sessionId)
            got = await session_client.get(sessionId)
            obj = (got and json_loads(got)) or {}
            if not obj:
                return json(dict(code=-1, msg="please login"))
            # {"user_id": user_id, "corp_id": corp_id, "instance_id": instance_data.get("instance_id"), "open_userid": open_userid}
            # if obj and obj['instance_id'] == 'mt000000000-neowsm': obj['instance_id'] = 'mt000000000-neocep'
            request.ctx.user_info = obj
            request.ctx.instance_id = obj.get("instance_id")
            resp = await handle(request, **kwargs)
            return resp
        except DoesNotExist as e:
            logger.exception(e)
            return json(dict(code=RC.PARAMS_INVALID, msg=str(e)))
        except AssertionError as e:
            logger.exception(e)
            return json(dict(code=RC.PARAMS_INVALID, msg=str(e)))
        except Exception as e:
            logger.exception(e)
            return json(dict(code=31999, msg=f"Error: {e}"))

    return wrapper


