#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import asyncio
import logging
import os
import sys

import ujson
from mtkext.mq import MessageQueue
from mtkext.proc import Processor
from sanic.kjson import json_dumps

sys.path.insert(0, "..")
from biz.utils import gen_event_no
from utils.misc import init_logger


logger = logging.getLogger(__name__)


async def _handle_give_coupon(app, crm_id, coupon):
    pass


async def handle_one_message(app, task):
    """处理这条task记录"""
    # 请求的包体 action body crm_id
    action = task.get("action")
    body = task.get("body")
    crm_id = task.get("crm_id")
    if action == 'give_user_coupon':
        """ action_item = dict(
            action='give_user_coupon',
            crm_id=crm_id,
            body=dict(card_info=card_info, member_no=member_no, event_at=datetime.now()))"""
        member_no = body.get("member_no")
        card_info = body.get("card_info")
        receive_id = gen_event_no("SEND")
        req_obj = dict(member_no=member_no, card_info=card_info, outer_str="等级权益赠送", receive_id=receive_id)
        flag, result = await app.client_crm.card.member_receive(req_obj, crm_id=crm_id, method='POST')
        logger.info(f"give_user_coupon flag={flag} result={result}")


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

        update_config(args, f"../conf/{cmd_args.env}.py")
        logger.info(cls.conf)
        ###
        from mtkext.cache import LocalCache
        cls.cache = LocalCache()
        ###
        import aioredis
        cls.redis = await aioredis.create_redis_pool(loop=loop, **args.PARAM_FOR_REDIS)
        queue_name = args.MQ_CRM_ADAPT_TASK
        cls.mq = MessageQueue(cls.redis, queue_name)
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        from models import db_neocrm_adapt
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        db_neocrm_adapt.initialize(db)
        cls.mgr = Manager(db_neocrm_adapt, loop=loop)
        ###
        from aiohttp import ClientSession, ClientTimeout, TCPConnector, DummyCookieJar
        client = ClientSession(connector=TCPConnector(
            limit=1000, keepalive_timeout=300, ssl=False, loop=loop),
            cookie_jar=DummyCookieJar(),
            json_serialize=json_dumps,
            timeout=ClientTimeout(total=120))

        from mtkext.hcp import HttpClientPool
        cls.http = HttpClientPool(loop=loop, client=client)
        ###
        # 初始化crm client
        from clients import CrmClient
        cls.client_crm = CrmClient(cls.http, url_prefix=cls.conf.CRM_APP_SERVER_URL)

    @classmethod
    async def release(cls):
        await cls.http.close()
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
