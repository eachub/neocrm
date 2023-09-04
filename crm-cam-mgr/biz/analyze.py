import os
import time
from collections import defaultdict

from mtkext.db import sql_printf
from mtkext.xlsx import XLSXBook
from mtkext.dt import dateFromString
from peewee import fn
from sanic.response import file
from sanic.log import logger
from datetime import datetime
from copy import copy, deepcopy

from biz.utils import scene_map, make_time_range, cache_to_date
from common.models.cam import StatCalData, CampaignInfo
from common.utils.check import date_slice, time_slice


async def get_panel_total(mgr, cid_list, from_date, to_date):
    # todo 逻辑可能要改成实时查询源数据表
    # 参与人数
    click_people = await get_campaign_record_total(mgr, cid_list, from_date, to_date, event_type=1)
    pick_people = await get_campaign_record_total(mgr, cid_list, from_date, to_date, event_type=2)
    # 曝光人数
    expose_people = await get_expose_people_total(mgr, cid_list, from_date, to_date)
    # 分享人数
    share_gift_people = await get_share_people_total(mgr, cid_list, from_date, to_date)
    # 注册人数
    register_member_people = await get_register_user_total(mgr, cid_list, from_date, to_date)
    for cid in cid_list:
        pass
    where = [
        StatCalData.cid.in_(cid_list),
        StatCalData.thour == 99,
        StatCalData.tdate.between(from_date, to_date)
    ]
    query = [
        StatCalData.cid,
        fn.sum(StatCalData.expose_people).alias("uv_total"),
        fn.sum(StatCalData.click_people).alias("parti_in_campaign_total"),
        fn.sum(StatCalData.share_gift_people).alias("share_gift_total"),
        fn.sum(StatCalData.register_member_people).alias("register_member_total")
    ]
    q = StatCalData.select(*query).where(*where).group_by(StatCalData.cid).dicts()
    logger.info(f'get_panel_total SQL {q}')
    return await mgr.execute(q)


async def get_panel_today(mgr, cid_list):
    today = str(datetime.now().date())
    where = [
        StatCalData.cid.in_(cid_list),
        StatCalData.thour == 99,
        StatCalData.tdate == today
    ]
    query = [
        StatCalData.cid,
        StatCalData.expose_people.alias("uv_today"),
        StatCalData.click_people.alias("parti_in_campaign_today"),
        StatCalData.share_gift_people.alias("share_gift_today"),
        StatCalData.register_member_people.alias("register_member_today")
    ]
    q = StatCalData.select(*query).where(*where).group_by(StatCalData.cid).dicts()
    logger.info(f'get_panel_today SQL {q}')
    return await mgr.execute(q)


async def get_panel_trend(mgr, cid_list, from_date, to_date, date_list):
    where = [
        StatCalData.cid.in_(cid_list),
        StatCalData.tdate.between(from_date, to_date),
        StatCalData.thour == 99
    ]
    query = [
        StatCalData.cid,
        StatCalData.tdate,
        StatCalData.expose_people.alias("uv_total"),
        StatCalData.click_people.alias("parti_in_campaign_total"),
        StatCalData.share_gift_people.alias("share_gift_total"),
        StatCalData.register_member_people.alias("register_member_total")
    ]
    order_by = [StatCalData.cid, StatCalData.tdate]
    ###
    q = StatCalData.select(*query).where(*where).order_by(*order_by).dicts()
    logger.debug(f'get_panel_trend SQL {q}')
    items = await mgr.execute(q)
    data = {}
    uv = [0] * len(date_list)  # 活动访客
    parti_in_campaign = copy(uv)  # 活动参与
    share_gift = copy(uv)  # 活动分享
    register_member = copy(uv)  # 注册会员
    trend_template = {"date": date_list, "uv": uv, "parti_in_campaign": parti_in_campaign,
                      "share_gift": share_gift, "register_member": register_member}
    ###
    for item in items:
        cid, tdate = int(item['cid']), str(item['tdate'])
        if not data.get(cid): data[cid] = deepcopy(trend_template)
        try:
            index = date_list.index(tdate)
        except ValueError:
            continue
        ###
        data[cid]['parti_in_campaign'][index] = item['parti_in_campaign_total']
        data[cid]['uv'][index] = item['uv_total']
        data[cid]['share_gift'][index] = item['share_gift_total']
        data[cid]['register_member'][index] = item['register_member_total']
    return data


async def get_panel_list(app, instance_id, from_date, to_date):
    mgr, now = app.mgr, datetime.now()
    # 查询当前实例下所有活动以及其主活动信息
    where = [
        CampaignInfo.instance_id == instance_id,
        CampaignInfo.begin_time <= now,
        CampaignInfo.end_time >= now,
    ]
    q = CampaignInfo.select().where(*where).order_by(CampaignInfo.begin_time.desc()).dicts()
    logger.debug(f'get_panel_list SQL {q}')
    items = await mgr.execute(q)
    if not items: return []
    ###
    date_list = date_slice(from_date, to_date)
    uv = [0] * len(date_list)  # 活动访客
    parti_in_campaign = copy(uv)  # 活动参与
    share_gift = copy(uv)  # 活动分享
    register_member = copy(uv)  # 注册会员
    activity_trend = {'date': date_list, 'uv': uv, 'parti_in_campaign': parti_in_campaign,
                      'share_gift': share_gift, 'register_member': register_member}
    ###
    data, cid_list = {}, []
    for item in items:
        activity_id, activity_name = item['campaign_id'], item['campaign_name']
        begin_time, cid = item['begin_time'], item['campaign_id']
        data[activity_id] = dict(activity_id=activity_id, activity_name=activity_name,
                                 begin_time=begin_time, cid=cid,
                                 parti_in_campaign_total=0, share_gift_total=0,
                                 uv_total=0, register_member_total=0,
                                 parti_in_campaign_today=0, share_gift_today=0,
                                 uv_today=0, register_member_today=0, trend=deepcopy(activity_trend),
                                 ac_id=activity_id, ac_type=item['campaign_type'], panel_type=1,
                                 item_type=item['campaign_type'], create_time=item['create_time']
                                 )
        cid_list.append(cid)
    logger.debug(f'cid_list: {cid_list}')
    ###
    # 从mysql实时查询
    cid_total_map = await mysql_get_panel_total(app, cid_list, from_date, to_date=to_date)
    logger.info(f"cid_total_map:{cid_total_map}")
    # total = await get_panel_total(mgr, cid_list, from_date, to_date)
    # cid_total_map = {int(i['cid']): i for i in total}
    today = await get_panel_today(mgr, cid_list)
    cid_today_map = {int(i['cid']): i for i in today}
    trend = await get_panel_trend(mgr, cid_list, from_date, to_date, date_list)
    ###
    for activity_id, item in data.items():
        cid = item['cid']
        if cid_total_map.get(str(cid)):
            one_total_map = cid_total_map.get(str(cid))
            item['uv_total'] = int(one_total_map.get("expose_people") or 0)
            item['parti_in_campaign_total'] = int(one_total_map.get("click_people") or 0)
            item['share_gift_total'] = int(one_total_map.get("share_gift_total") or 0)
            item['register_member_total'] = int(one_total_map.get("register_member_total") or 0)
        if cid_today_map.get(cid):
            item['uv_today'] = cid_today_map[cid]['uv_today']
            item['parti_in_campaign_today'] = cid_today_map[cid]['parti_in_campaign_today']
            item['share_gift_today'] = cid_today_map[cid]['share_gift_today']
            item['register_member_today'] = cid_today_map[cid]['register_member_today']
        if trend.get(cid):
            item['trend'] = trend[cid]
        logger.info(f'activity_id {activity_id} cid {cid} item {item}')
    return list(data.values())


async def get_panel_merge(app, instance_id, from_date, to_date):
    cep_list = await get_panel_list(app, instance_id, from_date, to_date)
    for cep in cep_list:
        cep['type'] = 'cep'
        cep.pop('cid', None)
        cep['timestamp'] = int(time.mktime(cep.pop('begin_time').timetuple()))
    ###
    # http = app.http
    # conf = app.conf
    # nft_param = conf.NFT_CLIENT
    # uri = '/panel/<instance_id>/list'
    # url = nft_param['host'] + nft_param['prefix'] + uri.replace('<instance_id>', instance_id)
    # result = await http.post(url, dict(from_date=from_date, to_date=to_date), timeout=30)
    # logger.info(f'instance_id: {instance_id}, result: {result}')
    ###
    # nft_list = [] if not result else result['data']
    # for nft in nft_list:
    #     nft['type'] = 'nft'
    #     nft['timestamp'] = nft.pop('begin_time')
    ###
    merge_list = cep_list
    return sorted(merge_list, key=lambda x: x['timestamp'], reverse=True)


def gen_excel_fileinfo():
    fname = f"{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    return fname, fpath


def write_to_excel(filepath, sheet_list):
    book = XLSXBook()
    for sheet_name, header, rows in sheet_list:
        t = book.add_sheet(sheet_name)
        if header: t.append_row(*header)
        for row in rows: t.append_row(*row)
    book.finalize(to_file=filepath)


async def get_panel_merge_export(app, instance_id, from_date, to_date):
    result = await get_panel_merge(app, instance_id, from_date, to_date)
    sheet_list = []
    name_one = '活动分析-汇总'
    header_one = ['活动名称', '活动访客', '活动参与', '活动分享', '注册会员', '今日活动访客', '今日活动参与', '今日活动分享', '今日注册会员']
    rows_one = []
    header_two = ['日期', '活动访客', '活动参与', '活动分享', '注册会员']
    ###
    for item in result:
        rows_one.append((item['activity_name'], item['uv_total'], item['parti_in_campaign_total'],
                         item['share_gift_total'], item['register_member_total'], item['uv_today'],
                         item['parti_in_campaign_today'], item['share_gift_today'], item['register_member_today']))
    sheet_list.append((name_one, header_one, rows_one))
    ###
    for item in result:
        activity_name, trend = item['activity_name'], item['trend']
        name, rows = f'{activity_name}-趋势', []
        for i in range(len(trend['date'])):
            rows.append((trend['date'][i], trend['uv'][i], trend['parti_in_campaign'][i],
                         trend['share_gift'][i], trend['register_member'][i]))
        sheet_list.append((name, header_two, rows))
    ###
    file_name, file_path = gen_excel_fileinfo()
    write_to_excel(file_path, sheet_list)
    return await file(file_path, filename=file_name)


async def get_panel_detail(app, instance_id, activity_id, type, from_date, to_date):
    if type == 'cep':
        return await get_panel_cep_detail(app, instance_id, activity_id, from_date, to_date)
    elif type == 'nft':
        return await get_panel_nft_detail(app, instance_id, activity_id, from_date, to_date)
    else:
        return {}


async def get_panel_cep_detail(app, instance_id, activity_id, from_date, to_date):
    mgr = app.mgr
    now = datetime.now()
    where = [
        CampaignInfo.instance_id == instance_id,
        CampaignInfo.campaign_id == activity_id,
        CampaignInfo.begin_time <= now,
        CampaignInfo.end_time >= now,
    ]
    q = CampaignInfo.select().where(*where).order_by(CampaignInfo.begin_time.desc())
    logger.debug(f'打印查询sql: {q}')
    items = await mgr.execute(q.dicts())
    if not items: return {}
    cid = items[0].get('campaign_id')
    ###
    date_list = time_slice() if from_date == to_date else date_slice(from_date, to_date)
    expose_times = [0] * len(date_list)  # 曝光数
    close_times = copy(expose_times)  # 关闭数
    expose_people = copy(expose_times)  # 曝光人数
    click_people = copy(expose_times)  # 点击人数
    pick_people = copy(expose_times)  # 领券人数
    pick_num = copy(expose_times)  # 领券数
    share_gift_people = copy(expose_times)  # 分享人数
    register_member_people = copy(expose_times)  # 注册人数
    trend_stat_cal = {'date': date_list, 'expose_times': expose_times, 'close_times': close_times,
                      'expose_people': expose_people, 'click_people': click_people,
                      'pick_people': pick_people, 'pick_num': pick_num,
                      "share_gift_people": share_gift_people, "register_member_people": register_member_people}
    sum_stat_cal = {"expose_times": 0, "close_times": 0, "expose_people": 0, "click_people": 0, "pick_people": 0,
                    "pick_num": 0, "share_gift_total": 0, "register_member_total": 0}
    result = {"sum_stat_cal": sum_stat_cal, "trend_stat_cal": trend_stat_cal,
              "from_stat_cal": [], "region_stat_cal": []}
    ###
    # 汇总数据
    if from_date == to_date:
        where = [
            StatCalData.cid == cid, StatCalData.thour == 99,
            StatCalData.tdate >= from_date, StatCalData.tdate <= to_date
        ]
        items = await mgr.execute(StatCalData.select(
            StatCalData.expose_times.alias("expose_times"),
            StatCalData.close_times.alias("close_times"),
            StatCalData.pick_num.alias("pick_num"),
            StatCalData.expose_people.alias("expose_people"),
            StatCalData.click_people.alias("click_people"),
            StatCalData.pick_people.alias("pick_people"),
            StatCalData.share_gift_people.alias("share_gift_total"),
            StatCalData.register_member_people.alias("register_member_total"),
        ).where(*where).dicts())
        if items and items[0]:
            result['sum_stat_cal'] = items[0]
    else:
        cid_total_map = await mysql_get_panel_total(app, [activity_id], from_date, to_date=to_date)
        result["sum_stat_cal"].update(cid_total_map.get(activity_id, {}))
    ###
    if from_date == to_date:
        where = [StatCalData.cid == cid, StatCalData.tdate == from_date, StatCalData.thour != 99]
        items = await mgr.execute(StatCalData.select().where(*where).dicts())
        for item in items:
            result['trend_stat_cal']['expose_times'][item['thour']] = item['expose_times']
            result['trend_stat_cal']['close_times'][item['thour']] = item['close_times']
            result['trend_stat_cal']['pick_num'][item['thour']] = item['pick_num']
            result['trend_stat_cal']['expose_people'][item['thour']] = item['expose_people']
            result['trend_stat_cal']['click_people'][item['thour']] = item['click_people']
            result['trend_stat_cal']['pick_people'][item['thour']] = item['pick_people']
            result['trend_stat_cal']['share_gift_people'][item['thour']] = item['share_gift_people']
            result['trend_stat_cal']['register_member_people'][item['thour']] = item['register_member_people']
    else:
        where = [StatCalData.cid == cid, StatCalData.tdate >= from_date,
                 StatCalData.tdate <= to_date, StatCalData.thour == 99]
        items = await mgr.execute(StatCalData.select().where(*where).dicts())
        for item in items:
            index = date_list.index(str(item['tdate']))
            result['trend_stat_cal']['expose_times'][index] = item['expose_times']
            result['trend_stat_cal']['close_times'][index] = item['close_times']
            result['trend_stat_cal']['pick_num'][index] = item['pick_num']
            result['trend_stat_cal']['expose_people'][index] = item['expose_people']
            result['trend_stat_cal']['click_people'][index] = item['click_people']
            result['trend_stat_cal']['pick_people'][index] = item['pick_people']
            result['trend_stat_cal']['share_gift_people'][index] = item['share_gift_people']
            result['trend_stat_cal']['register_member_people'][index] = item['register_member_people']
    # 地图分布
    from_nums, region_nums = 10, 10
    where_sql = " and ".join(
        [f"cid='{cid}'", "thour='99'"] + [f"tdate='{from_date}'"] if from_date == to_date else [
            f"tdate >= '{from_date}'", f"tdate <= '{to_date}'"])
    sql = f"""
            select
                province as name, sum(numbers) as value
            from 
                db_neocam.t_cam_stat_region_data
            """ + f" where {where_sql} " + f"""
            group by name
            order by value desc
            limit 0, {region_nums}
            """
    logger.info(f"region_sql: {sql}")
    region_stat_cal = await mgr.execute(StatCalData.raw(sql).dicts())
    logger.info(f"region_data: {[i for i in region_stat_cal]}")
    region_stat_cal = [item for item in region_stat_cal] if region_stat_cal else []
    result['region_stat_cal'] = region_stat_cal

    # 转换趋势图数据格式
    date_list = trend_stat_cal.get('date', [])
    trans_trend_stat_cal = []
    for index in range(len(date_list)):
        temp_item = dict(tdate=date_list[index])
        trans_field = [
            'expose_times', 'close_times', 'expose_people', 'click_people', 'pick_people', 'pick_num',
            'share_gift_people', 'register_member_people'
        ]
        [temp_item.update({x: trend_stat_cal[x][index]}) for x in trans_field]
        trans_trend_stat_cal.append(temp_item)

    result['trend_stat_cal'] = trans_trend_stat_cal
    return result


async def get_panel_nft_detail(app, instance_id, activity_id, from_date, to_date):
    return {}


async def handle_region_top(app, cid, from_date, to_date, types):
    region_nums = 10
    time_li = [f"tdate='{from_date}'"] if from_date == to_date else [f"tdate >= '{from_date}'", f"tdate <= '{to_date}'"]
    where_sql = " and ".join([f"cid='{cid}'", "thour='99'"] + time_li)
    if types == 1:
        sql = f"""
                select
                    province as name, sum(numbers) as value
                from 
                    db_neocam.t_cam_stat_region_data
                """ + f" where {where_sql} " + f"""
                group by name
                order by value desc
                limit 0, {region_nums}
                """
    else:
        sql = f"""
                select
                    city as name, sum(numbers) as value
                from 
                    db_neocam.t_cam_stat_region_data
                """ + f" where {where_sql} " + f"""
                group by name
                order by value desc
                limit 0, {region_nums}
                            """
    logger.info(f"region_sql: {sql}")
    region_stat_cal = await app.mgr.execute(StatCalData.raw(sql).dicts())
    logger.info(f"region_data: {[i for i in region_stat_cal]}")
    region_stat_cal = [item for item in region_stat_cal] if region_stat_cal else []
    return region_stat_cal


async def get_campaign_record_total(mgr, cid_list, from_date, to_date, event_type=1):
    """实时查询获取参加活动人数 领取活动人数
    type 1 参与活动 2 领券
    """
    # 时间范围大于两天的total数据的获取
    cidstr = ','.join(cid_list)
    union_table = []
    date_list = date_slice(from_date, to_date)
    where = f"campaign_id in ({cidstr}) and event_type={event_type}"
    for one_date in date_list:
        fmt_date = one_date.replace('-', '')
        one_table = f"(select * from db_neocam.t_cam_campaign_record_{fmt_date} where {where})"
        union_table.append(one_table)
    if event_type == 1:
        dim = "click_people"
    else:
        dim = "pick_people"
    union_tables = "union all ".join(union_table)
    sql = f"""
    SELECT t1.campaign_id as cid, count(DISTINCT member_no) as {dim} FROM ( {union_tables}) t1 
    group by t1.campaign_id 
    """
    logger.info(f"参与人数和领劵 sql:{sql}")
    try:
        items = await mgr.execute(StatCalData.raw(sql).dicts())
    except Exception as ex:
        logger.error(ex)
        items = []
    result_mp = defaultdict()
    for one in items:
        cid = one.get("cid")
        result_mp[cid] = one
    return result_mp


async def get_expose_people_total(mgr, cid_list, from_date, to_date):
    """活动访客"""
    from_time, to_time = make_time_range(from_date, to_date)
    sql = f"""
    select 
        cid, 
        count(DISTINCT member_no) as expose_people 
    from db_neocam.t_cam_web_traffic_event 
    where create_time  >= '{from_time}' and create_time  < '{to_time}' 
    and cid in ({','.join(cid_list)})
    group by cid
    """
    logger.info(f"total 活动访客:{sql}")
    items = await mgr.execute(StatCalData.raw(sql).dicts())
    result_mp = defaultdict()
    for one in items:
        cid = one.get("cid")
        result_mp[cid] = one
    return result_mp


async def get_share_people_total(mgr, cid_list, from_date, to_date):
    from_time, to_time = make_time_range(from_date, to_date)
    sql = """SELECT 
        cid, 
        COUNT(DISTINCT unionid) as share_gift_total
    FROM db_neocam.t_cam_wmp_share_event
    WHERE create_time > {from_time} and create_time <= {to_time}
    and cid in ({cid_list})
    GROUP BY cid
    """
    sql = sql_printf(sql, from_time=from_time, to_time=to_time, cid_list=','.join(cid_list))
    logger.info(f"total 活动分享:{sql}")
    items = await mgr.execute(StatCalData.raw(sql).dicts())
    result_mp = defaultdict()
    for one in items:
        cid = one.get("cid")
        result_mp[cid] = one
    return result_mp


async def get_register_user_total(mgr, cid_list, from_date, to_date):
    from_time, to_time = make_time_range(from_date, to_date)
    cid_code = [f"'cam_crm_{i}'" for i in cid_list]
    sql = f"""
        SELECT
        SUBSTRING(campaign_code, 9) as cid,
        count(1) as register_member_total 
        FROM  db_neocrm.t_crm_member_source_info 
        WHERE create_time >= '{from_time}' and create_time < '{to_time}'
        and campaign_code in ({','.join(cid_code)})
        group BY campaign_code
    """
    logger.info(f"total 活动注册:{sql}")
    items = await mgr.execute(StatCalData.raw(sql).dicts())
    result_mp = defaultdict()
    for one in items:
        cid = one.get("cid")
        result_mp[cid] = one
    return result_mp


@cache_to_date(ttl=180)
async def mysql_get_panel_total(app, cid_list, from_date, to_date=None):
    """实时查询mysql获取汇总数据 映射关系"""
    mgr = app.mgr
    cid_list = [str(i) for i in cid_list]
    # 参与人数 click_people
    click_people = await get_campaign_record_total(mgr, cid_list, from_date, to_date, event_type=1)
    # pick_people
    pick_people = await get_campaign_record_total(mgr, cid_list, from_date, to_date, event_type=2)
    # 曝光人数 expose_people
    expose_people = await get_expose_people_total(mgr, cid_list, from_date, to_date)
    # 分享人数 share_gift_total
    share_gift_people = await get_share_people_total(mgr, cid_list, from_date, to_date)
    # 注册人数 register_member_total
    register_member_total = await get_register_user_total(mgr, cid_list, from_date, to_date)
    cid_total_map = defaultdict(dict)
    for cid in cid_list:
        cid_total_map[cid].update(click_people.get(cid, {}))
        cid_total_map[cid].update(pick_people.get(cid, {}))
        cid_total_map[cid].update(expose_people.get(cid, {}))
        cid_total_map[cid].update(share_gift_people.get(cid, {}))
        cid_total_map[cid].update(register_member_total.get(cid, {}))
    return cid_total_map