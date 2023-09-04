#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/30
"""
# 券码导入proc
import asyncio

from common.biz.coupon_const import CardSource, CouponCodeStatus
from common.models.coupon import CouponInfo, CouponCodeInfo
from mtkext.proc import Processor
from sanic.log import logger

DEPOSIT = 50000
BATCH_NUM = 10000


class CrmCouponCodeExportProc(Processor):

    async def export_card_code(self, crm_id, card_id, card_key):
        async with self.mgr.atomic():
            # 更新激活券码数量 开启事务锁
            await self.mgr.execute(CouponInfo.update({CouponInfo.active_quantity: CouponInfo.active_quantity + BATCH_NUM}).where(
                CouponInfo.crm_id == crm_id, CouponInfo.card_id == card_id))
            # 获取批量搭配
            batch_coupon_code = await self.mgr.execute(CouponCodeInfo.select().where(
                CouponCodeInfo.crm_id == crm_id, CouponCodeInfo.card_id == card_id,
                CouponCodeInfo.card_code_status == CouponCodeStatus.INACTIVE.value).limit(BATCH_NUM).dicts())
            code_list = []
            auto_id_list = []
            for item in batch_coupon_code:
                code_list.append(item.get("card_code"))
                auto_id_list.append(item.get("auto_id"))
            code_len = len(batch_coupon_code)
            if code_len > 0:
                await self.redis.lpush(card_key, *code_list)
                # 修改券码状态
                num = await self.mgr.execute(
                    CouponCodeInfo.update({CouponCodeInfo.card_code_status: CouponCodeStatus.ACTIVE.value}).where(
                        CouponCodeInfo.crm_id == crm_id, CouponCodeInfo.card_id == card_id, CouponCodeInfo.auto_id.in_(auto_id_list)))
                code_len = len(batch_coupon_code)
                logger.info(f"crm_id {crm_id} card_id {card_id} BATCH_NUM {BATCH_NUM} query len {code_len} update len {num}")
                if code_len != BATCH_NUM:
                    # 修改激活库存数
                    await self.mgr.execute(
                        CouponInfo.update({CouponInfo.active_quantity: CouponInfo.active_quantity + (code_len - BATCH_NUM)}).where(
                            CouponInfo.crm_id == crm_id, CouponInfo.card_id == card_id))
            else:
                # todo 需要补充库存但是没有生成可用的库存数
                pass
        await asyncio.sleep(10)
        
    async def run(self, i):
        while not self.stopped:
            coupon_list = await self.mgr.execute(CouponInfo.select(CouponInfo.crm_id, CouponInfo.card_id).where(
                CouponInfo.removed == 0, CouponInfo.source == CardSource.CRM.value).dicts())
            for coupon in coupon_list:
                crm_id = coupon.get("crm_id")
                card_id = coupon.get("card_id")
                # 券码导入key
                card_key = self.conf.CRM_COUPON_CODE_QUEUE_FORMAT.format(crm_id=crm_id, card_id=card_id)
                code_len = await self.redis.llen(card_key)
                if code_len > DEPOSIT:
                    await asyncio.sleep(1)
                    continue
                await self.export_card_code(crm_id, card_id, card_key)

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()
        args.update_config(f"../common/conf/{cmd_args.env}.py")
        ###
        import aioredis
        cls.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        from common.models.base import db_eros_crm
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)

    @classmethod
    async def release(cls):
        await cls.mgr.close()
        cls.redis.close()
        await cls.redis.wait_closed()
        await super().release()
        logger.info("finish release-works")
