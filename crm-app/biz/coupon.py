# -*- coding: utf-8 -*-
"""
"""
from peewee import DoesNotExist
from peewee_async import Manager

from common.models.base import CRMModel
from mtkext.db import peewee_normalize_dict
from sanic.log import logger
from common.models.helper import _query_by_key_id
from common.models.coupon import UserInterestsCostInfo

async def card_list_plug(mgr, card_list_result, member_no, crm_id):
    # 加入额度和频次相关字段
    interests_rows = []
    for x in card_list_result:
        if x.get("interests_type"):
            interests_rows.append(x)

    if interests_rows:
        card_ids = [x.get("card_id") for x in interests_rows]
        card_codes = [x.get("card_code") for x in interests_rows]
        _query = UserInterestsCostInfo.select(
            UserInterestsCostInfo.card_code,
            UserInterestsCostInfo.interests_period_value,
            UserInterestsCostInfo.redeem_amount, UserInterestsCostInfo.create_time,
            UserInterestsCostInfo.update_time).where(
            UserInterestsCostInfo.member_no == member_no,
            UserInterestsCostInfo.crm_id == crm_id,
            UserInterestsCostInfo.card_code.in_(card_codes),
            UserInterestsCostInfo.card_id.in_(card_ids),
        )
        logger.info(f"query interests cost: {_query.sql()}")
        interests_results = await mgr.execute(_query.dicts())
        code_interests = dict()
        for x in interests_results:
            code = x.get("card_code")
            amount = x.get("redeem_amount")
            code_interest = code_interests.get(code, {
                "total_redeem_amount": 0,
                "period_redeem_amount": [],
            })
            code_interest["total_redeem_amount"] += amount
            code_interest["period_redeem_amount"].append({
                "interests_period_value": x.get("interests_period_value"),
                "redeem_amount": amount,
            })
            code_interests[code] = code_interest

        for x in card_list_result:
            card_code = x.get("card_code")
            code_interest = code_interests.get(card_code, {})
            x.update(code_interest)
    return card_list_result
