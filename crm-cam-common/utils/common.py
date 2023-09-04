from datetime import datetime, date

from peewee import DoesNotExist
from sanic.kjson import json_loads

# 获取的数据列表，转化为list
from urllib.parse import urlencode

from sanic.log import logger

from common.models.cam import CampaignInfo


def models_to_dict_list(models, is_fetch_one=False):
    dict_list = []
    for item in models:
        for k, v in item.items():
            if isinstance(v, bool):
                item[k] = int(v)
            elif isinstance(v, datetime):
                item[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(v, date):
                item[k] = v.strftime('%Y-%m-%d')
        dict_list.append(item)
    if is_fetch_one and dict_list: return dict_list[0]
    return dict_list


async def do_request(app, path, obj=None, method="POST", **kwargs):
    conf = app.conf
    http = app.http
    host = conf.WX_DATA_HOST
    env = 'prod' if app.cmd_args.env == "prod" else "trial"
    url = f"{host}/{env}/{path}"
    kwargs.update(parse_with_json=False)
    if method == "POST":
        result = await http.post(url, obj, **kwargs)
    else:
        if obj:
            url += "&" if "?" in url else "?" + urlencode(obj)
        result = await http.get(url, **kwargs)
    ###
    if result is None:
        return False, http.errinfo
    result = json_loads(result)
    return result.get('code', 0) == 0, result, url, obj


# 根据cid获取对应instance_id
async def get_instance_id_by_cid(app, campaign_id):
    try:
        item = await app.mgr.get(CampaignInfo, campaign_id=campaign_id, removed=0)
    except DoesNotExist:
        logger.error(f'获取instance_id失败: campaign_id {campaign_id}')
        return ''
    instance_id = item.instance_id
    return instance_id


# 根据cid获取对应appid
async def get_appid_by_cid(app, campaign_id):
    if app.conf.AIRDROP_APPID: return app.conf.AIRDROP_APPID
    instance_id = await get_instance_id_by_cid(app, campaign_id)
    if not instance_id: return ''
    try:
        params = {"instance_id": instance_id}
        path = 'wx/auth/instance_info'
        flag, result, *o = await do_request(app, path, obj=params, method="GET")
        if not flag: return ''
        items = result.get('data', {}).get('items')
        if not items: return ''
        return items[0].get('appid')
    except Exception as e:
        logger.exception(e)
        return ''


async def get_campaign_path(app, instance_id, nft_file, cid):
    # 如果是压缩包 追加预览
    preview_path = ''
    if nft_file and str(nft_file).strip()[-4:] == '.zip':
        # 组装路径，并发送请求
        conf = app.args
        cms_conf = conf.CMS_CLIENT
        url = f"{cms_conf['host']}{cms_conf['prefix']}/material/{instance_id}/get_preview_path"
        req = dict(
            base_path=nft_file
        )
        if req: url += '?' + urlencode(req)
        logger.info(f'cms转发url 压缩包转化获取预览路径:{url}')

        result = await app.http.get(url, parse_with_json=True, timeout=10)
        logger.info(f"压缩包转化获取预览路径结果: {url} {result}")
        if not result:
            logger.info(f"{app.http_client.errinfo}")
            return ''
        preview_path = result.get('data', '')
    return f'{preview_path}?cid={cid}' if preview_path else ''


def is_number(s):
    try:
        float(s)
        return True
    except Exception as e1:
        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except Exception as e2:
            exception = f'{e1},{e2}'
    return False


async def logical_remove_record(mgr, ThatModel, **kwargs):
    where = []
    for key, val in kwargs.items():
        where.append(getattr(ThatModel, key) == val)
    return await mgr.execute(ThatModel.update({
        ThatModel.removed: True,
        ThatModel.update_time: datetime.now(),
    }).where(*where))