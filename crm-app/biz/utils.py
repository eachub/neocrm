import logging
from datetime import datetime, timedelta
import time

from playhouse.shortcuts import model_to_dict
from common.biz.const import RC
from common.biz.coupon_const import InterestsPeriodType
from common.models.helper import add_record_from_dict
from common.models.points import OrderInfo, OrderItem, RefundInfo, RefundItem

logger = logging.getLogger(__name__)


def plus_some_day(start_time, days=0, hours=0):
    # 计算过期时间和冻结时间
    if not days and not hours:
        return None
    if isinstance(start_time, str):
        start_time = datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S")
    new_day = start_time + timedelta(days=days, hours=hours)
    # 过期时间和冷冻时间精度,是否取整到整天 23:59:59
    return new_day
    # return new_day.strftime("%Y-%m-%d %H:%M:%S")
    
    
def gen_event_no(sn_prefix="EACH"):
    """创建随机事件no"""
    import uuid
    _uid4 = str(uuid.uuid4()).replace('-', '')
    _str = ''
    for _u in _uid4:
        _str += str(ord(_u))
    return sn_prefix + datetime.now().strftime('%Y%m%d%H%M%S') + (str(int(time.process_time() * 1000000))[:-4] + _str)[:12]


async def save_order(app, crm_id, member_no, order, platform=None, event_no=None):
    """保存订单信息"""
    if not order:
        return
    logger.info(f"订单信息保存 {member_no}")
    try:
        one = dict(order, crm_id=crm_id, member_no=member_no, event_no=event_no)
        await add_record_from_dict(app.mgr, OrderInfo, one, excluded=[], on_conflict=3,
                                   target_keys=['order_sn', 'mall_id'])
        item_list = order.get('item_list', [])
        for item in item_list:
            item_id = item.pop("item_id", "")
            # erp_sku_code
            erp_sku_code = item.get("outer_sku_code")
            item.update(dict(crm_id=crm_id, member_no=member_no, item_code=str(item_id),
                             erp_sku_code=erp_sku_code))
            await add_record_from_dict(app.mgr, OrderItem, item, on_conflict=2, target_keys=[])
    except Exception as ex:
        logger.info(f"保存订单信息失败")
        logger.exception(ex)


async def save_refund(app, crm_id, member_no, refund, platform=None):
    """保存退单的信息"""
    if not refund:
        return
    try:
        logger.info("退单信息save")
        one = dict(refund, crm_id=crm_id, member_no=member_no)
        await add_record_from_dict(app.mgr, RefundInfo, one, excluded=[], on_conflict=3,
                                   target_keys=['mall_id', 'order_sn', 'refund_id'])
        item_list = refund.get('item_list', [])
        for item in item_list:
            item.update(dict(crm_id=crm_id, member_no=member_no))
            await add_record_from_dict(app.mgr, RefundItem, item, on_conflict=2, target_keys=[])
    except Exception as ex:
        logger.exception(ex)


def gen_period_value(interests_period_type, dt=None):
    if not dt:
        dt = datetime.now()
    if interests_period_type == InterestsPeriodType.DAY.value:
        return dt.strftime('%Y%m%d')
    elif interests_period_type == InterestsPeriodType.WEEK.value:
        return dt.strftime('%Y%W')
    elif interests_period_type == InterestsPeriodType.MONTH.value:
        return dt.strftime('%Y%m')
    elif interests_period_type == InterestsPeriodType.YEAR.value:
        return dt.strftime('%Y')
    return 9999


if __name__ == '__main__':
    ret = gen_event_no()
    print(ret)
    