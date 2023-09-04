#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/7/31
"""

import asyncio
import sys

from peewee import fn

sys.path.insert(0, '..')
from common.models.coupon import UserCouponRedeemInfo, CouponInfo
from common.utils.misc import init_logger
from mtkext.proc import Processor


class CrmCouponStatTask(Processor):
    async def run(self, i):
        query = UserCouponRedeemInfo.select(
            UserCouponRedeemInfo.crm_id, UserCouponRedeemInfo.card_id,
            fn.count(i).alias("redeem_count")).group_by(UserCouponRedeemInfo.crm_id, UserCouponRedeemInfo.card_id).where(
            UserCouponRedeemInfo.rollback_status == 0)
        redeem_data = await self.mgr.execute(query.dicts())
        for i in redeem_data:
            await self.mgr.execute(CouponInfo.update({CouponInfo.redeem_count: i.get("redeem_count")}).where(
                CouponInfo.crm_id == i.get("crm_id"), CouponInfo.card_id == i.get("card_id")))

        await self.mgr.close()

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
    async def start(cls, loop, cmd_args):
        await cls.init(loop, cmd_args)
        await cls().run(0)
        await cls.release()


if __name__ == '__main__':
    init_logger(f"logs/coupon_redeem_tasker.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="coupon_redeem_tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test'))
    cmd_args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(CrmCouponStatTask.start(loop, cmd_args))
    loop.close()
