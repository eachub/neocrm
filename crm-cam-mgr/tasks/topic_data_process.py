import asyncio
import logging
import re
from urllib import parse

import sys

sys.path.insert(0, '..')

import ujson
from mtkext.db import peewee_normalize_dict
from mtkext.proc import Processor

from common.models.event import WebTrafficEvent, WxmpShareEvent

logger = logging.getLogger(__name__)


class TaskHandle():
    def __init__(self, app, loop, cmd_args):
        self.app = app
        self.loop = loop
        self.cmd_args = cmd_args

    async def load_conf(self):
        from sanic.config import Config
        self.app.conf = args = Config()
        args.update_config(f"../conf/{self.cmd_args.env}.py")
        args.update_config(f"../common/conf/{self.cmd_args.env}.py")
        ###
        from mtkext.hcp import HttpClientPool
        self.app.http = HttpClientPool(self.loop)
        ###
        import aioredis
        self.app.redis = await aioredis.create_redis_pool(
            loop=self.loop, **args.PARAM_FOR_REDIS)
        ###
        from common.models.event import db_neocam
        from peewee_async import Manager, PooledMySQLDatabase
        pooled_db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        db_neocam.initialize(pooled_db)
        self.app.db = Manager(db_neocam, loop=self.loop)
        ###
        from common.models import event
        from mtkext.db import create_all_tables
        create_all_tables(event, [])
        ###
        # from gps_parse.gps import GPS
        # self.gps = GPS("gps_parse/dmerge_cleared.data")
        ###
        from aiokafka import AIOKafkaConsumer
        self.app.consumer = AIOKafkaConsumer(
            *self.app.conf.KAFKA_TOPIC,
            # group_id=self.app.conf.KAFKA_CONSUMER_GID,
            loop=self.loop,
            bootstrap_servers=self.app.conf.KAFKA_BOOTSTRAP_SERVERS,
            api_version=self.app.conf.KAFKA_API_VERSION,
            metadata_max_age_ms=(self.app.conf.KAFKA_METADATA_SECONDS * 1000),
            security_protocol="SASL_PLAINTEXT",
            sasl_plain_username='opuser',
            sasl_plain_password='Each@6688',
            auto_offset_reset='latest', )
        logger.info(
            f"kafka consumer init : group_id {self.app.conf.KAFKA_CONSUMER_GID} topic {self.app.conf.KAFKA_TOPIC}")
        await self.app.consumer.start()

    async def handle_data(self, topic, key, value):
        value = ujson.loads(value)
        logger.info(f"handle kafka data => {topic, value}")
        if topic == self.app.conf.KAFKA_TOPIC[0]:
            # 从qs里面过滤cid
            qs = value.get("qs", {})
            cid = qs.get('cid')
            if not cid:
                return
            value.update(dict(cid=cid))
            in_obj = peewee_normalize_dict(WebTrafficEvent, value)
            await self.app.db.execute(WebTrafficEvent.insert(in_obj).on_conflict_ignore())
        else:
            # path 里面的 query_string 里面有cid
            path = value.get('path') or ''
            parsed = parse.urlparse(path)
            qs = parse.parse_qs(parsed.query)
            cid_params = qs.get('cid')
            if not cid_params:
                return
            cid = cid_params[0]
            value.update(dict(cid=cid))
            in_obj = peewee_normalize_dict(WxmpShareEvent, value)
            await self.app.db.execute(WxmpShareEvent.insert(in_obj).on_conflict_ignore())


class TaskProc(Processor):

    async def run(self, i):
        logger.info(f"Coroutine-{i} is ready...")
        while not self.stopped:
            try:
                data = await self.consumer.getmany(timeout_ms=500, max_records=10)
                for tp, messages in data.items():
                    topic = tp.topic
                    for msg in messages:
                        k = msg.key.decode("utf-8")
                        v = msg.value.decode("utf-8")
                        await self.handle.handle_data(topic, k, v)
            except Exception as ex:
                logger.exception(ex)
                await asyncio.sleep(0.5)
        logger.info(f"Coroutine-{i} is stopped.")
        await self.release()

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        cls.handle = TaskHandle(cls, loop, cmd_args)
        await cls.handle.load_conf()
        logger.info('init finish!')

    @classmethod
    async def release(cls):
        await cls.db.close()
        cls.redis.close()
        await cls.redis.wait_closed()
        await cls.http.close()
        ###
        await super().release()
        logger.info("finish release-works")
