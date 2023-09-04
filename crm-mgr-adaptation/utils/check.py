

# 需要共用COOKIE的模块
EXT_COOKIE_KEY = ['__neonft_uuid__', '__neowsm_uuid__']


def build_cookie(cookies, union_key='__neocep_uuid__'):
    assert cookies and cookies.get(union_key), '用户登录无效'
    cep_cookie = cookies.get(union_key)
    return ';'.join([f'{x}={cep_cookie}' for x in [union_key]+EXT_COOKIE_KEY])
