#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/7/7
"""
import asyncio
import sys
sys.path.insert(0, '..')

from datetime import datetime, timedelta

from common.biz.coupon_const import UserPresentStatus, UserCardCodeStatus
from common.models.base import CRMModel
from common.models.coupon import UserPresentCouponInfo, UserCouponCodeInfo
from common.utils.misc import init_logger
from mtkext.proc import Processor
from sanic.log import logger


class CrmCouponExpiredProc(Processor):

    async def run(self, i):
        now = datetime.now()
        update_query = UserCouponCodeInfo.update({
            UserCouponCodeInfo.code_status: UserCardCodeStatus.EXPIRED.value, UserCouponCodeInfo.expired_time: now
        }).where(UserCouponCodeInfo.end_time <= now, UserCouponCodeInfo.code_status == UserCardCodeStatus.AVAILABLE.value)
        length = await self.mgr.execute(update_query)
        logger.info(f"{update_query.sql()} count {length}")

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
    init_logger(f"logs/coupon_expired.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="coupon_expired_tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test'))
    cmd_args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(CrmCouponExpiredProc.start(loop, cmd_args))
    loop.close()
