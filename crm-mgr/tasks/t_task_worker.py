#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import os
import sys

import ujson
from mtkext.mq import MessageQueue

from biz import utils
from mtkext.proc import Processor
import asyncio
import logging

sys.path.insert(0, "..")
from common.biz.points import calculate_add_points_by_rules, produce_points_event
from common.models.helper import get_rules_by_action
from common.biz.utils import gen_event_no
from common.utils.misc import init_logger
from common.models.member import *
from common.biz.member import score_change_member

logger = logging.getLogger(__name__)


async def handle_user_inviter(app, crm_id, body):
    try:
        async with app.mgr.atomic() as t:
            member_no = body.get('member_no')
            nickname = body.get('nickname')
            event_at = body.get("event_at")
            event_at = datetime.strptime(event_at, "%Y-%m-%d %H:%M:%S")
            invite_code = body.get("invite_code")
            if not invite_code:
                return
            member_info = await app.mgr.execute(MemberInfo.select().where(MemberInfo.invite_code == invite_code))
            in_member_no = member_info.member_no
            # 处理invite_code 为这个用户增加积分
            # 推送到适配层的队列里面
            # 写入队列调用增加成长值的接口
            _key = app.conf.MQ_CRM_ADAPT_TASK
            action = "give_user_points_byrule"
            body = dict(
                member_no=in_member_no,
                action_scene="invite_user",
                event_desc=f"您邀请了用户{nickname}注册获取积分",
                event_at=event_at,
            )
            task_body = dict(crm_id=crm_id, action=action, body=body)
            await app.redis.lpush(_key, ujson.dumps(task_body, ensure_ascii=False))
            logger.info(f"give_user_points_byrule push {_key} {task_body}")
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        logger.info("失败")


async def handle_user_register(app, crm_id, body):
    try:
        member_no = body.get('member_no')
        event_at = body.get("event_at")
        event_at = datetime.strptime(event_at, "%Y-%m-%d %H:%M:%S")
        _key = app.conf.MQ_CRM_ADAPT_TASK
        action = "give_user_points_byrule"
        body = dict(
            member_no=member_no,
            action_scene="register",
            event_desc=f"用户注册",
            event_at=event_at,
        )
        task_body = dict(crm_id=crm_id, action=action, body=body)
        await app.redis.lpush(_key, ujson.dumps(task_body, ensure_ascii=False))
        logger.info(f"give_user_points_byrule register push {_key} {task_body}")
        # 计算成长值
        change_score = 0
        # 增加等级和权益
        await score_change_member(app, crm_id, member_no, change_score)
    except Exception as ex:
        logger.exception(ex)
        logger.info("失败")


async def handle_one_message(app, task):
    """处理这条task记录"""
    # 请求的包体 action body crm_id
    action = task.get("action")
    body = task.get("body")
    crm_id = task.get("crm_id")
    if action == 'user_register':
        # 新用户注册
        # 增加一个 event_data
        # 增加会员的积分
        # 增加邀请者的积分
        await handle_user_register(app, crm_id, body)
        await handle_user_inviter(app, crm_id, body)


class TaskProc(Processor):
    async def run(self, i):
        while not self.stopped:
            try:
                msg = await self.mq.pop_front()
                if not msg:
                    await asyncio.sleep(0.1)
                    continue
                job_tasks = [msg]
                for msg in job_tasks:
                    logger.info(f"detect: {msg.decode()}")
                    obj = ujson.loads(msg)
                    await handle_one_message(self, obj)
            except Exception as ex:
                logger.exception(ex)
                await asyncio.sleep(0.5)
            await asyncio.sleep(0.5)
        logger.info(f"Coroutine-{i} is stopped.")

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
        queue_name = args.MQ_CRM_TASK
        cls.mq = MessageQueue(cls.redis, queue_name)
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


if __name__ == "__main__":
    init_logger(f"task_worker.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test'))
    cmd_args = parser.parse_args()
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TaskProc.start(loop, cmd_args.env))
    loop.close()
