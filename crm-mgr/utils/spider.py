#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import time
import asyncio
import os
from mtkext.proc import Processor
from argparse import Namespace
from types import FunctionType, MethodType
from inspect import isawaitable

import logging
logger = logging.getLogger()


async def _init_pools(cls, loop, cmd_args):
    from sanic.config import Config
    cls.conf = args = Config()
    args.update_config(f"../common/conf/{cmd_args.env}.py")
    if os.path.isfile("../conf/setting.py"):
        args.update_config("../conf/setting.py")
    else:
        args.update_config(f"../conf/{cmd_args.env}.py")
    ###
    from mtkext.cache import LocalCache
    cls.cache = LocalCache()
    ###
    # import aioredis
    # cls.redis = await aioredis.create_redis_pool(
    #     loop=loop, **args.PARAM_FOR_REDIS)
    ###
    from peewee_async import PooledMySQLDatabase, Manager
    db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
    from common.models.ecom import db_eros_crm
    db_eros_crm.initialize(db)
    cls.mgr = Manager(db_eros_crm, loop=loop)

    ###
    from mtkext.hcp import HttpClientPool
    cls.http = HttpClientPool(loop)


async def _kill_pools(cls):
    # await cls.jobs.close()
    await cls.http.close()
    await cls.mgr.close()
    # cls.redis.close()
    # await cls.redis.wait_closed()


def reload_stamp(fn, stamp=None):
    try:
        s = stamp or (fn and open(fn, "rt").read().strip())
        assert s, "NOT SPECIFIED [stamp]"
        from_time = int(time.mktime(time.strptime(s, "%Y%m%d%H%M%S")))
    except Exception as ex:
        logger.info(f"use default stamp: {ex}")
        from_time = int(time.time()) - 120
    # 修正结果：对齐自然5秒
    return from_time - (from_time % 5)


def update_stamp(fn, ts):
    try:
        s = time.strftime("%Y%m%d%H%M%S", time.localtime(ts))
        with open(fn, "wt") as fp: fp.write(s)
    except Exception as ex:
        logger.exception(ex)


class SpiderBase(Processor):
    ClientClass = None
    run_methods = []

    def __init__(self):
        self.fn = ""
        self.delta = 0

    async def fetch(self, client, from_time, to_time, run_method):
        raise Exception("爬虫类未实现fetch方法")

    async def init_client(self):
        raise Exception("爬虫类未实现init_client方法")

    async def run(self, i):
        assert self.fn, "需要指定时间戳文件名：self.fn"
        # assert self.delta, "需要指定爬取周期(秒)：self.delta"
        ###
        logger.info(f"Coroutine-{i} is ready...")
        prevStamp = reload_stamp(self.fn, stamp=None)
        logger.info(f"Coroutine-{i} start={prevStamp}, delta={self.delta}")
        ###
        client = await self.init_client()
        while (i == 0) and (not self.stopped):
            current = int(time.time())
            current -= (current % 5)
            if current - prevStamp >= self.delta:
                tasks = []
                for run_method in self.run_methods:
                    if not client:
                        logger.warning(f'client 初始化失败')
                        continue
                    one = self.fetch(client, prevStamp, current, run_method)
                    # 可以多添加几个方法
                    tasks.append(one)
                ###
                results = await asyncio.gather(*tasks, return_exceptions=True)
                okay = False
                for res in results:
                    if isinstance(res, Exception):
                        logger.exception(res)
                    elif res is True:
                        okay = True
                if okay is True:
                    prevStamp = current
                    update_stamp(self.fn, prevStamp)
            await asyncio.sleep(0.3)
        logger.info(f"Coroutine-{i} is stopped.")

    @classmethod
    async def execute(cls, i):
        client = await cls().init_client()
        await cls().fetch(client, None, None, None)
        await cls().release()

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args) #inherited
        await _init_pools(cls, loop, cmd_args)

    @classmethod
    async def release(cls):
        await _kill_pools(cls)
        await super().release() #inherited


    @classmethod
    async def exitfunc(cls, loop, env):
        if hasattr(cls, "on_exit") and isinstance(cls.on_exit, (FunctionType, MethodType)):
            cmd_args = Namespace(env=env)
            await cls.init(loop, cmd_args)
            result = cls().on_exit()
            if isawaitable(result): result = await result
            await cls.release()

