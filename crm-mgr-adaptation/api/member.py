from datetime import datetime, timedelta

from mtkext.dt import datetimeToString, dateFromString
from peewee import RawQuery
from sanic import Blueprint
from sanic.response import json
from sanic.log import logger
from collections import defaultdict

from biz.const import RC
from biz.member import *
from biz.utils import make_time_range
from models import *
from biz.wrapper import except_decorator
from clients import CrmBiz
from utils.wrapper import check_instance

bp = Blueprint('bp_hub_backend', url_prefix="/adapt/member")


@bp.post('/events')
@except_decorator
@check_instance
async def api_fetch_member_events(request):
    """获取会员行为数据支持分页"""
    # 从 db_event.t_wmp_custom_event 中出
    crm_id = request.ctx.instance.get("crm_id")
    app = request.app
    params_dict = request.json
    member_no = params_dict.get('member_no')
    # member_no = params_dict.get('oAXn65noK0CCvy2KjHIZNGnQSZJw')
    page_size = int(params_dict.get("page_size") or 20)
    keywords = None
    max_create_time = params_dict.get("next_max_create_time")  # 上次分页返回最小时间
    dr = params_dict.get('dr')
    assert not dr or dr.find("~") > 0, "dr必须是~分割的两个日期"

    # 查询会员的详细信息
    req_obj = dict(member_no=member_no, platform="wechat", t_platform=True)
    flag, result = await app.client_crm.member.member_query(req_obj, crm_id=crm_id, method='POST')
    logger.info(result)
    unionid = result['wechat_member_info']['unionid']
    appid = result['wechat_member_info']['appid']
    openid = result['wechat_member_info']['openid']
    ###
    param_where = ""
    if dr:
        from_date, to_date = map(dateFromString, dr.split("~"))
        logger.info(f"{from_date} {to_date}")
        from_time, to_time = make_time_range(from_date, to_date)
    else:
        to_time = datetime.now() + timedelta(days=1)
        from_time = to_time - timedelta(days=30)
        from_time = datetime.strftime(from_time, "%Y-%m-%d 00:00:00")
        to_time = datetime.strftime(to_time, "%Y-%m-%d 00:00:00")
    param_where += f""" and create_time >= '{from_time}' and create_time <= '{to_time}'"""
    if max_create_time:
        param_where += f"""and create_time <= '{max_create_time}'"""
        to_time = max_create_time
    if keywords:
        param_where += f""" and event_name like '%%{keywords}%%'"""
    # wmp数据
    try:
        wmp_event = await search_wmp_customer_event(app, appid, unionid, page_size, param_where=param_where)
        logger.info(wmp_event)
    except Exception as ex:
        logger.info(f"get wmp_event error:{ex}")
        wmp_event = []
    # 新数据源 h5事件
    try:
        h5_event = await search_web_customer_event(app, member_no, page_size, param_where=param_where)
    except Exception as ex:
        logger.info(f"get h5 event error:{ex}")
        h5_event = []
    # 订单数据
    try:
        order_event = await search_order_event(app, crm_id, member_no, from_time, to_time, page_size, keywords=keywords)
    except Exception as ex:
        logger.info(f"get order event error:{ex}")
        order_event = []
    # 退单数据
    try:
        refund_event = await search_refund_event(app, crm_id, member_no, from_time, to_time, page_size, keywords=keywords)
    except Exception as ex:
        logger.info(f"get refund event error:{ex}")
        refund_event = []
    # 领劵
    try:
        card_event = await search_card_event(app, member_no, openid, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"get card_event error:{ex}")
        card_event = []
    # 参加活动
    try:
        camp_event = await search_campaign_event(app, member_no, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"get camp_event error:{ex}")
        camp_event = []
    # 打开小程序
    try:
        open_app_event = await search_wmp_app_event(app, openid, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"get open_app_event error:{ex}")
        open_app_event = []
    items = []
    for i in (h5_event, wmp_event, order_event, refund_event, card_event, camp_event, open_app_event):
        if i:
            items += i
    # 排序后 取出 page_size 条
    logger.info(items)
    items = sorted(items, key=lambda e:e.get("create_time"), reverse=True)
    next_page = False
    items = items[:page_size]
    next_max_create_time = None
    if len(items) >= page_size:
        next_page = True
        next_max_create_time = items[-1].get('create_time')
    # 数据规则 相同日期的汇总起来
    result = defaultdict(list)
    for item in items:
        create_time = item.get("create_time")
        create_time = datetimeToString(create_time)
        date_ = create_time.split(' ')[0]
        time_ = create_time.split(' ')[1]
        item['time_str'] = time_
        event_name = item.get("event_name") or ''
        event_desc = item.get("describe") or ''
        if event_desc:
            item['event_name'] = event_name + ',' + event_desc.strip(',')
        else:
            item['event_name'] = event_name
        result[date_].append(item)
    ret_list = []
    for key, value in result.items():
        ret_list.append(dict(date=key, events=value))
    return json(dict(code=RC.OK, msg="OK", data=dict(
        items=ret_list, next_max_create_time=next_max_create_time, nex_page=next_page, page_size=page_size)))


@bp.get("/member_attrs")
@except_decorator
@check_instance
async def api_get_member_attrs(request):
    """从order_items中统计指标"""
    crm_id = request.ctx.instance.get("crm_id")
    app = request.app
    params_dict = request.args
    member_no = params_dict.get('member_no')
    assert type(member_no) is str, "member_no参数缺失或格式错误"
    now = datetime.now()
    start_dt = now - timedelta(days=30)
    now_dt = datetimeToString(now)
    start_dt = datetimeToString(start_dt)

    # 获取openid
    flag, result = await CrmBiz.member_query(app.client_crm, crm_id, member_no)
    openid =''
    if flag:
        openid = result['wechat_member_info']['openid']
    else:
        return json(dict(code=RC.DATA_NOT_FOUND, msg="会员号不存在", data=None))
    # 计算指标
    all_mounts_sql = f"""
        select (
            (SELECT COALESCE(sum(pay_amount),0) from db_neocrm.t_crm_order_info where member_no='{member_no}') -
            (SELECT COALESCE(sum(pay_amount),0) from db_neocrm.t_crm_refund_info where member_no='{member_no}')
        ) as amount
    """
    all_mounts = await app.mgr.execute(InstanceInfo.raw(all_mounts_sql).dicts()) or []
    all_mounts = list(all_mounts)
    all_mounts = all_mounts[0].get("amount") if all_mounts else 0

    mounts_30sql = f"""
        select (
            (
            SELECT COALESCE(sum(pay_amount),0) from  db_neocrm.t_crm_order_info 
            where create_time >'{start_dt}' and create_time <= '{now_dt}' and member_no = '{member_no}'
            ) -
            (
            SELECT COALESCE(sum(pay_amount),0) from  db_neocrm.t_crm_refund_info 
            where create_time >'{start_dt}' and create_time <= '{now_dt}' and member_no = '{member_no}'
            )
        ) as amount
        """
    mounts_30 = await app.mgr.execute(InstanceInfo.raw(mounts_30sql).dicts()) or []
    mounts_30 = list(mounts_30)
    mounts_30 = mounts_30[0].get('amount') if mounts_30 else 0
    # 消费次数
    order_times_30_sql = f"""
            SELECT count(1) as count from  db_neocrm.t_crm_order_info tcoi
            where create_time >'{start_dt}' and create_time <= '{now_dt}' and member_no = '{member_no}'
        """
    order_times_30 = await app.mgr.execute(InstanceInfo.raw(order_times_30_sql).dicts()) or []
    order_times_30 = list(order_times_30)
    order_times_30 = order_times_30[0].get('count') if order_times_30 else 0
    # 访问小程序天数
    try:
        app_times_sql = f"""SELECT count(*) as count from (
            SELECT date_format(create_time ,'%%Y-%%m-%%d') as 'date'  
            from db_event.t_wmp_app_event
            where openid='{openid}' and create_time > '{start_dt}' and create_time <='{now_dt}'
            group by date_format(create_time ,'%%Y-%%m-%%d')
        ) t1"""
        app_times = await app.db_event_mgr.execute(InstanceInfo.raw(app_times_sql).dicts())
        app_times_30 = app_times[0].get("count") if app_times else 0
        # 小程序加购次数
        add_cards_sql = f"""
            SELECT count(1) as count from db_event.t_wmp_custom_event twae 
        where event_name='加入购物车' and 
        create_time >'{start_dt}' and create_time <='{now_dt}' and openid='{openid}'
        """
        add_cards_times = await app.db_event_mgr.execute(InstanceInfo.raw(add_cards_sql).dicts())
        add_cards_30 = add_cards_times[0].get("count") if add_cards_times else 0
    except Exception as ex:
        logger.exception(ex)
        app_times_30 = 0
        add_cards_30 = 0
    # 金额保留两位小数
    all_mounts = round(all_mounts or 0, 2)
    mounts_30 = round(mounts_30 or 0, 2)
    return json(dict(code=RC.OK, msg="OK",
                     data=dict(all_mounts=all_mounts, order_times_30=order_times_30, mounts_30=mounts_30,
                               app_times_30=app_times_30, add_cards_30=add_cards_30)))


@bp.get('/show360')
@except_decorator
@check_instance
async def api_show360(request):
    crm_id = request.ctx.instance.get("crm_id")
    app = request.app
    params_dict = request.args
    member_no = params_dict.get('member_no')
    ###
    # 获取会员的标签数据
    flag, result = await app.client_crm.member.member_tags(dict(member_no=member_no), crm_id=crm_id, method='GET')
    tags = []
    if flag:
        tags = result.get('tags')
    # 计算会员的指标

    # 获取会员的统计数据 总消费金额 attr
    # 30天访问小程序天数，db_event.t_wmp_app_event
    # 30天小程序加购次数，db_event.t_wmp_custom_event
    return json(dict(code=RC.OK, msg="OK", data=dict(tags=tags, attr=None)))