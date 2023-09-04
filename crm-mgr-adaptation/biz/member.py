import logging

import ujson
from sanic.log import logger

from biz.utils import date_slice
from models import InstanceInfo


async def search_web_customer_event(app, member_no, page_size, param_where=None):
    base_where = f"""where member_no='{member_no}'"""
    where_sql = base_where
    sql = f"""select * from db_event.t_web_custom_event {where_sql} order by create_time desc  limit 0,{page_size}"""
    logger.info(sql)
    items = await app.db_event_mgr.execute(InstanceInfo.raw(sql).dicts())
    # 数据格式化
    result = []
    for item in items:
        typeid = item.get("typeid")
        event_name = typeid
        create_time = item.get('create_time')
        event_id = item.get('event_id')
        result.append(dict(event_name=event_name, create_time=create_time, event_id=event_id, source='web'))
    return result


async def search_wmp_customer_event(app, appid, unionid, page_size, param_where=None):
    event_name = ["查看商品类目", "查看商品详情", "加入购物车", "收藏商品", "分享商品", "商品评论", "发起订单支付", "商品结算",
                  "立即购买", "搜索商品", "生理检测下单", "确认绑定", "再次检测"]
    event_name = [f"'{i}'" for i in event_name]
    event_str = ','.join(event_name)
    base_where = f""" where unionid='{unionid}' and event_name in ({event_str}) """
    where_sql = base_where + param_where
    sql = f"""select * from db_event.t_wmp_custom_event {where_sql} order by create_time desc  limit 0,{page_size}"""
    logger.info(sql)
    items = await app.db_event_mgr.execute(InstanceInfo.raw(sql).dicts())
    # 数据格式化
    desc_map = dict(outer_code="erpcode", goods_category1="商品一级分类", goods_category2="商品二级分类", sku_code="SKU编码", qty="商品数量")
    result = []
    for item in items:
        event_name = item.get("event_name")
        create_time = item.get('create_time')
        event_id = item.get('event_id')
        # 描述信息
        param = item.get('param') or '{}'
        param = ujson.loads(param)
        desc = ""
        if event_name == "确认绑定":
            sample_code = param.get("sample_code")
            if sample_code:
                desc = f"绑定样品编码:{sample_code}"
        if event_name == "发起订单支付":
            for sku in param.get("sku_info"):
                goods_name = sku.get("goods_name") or ""
                sku_code = sku.get("sku_code") or ""
                qty = sku.get("qty") or ""
                desc += f"商品名称:{goods_name},SKU编码:{sku_code},数量:{qty}"
        if event_name == '立即购买':
            goods_name = param.get("goods_name")
            qty = param.get("qty") or ""
            sku_code = [str(i) for i in param.get("sku_list") or []]
            desc = f"商品名称:{goods_name},SKU编码:{','.join(sku_code)},数量:{qty}"
        param_data = param.get("param") or {}
        if param_data:
            for key, text in desc_map.items():
                val = param_data.get(key)
                if val:
                    desc += f"{text}:{val},"
        desc.strip(',')
        result.append(dict(event_name=event_name, create_time=create_time, event_id=event_id, source='wmp', describe=desc))
    return result


async def search_order_event(app, crm_id, member_no, from_time, to_time, page_size, keywords=None):
    # 订单行为：订单号、订单金额、商品列表（商品名称和SKU_CODE）、支付时间
    if keywords and keywords not in "用户下单":
        return []
    sql = f"""SELECT '用户下单' as event_name, pay_amount, order_sn, pay_time, create_time, item_list from db_neocrm.t_crm_order_info 
         where member_no = '{member_no}' and crm_id={crm_id} 
        and create_time >= '{from_time}' and create_time < '{to_time}' order by create_time desc limit {page_size}
    """
    logger.info(f"order sql:{sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts())
    # 拼接事件的描述信息
    for item in items:
        desc = ""
        order_sn = item.get("order_sn")
        if order_sn:
            desc += f"订单号: {order_sn}"
        # 商品信息
        item_list = item.get("item_list") or '{}'
        item_list = ujson.loads(item_list)
        if item_list:
            desc += "购买商品:"
        for i in item_list:
            goods_name = i.get('goods_name')
            sku_id = i.get('sku_id')
            if goods_name:
                desc += f"商品({goods_name})SKU({sku_id}),"
        item['describe'] = desc.strip(',')
    return list(items)


async def search_refund_event(app, crm_id, member_no, from_time, to_time, page_size, keywords=None):
    """获取退单信息"""
    if keywords and keywords not in "用户退单":
        return []
    sql = f"""select order_sn, '用户退单' as event_name, refund_id , refund_amount, create_time  from db_neocrm.t_crm_refund_info
            where member_no = '{member_no}' and crm_id={crm_id} 
            and create_time >= '{from_time}' and create_time < '{to_time} order by create_time desc limit {page_size}'
        """
    logger.info(f"refund sql {sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts())
    # 拼接描述信息
    for item in items:
        order_sn = item.get("order_sn")
        refund_amount = item.get("refund_amount")
        refund_id = item.get("refund_id")
        item['describe'] = f"订单号:{order_sn}, 售后单号:{refund_id}, 退款金额:{refund_amount}"
    return list(items)


async def search_merchant_send_event(app, openid, from_time, to_time, page_size, keywords=None):
    """商家劵领取事件 从 t_omni_event_send """
    event_name = "商家劵领取"
    if keywords and keywords not in event_name:
        return []
    sql = f"""select '{event_name}' as event_name, record_time as create_time, coupon_code  from db_omni.t_omni_event_send 
            where send_time >= '{from_time}' and  send_time >= '{to_time}'  
            and openid = '{openid}' order by send_time desc limit {page_size}"""
    logger.info(f"refund sql {sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts()) or []
    ###
    for item in items:
        coupon_code = item.get("coupon_code")
        item['describe'] = f"领取商家劵:{coupon_code}"
    return list(items)


async def search_merchant_redeem_event(app, openid, from_time, to_time, page_size, keywords=None):
    """商家劵核销事件 t_omni_event_redeem获取"""
    event_name = "商家劵核销"
    if keywords and keywords not in event_name:
        return []

    sql = f"""select '{event_name}' as event_name, redeem_time as create_time, coupon_code  from db_omni.t_omni_event_redeem 
                where redeem_time >= '{from_time}' and  redeem_time >= '{to_time}'  
                and openid = '{openid}' order by redeem_time desc limit {page_size}"""
    logger.info(f"{event_name} sql {sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts()) or []
    ###
    for item in items:
        coupon_code = item.get("coupon_code")
        item['describe'] = f"核销商家劵:{coupon_code}"
    return list(items)


async def search_coupon_event_received(app, member_no, from_time, to_time, page_size, keywords=None,):
    """领取自制劵"""
    event_name = "领劵自制劵"
    if keywords and keywords not in event_name:
        return []
    sql = f"""
    select t1.*, t2.title from (
    select '{event_name}' as event_name, card_id , card_code , received_time as create_time from db_neocrm.t_crm_coupon_user_info
    where  received_time > '{from_time}' and received_time  < '{to_time}' and received_time is not NULL 
    and member_no = '{member_no}'
    order by received_time desc limit {page_size} ) t1 left join db_neocrm.t_crm_coupon_info t2 on t2.card_id = t1.card_id"""
    logger.info(f"{event_name} sql {sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts()) or []
    ###
    for item in items:
        card_code = item.get("card_code")
        title = item.get("title")
        item['describe'] = f"{title}({card_code})"
    return list(items)


async def search_coupon_event_redeem(app, member_no, from_time, to_time, page_size, keywords=None,):
    event_name = "核销自制劵"
    if keywords and keywords not in event_name:
        return []
    sql = f"""select '{event_name}' as event_name, card_id , card_code , redeem_time as create_time from db_neocrm.t_crm_coupon_user_info
    where  redeem_time > '{from_time}' and redeem_time  < '{to_time}' and redeem_time is not NULL 
    and member_no = '{member_no}'
    order by redeem_time desc limit {page_size}"""
    logger.info(f"{event_name} sql {sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts()) or []
    ###
    for item in items:
        card_code = item.get("card_code")
        item['describe'] = f"核销:{card_code}"
    return items


async def search_coupon_event_present(app, member_no, from_time, to_time, page_size, keywords=None,):
    event_name = "转增自制劵"
    if keywords and keywords not in event_name:
        return []
    sql = f"""select '{event_name}' as event_name, card_id , card_code , present_time as create_time from db_neocrm.t_crm_coupon_user_info
    where  present_time > '{from_time}' and present_time  < '{to_time}' and present_time is not NULL 
    and member_no = '{member_no}'
    order by present_time desc limit {page_size}"""
    logger.info(f"{event_name} sql {sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts()) or []
    ###
    for item in items:
        card_code = item.get("card_code")
        item['describe'] = f"转增:{card_code}"
    return items


async def search_coupon_event_obsoleted(app, member_no, from_time, to_time, page_size, keywords=None):
    event_name = "作废自制劵"
    if keywords and keywords not in event_name:
        return []
    sql = f"""select '{event_name}' as event_name, card_id , card_code , obsoleted_time as create_time from db_neocrm.t_crm_coupon_user_info
    where  obsoleted_time > '{from_time}' and obsoleted_time  < '{to_time}' and obsoleted_time is not NULL 
    and member_no = '{member_no}'  and code_status = 7
    order by obsoleted_time desc limit {page_size}"""
    logger.info(f"{event_name} sql {sql}")
    items = await app.mgr.execute(InstanceInfo.raw(sql).dicts()) or []
    ###
    for item in items:
        card_code = item.get("card_code")
        item['describe'] = f"作废:{card_code}"
    return items


async def search_card_event(app, member_no, openid, from_time, to_time, page_size, keywords):
    try:
        r1 = await search_merchant_send_event(app, openid, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"search_merchant_send_event error")
        r1 = []
    try:
        r2 = await search_merchant_redeem_event(app, openid, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"search_merchant_redeem_event error")
        r2 = []
    try:
        r3 = await search_coupon_event_received(app, member_no, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"r3 error")
        r3 = []
    try:
        r4 = await search_coupon_event_redeem(app, member_no, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"r4 error")
        r4 = []
    try:
        r5 = await search_coupon_event_present(app, member_no, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"r5 error")
        r5 = []
    try:
        r6 = await search_coupon_event_obsoleted(app, member_no, from_time, to_time, page_size, keywords)
    except Exception as ex:
        logger.info(f"r6 error")
        r6 = []
    logger.info(f"{r1} {r2} {r3} {r4} {r5} {r6}")
    return r1+r2+r3+r4+r5+r6


async def search_campaign_event(app, member_no, from_time, to_time, page_size, keywords=None):
    event_name = "参与活动"
    if keywords and keywords not in event_name:
        return []

    from_date = from_time.split(' ')[0]
    to_date = to_time.split(' ')[0]
    union_table = []
    date_list = date_slice(from_date, to_date)
    where = f"member_no = '{member_no}' "
    for one_date in date_list:
        fmt_date = one_date.replace('-', '')
        one_table = f"(select * from db_neocam.t_cam_campaign_record_{fmt_date} where {where})"
        union_table.append(one_table)
    union_tables = "union all ".join(union_table)
    sql = f"""
    SELECT t1.campaign_id as cid, '{event_name}' as event_name, t1.create_time, t1.prize_conf  FROM ( {union_tables}) t1  limit {page_size}
    """
    try:
        logger.info(f"{event_name} sql {sql}")
        items = await app.mgr.execute(InstanceInfo.raw(sql).dicts())
    except Exception as ex:
        logger.info("活动分区表可能不存在报错")
        items = []
    # 拼接事件的描述信息
    for item in items:
        #
        describe = ''
        prize_conf = item.get("prize_conf") or '{}'
        prize_conf = ujson.loads(prize_conf)
        coupon_list = prize_conf.get('coupon_list')
        points = prize_conf.get('points')
        if coupon_list:
            describe += f"领取的卡券: {','.join(coupon_list)}"
        if points:
            describe += f"增加的积分: {points}"
        item['describe'] = describe
    return items


async def search_wmp_app_event(app, openid, from_time, to_time, page_size, keywords=None):
    event_name = "打开小程序"
    if keywords and keywords not in event_name:
        return []
    sql = f"""select '打开小程序' as event_name, create_time  from db_event.t_wmp_app_event twae
        where create_time > '{from_time}' and create_time < '{to_time}'
        and openid='{openid}'
        order by create_time desc limit {page_size}
    """
    logger.info(f"{event_name} sql {sql}")
    items = await app.db_event_mgr.execute(InstanceInfo.raw(sql).dicts())
    return items