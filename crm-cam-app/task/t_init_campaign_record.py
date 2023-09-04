#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import logging
import operator
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from functools import reduce

from mtkext.db import peewee_normalize_dict
from mtkext.db import FlexModel
from mtkext.proc import Processor
from peewee_async import PooledMySQLDatabase, Manager
sys.path.insert(0, os.path.dirname(os.getcwd()))

from common.models.cam import CampaignRecord
from datetime import timedelta, datetime
logger = logging.getLogger(__name__)


class CampaignProc(Processor):

    async def run(self, i):
        logger.info(f'Coroutine-{i} is ready ...')
        try:
            _now =  datetime.now()
            for i in range(-5,10):
                _date = (_now + timedelta(days=i)) .strftime("%Y%m%d")
                record_cls = FlexModel.get(CampaignRecord, _date)
                logger.info(f"create table {record_cls}")
        except Exception as ex:
            logger.error(ex)
        logger.info(f'Coroutine-{i} is stopped.')

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()
        args.update_config(f'../common/conf/{cmd_args.env}.py')
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        from common.models.cam import db_neocam
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        db_neocam.initialize(db)
        cls.mgr = Manager(db_neocam, loop=loop)
        ###
        logger.info('init finish!')

    @classmethod
    async def release(cls):
        ###
        await cls.mgr.close()
        ###
        logger.info('finish release-works')


async def main(loop, cmd_args):
    spider = CampaignProc()
    await spider.init(loop, cmd_args)
    await spider.run(0)
    await spider.release()


# 日志参数定义
def init_logger(filename, level=logging.DEBUG, count=90):
    import logging.handlers
    _handler = logging.handlers.TimedRotatingFileHandler(filename, when='midnight', interval=1, backupCount=count)
    _handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s'))
    _root = logging.getLogger()
    _root.setLevel(level)  # logging.INFO
    del _root.handlers[:]
    _root.addHandler(_handler)
    return _root


if __name__ == '__main__':
    init_logger(f'logs/crontab.t_init_campaign_record.log', level=logging.INFO, count=90)

    ###
    from argparse import ArgumentParser
    parser = ArgumentParser(prog='InitCampaignRecord')
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test', 'zzn'))
    cmd_args = parser.parse_args()
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, cmd_args))
    loop.close()
