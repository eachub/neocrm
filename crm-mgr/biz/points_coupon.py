
import time
from common.models.coupon import CouponInfo


async def get_mall_points_card_ids(mall, mall_id, source='1'):
    flag, result = await mall.goods.search(dict(is_onsale="all", price_type="2,3", goods_type=4, page_id=1,
                                                page_size=200), mall_id, method="GET")
    assert flag, "获取积分商城卡券失败"
    goods_list = result.get('goods_list')
    card_ids = [x.get('extra').get('card_id') for x in goods_list if x.get('extra')]
    if str(source) == '1':
        card_ids = {x for x in card_ids if x and len(x) != 16}
    else:
        card_ids = {x for x in card_ids if x and len(x) == 16}
    return list(card_ids)


async def get_mall_points_card_list(crm_id, mgr, mall, mall_id, source='1'):
    card_ids = await get_mall_points_card_ids(mall, mall_id, source)
    if not card_ids:
        return []

    query = CouponInfo.select(CouponInfo.card_id, CouponInfo.coupon_id, CouponInfo.title,  CouponInfo.subtitle,
                              CouponInfo.source, CouponInfo.card_type, CouponInfo.begin_time, CouponInfo.end_time
                              ).where(CouponInfo.crm_id == crm_id, CouponInfo.removed == 0,
                                      CouponInfo.card_id.in_(card_ids)).order_by(CouponInfo.create_time.desc())
    coupons = await mgr.execute(query.dicts())
    return coupons
