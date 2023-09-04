#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import asyncio
from datetime import datetime
import logging
import os
import sys
import time
from mtkext.proc import Processor

sys.path.insert(0, "..")

from common.utils.misc import init_logger
from common.models.points import *
from biz.utils import gen_event_no
from common.models.helper import add_record_from_dict
from sanic.log import logger


# 处理积分自动过期 处理转赠过期 处理积分冻结


async def process_one_expire_points(app, info, event_at):
    logger.info(f"process expire points: {info}")
    crm_id = info['crm_id']
    member_no = info['member_no']
    points = info['points']
    origin_event_no = info['event_no']

    try:
        async with app.mgr.atomic() as t:
            # 可用积分表及时删除过期记录
            got1 = await app.mgr.execute(PointsAvailable.delete().where(
                PointsAvailable.auto_id == info['auto_id']
            ))

            if not got1:
                logger.info(f"got1={got1} not found {info['auto_id']} rollback")
                await t.rollback()
                return False

            # 积分概览表更新 todo 要不要再判断过期时间 冻结时间等参数
            got2 = await app.mgr.execute(PointsSummary.update({
                "expired_points": PointsSummary.expired_points + points,
                "active_points": PointsSummary.active_points - points
            }).where(
                PointsSummary.member_no == member_no, PointsSummary.crm_id == crm_id
            ))
            if not got2:
                logger.info(f"got2={got2} not update PointsSummary point={points} rollback")
                await t.rollback()
                return False

            # 积分明细表添加一条过期明细
            event_no = gen_event_no('EXPIRE')
            event_data = dict(
                crm_id=crm_id,
                member_no=member_no,
                event_no=event_no,
                action_scene="expire",
                event_type="expire",
                event_at=event_at,
                points=points,
                expire_time=info.get("expire_time"),
                unfreeze_time=info.get("unfreeze_time"),
                operator="system",
                event_desc="过期机器人自动处理",
                origin_event_no=origin_event_no
            )
            logger.info(f"add event_no:{event_no} 过期积分")
            got3 = await add_record_from_dict(app.mgr, PointsHistory, event_data)
            if not got3:
                logger.info(f"got3={got3} rollback add event_no:{event_no} 过期积分")
                await t.rollback()
                return False
    except Exception as ex:
        logger.exception(ex)
        return False
    return True


async def process_one_transfer_points(app, info):
    """info 是转赠积分记录的数据"""
    try:
        async with app.mgr.atomic() as t:
            transfer_no = info['transfer_no']
            auto_id = info['auto_id']
            # 可用积分表的转赠标识删除
            points_detail = info['points_detail']
            if points_detail:
                for points_ava in points_detail:
                    ava_auto_id = points_ava['auto_id']
                    got1 = await app.mgr.execute(PointsAvailable.update(transfer_expire=None).where(
                        PointsAvailable.auto_id == ava_auto_id, PointsAvailable.transfer_expire != None
                    ))
                    if not got1:
                        logger.info(f"处理转赠的时候没有更新 transfer_no={transfer_no} ")
            # 积分转赠记录表处理
            await app.mgr.execute(PointsTransfer.update(
                done=-1
            ).where(PointsTransfer.auto_id == auto_id))
            logger.info(f"process 转增积分 transfer_no={transfer_no}")
    except Exception as ex:
        logger.exception(ex)
        return False
    return True


async def process_one_unfreeze_points(app, info, event_at):
    """解冻 增加事件记录"""
    logger.info(f"event_at:{event_at} process unfreeze:{info}")
    try:
        async with app.mgr.atomic() as t:
            points = info['points']
            crm_id = info['crm_id']
            member_no = info['member_no']
            # 修改可用积分表
            act_id = info['auto_id']
            origin_event_no = info['event_no']
            await app.mgr.execute(PointsAvailable.update(unfreeze_time=None).where(PointsAvailable.auto_id==act_id))
            # 积分概览处理
            got2 = await app.mgr.execute(PointsSummary.update({
                "freeze_points": PointsSummary.freeze_points - points,
                "active_points": PointsSummary.active_points + points,

            }).where(
                PointsSummary.member_no == member_no, PointsSummary.crm_id == crm_id
            ))
            if not got2:
                await t.rollback()
                return False

            # 积分明细表添加一条解冻明细
            event_no = gen_event_no('EXPIRE')
            event_data = dict(
                crm_id=crm_id,
                member_no=member_no,
                event_no=event_no,
                action_scene="unfreeze",
                event_type="unfreeze",
                event_at=event_at,
                points=points,
                expire_time=info.get("expire_time"),
                unfreeze_time=info.get("unfreeze_time"),
                operator="system",
                event_desc="解冻机器人自动处理",
                origin_event_no=origin_event_no
            )
            await add_record_from_dict(app.mgr, PointsHistory, event_data)
            logger.info(f"unfree event_no={event_no}")
    except Exception as ex:
        logger.exception(ex)
        return False
    return True
    pass


async def handle_expire_points(app, event_at, member_no=None):
    """处理过期的积分 触发的地方"""
    where = [
        (PointsAvailable.expire_time < event_at) & (PointsAvailable.expire_time != None)
    ]
    if member_no:
        where.append(PointsAvailable.member_no == member_no)
    _query = PointsAvailable.select().where(*where).order_by(PointsAvailable.expire_time.asc()).dicts()
    _list = await app.mgr.execute(_query)
    if not _list:
        logger.info("not need process")
        await asyncio.sleep(1)
        return
    for info in _list:
        await asyncio.sleep(0.01)
        await process_one_expire_points(app, info, event_at=event_at)
    ### 记录事件
    in_obj = dict(
        types="by_day",
        code="expirt_points",
        task_time=event_at,
    )
    await app.mgr.execute(TaskRecord.insert(in_obj))


async def handle_transfer_points(app, event_at, member_no=None):
    model = PointsTransfer
    where = [
        (model.transfer_expire < event_at) & (model.transfer_expire != None), model.done == 0
    ]
    if member_no:
        where.append(model.from_user == member_no)
    _query = model.select().where(*where).order_by(model.transfer_expire.asc()).dicts()
    _list = await app.mgr.execute(_query)
    if not _list:
        logger.info("not need process")
        await asyncio.sleep(0.5)
        return
    for info in _list:
        await asyncio.sleep(0.01)
        await process_one_transfer_points(app, info)
    ### 记录事件
    in_obj = dict(
        types="by_day",
        code="transfer_expire",
        task_time=event_at,
    )
    await app.mgr.execute(TaskRecord.insert(in_obj))


async def handle_unfreeze_points(app, event_at, member_no=None):
    model = PointsAvailable
    where = [
        model.unfreeze_time !=None,
        model.unfreeze_time <= event_at
    ]
    if member_no:
        where.append(model.member_no == member_no)
    _query = model.select().where(*where).order_by(model.unfreeze_time.asc()).dicts()
    _list = await app.mgr.execute(_query)
    if not _list:
        logger.info("not need process")
        await asyncio.sleep(0.5)
        return
    for info in _list:
        await process_one_unfreeze_points(app, info, event_at=event_at)
        await asyncio.sleep(0.01)
    ### 记录事件
    in_obj = dict(
        types="by_day",
        code="unfreeze_expire",
        task_time=event_at,
    )
    await app.mgr.execute(TaskRecord.insert(in_obj))


class TaskProc(Processor):

    async def run(self, i):
        # cmd时间参数娇艳
        try:
            event_at = datetime.now()
            logger.info(f"process data event_at = {event_at}")
            # 处理过期
            await handle_expire_points(self, event_at=event_at)
            # 处理转赠过期
            await handle_transfer_points(self, event_at=event_at)
            #  解冻处理
            await handle_unfreeze_points(self, event_at=event_at)
        except Exception as ex:
            logger.exception(ex)
            await asyncio.sleep(0.2)
        await asyncio.sleep(3)

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()

        # 加载配置
        def update_config(args, path):
            if not os.path.exists(path):
                return
            args.update_config(path)

        update_config(args, f"../common/conf/{cmd_args.env}.py")
        update_config(args, f"../conf/{cmd_args.env}.py")

        ###
        from mtkext.cache import LocalCache
        cls.cache = LocalCache()
        from mtkext.hcp import HttpClientPool
        # app.http = HttpClientPool(loop=loop, client=client)
        ###
        import aioredis
        cls.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        from common.models.base import db_eros_crm
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)

    @classmethod
    async def release(cls):
        await cls.mgr.close()
        cls.redis.close()
        await cls.redis.wait_closed()
        await super().release()
        logger.info("finish release-works")

    @classmethod
    async def start(cls, loop, cmd_args):
        await cls.init(loop, cmd_args)
        await cls().run(1)
        await cls.release()


if __name__ == '__main__':
    init_logger(f"logs/points_task.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test', 'local'))
    cmd_args = parser.parse_args()
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TaskProc.start(loop, cmd_args))
    loop.close()
