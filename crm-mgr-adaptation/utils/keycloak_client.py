# -*- coding: utf-8 -*-

import ujson
from urllib.parse import urlencode
from base64 import b64decode
from sanic.log import logger


class KeycloakClient(object):

    def __init__(self, http, server_url, realm_name, client_id, user_realm_name=None, redirect_uri=None, client_secret_key=None,
                 username=None, password=None, **kwargs):
        prefix = server_url.rstrip("/")
        self._http = http
        self._server_url = server_url
        self._client_id = client_id
        self._client_secret_key = client_secret_key
        self._username = username
        self._password = password
        self._kwargs = kwargs
        self._redirect_uri = redirect_uri
        self._realm_name = realm_name
        self._user_realm_name = user_realm_name
        self._token_info = {}

        ### USER URI
        self._token_url = f"{prefix}/realms/{realm_name}/protocol/openid-connect/token"
        self._realm_url = f"{prefix}/realms/{realm_name}"
        self._userinfo_url = f"{prefix}/realms/{realm_name}/protocol/openid-connect/userinfo"
        self._logout_url = f"{prefix}/realms/{realm_name}/protocol/openid-connect/logout"
        self._wellknown_url = f"{prefix}/realms/{realm_name}/.well-known/openid-configuration"
        self._certs_url = f"{prefix}/realms/{realm_name}/protocol/openid-connect/certs"
        self._introspect_url = f"{prefix}/realms/{realm_name}/protocol/openid-connect/token/introspect"
        self._entitlement_url = f"{prefix}/realms/{realm_name}/authz/entitlement/%s"
        self._make_auth_url = f"{prefix}/realms/{realm_name}/protocol/openid-connect/auth"

        ### ADMIN URI
        self._create_role_url = f"{prefix}/admin/realms/{realm_name}/clients/{self._client_id}/roles"
        self._query_role_url = f"{prefix}/admin/realms/{realm_name}/roles"
        self._band_role_to_user_url = f"{prefix}/admin/realms/{realm_name}/users/%s/role-mappings/clients/{client_id}"
        self._query_can_band_role_url = f"{prefix}/admin/realms/{realm_name}/users/%s/role-mappings/clients/{client_id}/available"
        self._query_user_role_list = f"{prefix}/admin/realms/%s/users/%s/role-mappings"
        self._get_user_info_by_id = f"{prefix}/admin/realms/%s/users/%s"

    @property
    def token(self):
        return self._token_info

    @staticmethod
    def decode_auth(access_token):
        data = access_token.split(".")[1]
        missing_padding = len(data) % 4
        if missing_padding != 0:
            data += '=' * (4 - missing_padding)
        return ujson.loads(b64decode(data))

    async def _remote_post(self, url, payload, access_token=None, jsondumps=False, method='POST'):
        headers = {"Content-Type": "application/x-www-form-urlencoded"} if not jsondumps else {
            "Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if jsondumps:
            data = ujson.dumps(payload) if type(payload) is not str else payload
        else:
            data = urlencode(payload) if type(payload) is not str else payload
        got = await self._http.request(
            url, method=method, data=data, headers=headers, timeout=3)
        if got is None:
            st, res = got, self._http.errinfo
        else:
            st, res = True, (got and ujson.loads(got) or {})
        msg = dict(url=url, method=method, headers=headers, req=data, res=res)
        logger.info(f"message {ujson.dumps(msg)}")
        return st, res

    async def _remote_get(self, url, access_token=None, jsondumps=False):
        headers = {
            "Authorization": f"Bearer {access_token}",
        } if access_token else {}
        if jsondumps:
            headers['Content-Type'] = "application/json"
        print(f"请求的接口是:{url}")
        got = await self._http.request(url, method="GET", headers=headers, timeout=3)
        if got is None:
            st, res = got, self._http.errinfo
        else:
            st, res = True, (got and ujson.loads(got) or {})
        msg = dict(url=url, method='GET', headers=headers, res=res)
        logger.info(f"message {ujson.dumps(msg)}")
        return st, res

    # 通过密钥获取access_token
    async def fetch_token_by_credentials(self, username=None, password=None):
        params = dict(
            client_id=self._client_id,
            grant_type="client_credentials",
        )
        if self._client_secret_key:
            params['client_secret'] = self._client_secret_key
        flag, result = await self._remote_post(self._token_url, params)
        if flag: self._token_info = result
        return flag, result

    # 通过用户名密码获取access_token
    async def fetch_token_by_password(self, username=None, password=None):
        params = dict(
            client_id=self._client_id,
            grant_type="password",
            username=username or self._username,
            password=password or self._password,
        )
        if self._client_secret_key:
            params['client_secret'] = self._client_secret_key
        flag, result = await self._remote_post(self._token_url, params)
        if flag: self._token_info = result
        return flag, result

    # 通过第三方登陆code获取access_token
    async def fetch_token_by_code(self, code, redirect_uri=None):
        params = dict(
            client_id=self._client_id,
            grant_type="authorization_code",
            code=code,
            redirect_uri=redirect_uri or self._redirect_uri
        )
        if self._client_secret_key:
            params['client_secret'] = self._client_secret_key
        flag, result = await self._remote_post(self._token_url, params)
        if flag: self._token_info = result
        return flag, result

    # 通过refresh_token刷新access_token
    async def fetch_token_by_refresh(self, refresh_token):
        params = dict(
            client_id=self._client_id,
            grant_type="refresh_token",
            refresh_token=refresh_token,
        )
        if self._client_secret_key:
            params['client_secret'] = self._client_secret_key
        flag, result = await self._remote_post(self._token_url, params)
        if flag: self._token_info = result
        return flag, result

    # 通过access_token获取用户信息
    async def get_userinfo(self, access_token):
        return await self._remote_get(self._userinfo_url, access_token)

    # 登出
    async def logout(self, refresh_token):
        params = {"client_id": self._client_id, "refresh_token": refresh_token}
        if self._client_secret_key:
            params['client_secret'] = self._client_secret_key
        flag, result = await self._remote_post(self._logout_url, params)
        ok = (self._http.status == 204)
        return ok, result

    # 生成第三方登陆链接
    def make_auth_url(self):
        return f"{self._make_auth_url}?client_id={self._client_id}&response_type=code&redirect_uri={self._redirect_uri}"

    async def well_know(self):
        return await self._remote_get(self._wellknown_url)

    async def get_certs(self):
        return await self._remote_get(self._certs_url)

    # 通过获取到的用户信息提取用户的client的角色
    def find_roles(self, uinfo):
        return ((uinfo.get('resource_access') or {}).get(self._client_id) or {}).get("roles") or []

    # 为client新增一个角色
    async def create_role_for_client(self, access_token, role_name):
        params = {'name': role_name, 'clientRole': 'true'}
        return await self._remote_post(self._create_role_url, params, access_token=access_token, jsondumps=True)

    # 查询client的所有角色
    async def query_roles_for_client(self, access_token):
        return await self._remote_get(self._query_role_url, access_token=access_token, jsondumps=True)

    # 查询用户在client里能够绑定的所有角色
    async def query_can_band_roles_for_client(self, user_id, access_token):
        url = self._query_can_band_role_url % user_id
        return await self._remote_get(url, access_token=access_token, jsondumps=True)

    # 为用户绑定client的角色
    async def band_role_to_user(self, user_id, roles, access_token):
        params = ujson.dumps(roles)
        url = self._band_role_to_user_url % user_id
        return await self._remote_post(url, params, access_token=access_token, jsondumps=True)

    # 从用户角色中删除client级角色
    async def del_role_to_user(self, user_id, roles, access_token):
        params = ujson.dumps(roles)
        url = self._band_role_to_user_url % user_id
        return await self._remote_post(url, params, access_token=access_token, jsondumps=True, method='DELETE')

    # # 获取用户的角色列表
    async def get_user_role(self, user_id, access_token, realm_name=None):
        """
        {
            "clientMappings":{
                "OCP-OMS":{
                    "client":"OCP-OMS",
                    "id":"de60ac53-15ea-47ca-825f-f4b34eff387e",
                    "mappings":[
                        {
                            "clientRole":true,
                            "composite":false,
                            "containerId":"de60ac53-15ea-47ca-825f-f4b34eff387e",
                            "id":"ea35b307-b62f-4812-8324-ff1a3183b09a",
                            "name":"仓管"
                        },
                        {
                            "clientRole":true,
                            "composite":false,
                            "containerId":"de60ac53-15ea-47ca-825f-f4b34eff387e",
                            "id":"7b295a1e-8d74-465d-8d9a-0094dcd39e3a",
                            "name":"超级管理员"
                        }
                    ]
                }
            },
            "realmMappings":[
                {
                    "clientRole":false,
                    "composite":true,
                    "containerId":"OCP",
                    "description":"${role_default-roles}",
                    "id":"d2ad0a51-21a8-40fd-846c-bed340ed17d0",
                    "name":"default-roles-ocp"
                }
            ]
        }
        """
        url = self._query_user_role_list % (realm_name or self._user_realm_name or self._realm_name, user_id)
        return await self._remote_get(url, access_token=access_token)

    # # # 根据用户id获取用户信息
    async def get_user_info_by_id(self, user_id, access_token, realm_name=None):
        url = self._get_user_info_by_id % (realm_name or self._user_realm_name or self._realm_name, user_id)
        return await self._remote_get(url, access_token=access_token)


if __name__ == "__main__":
    import asyncio
    from mtkext.hcp import HttpClientPool
    from pprint import pprint
    loop = asyncio.get_event_loop()
    async def test(loop):
        http = HttpClientPool(loop=loop)

        BASE_URL = "https://dev.quickshark.cn"
        BP_PREFIX = "/api/ec/mgr"
        KC_CLIENT_PARAM = dict(
            server_url="https://ocpsso-dev.icoke.cn/auth/",
            realm_name="OCP",
            user_realm_name="OCP",
            client_id="OCP-EC",
            client_secret_key='2b29404f-0b50-4263-95da-2a22e4254f45',
            # username='chenhao@163.com',
            # password='11111111',
            redirect_uri=f"{BASE_URL}{BP_PREFIX}/user/login/callback"
        )
        kc = KeycloakClient(http, **KC_CLIENT_PARAM)
        
        success, info = await kc.fetch_token_by_credentials()
        # info = kc.make_auth_url()
        # pprint(info)

        ac = info["access_token"]
        st, obj = await kc.get_userinfo(ac)
        print(obj)
        user_id = obj['sub']

        ires = await kc.get_user_info_by_id(user_id, access_token=ac)
        pprint(ires)
        # res = await kc.get_user_role(user_id, access_token=ac, realm_name="OCP")
        # pprint(res)
        # res, uinfo = await kc.get_userinfo(access_token="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJUQjVFalpHYWc2Z1BxV0tkWEdFYkVQaVZxcDhDazhIejkxWHBJbGJJMUhrIn0.eyJleHAiOjE2NDEyODcxNzgsImlhdCI6MTY0MTI4NTM3OCwianRpIjoiMjliOWQyMDAtNDBjYi00MWI4LTlkYmQtYTA0OTYxZGRjYjU3IiwiaXNzIjoiaHR0cHM6Ly9vY3Bzc28tZGV2Lmljb2tlLmNuL2F1dGgvcmVhbG1zL09DUCIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiIwNWMzNGI0Ny1hNjc1LTRmNTgtOGM3Ni05YzJiM2VhMjA0MWEiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhY2NvdW50LWNvbnNvbGUiLCJub25jZSI6ImM0NjdkODJiLWEwODEtNDY4Ni04NWQxLWZlMjg4NzRhM2FhYyIsInNlc3Npb25fc3RhdGUiOiI0ODhjZjhiYy0wOGNjLTRlMDYtYmNlOS1kYTI5M2MzYWNlNzUiLCJhY3IiOiIwIiwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJzaWQiOiI0ODhjZjhiYy0wOGNjLTRlMDYtYmNlOS1kYTI5M2MzYWNlNzUiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInByZWZlcnJlZF91c2VybmFtZSI6ImNoZW5oYW9AMTYzLmNvbSIsImVtYWlsIjoiY2hlbmhhb0AxNjMuY29tIn0.GwG1nQKK1BVOJD0Mf9CZVDQ2L6YiUCFrogdugvCb3RzoFM_9isrQ3IlKCuNE8klyTtmFSEBlggLqZ1RKj4IJu_H3l7t178E4V-iFEjjBqiMAGoR86EJCP6osmylTP2U3vODZtrWmQ3Yx8SFXWRb2DeQkBVznzAn-CRX5coim1XZNwRr4AyFfjj7v3FY_UIJB3z-5NPmin297Gvyw-PZmoPgxiwg-Kl2migBWg0MdkPR5TcPOHl4TJciewngkCqOMJfV38qt8xAcY8RVILGXAhS2486y31WvXygTgelAjibqEmnOzyMKSjmYdt7f8Z1tQGh09wWfQjWYq0VxUFkzSZg")
        # print(f"用户的信息是:{uinfo}")
        # roles = kc.find_roles(uinfo)
        # print(f"用户的角色是：{roles}")
    loop.run_until_complete(test(loop))