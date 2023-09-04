# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta
import time
import abc
import asyncio

from peewee import Model
from sanic.log import logger, set_logger
from mtkext.db import sql_printf, safe_string, peewee_normalize_dict


class MySQLTaskBase(metaclass=abc.ABCMeta):
    """
    使用前需要生成派生类，实现make_tasks方法：
    返回一个由3元组(datafunc, StatModel, params)构成的数组。
    注意1：datafunc包含的变量tdate, thour, from_time, to_time, extra_conds将被代入取值。
        如果还有其他参数也需要替换，可以通过params字典参数代入。
    注意2：sql_printf和format的区别在于，前者会根据类型决定代入时是否添加引号。
    """

    def __init__(self, mgr, mgv, redis, **kwargs):
        self.__mgr = mgr
        self.__mgv = mgv  # 读库
        self.__redis = redis
        self.__kwargs = kwargs

    @property
    def mgr(self):
        return self.__mgr

    @property
    def redis(self):
        return self.__redis

    @staticmethod
    async def data_func(mgr, from_time, to_time, tdate, thour, **params):
        return []

    @abc.abstractmethod
    async def make_tasks(self):
        return [(self.data_func, Model, {})]

    async def execute(self, from_time, to_time, tdate, thour):
        ###
        tasks = []
        for fetch_data_func, model, params in await self.make_tasks():
            try:
                items = await fetch_data_func(self.__mgv, from_time, to_time, tdate, thour, **params)
                if items and model:
                    for row in items:
                        in_data = peewee_normalize_dict(model, row)
                        got = await self.__mgr.execute(model.insert(in_data).on_conflict(update=in_data))
                        logger.info(f"{row}===>处理一条: {got}")
            except Exception as ex:
                logger.exception(ex)
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(results)

    async def exec_hourly_by_timestamp(self, from_date, from_hour):
        from_time = int(time.mktime(from_date.timetuple())) + (from_hour * 3600)
        to_time = from_time + 3599
        return await self.execute(from_time, to_time, from_date, from_hour)

    async def exec_daily_by_timestamp(self, from_date, from_hour=99):
        from_time = int(time.mktime(from_date.timetuple()))
        to_time = from_time + 86399
        return await self.execute(from_time, to_time, from_date, from_hour)

    async def exec_hourly_by_datetime(self, from_date, from_hour):
        tdate = f"{from_date:%Y-%m-%d}"
        from_time = f"{tdate} {from_hour:02d}:00:00"
        to_time = f"{tdate} {from_hour:02d}:59:59"
        return await self.execute(from_time, to_time, from_date, from_hour)

    async def exec_daily_by_datetime(self, from_date, from_hour=99):
        to_date = from_date + timedelta(days=1)
        from_time = f"{from_date:%Y-%m-%d} 00:00:00"
        to_time = f"{from_date:%Y-%m-%d} 23:59:59"
        return await self.execute(from_time, to_time, from_date, from_hour)

    EXEC_DICT = {
        (True, True): exec_hourly_by_timestamp,
        (True, False): exec_daily_by_timestamp,
        (False, True): exec_hourly_by_datetime,
        (False, False): exec_daily_by_datetime,
    }

    @classmethod
    async def start(cls, loop, conf, from_date, from_hour, **kwargs):
        use_timestamp = kwargs.get("use_timestamp") in (True, 1, "1", "yes")
        if from_hour == 99:
            is_hourly = False
        else:
            is_hourly = True
            assert 0 <= from_hour <= 23, "Invalid cmd_args: from_hour"
        func = cls.EXEC_DICT.get((use_timestamp, is_hourly))
        logger.info(f"执行{func.__name__}： from_date={from_date} from_hour={from_hour}")

        ###
        async def exec_func(mgr, mgv, redis, conf, **kwargs):
            app = cls(mgr, mgv, redis, **kwargs)
            await func(app, from_date, from_hour)

        await run_with_env(loop, conf, exec_func, **kwargs)


"""
Note: exec_func is an async-function like:
`exec_func(mgr, chc, redis, conf, **kwargs)`
"""


async def run_with_env(loop, conf, exec_func, **kwargs):
    from common.models.analyze import db_eros_crm
    from biz.utils import init_db_manager
    # 第一个是写的库存 第二个是只读库
    mgr, mgv = init_db_manager(loop, db_eros_crm, conf.PARAM_FOR_MYSQL, conf.PARAM_FOR_VIEW)
    import aioredis
    redis = await aioredis.create_redis_pool(loop=loop, **conf.PARAM_FOR_REDIS)
    ###
    try:
        await exec_func(mgr, mgv, redis, conf, **kwargs)
    except Exception as ex:
        logger.exception(ex)
    ###
    await mgr.close()
    await mgv.close()
    redis.close()
    await redis.wait_closed()


"""
入口函数，其中kwargs参数将传入TaskClass的__init__，可设置:
   + 并行处理： parallel=True
   + 使用timestamp时间格式：use_timestamp=True
在执行路径内，要有common软连接，以装载配置。
"""


def main(TaskClass, **kwargs):
    from argparse import ArgumentParser
    parser = ArgumentParser(prog="StatTask-Runner")
    parser.add_argument('--env', type=str, required=True, choices=('prod', 'test', 'local'))
    parser.add_argument('--from-date', dest='from_date', type=str, required=True, help='eg. 2021-08-01')
    parser.add_argument('--from-hour', dest='from_hour', type=int, default=99, help='wanted when hourly')
    cmd_args = parser.parse_args()
    set_logger(level="INFO", filename="logs/chtask-stat.log", count=30)
    logger.info(f"==>命令行参数：{cmd_args}")
    from_date = datetime.strptime(cmd_args.from_date, "%Y-%m-%d").date()
    ###
    from sanic.config import Config
    conf = Config()
    conf.update_config(f"../common/conf/{cmd_args.env}.py")
    logger.info(f"==>配置参数：{conf}")
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TaskClass.start(loop, conf, from_date, cmd_args.from_hour, **kwargs))
    loop.close()
