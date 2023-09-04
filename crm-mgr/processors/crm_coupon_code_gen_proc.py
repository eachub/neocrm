#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/28
"""
# 券码生成proc
import asyncio
import math

from common.biz.coupon_const import CouponCodeGenStatus, CouponCodeStatus
from common.models.coupon import CouponCodeGenInfo, CouponCodeInfo, CouponInfo
from mtkext.proc import Processor
from sanic.log import logger
from mtkext.sn import *

gen_count = 1000


class CrmCouponCodeGenProc(Processor):

    async def gen_code(self, coupon_gen_info):
        coupon_gen_id = coupon_gen_info.get("coupon_gen_id")
        card_id = coupon_gen_info.get("card_id")
        crm_id = coupon_gen_info.get("crm_id")
        gen_quantity = coupon_gen_info.get("quantity")
        result = await self.mgr.execute(CouponCodeGenInfo.update(
            {CouponCodeGenInfo.gen_status: CouponCodeGenStatus.GENERATING.value}).where(
            CouponCodeGenInfo.coupon_gen_id == coupon_gen_id, CouponCodeGenInfo.gen_status == CouponCodeGenStatus.PENDING.value))
        if not result:
            logger.info(f"{crm_id} {card_id} {coupon_gen_id} gen code status != {CouponCodeGenStatus.PENDING.name}")
            return None
        logger.info(f"{crm_id} {card_id} {coupon_gen_id} gen code starting!")
        tasks = []
        for _ in range(0, math.ceil(gen_quantity / gen_count)):
            if len(tasks) == 100:
                # 执行
                await asyncio.gather(*tasks)
                tasks = []
            if gen_quantity >= gen_count:
                tasks.append(self.gen_task(gen_count, crm_id, card_id, coupon_gen_id))
                gen_quantity = gen_quantity - gen_count
            else:
                tasks.append(self.gen_task(gen_quantity, crm_id, card_id, coupon_gen_id))
        else:
            await asyncio.gather(*tasks)
        gen_result = await self.mgr.execute(CouponCodeGenInfo.update(
            {CouponCodeGenInfo.gen_status: CouponCodeGenStatus.FINISH.value}).where(
            CouponCodeGenInfo.coupon_gen_id == coupon_gen_id, CouponCodeGenInfo.gen_status == CouponCodeGenStatus.GENERATING.value))
        logger.info(f"{crm_id} {card_id} {coupon_gen_id} {gen_result} gen code finished!")
        # 需要库存增加
        coupon_result = await self.mgr.execute(
            CouponInfo.update({CouponInfo.total_quantity: CouponInfo.total_quantity + coupon_gen_info.get("quantity")}).where(
                CouponInfo.crm_id == crm_id, CouponInfo.card_id == card_id))
        logger.info(f"更新 {crm_id} {card_id} {coupon_result} 库存!")

    async def gen_task(self, gen_len, crm_id, card_id, coupon_gen_id):
        gen_code_list = []
        for _ in range(0, gen_len):
            card_code = await create_sn18(self.redis, sep="", now=None, keybase="CRM-COUPON-SN-BASE")
            code_info = {"crm_id": crm_id, "card_id": card_id, "card_code": card_code, "coupon_gen_id": coupon_gen_id,
                         "card_code_status": CouponCodeStatus.INACTIVE.value}
            gen_code_list.append(code_info)
        await self.mgr.execute(CouponCodeInfo.insert_many(gen_code_list))

    async def run(self, i):
        while not self.stopped:
            need_gen_list = await self.mgr.execute(
                CouponCodeGenInfo.select(CouponCodeGenInfo.coupon_gen_id, CouponCodeGenInfo.crm_id,
                                         CouponCodeGenInfo.card_id, CouponCodeGenInfo.quantity).where(
                    CouponCodeGenInfo.gen_status == CouponCodeGenStatus.PENDING.value).dicts())
            if len(need_gen_list):
                gen_record = need_gen_list[0]
                await self.gen_code(gen_record)
            else:
                await asyncio.sleep(5)

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
