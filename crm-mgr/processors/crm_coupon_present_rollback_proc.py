#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/7/7
"""
import asyncio
from datetime import datetime, timedelta

from common.biz.coupon_const import UserPresentStatus, UserCardCodeStatus
from common.models.base import CRMModel
from common.models.coupon import UserPresentCouponInfo, UserCouponCodeInfo
from mtkext.proc import Processor
from sanic.log import logger


class CrmCouponPresentRollbackProc(Processor):

    async def run(self, i):
        while not self.stopped:
            crm_list = await self.mgr.execute(CRMModel.select(CRMModel.crm_id, CRMModel.coupon_present_validity).dicts())
            tasks = [self.crm_present(i.get("crm_id"), i.get("coupon_present_validity")) for i in crm_list]
            await asyncio.gather(*tasks)
            await asyncio.sleep(60 * 2)
        pass

    async def crm_present(self, crm_id, present_validity):
        now = datetime.now()
        data = await self.mgr.execute(UserPresentCouponInfo.select(
            UserPresentCouponInfo.card_id, UserPresentCouponInfo.card_code, UserPresentCouponInfo.present_gen_id,
            UserPresentCouponInfo.from_member_no).where(
            UserPresentCouponInfo.crm_id == crm_id,
            UserPresentCouponInfo.present_status == UserPresentStatus.PRESENTING.value,
            UserPresentCouponInfo.present_time <= now - timedelta(present_validity)).dicts())
        async with self.mgr.atomic():
            result = await self.mgr.execute(UserPresentCouponInfo.update({
                UserPresentCouponInfo.present_status: UserPresentStatus.AUTO_GOBACK.value,
                UserPresentCouponInfo.go_back_time: now
            }).where(UserPresentCouponInfo.crm_id == crm_id,
                     UserPresentCouponInfo.present_status == UserPresentStatus.PRESENTING.value,
                     UserPresentCouponInfo.present_time <= now - timedelta(present_validity)).dicts())
            logger.info(f"{now} update go back length {result}")
            for i in data:
                # todo
                update_query = UserCouponCodeInfo.update(
                    {UserCouponCodeInfo.code_status: UserCardCodeStatus.AVAILABLE.value}
                ).where(UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == i.get("from_member_no"),
                        UserCouponCodeInfo.card_id == i.get("card_id"), UserCouponCodeInfo.card_code == i.get("card_code"),
                        UserCouponCodeInfo.code_status == UserCardCodeStatus.PRESENTING.value, UserCouponCodeInfo.end_time > now
                        )
                logger.info(update_query.sql())
                result = await self.mgr.execute(update_query)
                if not result:
                    update_query = UserCouponCodeInfo.update(
                        {UserCouponCodeInfo.code_status: UserCardCodeStatus.EXPIRED.value, UserCouponCodeInfo.expired_time: now}
                    ).where(UserCouponCodeInfo.crm_id == crm_id, UserCouponCodeInfo.member_no == i.get("from_member_no"),
                            UserCouponCodeInfo.card_id == i.get("card_id"), UserCouponCodeInfo.card_code == i.get("card_code"),
                            UserCouponCodeInfo.code_status == UserCardCodeStatus.PRESENTING.value, UserCouponCodeInfo.end_time <= now
                            )
                    result = await self.mgr.execute(update_query)

        pass

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()
        args.update_config(f"../common/conf/{cmd_args.env}.py")
        ###
        # import aioredis
        # cls.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        from common.models.base import db_eros_crm
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)

    @classmethod
    async def release(cls):
        await cls.mgr.close()
        # cls.redis.close()
        # await cls.redis.wait_closed()
        await super().release()
        logger.info("finish release-works")
