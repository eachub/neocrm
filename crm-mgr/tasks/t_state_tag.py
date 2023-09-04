import asyncio
import os
import time
from datetime import datetime

from mtkext.proc import Processor
from sanic.log import logger
import sys
sys.path.insert(0, '..')
from biz.member import _build_tag_list
from biz.task import get_tag_qty, fill_those_qty, get_level_qty
from common.models.member import TagInfo, TagLevel
from common.models.analyze import StatTagsQty
from common.utils.misc import init_logger
from common.biz.utils import model_build_key_map

# 标签数量的统计脚本
async def task_gen(app):

    # 读取所有标签和分档数据
    tags = await _build_tag_list(app, None, True)
    all_tags = {}
    folder_tags = {}
    no_folder_tags = {}
    for tag in tags:
        all_tags[tag["tag_id"]] = tag
    levels_info = await app.mgr.execute(TagLevel.select())
    level_info_map = model_build_key_map(levels_info, "level_id", excludes=[])
    for tag in tags:
        crm_id = tag["crm_id"]
        if tag["only_folder"]:
            pass
        else:
            _tags = no_folder_tags.get(crm_id, {})
            _tags[tag["tag_id"]] = tag["bind_field"]
            no_folder_tags[crm_id] = _tags

            parent_tags = []
            _parent_tag = all_tags.get(tag["parent_id"])
            while _parent_tag and _parent_tag["parent_id"] != 0:
                parent_tags.append(_parent_tag)
                _parent_tag = all_tags.get(_parent_tag["parent_id"])

            _parent_tags = folder_tags.get(crm_id, [])
            _parent_tags.extend([x["tag_id"], tag["bind_field"]] for x in parent_tags)
            folder_tags[crm_id] = _parent_tags

    for crm_id, tag_fields in no_folder_tags.items():
        # 2。 计算非目录标签统计
        _qty = await get_tag_qty(app, crm_id, tag_fields)
        await fill_those_qty(app, crm_id, TagInfo, "tag_id", _qty)

        # 3。 计算标签分档的统计
        # 获取tag_id下的level列表
        level_qty = await get_level_qty(app, crm_id, tag_fields)
        await fill_those_qty(app, crm_id, TagLevel, "level_id", level_qty)
        # 写入到历史记录表里
        now_date = datetime.now()
        tdate = now_date.date()
        # tdate = datetime.strftime(now_date, "%Y-%m-%d")
        in_objs = []
        for one in level_qty:
            level_id = one.get('level_id')
            level_name = level_info_map.get(level_id, {}).get("level_name")
            qty = one.get('member_no')
            tag_id = one.get('tag_id')
            # 使用tag_id查询计算规则
            desc = all_tags.get(tag_id, {}).get("desc", [])
            in_objs.append(dict(crm_id=crm_id, level_id=level_id, level_name=level_name,
                                qty=qty, tag_id=tag_id, tdate=tdate, desc=desc))
        if in_objs:
            await app.mgr.execute(StatTagsQty.replace_many(in_objs))
            logger.info('replace level_id qty to t_crm_stat_tags_qty OK')
    return True, 0


class TaskProc(Processor):

    async def run(self, i):
        logger.info(f"Coroutine-{i} is ready...")
        last_time = 0
        while not self.stopped:
            try:
                _now = int(time.time())
                delta_sec = _now - last_time
                is_run = False
                if delta_sec >= 3600:
                    try:
                        flag, result = await task_gen(self)
                        logger.info(f"handle_action: {flag} ==> {result}")
                    except Exception as ex:
                        logger.exception(ex)
                    is_run = True
                if is_run:
                    last_time = _now
                await asyncio.sleep(5)
            except Exception as ex:
                logger.exception(ex)
                await asyncio.sleep(5)
        logger.info(f"Coroutine-{i} is stopped.")

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()

        def update_config(args, path):
            if not os.path.exists(path):
                return
            args.update_config(path)

        update_config(args, f"../common/conf/{cmd_args.env}.py")
        update_config(args, f"../conf/{cmd_args.env}.py")
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        from common.models.base import db_eros_crm
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)
        # 初始化标签的一些基础数据

    @classmethod
    async def release(cls):
        await cls.mgr.close()
        ###
        await super().release()
        logger.info("finish release-works")

    @classmethod
    async def start(cls, loop, cmd_args):
        await cls.init(loop, cmd_args)
        await cls().run(1)
        await cls.release()


if __name__ == "__main__":
    init_logger(f"logs/tag_worker.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="tasker")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test', 'local'))
    cmd_args = parser.parse_args()
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TaskProc.start(loop, cmd_args))
    loop.close()
