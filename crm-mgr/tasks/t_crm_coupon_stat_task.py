#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
date: 2022/7/12
"""
import asyncio
import sys

sys.path.insert(0, '..')
from common.models.coupon import UserCouponCodeInfo, UserCouponRedeemInfo, UserPresentCouponInfo, StatisticalCoupon
from common.utils.misc import init_logger
from mtkext.proc import Processor
from peewee import fn
from datetime import datetime, timedelta
from sanic.log import logger


class CrmCouponStatTask(Processor):
    async def run(self, i):
        stat_end_time = datetime.now()
        # 减一个小时
        stat_start_time = stat_end_time + timedelta(hours=-1)
        if stat_end_time.day != stat_start_time.day:
            # 跨天统计
            end_time = stat_end_time.date()
            start_time = stat_start_time.date()
            await self.stat(start_time, end_time, tdate=f"{stat_start_time: %Y-%m-%d}", thour=99)
        await self.stat(f"{stat_start_time: %Y-%m-%d %H}:00:00", f"{stat_end_time: %Y-%m-%d %H}:00:00",
                         tdate=f"{stat_start_time: %Y-%m-%d}", thour=stat_start_time.hour)

    async def stat(self, start_time, end_time, tdate, thour):
        await self.query(start_time, end_time, tdate, thour)
        await self.all_query(start_time, end_time, tdate, thour)
        pass

    async def query(self, start_time, end_time, tdate, thour):
        crm_card_receive_query = UserCouponCodeInfo.select(
            UserCouponCodeInfo.crm_id, UserCouponCodeInfo.card_id, fn.count(1).alias("receive_cards"),
            fn.count(UserCouponCodeInfo.member_no.distinct()).alias("receive_cards_user")).group_by(
            UserCouponCodeInfo.crm_id, UserCouponCodeInfo.card_id).where(
            UserCouponCodeInfo.received_time >= start_time, UserCouponCodeInfo.received_time <= end_time)
        receive_data = await self.mgr.execute(crm_card_receive_query.dicts())

        crm_card_redeem_query = UserCouponRedeemInfo.select(
            UserCouponRedeemInfo.crm_id, UserCouponRedeemInfo.card_id, fn.count(1).alias("redeem_cards"),
            fn.count(UserCouponRedeemInfo.member_no.distinct()).alias("redeem_cards_user")).group_by(
            UserCouponRedeemInfo.crm_id, UserCouponRedeemInfo.card_id).where(
            UserCouponRedeemInfo.redeem_time >= start_time, UserCouponRedeemInfo.redeem_time <= end_time)
        redeem_data = await self.mgr.execute(crm_card_redeem_query.dicts())

        crm_card_present_query = UserPresentCouponInfo.select(
            UserPresentCouponInfo.crm_id, UserPresentCouponInfo.card_id, fn.count(1).alias("present_cards"),
            fn.count(UserPresentCouponInfo.from_member_no.distinct()).alias("present_cards_user")).group_by(
            UserPresentCouponInfo.crm_id, UserPresentCouponInfo.card_id).where(
            UserPresentCouponInfo.present_time >= start_time, UserPresentCouponInfo.present_time <= end_time)
        present_data = await self.mgr.execute(crm_card_present_query.dicts())
        stat_info = {}

        for i in receive_data:
            key = f"{i.get('crm_id')}_{i.get('card_id')}"
            data = {"crm_id": i.get("crm_id"), "card_id": i.get("card_id"), "tdate": tdate, "thour": thour,
                    "receive_cards": i.get("receive_cards"), "receive_cards_user": i.get("receive_cards_user")}
            stat_info[key] = data
        for i in redeem_data:
            key = f"{i.get('crm_id')}_{i.get('card_id')}"
            if key in stat_info.keys():
                data = stat_info.get(key)
                data["redeem_cards"] = i.get("redeem_cards")
                data["redeem_cards_user"] = i.get("redeem_cards_user")
            else:
                data = {"crm_id": i.get("crm_id"), "card_id": i.get("card_id"), "tdate": tdate, "thour": thour,
                        "receive_cards": 0, "receive_cards_user": 0, "redeem_cards": i.get("redeem_cards"),
                        "redeem_cards_user": i.get("redeem_cards_user")}
            stat_info[key] = data
        for i in present_data:
            key = f"{i.get('crm_id')}_{i.get('card_id')}"
            if key in stat_info.keys():
                data = stat_info[key]
                data["present_cards"] = i.get("present_cards")
                data["present_cards_user"] = i.get("present_cards_user")
            else:
                data = {"crm_id": i.get("crm_id"), "card_id": i.get("card_id"), "tdate": tdate, "thour": thour,
                        "receive_cards": 0, "receive_cards_user": 0, "redeem_cards": i.get("redeem_cards"),
                        "redeem_cards_user": 0, "present_cards": 0, "present_cards_user": i.get("present_cards_user")}
            stat_info[key] = data
        insert_data = [v for _, v in stat_info.items()]
        logger.info(insert_data)
        if len(insert_data):
            await self.mgr.execute(StatisticalCoupon.insert_many(insert_data).on_conflict_ignore())
            logger.info(f"{len(insert_data)} record")
        else:
            logger.info(f"no record")

    async def all_query(self, start_time, end_time, tdate, thour):
        crm_card_receive_query = UserCouponCodeInfo.select(
            UserCouponCodeInfo.crm_id, fn.count(1).alias("receive_cards"),
            fn.count(UserCouponCodeInfo.member_no.distinct()).alias("receive_cards_user")).group_by(
            UserCouponCodeInfo.crm_id).where(
            UserCouponCodeInfo.received_time >= start_time, UserCouponCodeInfo.received_time <= end_time)
        receive_data = await self.mgr.execute(crm_card_receive_query.dicts())

        crm_card_redeem_query = UserCouponRedeemInfo.select(
            UserCouponRedeemInfo.crm_id, fn.count(1).alias("redeem_cards"),
            fn.count(UserCouponRedeemInfo.member_no.distinct()).alias("redeem_cards_user")).group_by(
            UserCouponRedeemInfo.crm_id).where(
            UserCouponRedeemInfo.redeem_time >= start_time, UserCouponRedeemInfo.redeem_time <= end_time)
        redeem_data = await self.mgr.execute(crm_card_redeem_query.dicts())

        crm_card_present_query = UserPresentCouponInfo.select(
            UserPresentCouponInfo.crm_id, fn.count(1).alias("present_cards"),
            fn.count(UserPresentCouponInfo.from_member_no.distinct()).alias("present_cards_user")).group_by(
            UserPresentCouponInfo.crm_id).where(
            UserPresentCouponInfo.present_time >= start_time, UserPresentCouponInfo.present_time <= end_time)
        present_data = await self.mgr.execute(crm_card_present_query.dicts())
        stat_info = {}

        for i in receive_data:
            key = f"{i.get('crm_id')}"
            data = {"crm_id": i.get("crm_id"), "card_id": None, "tdate": tdate, "thour": thour,
                    "receive_cards": i.get("receive_cards"), "receive_cards_user": i.get("receive_cards_user")}
            stat_info[key] = data
        for i in redeem_data:
            key = f"{i.get('crm_id')}"
            if key in stat_info.keys():
                data = stat_info.get(key)
                data["redeem_cards"] = i.get("redeem_cards")
                data["redeem_cards_user"] = i.get("redeem_cards_user")
            else:
                data = {"crm_id": i.get("crm_id"), "card_id": None, "tdate": tdate, "thour": thour,
                        "receive_cards": 0, "receive_cards_user": 0, "redeem_cards": i.get("redeem_cards"),
                        "redeem_cards_user": i.get("redeem_cards_user")}
            stat_info[key] = data
        for i in present_data:
            key = f"{i.get('crm_id')}"
            if key in stat_info.keys():
                data = stat_info[key]
                data["present_cards"] = i.get("present_cards")
                data["present_cards_user"] = i.get("present_cards_user")
            else:
                data = {"crm_id": i.get("crm_id"), "card_id": None, "tdate": tdate, "thour": thour,
                        "receive_cards": 0, "receive_cards_user": 0, "redeem_cards": i.get("redeem_cards"),
                        "redeem_cards_user": 0, "present_cards": 0, "present_cards_user": i.get("present_cards_user")}
            stat_info[key] = data
        insert_data = [v for _, v in stat_info.items()]
        logger.info(insert_data)
        if len(insert_data):
            await self.mgr.execute(StatisticalCoupon.insert_many(insert_data).on_conflict_ignore())
            logger.info(f"{len(insert_data)} record")
        else:
            logger.info(f"no record")

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()
        args.update_config(f"../common/conf/{cmd_args.env}.py")
        from peewee_async import PooledMySQLDatabase, Manager
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        from common.models.base import db_eros_crm
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)

    @classmethod
    async def release(cls):
        await cls.mgr.close()
        await super().release()
        logger.info("finish release-works")

    @classmethod
    async def start(cls, loop, cmd_args):
        await cls.init(loop, cmd_args)
        await cls().run(0)
        await cls.release()


if __name__ == '__main__':
    init_logger(f"logs/coupon_stat.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="coupon_stat_tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test'))
    cmd_args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(CrmCouponStatTask.start(loop, cmd_args))
    loop.close()
